#!/usr/bin/env python3
"""
Generate governance data once for immediate dashboard use
"""

import asyncio
import sys
import os
import json
import aiohttp
from datetime import datetime
from typing import Dict, List

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from utils.logging import get_logger

# Constants
GOVERNANCE_FILE = '/tmp/governance_updates.json'

logger = get_logger(__name__)

class CosmosRPCClient:
    """Client for interacting with Cosmos RPC endpoints"""
    
    def __init__(self):
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
                'rpc': 'https://kichain-rpc.polkachu.com',
                'rest': 'https://kichain-api.polkachu.com',
                'chain_id': 'kichain-2'
            },
            'gravity-bridge-3': {
                'name': 'Gravity Bridge',
                'rpc': 'https://gravitybridge-rpc.polkachu.com',
                'rest': 'https://gravitybridge-api.polkachu.com',
                'chain_id': 'gravity-bridge-3'
            },
            'phoenix-1': {
                'name': 'Terra Classic',
                'rpc': 'https://terra-classic-rpc.polkachu.com',
                'rest': 'https://terra-classic-api.polkachu.com',
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
                'rpc': 'https://cronos-pos-rpc.polkachu.com',
                'rest': 'https://cronos-pos-api.polkachu.com',
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
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()

async def generate_governance_data():
    """Generate governance data once for immediate dashboard use"""
    try:
        logger.info("🚀 Generating governance data for dashboard...")
        
        # Initialize RPC client
        rpc_client = CosmosRPCClient()
        
        # Fetch all active proposals
        logger.info("📡 Fetching proposals from all chains...")
        proposals = await rpc_client.fetch_all_proposals()
        
        # Create updates in the format expected by the web service
        updates = []
        for proposal in proposals:
            update_data = {
                'type': 'governance_update',
                'proposal': proposal,
                'timestamp': datetime.now().isoformat(),
                'source': 'governance_data_generator',
                'chain_id': proposal.get('chain_id', 'unknown'),
                'chain_name': proposal.get('chain_name', 'Unknown Chain')
            }
            updates.append(update_data)
        
        # Write to file
        with open(GOVERNANCE_FILE, 'w') as f:
            json.dump(updates, f, indent=2)
        
        logger.info(f"✅ Generated data for {len(updates)} proposals!")
        
        # Print summary by chain
        chains = {}
        for update in updates:
            chain_name = update['chain_name']
            if chain_name not in chains:
                chains[chain_name] = 0
            chains[chain_name] += 1
        
        print("📊 Proposal Distribution:")
        for chain_name, count in chains.items():
            print(f"  {chain_name}: {count} proposals")
        
        # Close the RPC client
        await rpc_client.close()
        
        return len(updates)
        
    except Exception as e:
        logger.error(f"❌ Error generating governance data: {e}")
        return 0

async def main():
    """Run the governance data generator once"""
    print("🚀 Generating governance data for dashboard...")
    print("=" * 60)
    
    proposal_count = await generate_governance_data()
    
    print(f"\n🎉 Successfully generated data for {proposal_count} proposals!")
    print("📄 Dashboard should now show real-time data instead of demo data")
    
    if proposal_count > 0:
        print("\n✅ READY: Your dashboard now has real blockchain governance data!")
    else:
        print("\n⚠️  No active proposals found - dashboard will show demo data")

if __name__ == "__main__":
    asyncio.run(main()) 