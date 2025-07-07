#!/usr/bin/env python3
"""
Generate a uAgents private key for the Cosmos Gov-Watcher system.
"""

import os
import secrets

def generate_private_key():
    """Generate a secure private key for uAgents."""
    # Generate a 64-character hex string (32 bytes)
    private_key = secrets.token_hex(32)
    return private_key

def main():
    print("🔑 Generating uAgents private key...")
    
    private_key = generate_private_key()
    
    print(f"✅ Generated private key: {private_key}")
    print("\n📝 To use this key:")
    print(f"1. Update your .env file:")
    print(f"   UAGENTS_PRIVATE_KEY={private_key}")
    print("\n2. Or export it directly:")
    print(f"   export UAGENTS_PRIVATE_KEY={private_key}")
    
    # Ask if user wants to update .env file automatically
    update_env = input("\n🔍 Update .env file automatically? (y/N): ").lower().strip()
    
    if update_env == 'y':
        try:
            # Read current .env file
            with open('.env', 'r') as f:
                content = f.read()
            
            # Replace the placeholder
            updated_content = content.replace(
                'UAGENTS_PRIVATE_KEY=your-uagents-private-key-here',
                f'UAGENTS_PRIVATE_KEY={private_key}'
            )
            
            # Write back to .env file
            with open('.env', 'w') as f:
                f.write(updated_content)
            
            print("✅ .env file updated successfully!")
            
        except Exception as e:
            print(f"❌ Failed to update .env file: {e}")
            print("Please update it manually.")
    
    return private_key

if __name__ == "__main__":
    main() 