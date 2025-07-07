#!/usr/bin/env python3
"""Load environment variables from .env file."""

import os
from pathlib import Path

def load_env():
    """Load environment variables from .env file."""
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                # Remove inline comments
                if ' #' in value:
                    value = value.split(' #')[0].strip()
                
                os.environ[key] = value
    
    return True

if __name__ == "__main__":
    if load_env():
        print("✅ Environment variables loaded from .env")
        # Show some key variables (without sensitive values)
        print(f"AWS_REGION: {os.getenv('AWS_REGION', 'Not set')}")
        print(f"DOMAIN_NAME: {os.getenv('DOMAIN_NAME', 'Not set')}")
        print(f"OPENAI_API_KEY: {'Set' if os.getenv('OPENAI_API_KEY') else 'Not set'}")
    else:
        print("❌ Failed to load environment variables") 