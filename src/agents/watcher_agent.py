"""
Enhanced Watcher Agent with Real-Time Cosmos RPC Integration
Monitors multiple chains for governance proposals and provides AI analysis
"""

import asyncio
import aiohttp
import json
import os
import tempfile
import shutil
import fcntl
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File path for governance updates
GOVERNANCE_FILE = "/tmp/governance_updates.json"
GOVERNANCE_BACKUP_FILE = "/tmp/governance_updates.backup.json"

def atomic_write_json(data: List[Dict], filepath: str) -> bool:
    """
    Atomically write JSON data to file with backup and error recovery
    """
    try:
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, dir=os.path.dirname(filepath))
        
        # Write data to temporary file
        json.dump(data, temp_file, indent=2)
        temp_file.flush()
        os.fsync(temp_file.fileno())  # Ensure data is written to disk
        temp_file.close()
        
        # Create backup of existing file if it exists
        if os.path.exists(filepath):
            shutil.copy2(filepath, GOVERNANCE_BACKUP_FILE)
        
        # Atomic move from temp to final location
        shutil.move(temp_file.name, filepath)
        
        logger.info(f"✅ Successfully wrote {len(data)} proposals to {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error writing to {filepath}: {e}")
        
        # Try to restore from backup if available
        if os.path.exists(GOVERNANCE_BACKUP_FILE):
            try:
                shutil.copy2(GOVERNANCE_BACKUP_FILE, filepath)
                logger.info(f"🔄 Restored {filepath} from backup")
                return True
            except Exception as restore_error:
                logger.error(f"❌ Failed to restore from backup: {restore_error}")
        
        return False

def load_governance_file() -> List[Dict]:
    """
    Safely load governance file with fallback to backup
    """
    try:
        # Try main file first
        if os.path.exists(GOVERNANCE_FILE):
            with open(GOVERNANCE_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                else:
                    logger.warning("⚠️ Governance file contains invalid data, trying backup")
        
        # Try backup file
        if os.path.exists(GOVERNANCE_BACKUP_FILE):
            with open(GOVERNANCE_BACKUP_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    logger.info("🔄 Loaded governance data from backup file")
                    return data
        
        logger.warning("⚠️ No valid governance file found, starting fresh")
        return []
        
    except Exception as e:
        logger.error(f"❌ Error loading governance file: {e}")
        return []

class CosmosRPCClient:
    """Client for interacting with Cosmos RPC endpoints"""
    
    def __init__(self):
        self.session = None
        self.session_lock = asyncio.Lock()
        self.chains = {
            # Major Cosmos SDK chains with comprehensive coverage
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
            },
            'fetchhub-4': {
                'name': 'Fetch.ai',
                'rpc': 'https://fetch-rpc.polkachu.com',
                'rest': 'https://fetch-api.polkachu.com',
                'chain_id': 'fetchhub-4'
            },
            'akashnet-2': {
                'name': 'Akash',
                'rpc': 'https://akash-rpc.polkachu.com',
                'rest': 'https://akash-api.polkachu.com',
                'chain_id': 'akashnet-2'
            },
            'bandchain': {
                'name': 'Band Protocol',
                'rpc': 'https://band-rpc.ibs.team',
                'rest': 'https://band-api.ibs.team',
                'chain_id': 'bandchain'
            },
            'dymension_1100-1': {
                'name': 'Dymension',
                'rpc': 'https://dymension-rpc.polkachu.com',
                'rest': 'https://dymension-api.polkachu.com',
                'chain_id': 'dymension_1100-1'
            },
            'kava_2222-10': {
                'name': 'Kava',
                'rpc': 'https://kava-rpc.polkachu.com',
                'rest': 'https://kava-api.polkachu.com',
                'chain_id': 'kava_2222-10'
            },
            'secret-4': {
                'name': 'Secret Network',
                'rpc': 'https://secret-rpc.polkachu.com',
                'rest': 'https://secret-api.polkachu.com',
                'chain_id': 'secret-4'
            },
            'stride-1': {
                'name': 'Stride',
                'rpc': 'https://stride-rpc.polkachu.com',
                'rest': 'https://stride-api.polkachu.com',
                'chain_id': 'stride-1'
            },
            'injective-1': {
                'name': 'Injective',
                'rpc': 'https://injective-rpc.polkachu.com',
                'rest': 'https://injective-api.polkachu.com',
                'chain_id': 'injective-1'
            },
            'evmos_9001-2': {
                'name': 'Evmos',
                'rpc': 'https://evmos-rpc.polkachu.com',
                'rest': 'https://evmos-api.polkachu.com',
                'chain_id': 'evmos_9001-2'
            },
            'stargaze-1': {
                'name': 'Stargaze',
                'rpc': 'https://stargaze-rpc.polkachu.com',
                'rest': 'https://stargaze-api.polkachu.com',
                'chain_id': 'stargaze-1'
            },
            'regen-1': {
                'name': 'Regen Network',
                'rpc': 'https://regen-rpc.polkachu.com',
                'rest': 'https://regen-api.polkachu.com',
                'chain_id': 'regen-1'
            },
            'terra-2': {
                'name': 'Terra',
                'rpc': 'https://terra-rpc.polkachu.com',
                'rest': 'https://terra-api.polkachu.com',
                'chain_id': 'terra-2'
            },
            'chihuahua-1': {
                'name': 'Chihuahua',
                'rpc': 'https://chihuahua-rpc.polkachu.com',
                'rest': 'https://chihuahua-api.polkachu.com',
                'chain_id': 'chihuahua-1'
            },
            'bitcanna-1': {
                'name': 'BitCanna',
                'rpc': 'https://bitcanna-rpc.polkachu.com',
                'rest': 'https://bitcanna-api.polkachu.com',
                'chain_id': 'bitcanna-1'
            },
            'comdex-1': {
                'name': 'Comdex',
                'rpc': 'https://comdex-rpc.polkachu.com',
                'rest': 'https://comdex-api.polkachu.com',
                'chain_id': 'comdex-1'
            },
            'kichain-2': {
                'name': 'Ki Chain',
                'rpc': 'https://ki-rpc.polkachu.com',
                'rest': 'https://ki-api.polkachu.com',
                'chain_id': 'kichain-2'
            },
            'gravity-bridge-3': {
                'name': 'Gravity Bridge',
                'rpc': 'https://gravity-bridge-rpc.polkachu.com',
                'rest': 'https://gravity-bridge-api.polkachu.com',
                'chain_id': 'gravity-bridge-3'
            },
            'phoenix-1': {
                'name': 'Terra Phoenix',
                'rpc': 'https://phoenix-rpc.polkachu.com',
                'rest': 'https://phoenix-api.polkachu.com',
                'chain_id': 'phoenix-1'
            },
            'carbon-1': {
                'name': 'Carbon',
                'rpc': 'https://carbon-rpc.polkachu.com',
                'rest': 'https://carbon-api.polkachu.com',
                'chain_id': 'carbon-1'
            },
            'crescent-1': {
                'name': 'Crescent',
                'rpc': 'https://crescent-rpc.polkachu.com',
                'rest': 'https://crescent-api.polkachu.com',
                'chain_id': 'crescent-1'
            },
            'irishub-1': {
                'name': 'IRISnet',
                'rpc': 'https://iris-rpc.polkachu.com',
                'rest': 'https://iris-api.polkachu.com',
                'chain_id': 'irishub-1'
            },
            'omniflixhub-1': {
                'name': 'OmniFlix',
                'rpc': 'https://omniflix-rpc.polkachu.com',
                'rest': 'https://omniflix-api.polkachu.com',
                'chain_id': 'omniflixhub-1'
            },
            'sommelier-3': {
                'name': 'Sommelier',
                'rpc': 'https://sommelier-rpc.polkachu.com',
                'rest': 'https://sommelier-api.polkachu.com',
                'chain_id': 'sommelier-3'
            },
            'umee-1': {
                'name': 'Umee',
                'rpc': 'https://umee-rpc.polkachu.com',
                'rest': 'https://umee-api.polkachu.com',
                'chain_id': 'umee-1'
            },
            'quicksilver-2': {
                'name': 'Quicksilver',
                'rpc': 'https://quicksilver-rpc.polkachu.com',
                'rest': 'https://quicksilver-api.polkachu.com',
                'chain_id': 'quicksilver-2'
            },
            'desmos-mainnet': {
                'name': 'Desmos',
                'rpc': 'https://desmos-rpc.polkachu.com',
                'rest': 'https://desmos-api.polkachu.com',
                'chain_id': 'desmos-mainnet'
            },
            'cerberus-chain-1': {
                'name': 'Cerberus',
                'rpc': 'https://cerberus-rpc.polkachu.com',
                'rest': 'https://cerberus-api.polkachu.com',
                'chain_id': 'cerberus-chain-1'
            },
            'kaiyo-1': {
                'name': 'Kujira',
                'rpc': 'https://kujira-rpc.polkachu.com',
                'rest': 'https://kujira-api.polkachu.com',
                'chain_id': 'kaiyo-1'
            },
            'noble-1': {
                'name': 'Noble',
                'rpc': 'https://noble-rpc.polkachu.com',
                'rest': 'https://noble-api.polkachu.com',
                'chain_id': 'noble-1'
            },
            'neutron-1': {
                'name': 'Neutron',
                'rpc': 'https://neutron-rpc.polkachu.com',
                'rest': 'https://neutron-api.polkachu.com',
                'chain_id': 'neutron-1'
            },
            'migaloo-1': {
                'name': 'Migaloo',
                'rpc': 'https://migaloo-rpc.polkachu.com',
                'rest': 'https://migaloo-api.polkachu.com',
                'chain_id': 'migaloo-1'
            },
            'archway-1': {
                'name': 'Archway',
                'rpc': 'https://archway-rpc.polkachu.com',
                'rest': 'https://archway-api.polkachu.com',
                'chain_id': 'archway-1'
            },
            'axelar-dojo-1': {
                'name': 'Axelar',
                'rpc': 'https://axelar-rpc.polkachu.com',
                'rest': 'https://axelar-api.polkachu.com',
                'chain_id': 'axelar-dojo-1'
            },
            'bitsong-2b': {
                'name': 'BitSong',
                'rpc': 'https://bitsong-rpc.polkachu.com',
                'rest': 'https://bitsong-api.polkachu.com',
                'chain_id': 'bitsong-2b'
            },
            'cheqd-mainnet-1': {
                'name': 'Cheqd',
                'rpc': 'https://cheqd-rpc.polkachu.com',
                'rest': 'https://cheqd-api.polkachu.com',
                'chain_id': 'cheqd-mainnet-1'
            },
            'cronos_25-1': {
                'name': 'Cronos POS',
                'rpc': 'https://cronos-rpc.polkachu.com',
                'rest': 'https://cronos-api.polkachu.com',
                'chain_id': 'cronos_25-1'
            },
            'emoney-3': {
                'name': 'e-Money',
                'rpc': 'https://emoney-rpc.polkachu.com',
                'rest': 'https://emoney-api.polkachu.com',
                'chain_id': 'emoney-3'
            },
            'jackal-1': {
                'name': 'Jackal',
                'rpc': 'https://jackal-rpc.polkachu.com',
                'rest': 'https://jackal-api.polkachu.com',
                'chain_id': 'jackal-1'
            },
            'likecoin-mainnet-2': {
                'name': 'LikeCoin',
                'rpc': 'https://likecoin-rpc.polkachu.com',
                'rest': 'https://likecoin-api.polkachu.com',
                'chain_id': 'likecoin-mainnet-2'
            },
            'mars-1': {
                'name': 'Mars Protocol',
                'rpc': 'https://mars-rpc.polkachu.com',
                'rest': 'https://mars-api.polkachu.com',
                'chain_id': 'mars-1'
            },
            'persistence-1': {
                'name': 'Persistence',
                'rpc': 'https://persistence-rpc.polkachu.com',
                'rest': 'https://persistence-api.polkachu.com',
                'chain_id': 'persistence-1'
            },
            'pio-mainnet-1': {
                'name': 'Provenance',
                'rpc': 'https://provenance-rpc.polkachu.com',
                'rest': 'https://provenance-api.polkachu.com',
                'chain_id': 'pio-mainnet-1'
            },
            'sentinelhub-2': {
                'name': 'Sentinel',
                'rpc': 'https://sentinel-rpc.polkachu.com',
                'rest': 'https://sentinel-api.polkachu.com',
                'chain_id': 'sentinelhub-2'
            },
            'shentu-2.2': {
                'name': 'Shentu',
                'rpc': 'https://shentu-rpc.polkachu.com',
                'rest': 'https://shentu-api.polkachu.com',
                'chain_id': 'shentu-2.2'
            },
            'sifchain-1': {
                'name': 'Sifchain',
                'rpc': 'https://sifchain-rpc.polkachu.com',
                'rest': 'https://sifchain-api.polkachu.com',
                'chain_id': 'sifchain-1'
            }
        }
    
    async def _ensure_session(self):
        """Ensure we have a valid session, recreate if needed"""
        async with self.session_lock:
            try:
                if self.session is None or self.session.closed:
                    logger.debug("🔄 Creating new aiohttp session")
                    self.session = aiohttp.ClientSession(
                        timeout=aiohttp.ClientTimeout(total=30),
                        connector=aiohttp.TCPConnector(limit=100, limit_per_host=10)
                    )
                return self.session
            except Exception as e:
                logger.error(f"❌ Error creating session: {e}")
                # Try to create a new session even if there was an error
                try:
                    self.session = aiohttp.ClientSession(
                        timeout=aiohttp.ClientTimeout(total=30),
                        connector=aiohttp.TCPConnector(limit=100, limit_per_host=10)
                    )
                    return self.session
                except Exception as e2:
                    logger.error(f"❌ Failed to create session after error: {e2}")
                    return None
    
    async def get_session(self):
        """Get or create aiohttp session - DEPRECATED, use _ensure_session instead"""
        return await self._ensure_session()
    
    async def fetch_active_proposals(self, chain_id: str) -> List[Dict]:
        """Fetch active governance proposals from a specific chain"""
        if chain_id not in self.chains:
            return None
        
        config = self.chains[chain_id]
        
        # Ensure we have a valid session
        session = await self._ensure_session()
        if session is None:
            logger.error(f"❌ Cannot create session for {config['name']}")
            return None
        
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
                    return None  # Return None to indicate failure, not empty list
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching proposals for {config['name']}: {e}")
            # Recreate session on network errors
            await self._recreate_session()
            return None
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching proposals for {config['name']}")
            return None
        except Exception as e:
            logger.error(f"Error fetching proposals for {config['name']}: {e}")
            # Check if it's a session-related error
            if "Event loop is closed" in str(e) or "session" in str(e).lower():
                await self._recreate_session()
            return None  # Return None to indicate failure, not empty list
    
    async def _recreate_session(self):
        """Recreate the session after errors"""
        async with self.session_lock:
            try:
                if self.session and not self.session.closed:
                    await self.session.close()
                self.session = None
                logger.info("🔄 Recreated aiohttp session after error")
            except Exception as e:
                logger.error(f"❌ Error recreating session: {e}")
    
    async def fetch_all_proposals(self) -> List[Dict]:
        """Fetch proposals from all monitored chains"""
        all_proposals = []
        successful_chains = 0
        total_chains = len(self.chains)
        
        for chain_id in self.chains.keys():
            proposals = await self.fetch_active_proposals(chain_id)
            if proposals is not None:  # None indicates failure, empty list [] is success
                successful_chains += 1
                all_proposals.extend(proposals)
                logger.info(f"Fetched {len(proposals)} proposals from {self.chains[chain_id]['name']}")
            else:
                logger.warning(f"Failed to fetch from {self.chains[chain_id]['name']}")
        
        logger.info(f"📊 Successfully connected to {successful_chains}/{total_chains} chains, found {len(all_proposals)} total proposals")
        
        # Only return proposals if we successfully connected to at least 25% of chains
        if successful_chains < (total_chains * 0.25):
            logger.error(f"❌ Too many connection failures ({successful_chains}/{total_chains} successful). Not updating governance file.")
            return []
        
        return all_proposals
    
    async def get_chain_status(self, chain_id: str) -> Dict:
        """Get basic chain status information"""
        if chain_id not in self.chains:
            return {}
        
        config = self.chains[chain_id]
        
        # Ensure we have a valid session
        session = await self._ensure_session()
        if session is None:
            return {'chain_id': chain_id, 'error': 'Cannot create session'}
        
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
        except aiohttp.ClientError as e:
            return {'chain_id': chain_id, 'error': f"Network error: {e}"}
        except asyncio.TimeoutError:
            return {'chain_id': chain_id, 'error': 'Timeout'}
        except Exception as e:
            return {'chain_id': chain_id, 'error': str(e)}
    
    async def close(self):
        """Close the aiohttp session"""
        async with self.session_lock:
            if self.session and not self.session.closed:
                await self.session.close()
                self.session = None

async def initialize_governance_file():
    """Initialize the governance file with current proposals at startup"""
    try:
        logger.info("🚀 Initializing governance file with current proposals...")
        
        # Fetch all active proposals
        proposals = await rpc_client.fetch_all_proposals()
        
        # Create updates in the format expected by the web service
        updates = []
        for proposal in proposals:
            update_data = {
                'type': 'governance_update',
                'proposal': proposal,
                'timestamp': datetime.now().isoformat(),
                'source': 'watcher_agent',
                'chain_id': proposal.get('chain_id', 'unknown'),
                'chain_name': proposal.get('chain_name', 'Unknown Chain')
            }
            updates.append(update_data)
        
        # Use atomic write with backup
        if atomic_write_json(updates, GOVERNANCE_FILE):
            logger.info(f"✅ Initialized governance file with {len(updates)} proposals")
        else:
            logger.error("❌ Failed to initialize governance file")
        
    except Exception as e:
        logger.error(f"❌ Error initializing governance file: {e}")
        # Create empty file if error
        atomic_write_json([], GOVERNANCE_FILE)

async def update_governance_file():
    """Update the governance file with current proposals - BULLETPROOF VERSION"""
    try:
        logger.info("🔄 Updating governance file...")
        
        # Load existing data safely
        existing_updates = load_governance_file()
        
        # Fetch all active proposals
        proposals = await rpc_client.fetch_all_proposals()
        
        # Don't update if we got no proposals (likely connection issues)
        if not proposals:
            logger.warning("⚠️ No proposals fetched - likely connection issues. Keeping existing file.")
            return
        
        # Create a map of existing proposals for quick lookup
        existing_proposals = {}
        for update in existing_updates:
            chain_id = update.get('chain_id')
            proposal_id = update.get('proposal', {}).get('proposal_id')
            if chain_id and proposal_id:
                key = f"{chain_id}_{proposal_id}"
                existing_proposals[key] = update
        
        # Process new proposals
        updated_proposals = {}
        new_count = 0
        updated_count = 0
        
        for proposal in proposals:
            chain_id = proposal.get('chain_id')
            proposal_id = proposal.get('proposal_id')
            key = f"{chain_id}_{proposal_id}"
            
            update_data = {
                'type': 'governance_update',
                'proposal': proposal,
                'timestamp': datetime.now().isoformat(),
                'source': 'watcher_agent',
                'chain_id': chain_id,
                'chain_name': proposal.get('chain_name', 'Unknown Chain')
            }
            
            if key in existing_proposals:
                # Check if proposal has been updated
                existing_proposal = existing_proposals[key].get('proposal', {})
                if (existing_proposal.get('status') != proposal.get('status') or
                    existing_proposal.get('voting_end_time') != proposal.get('voting_end_time')):
                    logger.info(f"📝 Updated proposal {proposal_id} from {proposal.get('chain_name')}")
                    updated_count += 1
                else:
                    # Keep existing timestamp for unchanged proposals
                    update_data['timestamp'] = existing_proposals[key].get('timestamp', update_data['timestamp'])
            else:
                logger.info(f"🆕 New proposal {proposal_id} from {proposal.get('chain_name')}: {proposal.get('title', 'Unknown')}")
                new_count += 1
            
            updated_proposals[key] = update_data
        
        # Remove proposals that are no longer active
        removed_count = 0
        for key in existing_proposals:
            if key not in updated_proposals:
                removed_count += 1
                chain_id, proposal_id = key.split('_', 1)
                logger.info(f"🗑️ Removed inactive proposal {proposal_id} from {chain_id}")
        
        # Convert back to list
        final_updates = list(updated_proposals.values())
        
        # Sort by timestamp (newest first)
        final_updates.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Use atomic write with backup
        if atomic_write_json(final_updates, GOVERNANCE_FILE):
            logger.info(f"✅ Updated governance file: {new_count} new, {updated_count} updated, {removed_count} removed, {len(final_updates)} total")
        else:
            logger.error("❌ Failed to update governance file - keeping existing data")
        
    except Exception as e:
        logger.error(f"❌ Error updating governance file: {e}")
        # Don't overwrite existing data on error

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

@governance_protocol.on_interval(period=3600.0)  # Check every 1 hour
async def monitor_governance_proposals(ctx: Context):
    """Monitor governance proposals across all chains - BULLETPROOF VERSION"""
    try:
        logger.info("🕐 Starting hourly governance check...")
        await update_governance_file()
        logger.info("✅ Hourly governance check completed")
    except Exception as e:
        logger.error(f"❌ Error in hourly monitoring: {e}")

@governance_protocol.on_interval(period=300.0)  # Check every 5 minutes for health
async def health_check(ctx: Context):
    """Regular health check - more frequent than governance updates"""
    try:
        # Check session health first
        session = await rpc_client._ensure_session()
        if session is None:
            logger.error("❌ Health check - Cannot create session")
            return
        
        # Check connection to a subset of chains for health monitoring
        health_chains = ['cosmoshub-4', 'osmosis-1', 'juno-1', 'akashnet-2']
        for chain_id in health_chains:
            if chain_id in rpc_client.chains:
                status = await rpc_client.get_chain_status(chain_id)
                if 'error' in status:
                    logger.warning(f"⚠️ Health check - Connection issue with {chain_id}: {status['error']}")
                else:
                    logger.debug(f"✅ Health check - {status['chain_name']} - Block: {status['latest_block_height']}")
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        # Try to recreate session on health check failure
        await rpc_client._recreate_session()

# Include the protocol in the agent
watcher.include(governance_protocol)

async def startup_tasks():
    """Run startup tasks"""
    try:
        logger.info("🚀 Starting Cosmos Governance Watcher Agent")
        logger.info(f"📡 Agent address: {watcher.address}")
        logger.info(f"🌐 Monitoring chains: {list(rpc_client.chains.keys())}")
        
        # Initialize governance file with current proposals
        await initialize_governance_file()
        
        logger.info("✅ Startup tasks completed")
        
    except Exception as e:
        logger.error(f"❌ Startup tasks failed: {e}")

if __name__ == "__main__":
    try:
        # Run startup tasks
        asyncio.run(startup_tasks())
        
        # Start the agent
        watcher.run()
        
    except KeyboardInterrupt:
        logger.info("👋 Shutting down watcher agent...")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
    finally:
        # Clean up
        try:
            asyncio.run(rpc_client.close())
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}") 