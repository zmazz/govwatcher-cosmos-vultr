"""
Cosmos chain client utilities for fetching governance proposals.
Supports multiple Cosmos SDK chains with different RPC endpoints.
"""

import os
import requests
import aiohttp
from typing import List, Dict, Any, Optional
import asyncio
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)


class CosmosChainConfig:
    """Configuration for a Cosmos SDK chain."""
    
    # Comprehensive chain configurations for major Cosmos SDK chains
    CHAIN_CONFIGS = {
        'cosmoshub-4': {
            'name': 'Cosmos Hub',
            'rpc_endpoints': [
                'https://cosmos-rpc.publicnode.com:443',
                'https://rpc-cosmoshub.blockapsis.com',
                'https://cosmos-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://cosmos-rest.publicnode.com',
                'https://lcd-cosmoshub.blockapsis.com',
                'https://cosmos-api.polkachu.com'
            ]
        },
        'osmosis-1': {
            'name': 'Osmosis',
            'rpc_endpoints': [
                'https://osmosis-rpc.publicnode.com:443',
                'https://rpc.osmosis.zone',
                'https://osmosis-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://osmosis-rest.publicnode.com',
                'https://lcd.osmosis.zone',
                'https://osmosis-api.polkachu.com'
            ]
        },
        'juno-1': {
            'name': 'Juno',
            'rpc_endpoints': [
                'https://juno-rpc.publicnode.com:443',
                'https://rpc-juno.itastakers.com',
                'https://juno-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://juno-rest.publicnode.com',
                'https://lcd-juno.itastakers.com',
                'https://juno-api.polkachu.com'
            ]
        },
        'fetchhub-4': {
            'name': 'Fetch.ai',
            'rpc_endpoints': [
                'https://rpc-fetchhub.fetch.ai',
                'https://fetch-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://rest-fetchhub.fetch.ai',
                'https://fetch-api.polkachu.com'
            ]
        },
        'akashnet-2': {
            'name': 'Akash',
            'rpc_endpoints': [
                'https://akash-rpc.publicnode.com:443',
                'https://rpc.akash.forbole.com',
                'https://akash-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://akash-rest.publicnode.com',
                'https://rest.akash.forbole.com',
                'https://akash-api.polkachu.com'
            ]
        },
        'bandchain': {
            'name': 'Band Protocol',
            'rpc_endpoints': [
                'https://rpc.laozi1.bandchain.org',
                'https://band-rpc.ibs.team'
            ],
            'rest_endpoints': [
                'https://laozi1.bandchain.org/api',
                'https://band-api.ibs.team'
            ]
        },
        'dymension_1100-1': {
            'name': 'Dymension',
            'rpc_endpoints': [
                'https://dymension-rpc.publicnode.com:443',
                'https://dymension-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://dymension-rest.publicnode.com',
                'https://dymension-api.polkachu.com'
            ]
        },
        'kava_2222-10': {
            'name': 'Kava',
            'rpc_endpoints': [
                'https://kava-rpc.publicnode.com:443',
                'https://rpc.kava.io',
                'https://kava-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://kava-rest.publicnode.com',
                'https://api.kava.io',
                'https://kava-api.polkachu.com'
            ]
        },
        'secret-4': {
            'name': 'Secret Network',
            'rpc_endpoints': [
                'https://secret-rpc.publicnode.com:443',
                'https://scrt-rpc.whispernode.com',
                'https://secret-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://secret-rest.publicnode.com',
                'https://scrt-lcd.whispernode.com',
                'https://secret-api.polkachu.com'
            ]
        },
        'stride-1': {
            'name': 'Stride',
            'rpc_endpoints': [
                'https://stride-rpc.publicnode.com:443',
                'https://stride-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://stride-rest.publicnode.com',
                'https://stride-api.polkachu.com'
            ]
        },
        'injective-1': {
            'name': 'Injective',
            'rpc_endpoints': [
                'https://injective-rpc.publicnode.com:443',
                'https://tm.injective.network',
                'https://injective-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://injective-rest.publicnode.com',
                'https://lcd.injective.network',
                'https://injective-api.polkachu.com'
            ]
        },
        'evmos_9001-2': {
            'name': 'Evmos',
            'rpc_endpoints': [
                'https://evmos-rpc.publicnode.com:443',
                'https://tendermint.bd.evmos.org:26657',
                'https://evmos-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://evmos-rest.publicnode.com',
                'https://rest.bd.evmos.org:1317',
                'https://evmos-api.polkachu.com'
            ]
        },
        'stargaze-1': {
            'name': 'Stargaze',
            'rpc_endpoints': [
                'https://stargaze-rpc.publicnode.com:443',
                'https://rpc.stargaze-apis.com',
                'https://stargaze-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://stargaze-rest.publicnode.com',
                'https://rest.stargaze-apis.com',
                'https://stargaze-api.polkachu.com'
            ]
        },
        'regen-1': {
            'name': 'Regen Network',
            'rpc_endpoints': [
                'https://regen-rpc.publicnode.com:443',
                'https://rpc-regen.ecostake.com',
                'https://regen-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://regen-rest.publicnode.com',
                'https://rest-regen.ecostake.com',
                'https://regen-api.polkachu.com'
            ]
        },
        'terra-2': {
            'name': 'Terra',
            'rpc_endpoints': [
                'https://terra-rpc.publicnode.com:443',
                'https://terra-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://terra-rest.publicnode.com',
                'https://terra-api.polkachu.com'
            ]
        },
        'chihuahua-1': {
            'name': 'Chihuahua',
            'rpc_endpoints': [
                'https://chihuahua-rpc.publicnode.com:443',
                'https://chihuahua-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://chihuahua-rest.publicnode.com',
                'https://chihuahua-api.polkachu.com'
            ]
        },
        'bitcanna-1': {
            'name': 'BitCanna',
            'rpc_endpoints': [
                'https://bitcanna-rpc.publicnode.com:443',
                'https://bitcanna-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://bitcanna-rest.publicnode.com',
                'https://bitcanna-api.polkachu.com'
            ]
        },
        'comdex-1': {
            'name': 'Comdex',
            'rpc_endpoints': [
                'https://comdex-rpc.publicnode.com:443',
                'https://comdex-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://comdex-rest.publicnode.com',
                'https://comdex-api.polkachu.com'
            ]
        },
        'kichain-2': {
            'name': 'Ki Chain',
            'rpc_endpoints': [
                'https://kichain-rpc.publicnode.com:443',
                'https://kichain-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://kichain-rest.publicnode.com',
                'https://kichain-api.polkachu.com'
            ]
        },
        'gravity-bridge-3': {
            'name': 'Gravity Bridge',
            'rpc_endpoints': [
                'https://gravitybridge-rpc.publicnode.com:443',
                'https://gravitybridge-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://gravitybridge-rest.publicnode.com',
                'https://gravitybridge-api.polkachu.com'
            ]
        },
        'phoenix-1': {
            'name': 'Terra Classic',
            'rpc_endpoints': [
                'https://terra-classic-rpc.publicnode.com:443',
                'https://terra-classic-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://terra-classic-rest.publicnode.com',
                'https://terra-classic-api.polkachu.com'
            ]
        },
        'carbon-1': {
            'name': 'Carbon',
            'rpc_endpoints': [
                'https://carbon-rpc.publicnode.com:443',
                'https://carbon-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://carbon-rest.publicnode.com',
                'https://carbon-api.polkachu.com'
            ]
        },
        'crescent-1': {
            'name': 'Crescent',
            'rpc_endpoints': [
                'https://crescent-rpc.publicnode.com:443',
                'https://crescent-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://crescent-rest.publicnode.com',
                'https://crescent-api.polkachu.com'
            ]
        },
        'irishub-1': {
            'name': 'IRISnet',
            'rpc_endpoints': [
                'https://iris-rpc.publicnode.com:443',
                'https://iris-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://iris-rest.publicnode.com',
                'https://iris-api.polkachu.com'
            ]
        },
        'omniflixhub-1': {
            'name': 'OmniFlix',
            'rpc_endpoints': [
                'https://omniflix-rpc.publicnode.com:443',
                'https://omniflix-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://omniflix-rest.publicnode.com',
                'https://omniflix-api.polkachu.com'
            ]
        },
        'sommelier-3': {
            'name': 'Sommelier',
            'rpc_endpoints': [
                'https://sommelier-rpc.publicnode.com:443',
                'https://sommelier-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://sommelier-rest.publicnode.com',
                'https://sommelier-api.polkachu.com'
            ]
        },
        'umee-1': {
            'name': 'Umee',
            'rpc_endpoints': [
                'https://umee-rpc.publicnode.com:443',
                'https://umee-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://umee-rest.publicnode.com',
                'https://umee-api.polkachu.com'
            ]
        },
        'quicksilver-2': {
            'name': 'Quicksilver',
            'rpc_endpoints': [
                'https://quicksilver-rpc.publicnode.com:443',
                'https://quicksilver-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://quicksilver-rest.publicnode.com',
                'https://quicksilver-api.polkachu.com'
            ]
        },
        'desmos-mainnet': {
            'name': 'Desmos',
            'rpc_endpoints': [
                'https://desmos-rpc.publicnode.com:443',
                'https://desmos-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://desmos-rest.publicnode.com',
                'https://desmos-api.polkachu.com'
            ]
        },
        'cerberus-chain-1': {
            'name': 'Cerberus',
            'rpc_endpoints': [
                'https://cerberus-rpc.publicnode.com:443',
                'https://cerberus-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://cerberus-rest.publicnode.com',
                'https://cerberus-api.polkachu.com'
            ]
        },
        'kaiyo-1': {
            'name': 'Kujira',
            'rpc_endpoints': [
                'https://kujira-rpc.publicnode.com:443',
                'https://kujira-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://kujira-rest.publicnode.com',
                'https://kujira-api.polkachu.com'
            ]
        },
        'noble-1': {
            'name': 'Noble',
            'rpc_endpoints': [
                'https://noble-rpc.publicnode.com:443',
                'https://noble-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://noble-rest.publicnode.com',
                'https://noble-api.polkachu.com'
            ]
        },
        'neutron-1': {
            'name': 'Neutron',
            'rpc_endpoints': [
                'https://neutron-rpc.publicnode.com:443',
                'https://neutron-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://neutron-rest.publicnode.com',
                'https://neutron-api.polkachu.com'
            ]
        },
        'migaloo-1': {
            'name': 'Migaloo',
            'rpc_endpoints': [
                'https://migaloo-rpc.publicnode.com:443',
                'https://migaloo-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://migaloo-rest.publicnode.com',
                'https://migaloo-api.polkachu.com'
            ]
        },
        'archway-1': {
            'name': 'Archway',
            'rpc_endpoints': [
                'https://archway-rpc.publicnode.com:443',
                'https://archway-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://archway-rest.publicnode.com',
                'https://archway-api.polkachu.com'
            ]
        },
        'axelar-dojo-1': {
            'name': 'Axelar',
            'rpc_endpoints': [
                'https://axelar-rpc.publicnode.com:443',
                'https://axelar-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://axelar-rest.publicnode.com',
                'https://axelar-api.polkachu.com'
            ]
        },
        'bitsong-2b': {
            'name': 'BitSong',
            'rpc_endpoints': [
                'https://bitsong-rpc.publicnode.com:443',
                'https://bitsong-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://bitsong-rest.publicnode.com',
                'https://bitsong-api.polkachu.com'
            ]
        },
        'cheqd-mainnet-1': {
            'name': 'Cheqd',
            'rpc_endpoints': [
                'https://cheqd-rpc.publicnode.com:443',
                'https://cheqd-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://cheqd-rest.publicnode.com',
                'https://cheqd-api.polkachu.com'
            ]
        },
        'cronos_25-1': {
            'name': 'Cronos POS',
            'rpc_endpoints': [
                'https://cronos-pos-rpc.publicnode.com:443',
                'https://cronos-pos-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://cronos-pos-rest.publicnode.com',
                'https://cronos-pos-api.polkachu.com'
            ]
        },
        'emoney-3': {
            'name': 'e-Money',
            'rpc_endpoints': [
                'https://emoney-rpc.publicnode.com:443',
                'https://emoney-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://emoney-rest.publicnode.com',
                'https://emoney-api.polkachu.com'
            ]
        },
        'jackal-1': {
            'name': 'Jackal',
            'rpc_endpoints': [
                'https://jackal-rpc.publicnode.com:443',
                'https://jackal-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://jackal-rest.publicnode.com',
                'https://jackal-api.polkachu.com'
            ]
        },
        'likecoin-mainnet-2': {
            'name': 'LikeCoin',
            'rpc_endpoints': [
                'https://likecoin-rpc.publicnode.com:443',
                'https://likecoin-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://likecoin-rest.publicnode.com',
                'https://likecoin-api.polkachu.com'
            ]
        },
        'mars-1': {
            'name': 'Mars Protocol',
            'rpc_endpoints': [
                'https://mars-rpc.publicnode.com:443',
                'https://mars-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://mars-rest.publicnode.com',
                'https://mars-api.polkachu.com'
            ]
        },
        'persistence-1': {
            'name': 'Persistence',
            'rpc_endpoints': [
                'https://persistence-rpc.publicnode.com:443',
                'https://persistence-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://persistence-rest.publicnode.com',
                'https://persistence-api.polkachu.com'
            ]
        },
        'pio-mainnet-1': {
            'name': 'Provenance',
            'rpc_endpoints': [
                'https://provenance-rpc.publicnode.com:443',
                'https://provenance-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://provenance-rest.publicnode.com',
                'https://provenance-api.polkachu.com'
            ]
        },
        'sentinelhub-2': {
            'name': 'Sentinel',
            'rpc_endpoints': [
                'https://sentinel-rpc.publicnode.com:443',
                'https://sentinel-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://sentinel-rest.publicnode.com',
                'https://sentinel-api.polkachu.com'
            ]
        },
        'shentu-2.2': {
            'name': 'Shentu',
            'rpc_endpoints': [
                'https://shentu-rpc.publicnode.com:443',
                'https://shentu-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://shentu-rest.publicnode.com',
                'https://shentu-api.polkachu.com'
            ]
        },
        'sifchain-1': {
            'name': 'Sifchain',
            'rpc_endpoints': [
                'https://sifchain-rpc.publicnode.com:443',
                'https://sifchain-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://sifchain-rest.publicnode.com',
                'https://sifchain-api.polkachu.com'
            ]
        },
        'theta-testnet-001': {
            'name': 'Theta Testnet',
            'rpc_endpoints': [
                'https://theta-testnet-rpc.polkachu.com'
            ],
            'rest_endpoints': [
                'https://theta-testnet-api.polkachu.com'
            ]
        }
    }
    
    @classmethod
    def get_config(cls, chain_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a chain ID."""
        return cls.CHAIN_CONFIGS.get(chain_id)
    
    @classmethod
    def get_rest_endpoint(cls, chain_id: str) -> Optional[str]:
        """Get primary REST endpoint for a chain."""
        config = cls.get_config(chain_id)
        if config and config['rest_endpoints']:
            return config['rest_endpoints'][0]
        return None


class CosmosProposalFetcher:
    """Fetches governance proposals from Cosmos SDK chains."""
    
    def __init__(self, chain_id: str):
        self.chain_id = chain_id
        self.config = CosmosChainConfig.get_config(chain_id)
        if not self.config:
            raise ValueError(f"Unsupported chain ID: {chain_id}")
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'GovWatcher/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, url: str) -> Optional[Dict[str, Any]]:
        """Make HTTP request with error handling and retries."""
        if not self.session:
            raise RuntimeError("Session not initialized - use async context manager")
        
        for attempt in range(3):
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(
                            "HTTP request failed",
                            url=url,
                            status=response.status,
                            attempt=attempt + 1
                        )
            except Exception as e:
                logger.warning(
                    "Request exception",
                    url=url,
                    error=str(e),
                    attempt=attempt + 1
                )
                if attempt < 2:  # Don't sleep on last attempt
                    await asyncio.sleep(1 * (attempt + 1))
        
        return None
    
    async def fetch_proposals(self, since_proposal_id: int = 0) -> List[Dict[str, Any]]:
        """Fetch governance proposals since the given proposal ID."""
        proposals = []
        
        for endpoint in self.config['rest_endpoints']:
            try:
                # First, get the latest proposal ID to know the range
                latest_url = f"{endpoint}/cosmos/gov/v1beta1/proposals"
                latest_data = await self._make_request(latest_url)
                
                if not latest_data or 'proposals' not in latest_data:
                    continue
                
                # Get all proposals and filter for new ones
                all_proposals = latest_data['proposals']
                
                for proposal in all_proposals:
                    try:
                        proposal_id = int(proposal['proposal_id'])
                        if proposal_id > since_proposal_id:
                            # Check if proposal is in voting period
                            status = proposal.get('status', '')
                            if status == 'PROPOSAL_STATUS_VOTING_PERIOD':
                                parsed_proposal = self._parse_proposal(proposal)
                                if parsed_proposal:
                                    proposals.append(parsed_proposal)
                                    logger.info(
                                        "New proposal found",
                                        chain=self.chain_id,
                                        proposal_id=proposal_id,
                                        title=parsed_proposal.get('title', 'Unknown')
                                    )
                    except (ValueError, KeyError) as e:
                        logger.warning(
                            "Failed to parse proposal",
                            chain=self.chain_id,
                            error=str(e),
                            proposal=proposal
                        )
                        continue
                
                # If we got proposals from this endpoint, break
                if proposals:
                    break
                    
            except Exception as e:
                logger.error(
                    "Failed to fetch from endpoint",
                    chain=self.chain_id,
                    endpoint=endpoint,
                    error=str(e)
                )
                continue
        
        return proposals
    
    def _parse_proposal(self, raw_proposal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse raw proposal data into our standard format."""
        try:
            proposal_id = int(raw_proposal['proposal_id'])
            
            # Extract content - handle different proposal types
            content = raw_proposal.get('content', {})
            if isinstance(content, dict):
                title = content.get('title', content.get('@type', 'Unknown Title'))
                description = content.get('description', 'No description available')
            else:
                title = f"Proposal #{proposal_id}"
                description = str(content) if content else 'No description available'
            
            # Parse voting times
            voting_start_time = None
            voting_end_time = None
            
            if 'voting_start_time' in raw_proposal:
                voting_start_time = self._parse_timestamp(raw_proposal['voting_start_time'])
            
            if 'voting_end_time' in raw_proposal:
                voting_end_time = self._parse_timestamp(raw_proposal['voting_end_time'])
            
            return {
                'chain': self.chain_id,
                'proposal_id': proposal_id,
                'title': title.strip()[:200],  # Limit title length
                'description': description.strip()[:2000],  # Limit description length
                'voting_start_time': voting_start_time,
                'voting_end_time': voting_end_time,
                'status': raw_proposal.get('status', 'unknown'),
                'raw_data': raw_proposal  # Keep original for debugging
            }
            
        except Exception as e:
            logger.error(
                "Failed to parse proposal",
                chain=self.chain_id,
                error=str(e),
                raw_proposal=raw_proposal
            )
            return None
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[int]:
        """Parse RFC3339 timestamp to Unix timestamp."""
        try:
            # Handle different timestamp formats
            if timestamp_str.endswith('Z'):
                dt = datetime.fromisoformat(timestamp_str[:-1] + '+00:00')
            else:
                dt = datetime.fromisoformat(timestamp_str)
            return int(dt.timestamp())
        except Exception as e:
            logger.warning("Failed to parse timestamp", timestamp=timestamp_str, error=str(e))
            return None


class MultiChainProposalFetcher:
    """Manages proposal fetching across multiple chains."""
    
    def __init__(self, chain_ids: List[str]):
        self.chain_ids = chain_ids
        self.fetchers = {}
    
    async def fetch_all_proposals(self, last_proposal_ids: Dict[str, int]) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch proposals from all configured chains."""
        results = {}
        
        # Create tasks for all chains
        tasks = []
        for chain_id in self.chain_ids:
            since_id = last_proposal_ids.get(chain_id, 0)
            task = self._fetch_chain_proposals(chain_id, since_id)
            tasks.append((chain_id, task))
        
        # Execute all tasks concurrently
        for chain_id, task in tasks:
            try:
                proposals = await task
                results[chain_id] = proposals
                logger.info(
                    "Chain proposals fetched",
                    chain=chain_id,
                    count=len(proposals)
                )
            except Exception as e:
                logger.error(
                    "Failed to fetch chain proposals",
                    chain=chain_id,
                    error=str(e)
                )
                results[chain_id] = []
        
        return results
    
    async def _fetch_chain_proposals(self, chain_id: str, since_proposal_id: int) -> List[Dict[str, Any]]:
        """Fetch proposals for a single chain."""
        async with CosmosProposalFetcher(chain_id) as fetcher:
            return await fetcher.fetch_proposals(since_proposal_id)


# Synchronous wrapper for Lambda environments that don't support async
def fetch_new_proposals(chain_id: str, last_proposal_id: int) -> List[Dict[str, Any]]:
    """Synchronous wrapper for fetching proposals from a single chain."""
    async def _async_fetch():
        async with CosmosProposalFetcher(chain_id) as fetcher:
            return await fetcher.fetch_proposals(last_proposal_id)
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(_async_fetch())
    except Exception as e:
        logger.error(
            "Failed to fetch proposals synchronously",
            chain=chain_id,
            error=str(e)
        )
        return []


def get_supported_chains() -> List[str]:
    """Get list of supported chain IDs."""
    return list(CosmosChainConfig.CHAIN_CONFIGS.keys()) 