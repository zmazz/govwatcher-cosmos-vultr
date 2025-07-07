"""
SubscriptionAgent - Handles user registrations and subscription management.
Triggered via API Gateway POST /subscribe -> Lambda proxy -> uAgent.
"""

import os
import time
import json
from typing import Dict, Any
from uagents import Agent, Context, Model
from uagents.setup import fund_agent_if_low

from ..models import SubConfig, SubscriptionRecord
from ..utils.aws_clients import get_dynamodb_helper, get_s3_helper
from ..utils.logging import get_logger, set_lambda_request_id, log_lambda_event

logger = get_logger(__name__)

# Agent configuration
AGENT_NAME = "SubscriptionAgent"
AGENT_SEED = os.getenv("SUBSCRIPTION_AGENT_SEED", "subscription_agent_seed_2024")
AGENT_PORT = int(os.getenv("SUBSCRIPTION_AGENT_PORT", "8001"))
ANNUAL_FEE_FET = int(os.getenv("ANNUAL_FEE_FET", "15"))
EXTRA_CHAIN_FEE_FET = int(os.getenv("EXTRA_CHAIN_FEE_FET", "1"))

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
    "SubscriptionAgent initialized",
    agent_address=agent.address,
    wallet_address=agent.wallet.address(),
    annual_fee=ANNUAL_FEE_FET,
    extra_chain_fee=EXTRA_CHAIN_FEE_FET
)


def calculate_subscription_fee(chains: list[str]) -> int:
    """Calculate total subscription fee based on number of chains."""
    base_chains = 1  # First chain included in annual fee
    extra_chains = max(0, len(chains) - base_chains)
    total_fee = ANNUAL_FEE_FET + (extra_chains * EXTRA_CHAIN_FEE_FET)
    
    logger.debug(
        "Subscription fee calculated",
        chain_count=len(chains),
        extra_chains=extra_chains,
        total_fee=total_fee
    )
    
    return total_fee


def validate_subscription_config(config: SubConfig) -> tuple[bool, str]:
    """Validate subscription configuration."""
    try:
        # Validate email format (already done by Pydantic EmailStr)
        if not config.email:
            return False, "Email address is required"
        
        # Validate chains
        if not config.chains or len(config.chains) == 0:
            return False, "At least one chain must be specified"
        
        # Check for supported chains (could be extended)
        from ..utils.cosmos_client import get_supported_chains
        supported_chains = get_supported_chains()
        
        unsupported_chains = [chain for chain in config.chains if chain not in supported_chains]
        if unsupported_chains:
            return False, f"Unsupported chains: {', '.join(unsupported_chains)}"
        
        # Validate policy blurbs
        if not config.policy_blurbs or len(config.policy_blurbs) == 0:
            return False, "At least one policy preference must be specified"
        
        # Check policy blurb quality
        total_policy_length = sum(len(blurb.strip()) for blurb in config.policy_blurbs)
        if total_policy_length < 50:
            return False, "Policy preferences must be more detailed (minimum 50 characters total)"
        
        return True, "Valid configuration"
        
    except Exception as e:
        logger.error("Configuration validation error", error=str(e))
        return False, f"Configuration validation failed: {str(e)}"


@agent.on_message(model=SubConfig)
async def handle_subscription_request(ctx: Context, sender: str, msg: SubConfig):
    """
    Handle subscription registration requests.
    This handler processes payment and stores subscription data.
    """
    request_id = getattr(ctx, 'request_id', f"req_{int(time.time())}")
    set_lambda_request_id(request_id)
    
    logger.info(
        "Subscription request received",
        sender=sender,
        email=msg.email,
        chains=msg.chains,
        policy_count=len(msg.policy_blurbs),
        request_id=request_id
    )
    
    # Validate configuration
    is_valid, validation_msg = validate_subscription_config(msg)
    if not is_valid:
        logger.warning(
            "Invalid subscription configuration",
            sender=sender,
            error=validation_msg,
            request_id=request_id
        )
        
        log_lambda_event(
            logger,
            "subscription_validation_failed",
            AGENT_NAME,
            request_id,
            {
                "sender": sender,
                "email": msg.email,
                "validation_error": validation_msg
            },
            success=False,
            error_msg=validation_msg
        )
        
        await ctx.send(sender, False)
        return
    
    # Calculate required fee
    required_fee = calculate_subscription_fee(msg.chains)
    
    # Check if payment was received (in a real implementation, this would check the blockchain)
    # For now, we'll simulate payment validation
    payment_received = await validate_payment(ctx, sender, required_fee, request_id)
    
    if not payment_received:
        logger.warning(
            "Insufficient payment",
            sender=sender,
            required_fee=required_fee,
            request_id=request_id
        )
        
        log_lambda_event(
            logger,
            "subscription_payment_failed",
            AGENT_NAME,
            request_id,
            {
                "sender": sender,
                "required_fee": required_fee,
                "chains": msg.chains
            },
            success=False,
            error_msg=f"Payment validation failed. Required: {required_fee} FET"
        )
        
        await ctx.send(sender, False)
        return
    
    # Create subscription record
    current_time = int(time.time())
    expiry_time = current_time + (365 * 24 * 60 * 60)  # 1 year from now
    
    subscription = SubscriptionRecord.from_sub_config(
        wallet=sender,
        config=msg,
        expires=expiry_time,
        created_at=current_time
    )
    
    # Store in DynamoDB
    dynamodb_helper = get_dynamodb_helper()
    subscription_data = subscription.dict()
    
    success = dynamodb_helper.put_subscription(subscription_data)
    
    if success:
        logger.info(
            "Subscription stored successfully",
            sender=sender,
            email=msg.email,
            expires=expiry_time,
            chains=msg.chains,
            request_id=request_id
        )
        
        # Log successful subscription to S3
        log_lambda_event(
            logger,
            "subscription_created",
            AGENT_NAME,
            request_id,
            {
                "sender": sender,
                "email": msg.email,
                "chains": msg.chains,
                "fee_paid": required_fee,
                "expires": expiry_time,
                "policy_blurbs_count": len(msg.policy_blurbs)
            },
            success=True
        )
        
        # Store detailed log in S3
        await store_subscription_log(subscription_data, request_id, success=True)
        
        await ctx.send(sender, True)
    else:
        logger.error(
            "Failed to store subscription",
            sender=sender,
            request_id=request_id
        )
        
        log_lambda_event(
            logger,
            "subscription_storage_failed",
            AGENT_NAME,
            request_id,
            {
                "sender": sender,
                "email": msg.email
            },
            success=False,
            error_msg="Database storage failed"
        )
        
        await store_subscription_log(subscription_data, request_id, success=False, error="DynamoDB storage failed")
        
        await ctx.send(sender, False)


async def validate_payment(ctx: Context, sender: str, required_amount: int, request_id: str) -> bool:
    """
    Validate that the required payment was received.
    In a real implementation, this would check the blockchain for FET token transfers.
    """
    # TODO: Implement actual blockchain payment validation
    # For now, we'll simulate payment validation based on environment or mock data
    
    if os.getenv("SKIP_PAYMENT_VALIDATION", "false").lower() == "true":
        logger.info(
            "Payment validation skipped (development mode)",
            sender=sender,
            required_amount=required_amount,
            request_id=request_id
        )
        return True
    
    # In production, this would:
    # 1. Check the sender's recent transactions
    # 2. Verify a transaction of the required amount was sent to this agent's address
    # 3. Ensure the transaction is confirmed and not already used
    
    # For demonstration, we'll check if the sender has a specific test token
    if sender.endswith("_test") or "test" in sender.lower():
        logger.info(
            "Test payment accepted",
            sender=sender,
            required_amount=required_amount,
            request_id=request_id
        )
        return True
    
    # In a real deployment, implement proper payment validation here
    logger.warning(
        "Payment validation not implemented - rejecting payment",
        sender=sender,
        required_amount=required_amount,
        request_id=request_id
    )
    return False


async def store_subscription_log(subscription_data: Dict[str, Any], request_id: str, success: bool, error: str = None):
    """Store detailed subscription log in S3."""
    try:
        s3_helper = get_s3_helper()
        
        log_entry = {
            "timestamp": int(time.time()),
            "lambda_name": AGENT_NAME,
            "request_id": request_id,
            "event_type": "subscription_request",
            "success": success,
            "subscription_data": subscription_data,
            "error_msg": error
        }
        
        # Generate S3 key
        from datetime import datetime
        dt = datetime.fromtimestamp(log_entry["timestamp"])
        s3_key = f"logs/{dt.year:04d}/{dt.month:02d}/{dt.day:02d}/{log_entry['timestamp']}_{AGENT_NAME}_{request_id}.json"
        
        s3_helper.put_log(log_entry, s3_key)
        
    except Exception as e:
        logger.error(
            "Failed to store subscription log in S3",
            error=str(e),
            request_id=request_id
        )


@agent.on_event("startup")
async def startup_handler():
    """Agent startup handler."""
    logger.info(
        "SubscriptionAgent starting up",
        agent_address=agent.address,
        wallet_address=agent.wallet.address()
    )


@agent.on_event("shutdown")
async def shutdown_handler():
    """Agent shutdown handler."""
    logger.info("SubscriptionAgent shutting down")


if __name__ == "__main__":
    # Run agent in standalone mode (development)
    logger.info("Running SubscriptionAgent in standalone mode")
    agent.run() 