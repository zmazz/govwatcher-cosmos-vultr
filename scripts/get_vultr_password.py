#!/usr/bin/env python3
"""
Vultr VPS Password/SSH Helper
Helps get root password or set up SSH key authentication
"""

import os
import requests
import json
import sys
import time

def get_instance_info():
    """Get current instance information"""
    api_key = os.getenv('VULTR_API_KEY')
    if not api_key:
        print("❌ VULTR_API_KEY not set in environment")
        return None
    
    # Try to read instance info from .vultr_instance file
    try:
        with open('.vultr_instance', 'r') as f:
            instance_info = {}
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    instance_info[key] = value
            return instance_info
    except FileNotFoundError:
        print("❌ .vultr_instance file not found. Run deployment first.")
        return None

def get_instance_details(instance_id):
    """Get detailed instance information from Vultr API"""
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
        print(f"❌ Error fetching instance details: {e}")
        return None

def get_instance_credentials(instance_id):
    """Get instance credentials from Vultr API"""
    api_key = os.getenv('VULTR_API_KEY')
    url = f"https://api.vultr.com/v2/instances/{instance_id}/credentials"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching credentials: {e}")
        return None

def setup_ssh_key(instance_id, ssh_key_path):
    """Set up SSH key for the instance"""
    api_key = os.getenv('VULTR_API_KEY')
    
    # Read SSH public key
    try:
        with open(ssh_key_path, 'r') as f:
            ssh_key = f.read().strip()
    except FileNotFoundError:
        print(f"❌ SSH key file not found: {ssh_key_path}")
        return False
    
    # First, create SSH key in Vultr
    url = "https://api.vultr.com/v2/ssh-keys"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "name": f"govwatcher-{instance_id}",
        "ssh_key": ssh_key
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        ssh_key_id = response.json()['ssh_key']['id']
        print(f"✅ SSH key created with ID: {ssh_key_id}")
        
        # Attach SSH key to instance
        url = f"https://api.vultr.com/v2/instances/{instance_id}"
        data = {
            "ssh_keys": [ssh_key_id]
        }
        
        response = requests.patch(url, headers=headers, json=data)
        response.raise_for_status()
        print("✅ SSH key attached to instance")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error setting up SSH key: {e}")
        return False

def main():
    print("🔑 Vultr VPS Authentication Helper")
    print("=" * 50)
    
    # Get instance info
    instance_info = get_instance_info()
    if not instance_info:
        sys.exit(1)
    
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
    
    print("\n🔐 Authentication Options:")
    print("1. Get root password (if available)")
    print("2. Set up SSH key authentication")
    print("3. Manual SSH connection")
    
    choice = input("\nChoose option (1-3): ").strip()
    
    if choice == "1":
        print("\n🔍 Fetching root password...")
        credentials = get_instance_credentials(instance_id)
        if credentials:
            creds = credentials.get('credentials', {})
            password = creds.get('password')
            if password:
                print(f"✅ Root password: {password}")
                print(f"\n🔗 SSH command:")
                print(f"ssh root@{vps_ip}")
                print(f"Password: {password}")
            else:
                print("❌ No password available for this instance")
        else:
            print("❌ Could not fetch credentials")
    
    elif choice == "2":
        print("\n🔑 Setting up SSH key authentication...")
        ssh_key_path = input("Path to your SSH public key (e.g., ~/.ssh/id_rsa.pub): ").strip()
        if not ssh_key_path:
            ssh_key_path = os.path.expanduser("~/.ssh/id_rsa.pub")
        
        # Expand user path if it contains ~
        ssh_key_path = os.path.expanduser(ssh_key_path)
        
        if setup_ssh_key(instance_id, ssh_key_path):
            print(f"\n✅ SSH key authentication set up!")
            print(f"🔗 SSH command:")
            print(f"ssh root@{vps_ip}")
        else:
            print("❌ Failed to set up SSH key authentication")
    
    elif choice == "3":
        print(f"\n🔗 Manual SSH Connection:")
        print(f"ssh root@{vps_ip}")
        print(f"\n📝 Notes:")
        print(f"- You'll need the root password")
        print(f"- If you don't have it, try option 1 to fetch it")
        print(f"- Or set up SSH key authentication with option 2")
    
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main() 