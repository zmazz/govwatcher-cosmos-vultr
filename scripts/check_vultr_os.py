#!/usr/bin/env python3
"""
Vultr OS ID Checker
Checks available OS IDs for Vultr deployment
"""

import os
import requests
import json
import sys

def get_available_os():
    """Get available OS IDs from Vultr API"""
    api_key = os.getenv('VULTR_API_KEY')
    if not api_key:
        print("❌ VULTR_API_KEY not set in environment")
        return None
    
    url = "https://api.vultr.com/v2/os"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching OS list: {e}")
        return None

def get_available_plans():
    """Get available plans from Vultr API"""
    api_key = os.getenv('VULTR_API_KEY')
    if not api_key:
        return None
    
    url = "https://api.vultr.com/v2/plans"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching plans: {e}")
        return None

def main():
    print("🔍 Checking Vultr OS availability...")
    
    # Get OS list
    os_data = get_available_os()
    if not os_data:
        sys.exit(1)
    
    # Get plans
    plans_data = get_available_plans()
    
    print("\n📋 Available Operating Systems:")
    print("=" * 80)
    
    # Filter for Ubuntu and common Linux distributions
    ubuntu_os = []
    other_linux = []
    
    for os_item in os_data.get('os', []):
        name = os_item.get('name', '').lower()
        os_id = os_item.get('id')
        
        if 'ubuntu' in name:
            ubuntu_os.append((os_id, os_item.get('name')))
        elif any(x in name for x in ['debian', 'centos', 'fedora', 'linux']):
            other_linux.append((os_id, os_item.get('name')))
    
    print("\n🐧 Ubuntu Distributions:")
    for os_id, name in sorted(ubuntu_os, key=lambda x: x[1]):
        print(f"  ID: {os_id:>4} | {name}")
    
    print("\n🐧 Other Linux Distributions:")
    for os_id, name in sorted(other_linux, key=lambda x: x[1]):
        print(f"  ID: {os_id:>4} | {name}")
    
    # Check current configuration
    print("\n🔧 Current Configuration:")
    print("=" * 80)
    print(f"Current OS ID: 387 (Ubuntu 22.04 LTS)")
    print(f"Current Plan: vc2-1c-1gb")
    print(f"Current Region: ewr")
    
    # Check if current OS ID exists
    current_os_exists = any(os_id == 387 for os_id, _ in ubuntu_os)
    
    if current_os_exists:
        print("✅ Current OS ID 387 is available")
    else:
        print("❌ Current OS ID 387 is NOT available")
        
        # Suggest alternatives
        if ubuntu_os:
            print("\n💡 Suggested Ubuntu alternatives:")
            for os_id, name in ubuntu_os[:3]:
                print(f"  ID: {os_id} | {name}")
    
    # Show available plans
    if plans_data:
        print("\n💻 Available Plans:")
        print("=" * 80)
        
        vc2_plans = []
        for plan in plans_data.get('plans', []):
            if plan.get('type') == 'vc2':
                vc2_plans.append(plan)
        
        for plan in sorted(vc2_plans, key=lambda x: x.get('price_per_month', 0)):
            name = plan.get('id')
            price = plan.get('price_per_month', 0)
            ram = plan.get('ram', 0)
            cpu = plan.get('vcpu_count', 0)
            print(f"  {name:>15} | ${price:>3}/month | {ram:>4}MB RAM | {cpu} CPU")
    
    print("\n🔧 To fix the deployment issue:")
    print("1. Check if OS ID 387 is available in your region")
    print("2. If not, update the VPS_OS variable in infra/vultr/deploy-vultr.sh")
    print("3. Use one of the available OS IDs listed above")

if __name__ == "__main__":
    main() 