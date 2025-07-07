"""
On-Chain Payment Agent for Cosmos GRC Co-Pilot
Handles FET token payments and integrates with web dashboard
"""

import asyncio
import json
import os
import time
from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime, timedelta

from uagents import Agent, Context, Model
from uagents.network import wait_for_tx_to_complete
import requests
import structlog

# Configure logging
logger = structlog.get_logger(__name__)

# Load configuration
config_path = os.path.join(os.path.dirname(__file__), 'onchain-config.json')
with open(config_path, 'r') as f:
    config = json.load(f)

# Initialize payment agent
payment_agent = Agent(
    name=config['agents']['payment']['name'],
    seed=config['agents']['payment']['private_key'],
    port=config['agents']['payment']['port'],
    endpoint=config['agents']['payment']['endpoints']
)

class PaymentRequest(Model):
    """Request for FET token payment processing"""
    organization_name: str
    contact_email: str
    subscription_tier: str  # basic, enterprise
    chains: List[str]
    payment_amount: float
    payment_tx_hash: str
    wallet_address: str
    metadata: Dict[str, Any] = {}

class PaymentResponse(Model):
    """Response from payment processing"""
    success: bool
    message: str
    subscription_id: str = ""
    payment_verified: bool = False
    expires_at: str = ""
    dashboard_url: str = ""
    agent_addresses: Dict[str, str] = {}
    access_token: str = ""

class SubscriptionStatus(Model):
    """Subscription status query"""
    wallet_address: str
    email: str = ""

class SubscriptionStatusResponse(Model):
    """Subscription status response"""
    active: bool
    subscription_id: str = ""
    tier: str = ""
    chains: List[str] = []
    expires_at: str = ""
    payment_method: str = ""

@payment_agent.on_message(model=PaymentRequest, replies=PaymentResponse)
async def handle_payment(ctx: Context, sender: str, msg: PaymentRequest):
    """Handle FET token payment and subscription creation"""
    
    try:
        logger.info(
            "Processing FET payment request",
            organization=msg.organization_name,
            email=msg.contact_email,
            tier=msg.subscription_tier,
            amount=msg.payment_amount,
            tx_hash=msg.payment_tx_hash
        )
        
        # Calculate expected payment amount
        base_fee = config['pricing']['annual_subscription_fet']
        if msg.subscription_tier == "enterprise":
            base_fee = config['pricing']['enterprise_tier_fet']
        
        additional_chains = max(0, len(msg.chains) - 1)
        total_fee = base_fee + (additional_chains * config['pricing']['additional_chain_fet'])
        
        # Verify payment amount
        if msg.payment_amount < total_fee:
            await ctx.send(sender, PaymentResponse(
                success=False,
                message=f"Insufficient payment. Expected {total_fee} FET, received {msg.payment_amount} FET"
            ))
            return
        
        # Verify payment on blockchain
        payment_valid = await verify_fet_payment(
            tx_hash=msg.payment_tx_hash,
            expected_amount=total_fee,
            recipient_address=payment_agent.address,
            sender_address=msg.wallet_address
        )
        
        if not payment_valid:
            await ctx.send(sender, PaymentResponse(
                success=False,
                message="Payment verification failed. Transaction not found or invalid.",
                payment_verified=False
            ))
            return
        
        # Create subscription in web dashboard
        subscription_data = {
            "organization_name": msg.organization_name,
            "contact_email": msg.contact_email,
            "chains": msg.chains, 
            "subscription_tier": msg.subscription_tier,
            "payment_verified": True,
            "payment_amount": total_fee,
            "payment_tx_hash": msg.payment_tx_hash,
            "payment_method": "blockchain",
            "wallet_address": msg.wallet_address,
            "sender_address": sender,
            "metadata": msg.metadata
        }
        
        dashboard_response = await create_dashboard_subscription(subscription_data)
        
        if dashboard_response.get('success'):
            # Return success with agent addresses and access token
            agent_addresses = {
                "payment": payment_agent.address,
                "subscription": config['agents']['subscription']['address'],
                "watcher_cosmoshub": config['agents']['watcher_cosmoshub']['address'],
                "watcher_osmosis": config['agents']['watcher_osmosis']['address'], 
                "integration": config['agents']['integration']['address']
            }
            
            await ctx.send(sender, PaymentResponse(
                success=True,
                message="Subscription activated successfully! Check your email for dashboard access.",
                subscription_id=dashboard_response.get('subscription_id', ''),
                payment_verified=True,
                expires_at=dashboard_response.get('expires_at', ''),
                dashboard_url=config['integration']['dashboard_url'],
                agent_addresses=agent_addresses,
                access_token=dashboard_response.get('access_token', '')
            ))
            
            logger.info(
                "Payment processed successfully",
                subscription_id=dashboard_response.get('subscription_id'),
                organization=msg.organization_name
            )
        else:
            await ctx.send(sender, PaymentResponse(
                success=False,
                message="Payment verified but subscription creation failed. Please contact support.",
                payment_verified=True
            ))
            
    except Exception as e:
        logger.error("Payment processing error", error=str(e))
        await ctx.send(sender, PaymentResponse(
            success=False,
            message="Internal error processing payment. Please try again."
        ))

@payment_agent.on_message(model=SubscriptionStatus, replies=SubscriptionStatusResponse)
async def handle_subscription_status(ctx: Context, sender: str, msg: SubscriptionStatus):
    """Handle subscription status queries"""
    
    try:
        # Query dashboard for subscription status
        status_data = await get_subscription_status(msg.wallet_address, msg.email)
        
        if status_data:
            await ctx.send(sender, SubscriptionStatusResponse(
                active=status_data.get('active', False),
                subscription_id=status_data.get('subscription_id', ''),
                tier=status_data.get('tier', ''),
                chains=status_data.get('chains', []),
                expires_at=status_data.get('expires_at', ''),
                payment_method=status_data.get('payment_method', '')
            ))
        else:
            await ctx.send(sender, SubscriptionStatusResponse(
                active=False,
                subscription_id='',
                tier='',
                chains=[],
                expires_at='',
                payment_method=''
            ))
            
    except Exception as e:
        logger.error("Subscription status query error", error=str(e))
        await ctx.send(sender, SubscriptionStatusResponse(
            active=False,
            subscription_id='',
            tier='',
            chains=[],
            expires_at='',
            payment_method=''
        ))

async def verify_fet_payment(
    tx_hash: str, 
    expected_amount: float, 
    recipient_address: str,
    sender_address: str
) -> bool:
    """Verify FET payment transaction on Fetch.ai blockchain"""
    try:
        # Query Fetch.ai blockchain for transaction details
        rpc_url = config.get('blockchain', {}).get('rpc_url', 'https://rpc-fetchhub.fetch.ai')
        
        # Get transaction details
        response = requests.get(f"{rpc_url}/tx?hash={tx_hash}", timeout=30)
        if response.status_code != 200:
            logger.warning("Transaction not found", tx_hash=tx_hash)
            return False
            
        tx_data = response.json()
        
        # Verify transaction was successful
        if tx_data.get('result', {}).get('tx_result', {}).get('code', 1) != 0:
            logger.warning("Transaction failed", tx_hash=tx_hash)
            return False
            
        # Check transaction events for transfer
        events = tx_data.get('result', {}).get('tx_result', {}).get('events', [])
        
        for event in events:
            if event.get('type') == 'transfer':
                attributes = {attr['key']: attr['value'] for attr in event.get('attributes', [])}
                
                # Check recipient, sender, and amount
                recipient_match = attributes.get('recipient') == recipient_address
                sender_match = attributes.get('sender') == sender_address
                
                # Convert amount from afet to FET (1 FET = 1e18 afet)
                amount_str = attributes.get('amount', '0').replace('afet', '')
                try:
                    amount_afet = float(amount_str)
                    amount_fet = amount_afet / 1e18
                except (ValueError, TypeError):
                    continue
                
                amount_sufficient = amount_fet >= expected_amount
                
                if recipient_match and sender_match and amount_sufficient:
                    logger.info(
                        "Payment verified successfully",
                        tx_hash=tx_hash,
                        amount_fet=amount_fet,
                        expected=expected_amount
                    )
                    return True
        
        logger.warning("Payment verification failed - no matching transfer found", tx_hash=tx_hash)
        return False
        
    except Exception as e:
        logger.error("Payment verification error", error=str(e), tx_hash=tx_hash)
        return False

async def create_dashboard_subscription(subscription_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create subscription in the web dashboard"""
    try:
        # Call dashboard API to create subscription
        dashboard_url = config['integration']['api_base_url']
        
        response = requests.post(
            f"{dashboard_url}/api/subscriptions/blockchain",
            json=subscription_data,
            headers={
                'Content-Type': 'application/json',
                'X-Agent-Source': 'payment-agent',
                'X-Agent-Address': payment_agent.address
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info("Dashboard subscription created", subscription_id=result.get('subscription_id'))
            return result
        else:
            logger.error("Dashboard API error", status_code=response.status_code, response=response.text)
            return {"success": False, "error": f"Dashboard API error: {response.status_code}"}
            
    except Exception as e:
        logger.error("Dashboard communication error", error=str(e))
        return {"success": False, "error": f"Dashboard communication error: {e}"}

async def get_subscription_status(wallet_address: str, email: str = "") -> Dict[str, Any]:
    """Get subscription status from dashboard"""
    try:
        dashboard_url = config['integration']['api_base_url']
        
        params = {"wallet_address": wallet_address}
        if email:
            params["email"] = email
        
        response = requests.get(
            f"{dashboard_url}/api/subscriptions/status",
            params=params,
            headers={'X-Agent-Source': 'payment-agent'},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {}
            
    except Exception as e:
        logger.error("Subscription status query error", error=str(e))
        return {}

@payment_agent.on_interval(period=300)  # Every 5 minutes
async def sync_subscription_status(ctx: Context):
    """Sync subscription status and handle renewals"""
    try:
        # Get expiring subscriptions from dashboard
        dashboard_url = config['integration']['api_base_url']
        response = requests.get(
            f"{dashboard_url}/api/subscriptions/expiring",
            headers={'X-Agent-Source': 'payment-agent'},
            timeout=30
        )
        
        if response.status_code == 200:
            expiring_subs = response.json().get('subscriptions', [])
            
            for sub in expiring_subs:
                if sub.get('payment_method') == 'blockchain':
                    # Check for renewal payments
                    await check_renewal_payments(sub)
                    
    except Exception as e:
        logger.error("Subscription sync error", error=str(e))

async def check_renewal_payments(subscription: Dict[str, Any]):
    """Check for renewal payments for a subscription"""
    try:
        wallet_address = subscription.get('wallet_address')
        if not wallet_address:
            return
        
        # Query blockchain for recent payments from this wallet
        # This is a simplified implementation
        logger.info("Checking renewal payments", wallet_address=wallet_address)
        
    except Exception as e:
        logger.error("Renewal payment check error", error=str(e))

@payment_agent.on_event("startup")
async def startup_event(ctx: Context):
    """Agent startup handler"""
    logger.info(
        "Payment Agent started",
        agent_address=payment_agent.address,
        port=config['agents']['payment']['port']
    )
    
    # Test dashboard connectivity
    health_url = config['integration']['health_check_url']
    try:
        response = requests.get(health_url, timeout=10)
        if response.status_code == 200:
            logger.info("Dashboard connectivity verified")
        else:
            logger.warning("Dashboard health check failed", status_code=response.status_code)
    except Exception as e:
        logger.error("Dashboard connectivity test failed", error=str(e))

@payment_agent.on_event("shutdown")
async def shutdown_event(ctx: Context):
    """Agent shutdown handler"""
    logger.info("Payment Agent shutting down")

if __name__ == "__main__":
    logger.info("Running Payment Agent in standalone mode")
    payment_agent.run() 