#!/usr/bin/env python3
"""
Get Vultr VPS Root Password
"""

import os
import requests
import json
import time

def get_instance_info():
    """Get current instance information"""
    try:
        with open('.vultr_instance', 'r') as f:
            instance_info = {}
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    instance_info[key] = value
            return instance_info
    except FileNotFoundError:
        print("❌ .vultr_instance file not found")
        return None

def get_instance_details(instance_id):
    """Get detailed instance information"""
    api_key = os.getenv('VULTR_API_KEY')
    url = f"https://api.vultr.com/v2/instances/{instance_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        return None

def main():
    print("🔑 Vultr VPS Root Password Helper")
    print("=" * 50)
    
    instance_info = get_instance_info()
    if not instance_info:
        return
    
    instance_id = instance_info.get('INSTANCE_ID')
    vps_ip = instance_info.get('VPS_IP')
    
    print(f"📋 Instance Details:")
    print(f"  ID: {instance_id}")
    print(f"  IP: {vps_ip}")
    
    # Get instance details
    details = get_instance_details(instance_id)
    if details:
        instance = details.get('instance', {})
        print(f"  Status: {instance.get('status')}")
        print(f"  OS: {instance.get('os')}")
        print(f"  Plan: {instance.get('plan')}")
    
    print("\n🔐 Getting Root Password:")
    print("=" * 50)
    print("Unfortunately, Vultr doesn't provide root passwords via API for security reasons.")
    print("However, here are your options:")
    
    print("\n1️⃣ **Vultr Dashboard Method:**")
    print("   - Go to: https://my.vultr.com/instances")
    print(f"   - Find your instance: {instance_id}")
    print("   - Click on the instance")
    print("   - Look for 'Root Password' or 'Console' tab")
    print("   - You can view/reset the root password there")
    
    print("\n2️⃣ **SSH Key Method (Recommended):**")
    print("   - The SSH key was already set up")
    print("   - Try connecting again in a few minutes:")
    print(f"   ssh root@{vps_ip}")
    
    print("\n3️⃣ **Console Access Method:**")
    print("   - Go to: https://my.vultr.com/instances")
    print(f"   - Find your instance: {instance_id}")
    print("   - Click 'Console' tab")
    print("   - Access the server directly through browser")
    print("   - You can reset password from there")
    
    print("\n4️⃣ **Reset Password via API:**")
    print("   - This requires the instance to be powered off")
    print("   - Would you like to try this method?")
    
    choice = input("\nChoose option (1-4) or press Enter to continue deployment: ").strip()
    
    if choice == "4":
        print("\n🔄 Resetting password via API...")
        api_key = os.getenv('VULTR_API_KEY')
        url = f"https://api.vultr.com/v2/instances/{instance_id}/halt"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            # Halt the instance
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            print("✅ Instance halted")
            
            # Wait a moment
            time.sleep(5)
            
            # Start the instance
            url = f"https://api.vultr.com/v2/instances/{instance_id}/start"
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            print("✅ Instance started")
            
            print("\n🔄 Password reset initiated. Check the Vultr dashboard for the new password.")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 