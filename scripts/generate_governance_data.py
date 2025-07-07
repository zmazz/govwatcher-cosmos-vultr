#!/usr/bin/env python3
"""
Generate governance data once for immediate dashboard use
"""

import asyncio
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from update_governance_data import GovernanceDataUpdater

async def main():
    """Run the governance data updater once"""
    print("🚀 Generating governance data for dashboard...")
    print("=" * 60)
    
    updater = GovernanceDataUpdater()
    proposal_count = await updater.update_governance_data()
    
    print(f"\n🎉 Successfully generated data for {proposal_count} proposals!")
    print("📄 Dashboard should now show real-time data instead of demo data")
    
    if proposal_count > 0:
        print("\n✅ READY: Your dashboard now has real blockchain governance data!")
    else:
        print("\n⚠️  No active proposals found - dashboard will show demo data")

if __name__ == "__main__":
    asyncio.run(main()) 