"""
Data models for the Cosmos Gov-Watcher SaaS system.
Based on the build specifications section 3.1.
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
import json


class SubConfig(BaseModel):
    """Subscription configuration model for user registration."""
    email: EmailStr = Field(..., description="User's verified email address")
    chains: List[str] = Field(..., min_length=1, description="List of Cosmos chain IDs to monitor")
    policy_blurbs: List[str] = Field(..., min_length=1, description="User's governance policy preferences")
    
    @field_validator('chains')
    @classmethod
    def validate_chains(cls, v):
        """Ensure chain IDs are non-empty strings."""
        if not all(isinstance(chain, str) and chain.strip() for chain in v):
            raise ValueError("All chain IDs must be non-empty strings")
        return [chain.strip().lower() for chain in v]
    
    @field_validator('policy_blurbs')
    @classmethod
    def validate_policy_blurbs(cls, v):
        """Ensure policy blurbs are meaningful."""
        if not all(isinstance(blurb, str) and len(blurb.strip()) >= 10 for blurb in v):
            raise ValueError("Policy blurbs must be at least 10 characters long")
        return [blurb.strip() for blurb in v]


class NewProposal(BaseModel):
    """New governance proposal detected by WatcherAgent."""
    chain: str = Field(..., description="Cosmos chain ID where proposal was found")
    proposal_id: int = Field(..., ge=1, description="Unique proposal ID on the chain")
    title: str = Field(..., min_length=1, description="Proposal title")
    description: str = Field(..., min_length=10, description="Proposal description/content")
    voting_start_time: Optional[int] = Field(None, description="Voting period start timestamp")
    voting_end_time: Optional[int] = Field(None, description="Voting period end timestamp")
    
    @field_validator('chain')
    @classmethod
    def validate_chain(cls, v):
        """Normalize chain ID."""
        return v.strip().lower()
    
    @field_validator('title', 'description')
    @classmethod
    def validate_text_fields(cls, v):
        """Clean up text fields."""
        return v.strip()


class VoteAdvice(BaseModel):
    """LLM-generated voting recommendation for a proposal."""
    chain: str = Field(..., description="Cosmos chain ID")
    proposal_id: int = Field(..., ge=1, description="Proposal ID")
    target_wallet: str = Field(..., description="Target subscriber wallet address")
    target_email: EmailStr = Field(..., description="Target subscriber email")
    decision: str = Field(..., pattern="^(YES|NO|ABSTAIN)$", description="Voting recommendation")
    rationale: str = Field(..., min_length=50, description="Detailed explanation for the recommendation")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="AI confidence in recommendation")
    
    @field_validator('chain')
    @classmethod
    def validate_chain(cls, v):
        """Normalize chain ID."""
        return v.strip().lower()
    
    @field_validator('decision')
    @classmethod
    def validate_decision(cls, v):
        """Ensure decision is uppercase."""
        return v.upper()


class SubscriptionRecord(BaseModel):
    """DynamoDB record structure for user subscriptions."""
    wallet: str = Field(..., description="User's wallet address (partition key)")
    email: EmailStr = Field(..., description="Verified email address")
    expires: int = Field(..., description="Subscription expiry timestamp")
    chains: List[str] = Field(..., description="Subscribed chain IDs")
    policy: str = Field(..., description="JSON-encoded policy blurbs")
    last_notified: Dict[str, int] = Field(default_factory=dict, description="Last proposal ID notified per chain")
    created_at: int = Field(..., description="Subscription creation timestamp")
    
    @classmethod
    def from_sub_config(cls, wallet: str, config: SubConfig, expires: int, created_at: int) -> 'SubscriptionRecord':
        """Create subscription record from configuration."""
        return cls(
            wallet=wallet,
            email=config.email,
            expires=expires,
            chains=config.chains,
            policy=json.dumps(config.policy_blurbs),
            created_at=created_at
        )
    
    def get_policy_blurbs(self) -> List[str]:
        """Parse policy JSON back to list."""
        try:
            return json.loads(self.policy)
        except json.JSONDecodeError:
            return []
    
    def is_active(self, current_time: int) -> bool:
        """Check if subscription is still active."""
        return self.expires > current_time
    
    def should_notify(self, chain: str, proposal_id: int) -> bool:
        """Check if user should be notified about this proposal."""
        if chain not in self.chains:
            return False
        
        last_notified_id = self.last_notified.get(chain, 0)
        return proposal_id > last_notified_id


class LogEntry(BaseModel):
    """Structured log entry for S3 storage."""
    timestamp: int = Field(..., description="Unix timestamp")
    lambda_name: str = Field(..., description="Lambda function name")
    request_id: str = Field(..., description="AWS request ID")
    event_type: str = Field(..., description="Type of event being logged")
    data: Dict = Field(..., description="Event-specific data")
    success: bool = Field(..., description="Whether the operation succeeded")
    error_msg: Optional[str] = Field(None, description="Error message if operation failed")
    
    def to_s3_key(self) -> str:
        """Generate S3 key for this log entry."""
        from datetime import datetime
        dt = datetime.fromtimestamp(self.timestamp)
        return f"logs/{dt.year:04d}/{dt.month:02d}/{dt.day:02d}/{self.timestamp}_{self.lambda_name}_{self.request_id}.json" 