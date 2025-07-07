"""
Enhanced Watcher Agent with Real-Time Cosmos RPC Integration
Monitors multiple chains for governance proposals and provides AI analysis
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CosmosRPCClient:
    """Client for interacting with Cosmos RPC endpoints"""
    
    def __init__(self):
        self.chains = {
            'cosmoshub-4': {
                'name': 'Cosmos Hub',
                'rpc': 'https://cosmos-rpc.polkachu.com',
                'rest': 'https://cosmos-api.polkachu.com',
                'chain_id': 'cosmoshub-4'
            },
            'osmosis-1': {
                'name': 'Osmosis',
                'rpc': 'https://osmosis-rpc.polkachu.com', 
                'rest': 'https://osmosis-api.polkachu.com',
                'chain_id': 'osmosis-1'
            },
            'juno-1': {
                'name': 'Juno',
                'rpc': 'https://juno-rpc.polkachu.com',
                'rest': 'https://juno-api.polkachu.com', 
                'chain_id': 'juno-1'
            }
        }
        self.session = None
    
    async def get_session(self):
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def fetch_active_proposals(self, chain_id: str) -> List[Dict]:
        """Fetch active governance proposals from a specific chain"""
        if chain_id not in self.chains:
            return []
        
        config = self.chains[chain_id]
        session = await self.get_session()
        
        try:
            # Fetch proposals in voting period (status=2)
            url = f"{config['rest']}/cosmos/gov/v1beta1/proposals?proposal_status=2"
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    proposals = []
                    
                    for prop in data.get('proposals', []):
                        proposals.append({
                            'chain_id': chain_id,
                            'chain_name': config['name'],
                            'proposal_id': prop['proposal_id'],
                            'title': prop['content']['title'],
                            'description': prop['content']['description'],
                            'status': prop['status'],
                            'voting_start_time': prop['voting_start_time'],
                            'voting_end_time': prop['voting_end_time'],
                            'type': prop['content']['@type'],
                            'submit_time': prop['submit_time'],
                            'deposit_end_time': prop['deposit_end_time'],
                            'final_tally_result': prop.get('final_tally_result', {}),
                            'total_deposit': prop.get('total_deposit', [])
                        })
                    
                    return proposals
                else:
                    logger.warning(f"Failed to fetch proposals for {config['name']}: HTTP {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching proposals for {config['name']}: {e}")
            return []
    
    async def fetch_all_proposals(self) -> List[Dict]:
        """Fetch proposals from all monitored chains"""
        all_proposals = []
        
        for chain_id in self.chains.keys():
            proposals = await self.fetch_active_proposals(chain_id)
            all_proposals.extend(proposals)
            logger.info(f"Fetched {len(proposals)} proposals from {self.chains[chain_id]['name']}")
        
        return all_proposals
    
    async def get_chain_status(self, chain_id: str) -> Dict:
        """Get basic chain status information"""
        if chain_id not in self.chains:
            return {}
        
        config = self.chains[chain_id]
        session = await self.get_session()
        
        try:
            async with session.get(f"{config['rpc']}/status", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'chain_id': chain_id,
                        'chain_name': config['name'],
                        'latest_block_height': data['result']['sync_info']['latest_block_height'],
                        'latest_block_time': data['result']['sync_info']['latest_block_time'],
                        'catching_up': data['result']['sync_info']['catching_up'],
                        'node_info': data['result']['node_info']
                    }
                else:
                    return {'chain_id': chain_id, 'error': f"HTTP {response.status}"}
        except Exception as e:
            return {'chain_id': chain_id, 'error': str(e)}
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()

# Create the watcher agent
watcher = Agent(
    name="cosmos-governance-watcher",
    seed="cosmos-governance-watcher-seed-2024",
    port=8001,
    endpoint=["http://localhost:8001/submit"]
)

# Initialize RPC client
rpc_client = CosmosRPCClient()

# Fund agent if needed
fund_agent_if_low(watcher.wallet.address())

# Protocol for governance monitoring
governance_protocol = Protocol("GovernanceMonitoring")

@governance_protocol.on_interval(period=300.0)  # Check every 5 minutes
async def monitor_governance_proposals(ctx: Context):
    """Monitor governance proposals across all chains"""
    try:
        logger.info("🔍 Monitoring governance proposals...")
        
        # Fetch all active proposals
        proposals = await rpc_client.fetch_all_proposals()
        
        if proposals:
            logger.info(f"📋 Found {len(proposals)} active proposals")
            
            # Process each proposal
            for proposal in proposals:
                await process_proposal(ctx, proposal)
        else:
            logger.info("📋 No active proposals found")
            
    except Exception as e:
        logger.error(f"Error monitoring proposals: {e}")

async def process_proposal(ctx: Context, proposal: Dict):
    """Process a single governance proposal"""
    try:
        # Check if proposal is ending soon (within 24 hours)
        voting_end = datetime.fromisoformat(proposal['voting_end_time'].replace('Z', '+00:00'))
        time_until_end = voting_end - datetime.now().replace(tzinfo=voting_end.tzinfo)
        
        if time_until_end <= timedelta(hours=24):
            logger.warning(f"⏰ Proposal #{proposal['proposal_id']} on {proposal['chain_name']} ends in {time_until_end}")
            
            # Send urgent notification
            await send_proposal_alert(ctx, proposal, urgent=True)
        else:
            # Regular monitoring
            await send_proposal_update(ctx, proposal)
        
    except Exception as e:
        logger.error(f"Error processing proposal {proposal.get('proposal_id', 'unknown')}: {e}")

async def send_proposal_alert(ctx: Context, proposal: Dict, urgent: bool = False):
    """Send proposal alert to analysis agent"""
    try:
        alert_data = {
            'type': 'governance_alert',
            'urgent': urgent,
            'proposal': proposal,
            'timestamp': datetime.now().isoformat(),
            'source': 'watcher_agent'
        }
        
        # In a real implementation, you would send this to the analysis agent
        # For now, we'll log it
        logger.info(f"🚨 {'URGENT' if urgent else 'ALERT'}: {proposal['title']}")
        
        # Save to file for dashboard to pick up
        alerts_file = '/tmp/governance_alerts.json'
        try:
            with open(alerts_file, 'r') as f:
                alerts = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            alerts = []
        
        alerts.append(alert_data)
        
        # Keep only last 100 alerts
        alerts = alerts[-100:]
        
        with open(alerts_file, 'w') as f:
            json.dump(alerts, f, indent=2)
        
    except Exception as e:
        logger.error(f"Error sending proposal alert: {e}")

async def send_proposal_update(ctx: Context, proposal: Dict):
    """Send regular proposal update"""
    try:
        update_data = {
            'type': 'governance_update',
            'proposal': proposal,
            'timestamp': datetime.now().isoformat(),
            'source': 'watcher_agent',
            'chain_id': proposal.get('chain_id', 'unknown'),
            'chain_name': proposal.get('chain_name', 'Unknown Chain')
        }
        
        # Save to file for dashboard
        updates_file = '/tmp/governance_updates.json'
        try:
            with open(updates_file, 'r') as f:
                updates = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            updates = []
        
        # Check if this proposal already exists (avoid duplicates)
        existing_update = None
        for i, existing in enumerate(updates):
            if (existing.get('chain_id') == proposal.get('chain_id') and 
                existing.get('proposal', {}).get('proposal_id') == proposal.get('proposal_id')):
                existing_update = i
                break
        
        if existing_update is not None:
            # Update existing proposal
            updates[existing_update] = update_data
            logger.info(f"Updated existing proposal {proposal.get('proposal_id')} from {proposal.get('chain_name')}")
        else:
            # Add new proposal
            updates.append(update_data)
            logger.info(f"Added new proposal {proposal.get('proposal_id')} from {proposal.get('chain_name')}")
        
        # Keep only last 50 updates but ensure we have at least one per chain
        if len(updates) > 50:
            # Keep the most recent proposals, but ensure chain diversity
            chain_proposals = {}
            for update in updates:
                chain_id = update.get('chain_id', 'unknown')
                if chain_id not in chain_proposals:
                    chain_proposals[chain_id] = []
                chain_proposals[chain_id].append(update)
            
            # Keep the most recent proposals from each chain
            filtered_updates = []
            for chain_id, proposals in chain_proposals.items():
                # Sort by timestamp and keep the most recent ones
                proposals.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                filtered_updates.extend(proposals[:10])  # Keep up to 10 per chain
            
            updates = filtered_updates[-50:]  # Final limit of 50 total
        
        with open(updates_file, 'w') as f:
            json.dump(updates, f, indent=2)
            
        logger.info(f"Saved {len(updates)} governance updates to file")
            
    except Exception as e:
        logger.error(f"Error sending proposal update: {e}")

@governance_protocol.on_interval(period=60.0)  # Check every minute
async def health_check(ctx: Context):
    """Regular health check"""
    try:
        # Check connection to all chains
        for chain_id in rpc_client.chains.keys():
            status = await rpc_client.get_chain_status(chain_id)
            if 'error' in status:
                logger.warning(f"⚠️ Connection issue with {chain_id}: {status['error']}")
            else:
                logger.debug(f"✅ {status['chain_name']} - Block: {status['latest_block_height']}")
    except Exception as e:
        logger.error(f"Health check failed: {e}")

# Include the protocol in the agent
watcher.include(governance_protocol)

if __name__ == "__main__":
    logger.info("🚀 Starting Cosmos Governance Watcher Agent")
    logger.info(f"📡 Agent address: {watcher.address}")
    logger.info(f"🌐 Monitoring chains: {list(rpc_client.chains.keys())}")
    
    try:
        watcher.run()
    except KeyboardInterrupt:
        logger.info("👋 Shutting down watcher agent...")
    finally:
        # Clean up
        asyncio.run(rpc_client.close()) 