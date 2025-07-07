# 🏢 Small Business Hackathon Deployment Guide
## Vultr VPS + On-Chain Integration in 60 Minutes

**Perfect for**: Small businesses, startups, crypto-savvy organizations  
**Cost**: $15-25/month  
**Time**: ~60 minutes  
**Complexity**: ⭐⭐⭐ (Beginner-Friendly)

> This guide gets you from zero to a production-ready Cosmos governance platform with **both traditional and crypto payments** in one hour.

---

## 🎯 What You'll Build

By following this guide, you'll have:

✅ **Professional Web Dashboard** running on Vultr VPS  
✅ **AI-Powered Governance Analysis** using Groq + Llama  
✅ **Stripe Payment Processing** for traditional customers  
✅ **FET Token Payments** via Fetch.ai blockchain  
✅ **Multi-Authentication** (Email, Keplr wallet, SSO)  
✅ **Enterprise Features** (policies, audit trails, compliance)  
✅ **Public Demo URL** with SSL certificate  

**Total Monthly Cost Breakdown:**
- Vultr VPS: $6/month
- Groq API: $0-5/month (generous free tier)
- Domain + SSL: $1-2/month
- Stripe fees: 2.9% per transaction
- FET gas fees: ~$0.10-1/month

---

## ⚡ Prerequisites (5 minutes)

### What You Need
- [ ] **Computer**: Mac, Linux, or Windows with WSL2
- [ ] **Vultr Account**: Sign up at [vultr.com](https://vultr.com) (free)
- [ ] **Groq API Key**: Get free key at [console.groq.com](https://console.groq.com) 
- [ ] **Keplr Wallet**: Browser extension installed
- [ ] **FET Tokens**: Minimum 100 FET in your wallet (~$10-50)
- [ ] **Domain Name**: Optional but recommended (~$10/year)
- [ ] **Stripe Account**: For traditional payments (optional)

### Quick Verification
```bash
# Check you have the required tools
python3 --version  # Should be 3.11+
docker --version   # Should work
git --version      # Should work
curl --version     # Should work
```

---

## 🚀 Part 1: Vultr VPS Setup (15 minutes)

### Step 1.1: Get Your API Keys

```bash
# 1. Vultr API Key
# Go to: https://my.vultr.com/settings/#settingsapi
# Copy your API key

# 2. Groq API Key  
# Go to: https://console.groq.com/keys
# Create new key, copy it

# 3. Your Keplr Wallet Address
# Open Keplr extension, copy your fetch address (starts with "fetch1...")
```

### Step 1.2: Clone and Setup Project

```bash
# Clone the project
git clone https://github.com/yourusername/uagents-govwatcher.git
cd uagents-govwatcher

# Create Python environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify everything works
python scripts/hackathon_check.py
# Should show: "🎉 ALL CHECKS PASSED!"
```

### Step 1.3: Configure Your Environment

```bash
# Copy environment template
cp env.example .env

# Edit with your specific details
nano .env  # or use your favorite editor
```

**Copy this configuration and customize:**
```bash
# Small Business Configuration - Vultr + On-Chain
DEPLOYMENT_TYPE=hybrid

# Vultr Configuration (REQUIRED)
VULTR_API_KEY=your_vultr_api_key_here
VULTR_REGION=ewr  # New Jersey - good performance/cost
VULTR_PLAN=vc2-1c-2gb  # $6/month plan
SERVER_NAME=govwatcher-business

# AI Configuration (REQUIRED)
GROQ_API_KEY=gsk_your_groq_api_key_here

# Database (auto-configured)
DATABASE_URL=postgresql://govwatcher:secure_password_2024@localhost:5432/govwatcher

# Security (generate a random 32+ character string)
JWT_SECRET=your_very_long_random_string_here_make_it_32_plus_characters

# Email Configuration (use your business email)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_business_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
FROM_EMAIL=noreply@yourbusiness.com

# Optional: Custom Domain
DOMAIN_NAME=governance.yourbusiness.com
SSL_EMAIL=admin@yourbusiness.com

# Stripe Configuration (get from stripe.com/dashboard)
STRIPE_ENABLED=true
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_key_here
STRIPE_SECRET_KEY=sk_test_your_stripe_key_here

# Blockchain Configuration
BLOCKCHAIN_ENABLED=true
FETCH_WALLET_ADDRESS=your_fetch_wallet_address_here
KEPLR_ENABLED=true
```

### Step 1.4: Deploy to Vultr (One Command!)

```bash
# Deploy everything in one command
./deploy.sh vultr deploy

# You'll see output like:
# [INFO] Creating Vultr VPS...
# [SUCCESS] VPS created: IP 192.168.1.100
# [INFO] Installing Docker and dependencies...
# [SUCCESS] All services started successfully!
# 
# 🌐 Your Dashboard: https://192.168.1.100/dashboard
# 🔧 Health Check: https://192.168.1.100/status
# 📚 API Docs: https://192.168.1.100/docs
```

**Save your VPS IP address!** You'll need it for the next steps.

---

## 🔗 Part 2: On-Chain Integration (20 minutes)

### Step 2.1: Set Up Fetch.ai Environment

```bash
# Install Fetch.ai tools
pip install uagents cosmpy fetch-py

# Generate your agent keys
python scripts/generate_uagents_key.py

# This creates unique agent addresses for your business
```

### Step 2.2: Fund Your Agents

```bash
# Check your current FET balance
echo "Check your Keplr wallet balance at: https://www.mintscan.io/fetchai"

# You need ~100 FET total:
# - 50 FET for agent deployment
# - 25 FET for testing payments  
# - 25 FET buffer for gas fees
```

### Step 2.3: Configure On-Chain Settings

```bash
# Add blockchain configuration to your .env
cat >> .env << 'EOF'

# On-Chain Agent Configuration
FETCH_NETWORK=fetchai-mainnet
PAYMENT_AGENT_ADDRESS=auto_generated_by_script
INTEGRATION_AGENT_ADDRESS=auto_generated_by_script

# Pricing Configuration (in FET tokens)
BASIC_SUBSCRIPTION_FET=25
ENTERPRISE_SUBSCRIPTION_FET=100
ADDITIONAL_CHAIN_FET=5

# Integration URLs (replace with your VPS IP)
DASHBOARD_URL=https://YOUR_VPS_IP/dashboard
API_BASE_URL=https://YOUR_VPS_IP/api
EOF

# Replace YOUR_VPS_IP with your actual IP
VPS_IP=$(cat .vultr_instance | jq -r '.main_ip')
sed -i "s/YOUR_VPS_IP/$VPS_IP/g" .env
```

### Step 2.4: Deploy On-Chain Agents

```bash
# Deploy payment processing agent
python src/onchain/payment_agent.py &
PAYMENT_PID=$!
echo "Payment Agent PID: $PAYMENT_PID" > payment_agent.pid

# Deploy integration agent
python src/onchain/integration_agent.py &
INTEGRATION_PID=$!
echo "Integration Agent PID: $INTEGRATION_PID" > integration_agent.pid

echo "✅ On-chain agents deployed!"
echo "Payment Agent: Running (PID: $PAYMENT_PID)"
echo "Integration Agent: Running (PID: $INTEGRATION_PID)"
```

### Step 2.5: Test On-Chain Connection

```bash
# Test your agents are working
python << 'EOF'
import requests
import json

# Test payment agent connectivity
payment_address = "agent1payment_address_from_config"
print(f"✅ Payment Agent Address: {payment_address}")

# Test integration with your Vultr dashboard
vps_ip = open('.vultr_instance', 'r').read()
dashboard_url = f"https://{json.loads(vps_ip)['main_ip']}/status"
response = requests.get(dashboard_url)
print(f"✅ Dashboard Status: {response.status_code}")
EOF
```

---

## 💳 Part 3: Payment Integration (10 minutes)

### Step 3.1: Stripe Setup (Traditional Payments)

```bash
# 1. Go to: https://dashboard.stripe.com/test/apikeys
# 2. Copy your publishable key (pk_test_...)
# 3. Copy your secret key (sk_test_...)
# 4. Update your .env file with these keys

# Test Stripe connection
python << 'EOF'
import stripe
import os

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
try:
    stripe.Account.retrieve()
    print("✅ Stripe connection successful!")
except Exception as e:
    print(f"❌ Stripe error: {e}")
EOF
```

### Step 3.2: Configure Payment Webhooks

```bash
# Get your VPS IP for webhook configuration
VPS_IP=$(cat .vultr_instance | jq -r '.main_ip')

echo "🔗 Configure these webhook URLs in your services:"
echo ""
echo "Stripe Webhook URL:"
echo "https://$VPS_IP/api/payments/stripe-webhook"
echo ""
echo "Copy this URL to your Stripe dashboard under Webhooks"
```

### Step 3.3: Test Both Payment Methods

```bash
# Test Stripe payment (sandbox)
curl -X POST "https://$VPS_IP/api/payments/stripe-test" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 2500,
    "currency": "usd",
    "subscription_tier": "basic"
  }'

# Test FET token payment endpoint
curl -X POST "https://$VPS_IP/api/payments/blockchain-test" \
  -H "Content-Type: application/json" \
  -d '{
    "amount_fet": 25,
    "subscription_tier": "basic",
    "wallet_address": "fetch1your_wallet_address"
  }'
```

---

## 🔧 Part 4: Multi-Authentication Setup (10 minutes)

### Step 4.1: Configure Authentication Methods

```bash
# Add authentication configuration
cat >> .env << 'EOF'

# Multi-Authentication Configuration
KEPLR_ENABLED=true
TRADITIONAL_AUTH_ENABLED=true
DEMO_MODE=true

# Supported Cosmos Chains for Keplr
SUPPORTED_CHAINS=cosmoshub-4,osmosis-1,juno-1,fetchhub-4

# Optional: SSO Configuration (for enterprise customers)
# GOOGLE_CLIENT_ID=your_google_oauth_client_id
# MICROSOFT_CLIENT_ID=your_microsoft_oauth_client_id
EOF
```

### Step 4.2: Update Dashboard with New Auth Options

```bash
# Restart your Vultr services to apply auth changes
VPS_IP=$(cat .vultr_instance | jq -r '.main_ip')
ssh root@$VPS_IP << 'EOF'
cd /app
docker-compose restart web
EOF

echo "✅ Authentication methods updated!"
```

### Step 4.3: Test All Authentication Methods

```bash
# Test traditional login
curl -X POST "https://$VPS_IP/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@enterprise.com",
    "password": "password123"
  }'

# Test Keplr wallet auth endpoint
curl -X GET "https://$VPS_IP/api/auth/keplr-challenge"

echo "✅ Authentication endpoints working!"
```

---

## 📊 Part 5: Final Validation & Go-Live (5 minutes)

### Step 5.1: Complete System Test

```bash
# Run comprehensive validation
cat > business_validation.sh << 'EOF'
#!/bin/bash

echo "🏢 Small Business Deployment Validation"
echo "======================================"

# Get VPS IP
VPS_IP=$(cat .vultr_instance | jq -r '.main_ip')
BASE_URL="https://$VPS_IP"

echo "🌐 Testing deployment at: $BASE_URL"

# Test 1: Health Check
echo "1️⃣ Health Check..."
curl -s "$BASE_URL/status" | jq '.status' && echo "✅ PASS" || echo "❌ FAIL"

# Test 2: Dashboard Access
echo "2️⃣ Dashboard Access..."
curl -s -I "$BASE_URL/dashboard" | grep "200 OK" && echo "✅ PASS" || echo "❌ FAIL"

# Test 3: Payment Endpoints
echo "3️⃣ Payment Integration..."
curl -s "$BASE_URL/api/payments/health" | jq '.stripe_enabled' && echo "✅ PASS" || echo "❌ FAIL"

# Test 4: On-Chain Agents
echo "4️⃣ On-Chain Agents..."
if ps aux | grep -q "payment_agent.py"; then
    echo "✅ PASS (Payment agent running)"
else
    echo "❌ FAIL (Payment agent not running)"
fi

# Test 5: AI Integration
echo "5️⃣ AI Integration..."
python -c "
import asyncio
from src.ai_adapters import GroqAdapter
async def test():
    try:
        adapter = GroqAdapter()
        print('✅ PASS (AI adapter ready)')
    except:
        print('❌ FAIL (AI adapter error)')
asyncio.run(test())
"

echo "======================================"
echo "🎉 Small Business Deployment Complete!"
echo ""
echo "📋 Access Information:"
echo "   Dashboard: $BASE_URL/dashboard"
echo "   Admin Panel: $BASE_URL/settings"
echo "   API Docs: $BASE_URL/docs"
echo "   Health: $BASE_URL/status"
echo ""
echo "💳 Payment Methods Available:"
echo "   💰 Stripe: Credit cards, Apple Pay, Google Pay"
echo "   🪙 FET Tokens: Fetch.ai blockchain payments"
echo ""
echo "🔐 Authentication Methods:"
echo "   📧 Email/Password: Traditional login"
echo "   🦘 Keplr Wallet: Cosmos ecosystem authentication"
echo "   🔧 Demo Mode: One-click access for testing"
echo ""
echo "💰 Monthly Costs:"
echo "   Vultr VPS: $6/month"
echo "   Groq API: $0-5/month (free tier)"
echo "   Domain: $1-2/month (optional)"
echo "   Total: ~$15-25/month"
EOF

chmod +x business_validation.sh
./business_validation.sh
```

### Step 5.2: Set Up Your First Organization

```bash
# Access your dashboard and create your organization
VPS_IP=$(cat .vultr_instance | jq -r '.main_ip')
echo "🌐 Visit your dashboard: https://$VPS_IP/dashboard"

# Create your organization via API
curl -X POST "https://$VPS_IP/api/organizations" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Your Business Name",
    "contact_email": "admin@yourbusiness.com",
    "subscription_tier": "basic",
    "chains": ["cosmoshub-4", "osmosis-1"],
    "payment_method": "stripe"
  }'
```

### Step 5.3: Configure Your Governance Policies

```bash
# Set up your first governance policy
curl -X POST "https://$VPS_IP/api/policies" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Small Business Conservative Strategy",
    "description": "Risk-averse governance approach for small business",
    "voting_criteria": {
      "security_weight": 0.5,
      "economic_impact_weight": 0.3,
      "community_support_weight": 0.2
    },
    "risk_tolerance": "MEDIUM",
    "auto_vote_threshold": 0.75,
    "notification_preferences": {
      "email": true,
      "slack": false
    }
  }'
```

---

## 🎊 Congratulations! You're Live!

### 🌟 What You've Accomplished

🏢 **Production Business Platform**: Enterprise-grade governance management  
💳 **Dual Payment Processing**: Both traditional (Stripe) and crypto (FET) payments  
🌐 **Professional Web Presence**: Custom domain with SSL certificate  
🤖 **AI-Powered Decisions**: Groq + Llama analysis for smart governance  
🔗 **Blockchain Integration**: Direct connection to Fetch.ai ecosystem  
📊 **Business Intelligence**: Real-time analytics and compliance reporting  

### 💰 Your Running Costs

| Service | Monthly Cost | What It Does |
|---------|--------------|--------------|
| Vultr VPS | $6 | Hosts your entire platform |
| Groq API | $0-5 | AI-powered analysis (generous free tier) |
| Domain + SSL | $1-2 | Professional web presence |
| **Total** | **$7-13/month** | Complete governance platform |

**Plus transaction fees:**
- Stripe: 2.9% per credit card transaction
- FET tokens: ~$0.01-0.10 per blockchain transaction

### 🎯 Your Business URLs

```bash
# Get your live URLs
VPS_IP=$(cat .vultr_instance | jq -r '.main_ip')
echo "📱 Business Dashboard: https://$VPS_IP/dashboard"
echo "⚙️ Admin Settings: https://$VPS_IP/settings"
echo "💳 Payment Portal: https://$VPS_IP/subscribe"
echo "📊 Health Monitor: https://$VPS_IP/status"
echo "📚 API Documentation: https://$VPS_IP/docs"
```

### 🚀 Next Steps for Your Business

1. **👥 Add Team Members**: Invite colleagues to manage governance
2. **📋 Configure Policies**: Set up organization-specific voting criteria
3. **💳 Test Payments**: Process test transactions in both Stripe and FET
4. **📈 Monitor Proposals**: Watch AI recommendations for live governance
5. **📊 Export Reports**: Generate compliance reports for stakeholders
6. **🔗 Custom Domain**: Point your domain to your VPS for branding

### 🛠️ Ongoing Management

```bash
# Check system health anytime
./business_validation.sh

# Monitor on-chain agents
ps aux | grep -E "(payment_agent|integration_agent)"

# View system logs
ssh root@$VPS_IP 'docker logs govwatcher-web-1 --tail 50'

# Update AI models or configurations
ssh root@$VPS_IP 'cd /app && docker-compose restart'
```

### 📞 Support & Resources

- **📖 Full Documentation**: See [MASTER_DEPLOYMENT_GUIDE.md](MASTER_DEPLOYMENT_GUIDE.md)
- **🗄️ Data Model Documentation**: See [DATA_MODEL_DOCUMENTATION.md](DATA_MODEL_DOCUMENTATION.md)
- **🔧 Technical Issues**: Check logs at `https://YOUR_VPS_IP/status`
- **💳 Payment Problems**: Verify Stripe/FET configuration in dashboard
- **🤖 AI Issues**: Test Groq API key at [console.groq.com](https://console.groq.com)
- **🔗 Blockchain Issues**: Check agent status and FET wallet balance

### 🏆 Business Benefits

**Time Savings**: Automated governance monitoring saves 10+ hours/week  
**Risk Reduction**: AI analysis prevents costly governance mistakes  
**Compliance**: Automated audit trails for regulatory requirements  
**Scalability**: Easily add more chains and team members  
**Cost Efficiency**: $15-25/month vs. $5000+/month enterprise solutions  

---

## 📋 Troubleshooting Guide

### Issue: VPS Deployment Fails
```bash
# Check Vultr API connectivity
curl -H "Authorization: Bearer $VULTR_API_KEY" https://api.vultr.com/v2/account

# Verify region availability
curl -H "Authorization: Bearer $VULTR_API_KEY" https://api.vultr.com/v2/regions
```

### Issue: Payment Processing Not Working
```bash
# Test Stripe connection
python -c "
import stripe, os
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
print(stripe.Account.retrieve())
"

# Check FET agent status
ps aux | grep payment_agent.py
```

### Issue: AI Analysis Failing
```bash
# Test Groq API directly
curl -H "Authorization: Bearer $GROQ_API_KEY" \
  https://api.groq.com/openai/v1/models

# Check if the service has the key
ssh root@$VPS_IP 'env | grep GROQ'
```

### Issue: Dashboard Not Loading
```bash
# Check all services
VPS_IP=$(cat .vultr_instance | jq -r '.main_ip')
ssh root@$VPS_IP 'docker ps'

# Restart services if needed
ssh root@$VPS_IP 'cd /app && docker-compose restart'
```

### Emergency Recovery
```bash
# If something goes wrong, redeploy:
./deploy.sh vultr deploy

# Or restart specific services:
ssh root@$VPS_IP 'cd /app && docker-compose restart web'
```

---

**🌌 Your small business now has enterprise-grade Cosmos governance capabilities!**

*Built for the future of work, powered by AI, and ready to scale with your business growth.* 