#!/usr/bin/env python3
"""
AI Adapters for OpenAI, Groq and Llama Model Integration
Provides governance analysis and recommendations for Cosmos proposals
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
import structlog
from datetime import datetime

# Import AI libraries
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

try:
    import groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    groq = None

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False
    AutoTokenizer = None
    AutoModelForCausalLM = None
    torch = None

logger = structlog.get_logger(__name__)

class AIAdapter(ABC):
    """Abstract base class for AI adapters."""
    
    @abstractmethod
    async def analyze_proposal(self, proposal: Dict[str, Any], policy: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a governance proposal and provide recommendations."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the AI service is available."""
        pass

class OpenAIAdapter(AIAdapter):
    """OpenAI GPT adapter for governance analysis."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        
        if OPENAI_AVAILABLE and self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                logger.info("OpenAI adapter initialized successfully")
            except Exception as e:
                logger.error("Failed to initialize OpenAI client", error=str(e))
                self.client = None
        else:
            logger.warning("OpenAI not available - missing API key or library")
    
    def is_available(self) -> bool:
        """Check if OpenAI service is available."""
        return self.client is not None and self.api_key is not None
    
    async def analyze_proposal(self, proposal: Dict[str, Any], policy: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze proposal using OpenAI GPT."""
        if not self.is_available():
            return self._fallback_analysis(proposal, policy)
        
        try:
            # Construct analysis prompt
            prompt = self._build_analysis_prompt(proposal, policy)
            
            # Call OpenAI API
            response = await self._call_openai_api(prompt)
            
            # Parse response
            analysis = self._parse_openai_response(response)
            
            return {
                "provider": "openai",
                "recommendation": analysis.get("recommendation", "ABSTAIN"),
                "confidence": analysis.get("confidence", 50),
                "reasoning": analysis.get("reasoning", "Analysis unavailable"),
                "risk_assessment": analysis.get("risk_assessment", "MEDIUM"),
                "policy_alignment": analysis.get("policy_alignment", 50),
                "economic_impact": analysis.get("economic_impact", "NEUTRAL"),
                "security_implications": analysis.get("security_implications", "MINIMAL"),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Error in OpenAI analysis", error=str(e))
            return self._fallback_analysis(proposal, policy)
    
    def _build_analysis_prompt(self, proposal: Dict[str, Any], policy: Dict[str, Any]) -> str:
        """Build comprehensive analysis prompt for OpenAI."""
        
        # Extract key proposal details for more specific analysis
        title = proposal.get('title', 'Unknown')
        description = proposal.get('description', 'No description')
        chain_name = proposal.get('chain_name', 'Unknown')
        chain_id = proposal.get('chain_id', 'unknown')
        proposal_type = proposal.get('type', 'unknown')
        
        # Determine proposal category for specialized analysis
        proposal_category = self._categorize_proposal(title, description, proposal_type)
        
        # Build chain-specific context
        chain_context = self._get_chain_context(chain_id, chain_name)
        
        # Build specialized analysis based on category
        specialized_prompt = self._get_specialized_analysis_prompt(proposal_category, proposal, policy)
        
        return f"""
        You are an expert blockchain governance analyst specializing in {chain_name} ({chain_id}) ecosystem with deep knowledge of:
        - {chain_name} specific governance mechanisms and economic models
        - {proposal_category} proposal types and their implications
        - Cross-chain governance patterns and risk assessment
        - Regulatory compliance and institutional risk management
        
        CHAIN CONTEXT:
        {chain_context}
        
        PROPOSAL DETAILS:
        Title: {title}
        Description: {description[:500]}{'...' if len(description) > 500 else ''}
        Chain: {chain_name} ({chain_id})
        Type: {proposal_type}
        Category: {proposal_category}
        Status: {proposal.get('status', 'Unknown')}
        Voting End: {proposal.get('voting_end_time', 'Unknown')}
        
        ORGANIZATION POLICY FRAMEWORK:
        Risk Tolerance: {policy.get('risk_tolerance', 'MEDIUM')}
        Security Priority: {policy.get('security_weight', 0.4)} (Weight: {policy.get('security_weight', 0.4):.1%})
        Economic Priority: {policy.get('economic_weight', 0.3)} (Weight: {policy.get('economic_weight', 0.3):.1%})
        Governance Priority: {policy.get('governance_weight', 0.2)} (Weight: {policy.get('governance_weight', 0.2):.1%})
        Community Priority: {policy.get('community_weight', 0.1)} (Weight: {policy.get('community_weight', 0.1):.1%})
        Auto-Vote Threshold: {policy.get('auto_vote_threshold', 80)}%
        
        SPECIALIZED ANALYSIS REQUIREMENTS:
        {specialized_prompt}
        
        CRITICAL ANALYSIS FACTORS:
        1. **Chain-Specific Impact**: How does this proposal affect {chain_name}'s unique features and ecosystem?
        2. **Economic Implications**: Token economics, validator rewards, inflation, fee structures
        3. **Security Assessment**: Network security, upgrade risks, validator set changes
        4. **Governance Evolution**: Voting mechanisms, parameter changes, community governance
        5. **Cross-Chain Effects**: IBC implications, interoperability, ecosystem relationships
        6. **Regulatory Considerations**: Compliance implications, legal risks, regulatory alignment
        7. **Implementation Feasibility**: Technical complexity, timeline, resource requirements
        8. **Stakeholder Impact**: Validators, delegators, developers, users, institutions
        
        Provide your analysis in the following JSON format (respond ONLY with valid JSON):
        {{
            "recommendation": "APPROVE|REJECT|ABSTAIN",
            "confidence": <0-100 integer>,
            "reasoning": "<specific 2-3 sentence reasoning based on proposal content and chain context>",
            "risk_assessment": "LOW|MEDIUM|HIGH",
            "policy_alignment": <0-100 integer>,
            "economic_impact": "POSITIVE|NEGATIVE|NEUTRAL",
            "security_implications": "MINIMAL|MODERATE|SIGNIFICANT",
            "key_considerations": [
                "<chain-specific consideration>",
                "<economic/technical consideration>",
                "<governance/compliance consideration>"
            ],
            "implementation_risk": "LOW|MEDIUM|HIGH",
            "chain_specific_notes": "<notes about {chain_name} specific implications>",
            "timeline_urgency": "LOW|MEDIUM|HIGH"
        }}
        """
    
    def _categorize_proposal(self, title: str, description: str, proposal_type: str) -> str:
        """Categorize proposal for specialized analysis."""
        title_lower = title.lower()
        description_lower = description.lower()
        
        # Security and upgrade related
        if any(keyword in title_lower for keyword in ['upgrade', 'security', 'patch', 'fix', 'vulnerability']):
            return "SECURITY_UPGRADE"
        
        # Economic and parameter changes
        if any(keyword in title_lower for keyword in ['parameter', 'inflation', 'fee', 'reward', 'tax', 'burn']):
            return "ECONOMIC_PARAMETER"
        
        # Governance and voting
        if any(keyword in title_lower for keyword in ['governance', 'voting', 'quorum', 'threshold', 'proposal']):
            return "GOVERNANCE_CHANGE"
        
        # Community pool and funding
        if any(keyword in title_lower for keyword in ['community', 'pool', 'fund', 'grant', 'spend']):
            return "COMMUNITY_FUNDING"
        
        # Validator and staking
        if any(keyword in title_lower for keyword in ['validator', 'staking', 'delegation', 'slash', 'jail']):
            return "VALIDATOR_STAKING"
        
        # IBC and interoperability
        if any(keyword in title_lower for keyword in ['ibc', 'interchain', 'bridge', 'cross-chain']):
            return "INTEROPERABILITY"
        
        # Smart contracts and CosmWasm
        if any(keyword in title_lower for keyword in ['contract', 'cosmwasm', 'wasm', 'smart']):
            return "SMART_CONTRACT"
        
        return "GENERAL_GOVERNANCE"
    
    def _get_chain_context(self, chain_id: str, chain_name: str) -> str:
        """Get chain-specific context for analysis."""
        chain_contexts = {
            'cosmoshub-4': """
            Cosmos Hub is the first blockchain in the Cosmos Network, serving as the central hub for IBC transfers.
            Key characteristics: ATOM token, validator-based PoS, IBC hub, minimal smart contract functionality.
            Governance focus: Network security, IBC protocol upgrades, validator set management, ATOM economics.
            Risk considerations: Central hub status means high security requirements, IBC stability critical.
            """,
            'osmosis-1': """
            Osmosis is the premier DEX and AMM protocol in the Cosmos ecosystem.
            Key characteristics: OSMO token, superfluid staking, AMM pools, governance-driven tokenomics.
            Governance focus: DEX parameters, liquidity incentives, tokenomics, superfluid staking.
            Risk considerations: DeFi protocol risks, MEV considerations, liquidity management.
            """,
            'juno-1': """
            Juno is a smart contract platform focused on CosmWasm and decentralized applications.
            Key characteristics: JUNO token, CosmWasm smart contracts, developer-focused ecosystem.
            Governance focus: Smart contract parameters, developer incentives, network upgrades.
            Risk considerations: Smart contract security, developer ecosystem growth, competition.
            """
        }
        
        return chain_contexts.get(chain_id, f"""
        {chain_name} is a Cosmos SDK-based blockchain with its own governance mechanisms.
        Key characteristics: Cosmos SDK framework, Tendermint consensus, IBC compatibility.
        Governance focus: Network parameters, validator management, protocol upgrades.
        Risk considerations: Standard Cosmos SDK risks, validator centralization, upgrade coordination.
        """)
    
    def _get_specialized_analysis_prompt(self, category: str, proposal: Dict[str, Any], policy: Dict[str, Any]) -> str:
        """Get specialized analysis prompt based on proposal category."""
        prompts = {
            "SECURITY_UPGRADE": """
            Focus on security implications, upgrade risks, and network stability.
            Assess: Code quality, testing coverage, backward compatibility, emergency response.
            Consider: Validator coordination, network downtime, rollback scenarios.
            """,
            "ECONOMIC_PARAMETER": """
            Focus on economic impact, tokenomics, and market effects.
            Assess: Inflation changes, fee structures, reward mechanisms, token supply.
            Consider: Validator economics, delegator returns, market competitiveness.
            """,
            "GOVERNANCE_CHANGE": """
            Focus on governance evolution, voting mechanisms, and democratic processes.
            Assess: Proposal thresholds, voting periods, quorum requirements, participation.
            Consider: Decentralization, voter turnout, governance attacks, representation.
            """,
            "COMMUNITY_FUNDING": """
            Focus on fund allocation, community development, and resource management.
            Assess: Funding purpose, team credentials, deliverables, accountability.
            Consider: Community pool sustainability, ROI, ecosystem development.
            """,
            "VALIDATOR_STAKING": """
            Focus on validator operations, staking mechanics, and network security.
            Assess: Validator requirements, slashing conditions, delegation mechanisms.
            Consider: Centralization risks, validator economics, network security.
            """,
            "INTEROPERABILITY": """
            Focus on cross-chain functionality, IBC protocols, and ecosystem integration.
            Assess: IBC compatibility, bridge security, cross-chain risks.
            Consider: Ecosystem connectivity, interchain security, protocol coordination.
            """,
            "SMART_CONTRACT": """
            Focus on smart contract functionality, CosmWasm integration, and developer tools.
            Assess: Contract security, gas optimization, developer experience.
            Consider: Contract risks, ecosystem growth, developer adoption.
            """
        }
        
        return prompts.get(category, """
        Provide general governance analysis covering security, economic, and governance aspects.
        Assess: Overall proposal merit, implementation feasibility, risk factors.
        Consider: Stakeholder impact, network effects, long-term implications.
        """)
    
    async def _call_openai_api(self, prompt: str) -> str:
        """Call OpenAI API asynchronously."""
        if not self.client:
            raise Exception("OpenAI client not initialized")
        
        try:
            # Use async wrapper for OpenAI client
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model="gpt-4",  # Use GPT-4 for better analysis
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are a professional blockchain governance analyst. Respond only with valid JSON as requested."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,  # Lower temperature for more consistent analysis
                    max_tokens=1500
                )
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error("OpenAI API call failed", error=str(e))
            raise
    
    def _parse_openai_response(self, response: str) -> Dict[str, Any]:
        """Parse OpenAI API response."""
        try:
            # Clean the response and extract JSON
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            # Parse JSON response
            analysis = json.loads(response)
            
            # Validate required fields
            required_fields = ['recommendation', 'confidence', 'reasoning']
            for field in required_fields:
                if field not in analysis:
                    raise ValueError(f"Missing required field: {field}")
            
            # Ensure confidence is within valid range
            analysis['confidence'] = max(0, min(100, int(analysis.get('confidence', 50))))
            
            return analysis
            
        except Exception as e:
            logger.error("Error parsing OpenAI response", error=str(e), response=response[:200])
            return self._fallback_parse(response)
    
    def _fallback_parse(self, response: str) -> Dict[str, Any]:
        """Fallback parsing for non-JSON responses."""
        recommendation = "ABSTAIN"
        confidence = 50
        reasoning = response[:200] if response else "Analysis unavailable"
        
        # Enhanced keyword analysis
        response_lower = response.lower()
        if any(word in response_lower for word in ["approve", "support", "favor", "beneficial"]):
            recommendation = "APPROVE"
            confidence = 70
        elif any(word in response_lower for word in ["reject", "oppose", "against", "harmful", "risky"]):
            recommendation = "REJECT"
            confidence = 70
        
        return {
            "recommendation": recommendation,
            "confidence": confidence,
            "reasoning": reasoning,
            "risk_assessment": "MEDIUM",
            "policy_alignment": 50,
            "economic_impact": "NEUTRAL",
            "security_implications": "MINIMAL"
        }
    
    def _fallback_analysis(self, proposal: Dict[str, Any], policy: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback analysis when OpenAI is unavailable."""
        return {
            "provider": "fallback",
            "recommendation": "ABSTAIN",
            "confidence": 30,
            "reasoning": "AI analysis unavailable - manual review required",
            "risk_assessment": "MEDIUM",
            "policy_alignment": 50,
            "economic_impact": "NEUTRAL",
            "security_implications": "MINIMAL",
            "timestamp": datetime.utcnow().isoformat()
        }

class GroqAdapter(AIAdapter):
    """Groq API adapter for governance analysis."""
    
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.client = None
        
        if GROQ_AVAILABLE and self.api_key:
            try:
                self.client = groq.Groq(api_key=self.api_key)
                logger.info("Groq adapter initialized successfully")
            except Exception as e:
                logger.error("Failed to initialize Groq client", error=str(e))
                self.client = None
        else:
            logger.warning("Groq not available - missing API key or library")
    
    def is_available(self) -> bool:
        """Check if Groq service is available."""
        return self.client is not None
    
    async def analyze_proposal(self, proposal: Dict[str, Any], policy: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze proposal using Groq API."""
        if not self.is_available():
            return self._fallback_analysis(proposal, policy)
        
        try:
            # Construct analysis prompt
            prompt = self._build_analysis_prompt(proposal, policy)
            
            # Call Groq API
            response = await self._call_groq_api(prompt)
            
            # Parse response
            analysis = self._parse_groq_response(response)
            
            return {
                "provider": "groq",
                "recommendation": analysis.get("recommendation", "ABSTAIN"),
                "confidence": analysis.get("confidence", 50),
                "reasoning": analysis.get("reasoning", "Analysis unavailable"),
                "risk_assessment": analysis.get("risk_assessment", "MEDIUM"),
                "policy_alignment": analysis.get("policy_alignment", 50),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Error in Groq analysis", error=str(e))
            return self._fallback_analysis(proposal, policy)
    
    def _build_analysis_prompt(self, proposal: Dict[str, Any], policy: Dict[str, Any]) -> str:
        """Build analysis prompt for Groq."""
        return f"""
        You are an expert governance analyst for Cosmos blockchain ecosystems. 
        Analyze the following proposal against the organization's policy and provide a recommendation.
        
        PROPOSAL:
        Title: {proposal.get('title', 'Unknown')}
        Description: {proposal.get('description', 'No description')}
        Chain: {proposal.get('chain_id', 'Unknown')}
        Type: {proposal.get('type', 'Unknown')}
        
        ORGANIZATION POLICY:
        Risk Tolerance: {policy.get('risk_tolerance', 'MEDIUM')}
        Voting Criteria: {json.dumps(policy.get('voting_criteria', {}), indent=2)}
        
        Provide your analysis in the following JSON format:
        {{
            "recommendation": "APPROVE|REJECT|ABSTAIN",
            "confidence": <0-100>,
            "reasoning": "<detailed reasoning>",
            "risk_assessment": "LOW|MEDIUM|HIGH",
            "policy_alignment": <0-100>
        }}
        """
    
    async def _call_groq_api(self, prompt: str) -> str:
        """Call Groq API asynchronously."""
        if not self.client:
            raise Exception("Groq client not initialized")
        
        try:
            # Use async wrapper for synchronous Groq client
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model="llama3-70b-8192",  # or "mixtral-8x7b-32768"
                    messages=[
                        {"role": "system", "content": "You are a governance analysis expert."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error("Groq API call failed", error=str(e))
            raise
    
    def _parse_groq_response(self, response: str) -> Dict[str, Any]:
        """Parse Groq API response."""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback parsing
                return self._fallback_parse(response)
        except Exception as e:
            logger.error("Error parsing Groq response", error=str(e))
            return self._fallback_parse(response)
    
    def _fallback_parse(self, response: str) -> Dict[str, Any]:
        """Fallback parsing for non-JSON responses."""
        recommendation = "ABSTAIN"
        confidence = 50
        reasoning = response[:500] if response else "Analysis unavailable"
        
        # Simple keyword analysis
        if "approve" in response.lower() or "support" in response.lower():
            recommendation = "APPROVE"
            confidence = 70
        elif "reject" in response.lower() or "oppose" in response.lower():
            recommendation = "REJECT"
            confidence = 70
        
        return {
            "recommendation": recommendation,
            "confidence": confidence,
            "reasoning": reasoning,
            "risk_assessment": "MEDIUM",
            "policy_alignment": 50
        }
    
    def _fallback_analysis(self, proposal: Dict[str, Any], policy: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback analysis when Groq is unavailable."""
        return {
            "provider": "fallback",
            "recommendation": "ABSTAIN",
            "confidence": 30,
            "reasoning": "AI analysis unavailable - manual review required",
            "risk_assessment": "MEDIUM",
            "policy_alignment": 50,
            "timestamp": datetime.utcnow().isoformat()
        }

class LlamaAdapter(AIAdapter):
    """Llama model adapter for governance analysis."""
    
    def __init__(self):
        self.model_name = os.getenv("LLAMA_MODEL", "meta-llama/Llama-2-7b-chat-hf")
        self.tokenizer = None
        self.model = None
        
        if LLAMA_AVAILABLE:
            try:
                self._load_model()
                logger.info("Llama adapter initialized successfully")
            except Exception as e:
                logger.error("Failed to initialize Llama model", error=str(e))
        else:
            logger.warning("Llama not available - missing libraries")
    
    def _load_model(self):
        """Load Llama model and tokenizer."""
        try:
            # For production, consider using quantized models or API endpoints
            # This is a simplified implementation
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # Use CPU for demo - in production, use GPU
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            
            logger.info(f"Loaded Llama model: {self.model_name}")
            
        except Exception as e:
            logger.error("Error loading Llama model", error=str(e))
            raise
    
    def is_available(self) -> bool:
        """Check if Llama model is available."""
        return self.model is not None and self.tokenizer is not None
    
    async def analyze_proposal(self, proposal: Dict[str, Any], policy: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze proposal using Llama model."""
        if not self.is_available():
            return self._fallback_analysis(proposal, policy)
        
        try:
            # Build prompt
            prompt = self._build_llama_prompt(proposal, policy)
            
            # Generate response
            response = await self._generate_llama_response(prompt)
            
            # Parse response
            analysis = self._parse_llama_response(response)
            
            return {
                "provider": "llama",
                "recommendation": analysis.get("recommendation", "ABSTAIN"),
                "confidence": analysis.get("confidence", 50),
                "reasoning": analysis.get("reasoning", "Analysis unavailable"),
                "risk_assessment": analysis.get("risk_assessment", "MEDIUM"),
                "policy_alignment": analysis.get("policy_alignment", 50),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Error in Llama analysis", error=str(e))
            return self._fallback_analysis(proposal, policy)
    
    def _build_llama_prompt(self, proposal: Dict[str, Any], policy: Dict[str, Any]) -> str:
        """Build analysis prompt for Llama."""
        return f"""
        <s>[INST] You are an expert blockchain governance analyst. 
        Analyze this Cosmos governance proposal and provide a recommendation.
        
        PROPOSAL:
        Title: {proposal.get('title', 'Unknown')}
        Description: {proposal.get('description', 'No description')[:1000]}
        Chain: {proposal.get('chain_id', 'Unknown')}
        
        POLICY:
        Risk Tolerance: {policy.get('risk_tolerance', 'MEDIUM')}
        
        Provide recommendation (APPROVE/REJECT/ABSTAIN), confidence (0-100), 
        and brief reasoning. [/INST]
        """
    
    async def _generate_llama_response(self, prompt: str) -> str:
        """Generate response using Llama model."""
        if not self.model or not self.tokenizer:
            raise Exception("Llama model not loaded")
        
        try:
            # Tokenize input
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
            
            # Generate response asynchronously
            loop = asyncio.get_event_loop()
            
            def generate():
                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=256,
                        temperature=0.3,
                        do_sample=True,
                        pad_token_id=self.tokenizer.eos_token_id
                    )
                    
                    response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                    # Remove the prompt from response
                    response = response[len(prompt):].strip()
                    return response
            
            response = await loop.run_in_executor(None, generate)
            return response
            
        except Exception as e:
            logger.error("Llama generation failed", error=str(e))
            raise
    
    def _parse_llama_response(self, response: str) -> Dict[str, Any]:
        """Parse Llama model response."""
        try:
            # Simple parsing - in production, use more sophisticated NLP
            recommendation = "ABSTAIN"
            confidence = 50
            reasoning = response[:500] if response else "Analysis unavailable"
            
            # Extract recommendation
            if "APPROVE" in response.upper():
                recommendation = "APPROVE"
                confidence = 70
            elif "REJECT" in response.upper():
                recommendation = "REJECT"
                confidence = 70
            elif "ABSTAIN" in response.upper():
                recommendation = "ABSTAIN"
                confidence = 60
            
            # Extract confidence if mentioned
            import re
            conf_match = re.search(r'confidence.*?(\d+)', response, re.IGNORECASE)
            if conf_match:
                confidence = min(100, max(0, int(conf_match.group(1))))
            
            return {
                "recommendation": recommendation,
                "confidence": confidence,
                "reasoning": reasoning,
                "risk_assessment": "MEDIUM",
                "policy_alignment": confidence
            }
            
        except Exception as e:
            logger.error("Error parsing Llama response", error=str(e))
            return {
                "recommendation": "ABSTAIN",
                "confidence": 30,
                "reasoning": response[:500] if response else "Parsing error",
                "risk_assessment": "MEDIUM",
                "policy_alignment": 50
            }
    
    def _fallback_analysis(self, proposal: Dict[str, Any], policy: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback analysis when Llama is unavailable."""
        return {
            "provider": "fallback",
            "recommendation": "ABSTAIN",
            "confidence": 30,
            "reasoning": "Llama model unavailable - manual review required",
            "risk_assessment": "MEDIUM",
            "policy_alignment": 50,
            "timestamp": datetime.utcnow().isoformat()
        }

class HybridAIAnalyzer:
    """Hybrid analyzer that uses OpenAI, Groq and Llama for comprehensive analysis."""
    
    def __init__(self):
        self.openai_adapter = OpenAIAdapter()
        self.groq_adapter = GroqAdapter()
        self.llama_adapter = LlamaAdapter()
        
        # Priority order: OpenAI -> Groq -> Llama -> Fallback
        self.adapters = [
            ("openai", self.openai_adapter),
            ("groq", self.groq_adapter),
            ("llama", self.llama_adapter)
        ]
        
        logger.info(f"HybridAIAnalyzer initialized with adapters: {[name for name, adapter in self.adapters if adapter.is_available()]}")
        
    async def analyze_governance_proposal(
        self,
        chain_id: str,
        proposal_id: str,
        title: str,
        description: str,
        organization_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze governance proposal with hybrid AI approach."""
        proposal_data = {
            "chain_id": chain_id,
            "proposal_id": proposal_id,
            "title": title,
            "description": description
        }
        
        policy_data = organization_preferences or {}
        
        return await self.analyze_proposal(proposal_data, policy_data)
        
    async def analyze_proposal(self, proposal: Dict[str, Any], policy: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze proposal using available AI services with intelligent fallback."""
        
        # Try primary analysis with OpenAI first
        if self.openai_adapter.is_available():
            try:
                logger.info("Using OpenAI for primary analysis")
                result = await self.openai_adapter.analyze_proposal(proposal, policy)
                result["analysis_method"] = "primary_openai"
                return result
            except Exception as e:
                logger.warning(f"OpenAI analysis failed, falling back: {e}")
        
        # Fallback to Groq if OpenAI unavailable
        if self.groq_adapter.is_available():
            try:
                logger.info("Using Groq for fallback analysis")
                result = await self.groq_adapter.analyze_proposal(proposal, policy)
                result["analysis_method"] = "fallback_groq"
                return result
            except Exception as e:
                logger.warning(f"Groq analysis failed, trying Llama: {e}")
        
        # Final fallback to Llama
        if self.llama_adapter.is_available():
            try:
                logger.info("Using Llama for final fallback analysis")
                result = await self.llama_adapter.analyze_proposal(proposal, policy)
                result["analysis_method"] = "fallback_llama"
                return result
            except Exception as e:
                logger.warning(f"Llama analysis failed: {e}")
        
        # Ultimate fallback - rule-based analysis
        logger.warning("All AI services unavailable, using rule-based analysis")
        return self._rule_based_analysis(proposal, policy)
    
    async def get_multi_provider_analysis(self, proposal: Dict[str, Any], policy: Dict[str, Any]) -> Dict[str, Any]:
        """Get analysis from multiple providers for comparison (when needed for critical decisions)."""
        results = []
        
        # Run all available analyses concurrently
        tasks = []
        for name, adapter in self.adapters:
            if adapter.is_available():
                tasks.append(self._safe_analyze(name, adapter, proposal, policy))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            valid_results = [r for r in results if isinstance(r, dict)]
            
            if valid_results:
                return self._combine_analyses(valid_results, proposal, policy)
        
        return self._rule_based_analysis(proposal, policy)
    
    async def _safe_analyze(self, name: str, adapter: AIAdapter, proposal: Dict[str, Any], policy: Dict[str, Any]) -> Dict[str, Any]:
        """Safely run analysis with error handling."""
        try:
            result = await adapter.analyze_proposal(proposal, policy)
            result["provider"] = name
            return result
        except Exception as e:
            logger.error(f"Analysis failed for {name}: {e}")
            return {"provider": name, "error": str(e)}
    
    def _combine_analyses(self, results: List[Dict[str, Any]], proposal: Dict[str, Any], policy: Dict[str, Any]) -> Dict[str, Any]:
        """Combine multiple AI analyses into a single recommendation."""
        valid_results = [r for r in results if "error" not in r]
        
        if not valid_results:
            return self._rule_based_analysis(proposal, policy)
        
        # Weight recommendations by confidence and provider reliability
        provider_weights = {"openai": 1.0, "groq": 0.8, "llama": 0.6}
        
        weighted_votes = {"APPROVE": 0, "REJECT": 0, "ABSTAIN": 0}
        total_weight = 0
        confidences = []
        reasoning_parts = []
        
        for result in valid_results:
            provider = result.get("provider", "unknown")
            weight = provider_weights.get(provider, 0.5)
            confidence = result.get("confidence", 50)
            recommendation = result.get("recommendation", "ABSTAIN")
            
            # Weight the vote by provider reliability and confidence
            vote_weight = weight * (confidence / 100)
            weighted_votes[recommendation] += vote_weight
            total_weight += weight
            
            confidences.append(confidence)
            reasoning_parts.append(f"{provider.upper()}: {result.get('reasoning', '')}")
        
        # Determine final recommendation
        final_recommendation = max(weighted_votes, key=weighted_votes.get)
        
        # Calculate weighted average confidence
        avg_confidence = sum(confidences) / len(confidences) if confidences else 50
        
        # Combine reasoning
        combined_reasoning = " | ".join(reasoning_parts)
        
        return {
            "provider": "hybrid_multi",
            "recommendation": final_recommendation,
            "confidence": int(avg_confidence),
            "reasoning": combined_reasoning,
            "risk_assessment": self._assess_combined_risk(valid_results),
            "policy_alignment": int(avg_confidence),
            "vote_distribution": weighted_votes,
            "individual_analyses": valid_results,
            "analysis_method": "multi_provider_consensus",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _assess_combined_risk(self, results: List[Dict[str, Any]]) -> str:
        """Assess combined risk from multiple analyses."""
        risk_levels = [r.get("risk_assessment", "MEDIUM") for r in results]
        risk_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        
        for risk in risk_levels:
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
        
        # If any analysis says HIGH risk, consider it HIGH
        if risk_counts["HIGH"] > 0:
            return "HIGH"
        elif risk_counts["MEDIUM"] > risk_counts["LOW"]:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _rule_based_analysis(self, proposal: Dict[str, Any], policy: Dict[str, Any]) -> Dict[str, Any]:
        """Rule-based analysis when AI services are unavailable."""
        title = proposal.get("title", "").lower()
        description = proposal.get("description", "").lower()
        chain_id = proposal.get("chain_id", "")
        
        # Basic keyword analysis
        risk_keywords = ["upgrade", "parameter", "change", "migration", "fork"]
        positive_keywords = ["security", "fix", "improvement", "optimization"]
        negative_keywords = ["increase", "fee", "tax", "inflation", "dilution"]
        
        recommendation = "ABSTAIN"
        confidence = 40
        reasoning = "Rule-based analysis due to AI unavailability. "
        
        # Check for risk indicators
        has_risk = any(keyword in title or keyword in description for keyword in risk_keywords)
        has_positive = any(keyword in title or keyword in description for keyword in positive_keywords)
        has_negative = any(keyword in title or keyword in description for keyword in negative_keywords)
        
        # Apply policy-based rules
        risk_tolerance = policy.get("risk_tolerance", "MEDIUM")
        
        if has_positive and not has_negative:
            recommendation = "APPROVE"
            confidence = 60
            reasoning += "Proposal contains positive indicators. "
        elif has_negative and risk_tolerance == "LOW":
            recommendation = "REJECT"
            confidence = 65
            reasoning += "Proposal contains risk indicators incompatible with low risk tolerance. "
        elif has_risk and risk_tolerance == "HIGH":
            recommendation = "APPROVE"
            confidence = 55
            reasoning += "Proposal involves changes but organization has high risk tolerance. "
        
        reasoning += "Manual review recommended for comprehensive analysis."
        
        return {
            "provider": "rule_based",
            "recommendation": recommendation,
            "confidence": confidence,
            "reasoning": reasoning,
            "risk_assessment": "MEDIUM",
            "policy_alignment": confidence,
            "analysis_method": "rule_based_fallback",
            "timestamp": datetime.utcnow().isoformat()
        } 