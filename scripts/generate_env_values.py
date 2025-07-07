#!/usr/bin/env python3
"""
Generate missing environment variables for the Cosmos GRC Co-Pilot
This script helps you create secure values for JWT secrets and other configurations
"""

import secrets
import string
import os

def generate_jwt_secret(length=64):
    """Generate a secure JWT secret"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_uagents_key():
    """Generate a uAgents private key"""
    return secrets.token_hex(32)

def main():
    print("🔐 Cosmos GRC Co-Pilot - Environment Variable Generator")
    print("=" * 60)
    
    # Generate JWT secret
    jwt_secret = generate_jwt_secret()
    print(f"JWT_SECRET={jwt_secret}")
    print()
    
    # Generate uAgents key
    uagents_key = generate_uagents_key()
    print(f"UAGENTS_PRIVATE_KEY={uagents_key}")
    print()
    
    print("📧 Email Configuration Instructions:")
    print("=" * 40)
    print("For Gmail SMTP (recommended for testing):")
    print("1. Go to: https://myaccount.google.com/security")
    print("2. Enable 2-Step Verification")
    print("3. Go to: https://myaccount.google.com/apppasswords")
    print("4. Generate an App Password for 'Mail'")
    print("5. Use these values:")
    print("   SMTP_SERVER=smtp.gmail.com")
    print("   SMTP_PORT=587")
    print("   SMTP_USERNAME=your-email@gmail.com")
    print("   SMTP_PASSWORD=your-16-character-app-password")
    print("   FROM_EMAIL=your-email@gmail.com")
    print()
    
    print("🔗 API Keys You Need:")
    print("=" * 25)
    print("1. Vultr API Key:")
    print("   - Go to: https://my.vultr.com/settings/#settingsapi")
    print("   - Create new API key")
    print("   - Copy the key")
    print()
    print("2. Groq API Key:")
    print("   - Go to: https://console.groq.com/keys")
    print("   - Create new API key")
    print("   - Copy the key")
    print()
    print("3. Stripe Keys (Optional, for payments):")
    print("   - Go to: https://dashboard.stripe.com/test/apikeys")
    print("   - Copy Publishable key (pk_test_...)")
    print("   - Copy Secret key (sk_test_...)")
    print()
    
    print("📝 Complete .env Template:")
    print("=" * 25)
    print("Copy this to your .env file and fill in the API keys:")
    print()
    
    env_template = f"""# Generated configuration
DEPLOYMENT_TYPE=vultr
CLOUD_PROVIDER=vultr

# REQUIRED: Get from https://my.vultr.com/settings/#settingsapi
VULTR_API_KEY=your_vultr_api_key_here

# REQUIRED: Get from https://console.groq.com/keys
GROQ_API_KEY=your_groq_api_key_here

# Generated secure values
JWT_SECRET={jwt_secret}
UAGENTS_PRIVATE_KEY={uagents_key}

# Database
DATABASE_URL=postgresql://govwatcher:strongpassword123@postgres:5432/govwatcher
POSTGRES_PASSWORD=strongpassword123

# Web server
WEB_HOST=0.0.0.0
WEB_PORT=8080

# Email (configure with your Gmail)
FROM_EMAIL=your-email@gmail.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
SMTP_USE_TLS=true

# Blockchain
FETCH_NETWORK=fetchai-mainnet
FETCH_RPC_URL=https://rpc-fetchhub.fetch.ai
FETCH_CHAIN_ID=fetchhub-4

# Agent configuration
SUBSCRIPTION_AGENT_SEED=govwatcher_subscription_vultr_track_2024
WATCHER_AGENT_SEED=govwatcher_watcher_vultr_track_2024
ANALYSIS_AGENT_SEED=govwatcher_analysis_vultr_track_2024
MAIL_AGENT_SEED=govwatcher_mail_vultr_track_2024

# Optional: Stripe payments
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_key_here
STRIPE_SECRET_KEY=sk_test_your_stripe_key_here

# Development
ENVIRONMENT=development
CHAIN_ID=cosmoshub-4
"""
    
    print(env_template)
    
    # Save to file
    with open('.env.generated', 'w') as f:
        f.write(env_template)
    
    print("✅ Template saved to .env.generated")
    print("📋 Next steps:")
    print("1. Copy .env.generated to .env")
    print("2. Replace 'your_vultr_api_key_here' with your actual Vultr API key")
    print("3. Replace 'your_groq_api_key_here' with your actual Groq API key")
    print("4. Configure email settings with your Gmail credentials")
    print("5. Run: ./deploy.sh vultr deploy")

if __name__ == "__main__":
    main() 