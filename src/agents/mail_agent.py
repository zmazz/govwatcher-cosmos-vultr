"""
MailAgent - Sends voting advice emails via SES.
Receives VoteAdvice messages and sends formatted emails to subscribers.
"""

import os
import time
from typing import Dict, Any
from uagents import Agent, Context
from uagents.setup import fund_agent_if_low

from ..models import VoteAdvice
from ..utils.aws_clients import get_dynamodb_helper, get_s3_helper, get_ses_helper
from ..utils.logging import get_logger, set_lambda_request_id, log_lambda_event

logger = get_logger(__name__)

# Agent configuration
AGENT_NAME = "MailAgent"
AGENT_SEED = os.getenv("MAIL_AGENT_SEED", "mail_agent_seed_2024")
AGENT_PORT = int(os.getenv("MAIL_AGENT_PORT", "8004"))
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@govwatcher.com")
SERVICE_URL = os.getenv("SERVICE_URL", "https://govwatcher.com")

# Initialize agent
agent = Agent(
    name=AGENT_NAME,
    seed=AGENT_SEED,
    port=AGENT_PORT,
    endpoint=[f"http://localhost:{AGENT_PORT}/submit"]
)

# Fund agent if needed (for development)
if os.getenv("FUND_AGENT_IF_LOW", "false").lower() == "true":
    fund_agent_if_low(agent.wallet.address())

logger.info(
    "MailAgent initialized",
    agent_address=agent.address,
    wallet_address=agent.wallet.address(),
    from_email=FROM_EMAIL
)


def already_sent(chain: str, proposal_id: int, target_wallet: str) -> bool:
    """Check if email was already sent for this proposal to this wallet."""
    try:
        dynamodb_helper = get_dynamodb_helper()
        subscription = dynamodb_helper.get_subscription(target_wallet)
        
        if not subscription:
            return True  # No subscription found, consider as already sent to prevent spam
        
        last_notified = subscription.get('last_notified', {})
        last_proposal_id = last_notified.get(chain, 0)
        
        return proposal_id <= last_proposal_id
        
    except Exception as e:
        logger.error(
            "Failed to check if already sent",
            error=str(e),
            chain=chain,
            proposal_id=proposal_id,
            wallet=target_wallet
        )
        return True  # Err on the side of caution


def mark_sent(chain: str, proposal_id: int, target_wallet: str) -> bool:
    """Mark that email was sent for this proposal to this wallet."""
    try:
        dynamodb_helper = get_dynamodb_helper()
        return dynamodb_helper.update_last_notified(target_wallet, chain, proposal_id)
    except Exception as e:
        logger.error(
            "Failed to mark as sent",
            error=str(e),
            chain=chain,
            proposal_id=proposal_id,
            wallet=target_wallet
        )
        return False


def format_email_content(advice: VoteAdvice) -> tuple[str, str, str]:
    """Format email subject and body (text and HTML)."""
    
    # Subject
    subject = f"🗳️ Governance Alert: {advice.chain.upper()} Proposal #{advice.proposal_id}"
    
    # Text body
    text_body = f"""
Governance Voting Recommendation - {advice.chain.upper()}

Proposal #{advice.proposal_id} is now in voting period.

RECOMMENDATION: {advice.decision}
Confidence: {advice.confidence:.1%}

ANALYSIS:
{advice.rationale}

---
This recommendation was generated based on your governance policy preferences.

Visit {SERVICE_URL} to manage your subscription or update your preferences.

Best regards,
The GovWatcher Team
""".strip()
    
    # HTML body
    decision_color = {
        'YES': '#28a745',    # Green
        'NO': '#dc3545',     # Red
        'ABSTAIN': '#ffc107' # Yellow
    }.get(advice.decision, '#6c757d')
    
    confidence_bar_width = int(advice.confidence * 100)
    
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Governance Voting Recommendation</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 24px;">🗳️ Governance Alert</h1>
        <p style="color: #e8e8e8; margin: 10px 0 0 0; font-size: 16px;">{advice.chain.upper()} Proposal #{advice.proposal_id}</p>
    </div>
    
    <div style="background: white; padding: 30px; border: 1px solid #ddd; border-radius: 0 0 10px 10px;">
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
            <h2 style="margin: 0 0 15px 0; color: #495057;">Voting Recommendation</h2>
            
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <span style="font-weight: bold; margin-right: 10px;">Decision:</span>
                <span style="background: {decision_color}; color: white; padding: 8px 16px; border-radius: 20px; font-weight: bold;">
                    {advice.decision}
                </span>
            </div>
            
            <div style="margin-bottom: 10px;">
                <span style="font-weight: bold;">Confidence:</span> {advice.confidence:.1%}
            </div>
            
            <div style="background: #e9ecef; height: 8px; border-radius: 4px; overflow: hidden;">
                <div style="background: {decision_color}; height: 100%; width: {confidence_bar_width}%; transition: width 0.3s ease;"></div>
            </div>
        </div>
        
        <div style="margin-bottom: 25px;">
            <h3 style="color: #495057; margin-bottom: 15px;">Analysis</h3>
            <p style="background: #f8f9fa; padding: 20px; border-left: 4px solid {decision_color}; margin: 0; border-radius: 0 4px 4px 0;">
                {advice.rationale}
            </p>
        </div>
        
        <div style="border-top: 1px solid #dee2e6; padding-top: 20px; text-align: center;">
            <p style="color: #6c757d; font-size: 14px; margin-bottom: 15px;">
                This recommendation was generated based on your governance policy preferences.
            </p>
            
            <a href="{SERVICE_URL}" 
               style="background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold;">
                Manage Subscription
            </a>
        </div>
        
        <div style="margin-top: 25px; padding-top: 20px; border-top: 1px solid #dee2e6; text-align: center;">
            <p style="color: #6c757d; font-size: 12px; margin: 0;">
                © 2024 GovWatcher. All rights reserved.<br>
                You received this email because you have an active governance monitoring subscription.
            </p>
        </div>
    </div>
</body>
</html>
""".strip()
    
    return subject, text_body, html_body


async def store_mail_log(advice: VoteAdvice, request_id: str, success: bool, error: str = None):
    """Store mail activity log in S3."""
    try:
        s3_helper = get_s3_helper()
        
        log_entry = {
            "timestamp": int(time.time()),
            "lambda_name": AGENT_NAME,
            "request_id": request_id,
            "event_type": "email_sent",
            "success": success,
            "vote_advice": advice.dict(),
            "error_msg": error
        }
        
        # Generate S3 key
        from datetime import datetime
        dt = datetime.fromtimestamp(log_entry["timestamp"])
        s3_key = f"logs/{dt.year:04d}/{dt.month:02d}/{dt.day:02d}/{log_entry['timestamp']}_{AGENT_NAME}_{request_id}.json"
        
        s3_helper.put_log(log_entry, s3_key)
        
    except Exception as e:
        logger.error(
            "Failed to store mail log in S3",
            error=str(e),
            request_id=request_id
        )


@agent.on_message(model=VoteAdvice)
async def send_email(ctx: Context, sender: str, advice: VoteAdvice):
    """
    Main email handler - sends voting advice emails and enforces one-shot delivery.
    """
    request_id = f"mail_{advice.chain}_{advice.proposal_id}_{advice.target_wallet}_{int(time.time())}"
    set_lambda_request_id(request_id)
    
    logger.info(
        "Email request received",
        chain=advice.chain,
        proposal_id=advice.proposal_id,
        target_email=advice.target_email,
        decision=advice.decision,
        request_id=request_id
    )
    
    try:
        # Check if already sent (enforce one-shot)
        if already_sent(advice.chain, advice.proposal_id, advice.target_wallet):
            logger.info(
                "Email already sent for this proposal",
                chain=advice.chain,
                proposal_id=advice.proposal_id,
                target_wallet=advice.target_wallet,
                request_id=request_id
            )
            
            log_lambda_event(
                logger,
                "email_already_sent",
                AGENT_NAME,
                request_id,
                {
                    "chain": advice.chain,
                    "proposal_id": advice.proposal_id,
                    "target_wallet": advice.target_wallet
                },
                success=True
            )
            
            await store_mail_log(advice, request_id, success=True)
            return
        
        # Check if emails are paused (admin control)
        if os.getenv("PAUSED", "0") == "1":
            logger.warning(
                "Email sending is paused",
                request_id=request_id
            )
            
            log_lambda_event(
                logger,
                "email_paused",
                AGENT_NAME,
                request_id,
                {
                    "chain": advice.chain,
                    "proposal_id": advice.proposal_id,
                    "target_email": advice.target_email
                },
                success=False,
                error_msg="Email sending is administratively paused"
            )
            
            await store_mail_log(advice, request_id, success=False, error="Email sending paused")
            return
        
        # Format email content
        subject, text_body, html_body = format_email_content(advice)
        
        # Send email via SES
        ses_helper = get_ses_helper()
        email_sent = ses_helper.send_vote_advice_email(
            to_email=advice.target_email,
            subject=subject,
            body_text=text_body,
            body_html=html_body
        )
        
        if email_sent:
            # Mark as sent in DynamoDB
            mark_sent(advice.chain, advice.proposal_id, advice.target_wallet)
            
            logger.info(
                "Email sent successfully",
                chain=advice.chain,
                proposal_id=advice.proposal_id,
                target_email=advice.target_email,
                decision=advice.decision,
                request_id=request_id
            )
            
            log_lambda_event(
                logger,
                "email_sent_successfully",
                AGENT_NAME,
                request_id,
                {
                    "chain": advice.chain,
                    "proposal_id": advice.proposal_id,
                    "target_email": advice.target_email,
                    "decision": advice.decision,
                    "confidence": advice.confidence
                },
                success=True
            )
            
            await store_mail_log(advice, request_id, success=True)
            
        else:
            logger.error(
                "Failed to send email",
                chain=advice.chain,
                proposal_id=advice.proposal_id,
                target_email=advice.target_email,
                request_id=request_id
            )
            
            log_lambda_event(
                logger,
                "email_send_failed",
                AGENT_NAME,
                request_id,
                {
                    "chain": advice.chain,
                    "proposal_id": advice.proposal_id,
                    "target_email": advice.target_email
                },
                success=False,
                error_msg="SES email delivery failed"
            )
            
            await store_mail_log(advice, request_id, success=False, error="SES delivery failed")
        
    except Exception as e:
        logger.error(
            "Email processing failed",
            chain=advice.chain,
            proposal_id=advice.proposal_id,
            target_email=advice.target_email,
            error=str(e),
            request_id=request_id
        )
        
        log_lambda_event(
            logger,
            "email_processing_failed",
            AGENT_NAME,
            request_id,
            {
                "chain": advice.chain,
                "proposal_id": advice.proposal_id,
                "target_email": advice.target_email,
                "error": str(e)
            },
            success=False,
            error_msg=str(e)
        )
        
        await store_mail_log(advice, request_id, success=False, error=str(e))


@agent.on_event("startup")
async def startup_handler():
    """Agent startup handler."""
    logger.info(
        "MailAgent starting up",
        agent_address=agent.address,
        wallet_address=agent.wallet.address(),
        from_email=FROM_EMAIL,
        paused=os.getenv("PAUSED", "0") == "1"
    )


@agent.on_event("shutdown")
async def shutdown_handler():
    """Agent shutdown handler."""
    logger.info("MailAgent shutting down")


if __name__ == "__main__":
    # Run agent in standalone mode (development)
    logger.info("Running MailAgent in standalone mode")
    agent.run() 