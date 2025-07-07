#!/usr/bin/env python3
"""
Generate test governance data for the Cosmos GRC Co-Pilot
Creates diverse proposals from different chains with various types
"""

import json
import os
from datetime import datetime, timedelta
import random

def generate_test_proposals():
    """Generate diverse test proposals for different chains."""
    
    # Chain configurations
    chains = {
        'cosmoshub-4': {
            'name': 'Cosmos Hub',
            'proposals': [
                {
                    'title': 'Cosmos Hub v15 Upgrade: Gaia v15.0.0',
                    'description': 'This proposal upgrades the Cosmos Hub to Gaia v15.0.0, introducing new features including improved IBC functionality, enhanced validator operations, and security improvements. The upgrade includes bug fixes, performance optimizations, and preparation for future interchain security features.',
                    'type': '/cosmos.upgrade.v1beta1.SoftwareUpgradeProposal',
                    'category': 'SECURITY_UPGRADE'
                },
                {
                    'title': 'Adjust Minimum Commission Rate to 5%',
                    'description': 'This proposal adjusts the minimum commission rate for validators from 0% to 5% to ensure sustainable validator operations and prevent a race to the bottom in commission rates. This change will help maintain network security by ensuring validators can cover operational costs.',
                    'type': '/cosmos.staking.v1beta1.ParameterChangeProposal',
                    'category': 'VALIDATOR_STAKING'
                }
            ]
        },
        'osmosis-1': {
            'name': 'Osmosis',
            'proposals': [
                {
                    'title': 'Enable Superfluid Staking for OSMO/USDC Pool',
                    'description': 'This proposal enables superfluid staking for the OSMO/USDC liquidity pool, allowing LPs to earn staking rewards on their OSMO portion while providing liquidity. This will increase the security of the network while incentivizing liquidity provision.',
                    'type': '/osmosis.superfluid.v1beta1.SetSuperfluidAssetsProposal',
                    'category': 'ECONOMIC_PARAMETER'
                },
                {
                    'title': 'Community Pool Spend: DEX UI/UX Improvements',
                    'description': 'Request for 50,000 OSMO from the community pool to fund comprehensive UI/UX improvements to the Osmosis DEX interface. The proposal includes mobile optimization, advanced trading features, and improved user onboarding experience.',
                    'type': '/cosmos.distribution.v1beta1.CommunityPoolSpendProposal',
                    'category': 'COMMUNITY_FUNDING'
                }
            ]
        },
        'juno-1': {
            'name': 'Juno',
            'proposals': [
                {
                    'title': 'Increase CosmWasm Contract Upload Fee',
                    'description': 'This proposal increases the fee for uploading CosmWasm contracts from 1000 JUNO to 5000 JUNO to prevent spam and ensure only serious developers upload contracts. The increased fee will help maintain network quality and reduce blockchain bloat.',
                    'type': '/cosmwasm.wasm.v1.ParameterChangeProposal',
                    'category': 'SMART_CONTRACT'
                },
                {
                    'title': 'Juno v18 Network Upgrade',
                    'description': 'This proposal upgrades the Juno network to v18, introducing new CosmWasm features, performance improvements, and enhanced smart contract capabilities. The upgrade includes bug fixes and preparation for upcoming governance improvements.',
                    'type': '/cosmos.upgrade.v1beta1.SoftwareUpgradeProposal',
                    'category': 'SECURITY_UPGRADE'
                }
            ]
        }
    }
    
    # Generate test data
    governance_updates = []
    
    for chain_id, chain_data in chains.items():
        for i, proposal_template in enumerate(chain_data['proposals']):
            # Generate realistic proposal data
            proposal_id = str(random.randint(100, 999))
            voting_end_time = datetime.now() + timedelta(days=random.randint(1, 14))
            submit_time = datetime.now() - timedelta(days=random.randint(1, 7))
            
            proposal = {
                'proposal_id': proposal_id,
                'title': proposal_template['title'],
                'description': proposal_template['description'],
                'status': '2',  # Voting period
                'voting_start_time': submit_time.isoformat() + 'Z',
                'voting_end_time': voting_end_time.isoformat() + 'Z',
                'submit_time': submit_time.isoformat() + 'Z',
                'type': proposal_template['type'],
                'deposit_end_time': (submit_time + timedelta(days=14)).isoformat() + 'Z',
                'final_tally_result': {
                    'yes': '0',
                    'abstain': '0',
                    'no': '0',
                    'no_with_veto': '0'
                },
                'total_deposit': [
                    {
                        'denom': 'uatom' if chain_id == 'cosmoshub-4' else ('uosmo' if chain_id == 'osmosis-1' else 'ujuno'),
                        'amount': str(random.randint(500000000, 1000000000))
                    }
                ]
            }
            
            # Create governance update
            update = {
                'type': 'governance_update',
                'proposal': proposal,
                'timestamp': datetime.now().isoformat(),
                'source': 'test_data_generator',
                'chain_id': chain_id,
                'chain_name': chain_data['name']
            }
            
            governance_updates.append(update)
    
    return governance_updates

def save_test_data():
    """Save test data to the expected file location."""
    try:
        # Generate test proposals
        governance_updates = generate_test_proposals()
        
        # Save to the expected location
        output_file = '/tmp/governance_updates.json'
        with open(output_file, 'w') as f:
            json.dump(governance_updates, f, indent=2)
        
        print(f"✅ Generated {len(governance_updates)} test proposals")
        print(f"📁 Saved to: {output_file}")
        
        # Print summary
        chains = {}
        for update in governance_updates:
            chain_name = update['chain_name']
            if chain_name not in chains:
                chains[chain_name] = 0
            chains[chain_name] += 1
        
        print("\n📊 Proposal Distribution:")
        for chain_name, count in chains.items():
            print(f"  {chain_name}: {count} proposals")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating test data: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Generating test governance data...")
    success = save_test_data()
    if success:
        print("\n✅ Test data generation completed successfully!")
    else:
        print("\n❌ Test data generation failed!") 