"""
AnalysisAgent - Processes proposals with LLM and generates voting recommendations.
Receives NewProposal messages and generates VoteAdvice for each active subscriber.
"""

import os
import time
import json
from typing import List, Dict, Any, Optional
from uagents import Agent, Context
from uagents.setup import fund_agent_if_low
import asyncio

from ..models import NewProposal, VoteAdvice, SubscriptionRecord
from ..ai_adapters import GroqAdapter, LlamaAdapter, HybridAIAnalyzer
from ..utils.aws_clients import get_dynamodb_helper, get_s3_helper, get_secrets_helper
from ..utils.logging import get_logger, set_lambda_request_id, log_lambda_event

logger = get_logger(__name__)

# Agent configuration
AGENT_NAME = "AnalysisAgent"
AGENT_SEED = os.getenv("ANALYSIS_AGENT_SEED", "analysis_agent_seed_2024")
AGENT_PORT = int(os.getenv("ANALYSIS_AGENT_PORT", "8003"))
MAIL_AGENT_ADDRESS = os.getenv("MAIL_AGENT_ADDRESS", "")

# Initialize agent
agent = Agent(
    name=AGENT_NAME,
    seed=AGENT_SEED,
    port=AGENT_PORT,
    endpoint=[f"http://localhost:{AGENT_PORT}/submit"]
)

# Initialize AI analyzers
ai_analyzer = HybridAIAnalyzer()

# Fund agent if needed (for development)
if os.getenv("FUND_AGENT_IF_LOW", "false").lower() == "true":
    fund_agent_if_low(agent.wallet.address())

logger.info(
    "AnalysisAgent initialized",
    agent_address=agent.address,
    wallet_address=agent.wallet.address(),
    ai_analyzer=type(ai_analyzer).__name__,
    mail_agent_address=MAIL_AGENT_ADDRESS
)


async def analyze_with_ai(proposal: NewProposal, policy_blurbs: List[str], request_id: str) -> Optional[Dict[str, Any]]:
    """Analyze proposal using the hybrid AI analyzer."""
    try:
        # Build prompt
        prompt = build_analysis_prompt(proposal, policy_blurbs)
        
        logger.info(
            "Sending proposal to AI for analysis",
            chain=proposal.chain,
            proposal_id=proposal.proposal_id,
            analyzer=type(ai_analyzer).__name__,
            request_id=request_id
        )
        
        # Use the hybrid AI analyzer
        response = await ai_analyzer.analyze_governance_proposal(
            chain_id=proposal.chain,
            proposal_id=str(proposal.proposal_id),
            title=proposal.title,
            description=proposal.description,
            organization_preferences={"policy_blurbs": policy_blurbs}
        )
        
        if not response or not response.get("success"):
            logger.error("AI analysis failed", request_id=request_id, response=response)
            return None
        
        # Extract recommendation details
        recommendation = response.get("recommendation", "ABSTAIN")
        confidence = response.get("confidence", 0.5)
        reasoning = response.get("reasoning", "Analysis completed with AI system.")
        
        # Map recommendation to expected format
        if recommendation.upper() in ["APPROVE", "YES", "SUPPORT"]:
            decision = "YES"
        elif recommendation.upper() in ["REJECT", "NO", "OPPOSE"]:
            decision = "NO"
        else:
            decision = "ABSTAIN"
        
        return {
            'decision': decision,
            'confidence': float(confidence),
            'rationale': reasoning
        }
        
    except Exception as e:
        logger.error(
            "AI analysis failed",
            error=str(e),
            chain=proposal.chain,
            proposal_id=proposal.proposal_id,
            request_id=request_id
        )
        return None


def build_analysis_prompt(proposal: NewProposal, policy_blurbs: List[str]) -> str:
    """Build the prompt for LLM analysis based on proposal and user policy."""
    policy_text = "\n".join([f"- {blurb}" for blurb in policy_blurbs])
    
    prompt = f"""You are a governance analyst for {proposal.chain} blockchain proposals. 

Analyze the following governance proposal and provide a voting recommendation based on the user's policy preferences.

**PROPOSAL DETAILS:**
Chain: {proposal.chain}
Proposal ID: {proposal.proposal_id}
Title: {proposal.title}
Description: {proposal.description}

**USER'S GOVERNANCE POLICY:**
{policy_text}

**INSTRUCTIONS:**
1. Analyze the proposal against the user's policy preferences
2. Consider the technical implications, economic impact, and alignment with stated policies
3. Provide a clear voting recommendation: YES, NO, or ABSTAIN
4. Give a detailed rationale (minimum 100 words) explaining your reasoning
5. Be objective and focus on how the proposal aligns with the user's stated preferences

**RESPONSE FORMAT:**
Decision: [YES/NO/ABSTAIN]
Confidence: [0.0-1.0]
Rationale: [Detailed explanation of your reasoning]

Respond with just the decision, confidence, and rationale - no additional formatting."""

    return prompt


# Removed - now using analyze_with_ai function above


def parse_llm_response(content: str, proposal: NewProposal, request_id: str) -> Optional[Dict[str, Any]]:
    """Parse LLM response into structured format."""
    try:
        lines = content.split('\n')
        decision = None
        confidence = 0.5
        rationale = ""
        
        current_section = None
        rationale_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.lower().startswith('decision:'):
                decision = line.split(':', 1)[1].strip().upper()
            elif line.lower().startswith('confidence:'):
                try:
                    confidence = float(line.split(':', 1)[1].strip())
                    confidence = max(0.0, min(1.0, confidence))  # Clamp to 0-1
                except ValueError:
                    confidence = 0.5
            elif line.lower().startswith('rationale:'):
                current_section = 'rationale'
                rationale_text = line.split(':', 1)[1].strip()
                if rationale_text:
                    rationale_lines.append(rationale_text)
            elif current_section == 'rationale':
                rationale_lines.append(line)
        
        rationale = ' '.join(rationale_lines).strip()
        
        # Validate decision
        if decision not in ['YES', 'NO', 'ABSTAIN']:
            logger.warning(
                "Invalid decision from LLM, defaulting to ABSTAIN",
                original_decision=decision,
                request_id=request_id
            )
            decision = 'ABSTAIN'
        
        # Ensure minimum rationale length
        if len(rationale) < 50:
            rationale += " Based on analysis of the proposal content and alignment with user policies."
        
        return {
            'decision': decision,
            'confidence': confidence,
            'rationale': rationale
        }
        
    except Exception as e:
        logger.error(
            "Failed to parse LLM response",
            error=str(e),
            content=content[:200],
            request_id=request_id
        )
        return {
            'decision': 'ABSTAIN',
            'confidence': 0.0,
            'rationale': 'Analysis failed due to parsing error. Recommending abstention for safety.'
        }


async def get_active_subscribers(chain: str, current_time: int) -> List[Dict[str, Any]]:
    """Get all active subscribers for a specific chain."""
    try:
        dynamodb_helper = get_dynamodb_helper()
        return dynamodb_helper.get_active_subscriptions_for_chain(chain, current_time)
    except Exception as e:
        logger.error("Failed to fetch active subscribers", chain=chain, error=str(e))
        return []


async def store_analysis_log(
    proposal: NewProposal, 
    analyses: List[Dict[str, Any]], 
    request_id: str, 
    success: bool, 
    error: str = None
):
    """Store analysis activity log in S3."""
    try:
        s3_helper = get_s3_helper()
        
        log_entry = {
            "timestamp": int(time.time()),
            "lambda_name": AGENT_NAME,
            "request_id": request_id,
            "event_type": "proposal_analysis",
            "proposal": proposal.dict(),
            "analyses_generated": len(analyses),
            "success": success,
            "analyses": analyses,
            "error_msg": error
        }
        
        # Generate S3 key
        from datetime import datetime
        dt = datetime.fromtimestamp(log_entry["timestamp"])
        s3_key = f"logs/{dt.year:04d}/{dt.month:02d}/{dt.day:02d}/{log_entry['timestamp']}_{AGENT_NAME}_{request_id}.json"
        
        s3_helper.put_log(log_entry, s3_key)
        
    except Exception as e:
        logger.error(
            "Failed to store analysis log in S3",
            error=str(e),
            request_id=request_id
        )


@agent.on_message(model=NewProposal)
async def analyze_proposal(ctx: Context, sender: str, proposal: NewProposal):
    """
    Main analysis handler - processes proposals and generates vote advice for all subscribers.
    """
    request_id = f"analysis_{proposal.chain}_{proposal.proposal_id}_{int(time.time())}"
    set_lambda_request_id(request_id)
    
    logger.info(
        "Proposal analysis started",
        chain=proposal.chain,
        proposal_id=proposal.proposal_id,
        title=proposal.title[:100],
        sender=sender,
        request_id=request_id
    )
    
    try:
        current_time = int(time.time())
        
        # Get active subscribers for this chain
        subscribers = await get_active_subscribers(proposal.chain, current_time)
        
        if not subscribers:
            logger.info(
                "No active subscribers for chain",
                chain=proposal.chain,
                proposal_id=proposal.proposal_id,
                request_id=request_id
            )
            
            log_lambda_event(
                logger,
                "no_subscribers_found",
                AGENT_NAME,
                request_id,
                {
                    "chain": proposal.chain,
                    "proposal_id": proposal.proposal_id
                },
                success=True
            )
            
            await store_analysis_log(proposal, [], request_id, success=True)
            return
        
        logger.info(
            "Processing proposal for subscribers",
            chain=proposal.chain,
            proposal_id=proposal.proposal_id,
            subscriber_count=len(subscribers),
            request_id=request_id
        )
        
        analyses_generated = []
        
        # Process each subscriber
        for subscriber in subscribers:
            try:
                # Parse subscriber data
                wallet = subscriber['wallet']
                email = subscriber['email']
                policy_blurbs = json.loads(subscriber.get('policy', '[]'))
                
                # Check if we should notify this subscriber
                last_notified = subscriber.get('last_notified', {})
                if proposal.chain in last_notified:
                    last_proposal_id = last_notified[proposal.chain]
                    if proposal.proposal_id <= last_proposal_id:
                        logger.debug(
                            "Subscriber already notified of this proposal",
                            wallet=wallet,
                            chain=proposal.chain,
                            proposal_id=proposal.proposal_id,
                            request_id=request_id
                        )
                        continue
                
                # Generate analysis using AI
                analysis = await analyze_with_ai(proposal, policy_blurbs, request_id)
                
                if not analysis:
                    logger.error(
                        "Failed to generate analysis for subscriber",
                        wallet=wallet,
                        chain=proposal.chain,
                        proposal_id=proposal.proposal_id,
                        request_id=request_id
                    )
                    continue
                
                # Create VoteAdvice message
                vote_advice = VoteAdvice(
                    chain=proposal.chain,
                    proposal_id=proposal.proposal_id,
                    target_wallet=wallet,
                    target_email=email,
                    decision=analysis['decision'],
                    rationale=analysis['rationale'],
                    confidence=analysis['confidence']
                )
                
                # Send to MailAgent if configured
                if MAIL_AGENT_ADDRESS:
                    await ctx.send(MAIL_AGENT_ADDRESS, vote_advice)
                    analyses_generated.append({
                        'wallet': wallet,
                        'email': email,
                        'decision': analysis['decision'],
                        'confidence': analysis['confidence']
                    })
                    
                    logger.info(
                        "Vote advice sent to mail agent",
                        wallet=wallet,
                        chain=proposal.chain,
                        proposal_id=proposal.proposal_id,
                        decision=analysis['decision'],
                        request_id=request_id
                    )
                else:
                    logger.warning(
                        "Mail agent address not configured",
                        request_id=request_id
                    )
                
            except Exception as e:
                logger.error(
                    "Failed to process subscriber",
                    wallet=subscriber.get('wallet', 'unknown'),
                    error=str(e),
                    request_id=request_id
                )
                continue
        
        logger.info(
            "Proposal analysis completed",
            chain=proposal.chain,
            proposal_id=proposal.proposal_id,
            analyses_generated=len(analyses_generated),
            request_id=request_id
        )
        
        # Log successful completion
        log_lambda_event(
            logger,
            "proposal_analysis_completed",
            AGENT_NAME,
            request_id,
            {
                "chain": proposal.chain,
                "proposal_id": proposal.proposal_id,
                "subscribers_processed": len(subscribers),
                "analyses_generated": len(analyses_generated)
            },
            success=True
        )
        
        await store_analysis_log(proposal, analyses_generated, request_id, success=True)
        
    except Exception as e:
        logger.error(
            "Proposal analysis failed",
            chain=proposal.chain,
            proposal_id=proposal.proposal_id,
            error=str(e),
            request_id=request_id
        )
        
        log_lambda_event(
            logger,
            "proposal_analysis_failed",
            AGENT_NAME,
            request_id,
            {
                "chain": proposal.chain,
                "proposal_id": proposal.proposal_id,
                "error": str(e)
            },
            success=False,
            error_msg=str(e)
        )
        
        await store_analysis_log(proposal, [], request_id, success=False, error=str(e))


@agent.on_event("startup")
async def startup_handler():
    """Agent startup handler."""
    logger.info(
        "AnalysisAgent starting up",
        agent_address=agent.address,
        wallet_address=agent.wallet.address(),
        ai_analyzer=type(ai_analyzer).__name__
    )
    
    # Test AI analyzer connections
    groq_available = ai_analyzer.groq_adapter.is_available()
    llama_available = ai_analyzer.llama_adapter.is_available()
    
    logger.info(
        "AI analyzers status",
        groq_available=groq_available,
        llama_available=llama_available
    )
    
    if not groq_available and not llama_available:
        logger.error("No AI analyzers available - analysis will fail")
    
    # Validate mail agent address
    if not MAIL_AGENT_ADDRESS:
        logger.warning("Mail agent address not configured - vote advice will not be sent")


@agent.on_event("shutdown")
async def shutdown_handler():
    """Agent shutdown handler."""
    logger.info("AnalysisAgent shutting down")


if __name__ == "__main__":
    logger.info("Running AnalysisAgent in standalone mode")
    agent.run() 