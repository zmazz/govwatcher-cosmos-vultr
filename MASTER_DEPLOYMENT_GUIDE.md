# 🌌 Cosmos GRC Co-Pilot - Complete Deployment Guide
## From Development to Production

This guide provides comprehensive deployment instructions for the Cosmos Governance Risk & Compliance Co-Pilot. Choose your deployment method based on your needs and technical requirements.

---

## 📋 Table of Contents

1. [🎯 Deployment Options Overview](#-deployment-options-overview)
2. [⚡ Prerequisites & Setup](#-prerequisites--setup)
3. [🟦 Option A: Vultr VPS Deployment](#-option-a-vultr-vps-deployment)
4. [🟠 Option B: AWS CloudFormation](#-option-b-aws-cloudformation)
5. [🔄 Option C: Docker Compose (Local)](#-option-c-docker-compose-local)
6. [🔗 Option D: Hybrid Deployment](#-option-d-hybrid-deployment)
7. [📊 Monitoring & Validation](#-monitoring--validation)
8. [🚨 Troubleshooting](#-troubleshooting)

**📚 Related Documentation:**
- [🗄️ Data Model Documentation](DATA_MODEL_DOCUMENTATION.md) - Database schemas and API reference
- [🏢 Hackathon Quick Start](MASTER_DEPLOYMENT_GUIDE_HACKATHON.md) - 60-minute setup guide

---

## 🎯 Deployment Options Overview

Choose your deployment method:

| Option | Best For | Time | Monthly Cost | Complexity | Status |
|--------|----------|------|--------------|------------|---------|
| **Vultr VPS** | Most users, hackathons | 30 min | $6-12 | ⭐⭐ | ✅ Implemented |
| **AWS CloudFormation** | Enterprise scale | 45 min | $25-100 | ⭐⭐⭐ | ✅ Implemented |
| **Docker Compose** | Development/testing | 5 min | Free | ⭐ | ✅ Implemented |
| **Hybrid** | Maximum flexibility | 60 min | $30-120 | ⭐⭐⭐⭐ | 🔄 Partial |

---

## ⚡ Prerequisites & Setup

### System Requirements
- **Operating System**: Linux, macOS, or Windows with WSL2
- **Python**: 3.11 or higher
- **Docker**: Latest version with Docker Compose
- **Memory**: 8GB+ RAM recommended
- **Storage**: 20GB+ available space

### Step 1: Clone and Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/govwatcher-cosmos-vultr.git
cd govwatcher-cosmos-vultr

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Get API Keys

#### Required API Keys
```bash
# Groq API (Primary AI provider)
# Get from: https://console.groq.com/keys
GROQ_API_KEY=gsk_your_groq_api_key_here

# OpenAI API (Fallback, optional)
# Get from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk_your_openai_api_key_here
```

#### Platform-Specific Keys
```bash
# For Vultr deployment
VULTR_API_KEY=your_vultr_api_key  # Get from: https://my.vultr.com/settings/#settingsapi

# For AWS deployment
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
```

### Step 3: Configure Environment
```bash
# Copy environment template
cp env.example .env

# Edit with your configuration
nano .env  # or use your preferred editor
```

**Essential Configuration:**
```bash
# AI Configuration (REQUIRED)
GROQ_API_KEY=gsk_your_groq_api_key_here

# Database
DATABASE_URL=sqlite:///./data/govwatcher.db  # Local development
# DATABASE_URL=postgresql://user:pass@localhost:5432/govwatcher  # Production

# Security
JWT_SECRET=your_very_long_random_secret_key_here

# Email (optional, for notifications)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### Step 4: Validate Setup
```bash
# Run compliance check
python scripts/hackathon_check.py
# Should show: 🎉 ALL CHECKS PASSED! (9/9)

# Test basic functionality
python scripts/test_basic_setup.py

# Generate test data
python scripts/generate_governance_data.py
```

---

## 🟦 Option A: Vultr VPS Deployment

**Best for**: Most users, cost-effective, Vultr Track compliance

### A1: Vultr Account Setup
1. Create account at [vultr.com](https://vultr.com)
2. Get API key from [vultr.com/settings/api](https://my.vultr.com/settings/#settingsapi)
3. Test API access:
```bash
export VULTR_API_KEY=your_vultr_api_key_here
curl -H "Authorization: Bearer $VULTR_API_KEY" https://api.vultr.com/v2/account
```

### A2: Configure Vultr Settings
```bash
# Add to .env file
cat >> .env << 'EOF'
DEPLOYMENT_TYPE=vultr
VULTR_API_KEY=your_vultr_api_key_here
VULTR_REGION=ewr  # New Jersey
VULTR_PLAN=vc2-1c-2gb  # $6/month
SERVER_NAME=govwatcher-prod

# Optional: Custom domain
DOMAIN_NAME=yourdomain.com
SSL_EMAIL=admin@yourdomain.com
EOF
```

### A3: Deploy to Vultr
```bash
# Deploy complete stack
./deploy.sh vultr deploy

# Monitor deployment
./deploy.sh vultr status

# Expected output:
# ✅ VPS created: IP 192.168.1.100
# ✅ Docker services started
# ✅ Application healthy
```

### A4: Access Your Deployment
```bash
# Get VPS IP
VPS_IP=$(./deploy.sh vultr get-ip)

# Access URLs
echo "Dashboard: https://$VPS_IP/dashboard"
echo "Health: https://$VPS_IP/status"
echo "API Docs: https://$VPS_IP/docs"
```

**✅ Vultr deployment complete!** Cost: ~$6-12/month

---

## 🟠 Option B: AWS CloudFormation

**Best for**: Enterprise organizations, scalability requirements

### B1: AWS Prerequisites
```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Default region: us-east-1
# Default output format: json

# Verify access
aws sts get-caller-identity
```

### B2: Configure AWS Settings
```bash
# Add to .env file
cat >> .env << 'EOF'
DEPLOYMENT_TYPE=aws
AWS_REGION=us-east-1
STACK_NAME=govwatcher-enterprise
STAGE=prod
EOF
```

### B3: Deploy to AWS
```bash
# Deploy CloudFormation stack
./deploy.sh aws deploy

# Monitor deployment
./deploy.sh aws status

# Get deployment info
aws cloudformation describe-stacks --stack-name govwatcher-enterprise
```

### B4: Access AWS Deployment
```bash
# Get API Gateway URL
API_URL=$(aws cloudformation describe-stacks \
  --stack-name govwatcher-enterprise \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text)

echo "API URL: $API_URL"
echo "Dashboard: $API_URL/dashboard"
```

**✅ AWS deployment complete!** Cost: ~$25-100/month

---

## 🔄 Option C: Docker Compose (Local)

**Best for**: Development, testing, local demos

### C1: Start Local Services
```bash
# Start all services
docker-compose -f infra/docker/docker-compose.yml up -d

# Check status
docker-compose -f infra/docker/docker-compose.yml ps

# View logs
docker-compose -f infra/docker/docker-compose.yml logs -f
```

### C2: Access Local Deployment
```bash
# Application URLs
echo "Dashboard: http://localhost:8080/dashboard"
echo "Health: http://localhost:8080/status"
echo "API Docs: http://localhost:8080/docs"

# Database access
docker exec -it govwatcher-postgres psql -U govwatcher -d govwatcher
```

### C3: Development Commands
```bash
# Restart specific service
docker-compose -f infra/docker/docker-compose.yml restart web

# Stop all services
docker-compose -f infra/docker/docker-compose.yml down

# Clean up volumes
docker-compose -f infra/docker/docker-compose.yml down -v
```

**✅ Local deployment complete!** Cost: Free

---

## 🔗 Option D: Hybrid Deployment

**Best for**: Maximum flexibility and redundancy

### D1: Deploy Frontend (Vultr)
```bash
# Deploy web interface to Vultr
./deploy.sh vultr deploy

# Get frontend URL
FRONTEND_URL=$(./deploy.sh vultr get-ip)
```

### D2: Deploy Backend (AWS)
```bash
# Deploy serverless backend
export DEPLOYMENT_TARGET=backend-only
./deploy.sh aws deploy

# Get backend URL
BACKEND_URL=$(aws cloudformation describe-stacks \
  --stack-name govwatcher-enterprise \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text)
```

### D3: Configure Integration
```bash
# Update frontend to use AWS backend
ssh root@$FRONTEND_URL << EOF
echo "AWS_BACKEND_URL=$BACKEND_URL" >> /app/.env
docker-compose restart web
EOF
```

**✅ Hybrid deployment complete!** Cost: ~$30-120/month

---

## 📊 Monitoring & Validation

### Health Monitoring
```bash
# Create monitoring script
cat > monitor_health.py << 'EOF'
#!/usr/bin/env python3
import requests
import json
import sys
from datetime import datetime

def check_health(base_url):
    """Check system health"""
    try:
        response = requests.get(f"{base_url}/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {base_url} - {data.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ {base_url} - HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {base_url} - Error: {e}")
        return False

if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    success = check_health(base_url)
    sys.exit(0 if success else 1)
EOF

chmod +x monitor_health.py

# Test monitoring
python monitor_health.py http://localhost:8080
```

### Compliance Validation
```bash
# Run all validation checks
python scripts/hackathon_check.py

# Validate data models
python scripts/validate_data_models.py

# Test AI integration
python -c "
import asyncio
from src.ai_adapters import GroqAdapter

async def test_ai():
    adapter = GroqAdapter()
    print('AI adapter initialized successfully')

asyncio.run(test_ai())
"
```

### Performance Testing
```bash
# Basic performance test
cat > performance_test.py << 'EOF'
#!/usr/bin/env python3
import requests
import time
import statistics

def test_performance(base_url, num_requests=10):
    """Test API performance"""
    response_times = []
    
    for i in range(num_requests):
        start = time.time()
        try:
            response = requests.get(f"{base_url}/status", timeout=10)
            end = time.time()
            if response.status_code == 200:
                response_times.append(end - start)
        except Exception as e:
            print(f"Request {i+1} failed: {e}")
    
    if response_times:
        avg_time = statistics.mean(response_times)
        print(f"Average response time: {avg_time:.3f}s")
        print(f"Min: {min(response_times):.3f}s, Max: {max(response_times):.3f}s")
    else:
        print("All requests failed")

if __name__ == "__main__":
    import sys
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    test_performance(base_url)
EOF

chmod +x performance_test.py
python performance_test.py http://localhost:8080
```

---

## 🚨 Troubleshooting

### Common Issues

#### Issue 1: Health Check Fails
```bash
# Check service status
docker ps
docker logs govwatcher-web

# For Vultr deployment
ssh root@$VPS_IP 'docker ps'
ssh root@$VPS_IP 'docker logs govwatcher-web'
```

#### Issue 2: AI Analysis Not Working
```bash
# Verify API keys
echo "Groq API Key: ${GROQ_API_KEY:0:10}..."

# Test API directly
curl -H "Authorization: Bearer $GROQ_API_KEY" \
  https://api.groq.com/openai/v1/models

# Check application logs
docker logs govwatcher-web | grep -i groq
```

#### Issue 3: Database Connection Issues
```bash
# For PostgreSQL
docker exec -it govwatcher-postgres psql -U govwatcher -d govwatcher -c "SELECT 1;"

# For SQLite
ls -la data/govwatcher.db
sqlite3 data/govwatcher.db ".tables"
```

#### Issue 4: Deployment Failures
```bash
# Check deployment logs
./deploy.sh vultr logs

# Verify prerequisites
python scripts/test_basic_setup.py

# Clean and retry
./deploy.sh vultr cleanup
./deploy.sh vultr deploy
```

### Recovery Procedures

#### Emergency Restart
```bash
# Docker Compose
docker-compose -f infra/docker/docker-compose.yml restart

# Vultr VPS
ssh root@$VPS_IP 'cd /app && docker-compose restart'

# AWS Lambda
aws lambda update-function-code --function-name govwatcher-web
```

#### Data Recovery
```bash
# Backup database
docker exec govwatcher-postgres pg_dump -U govwatcher govwatcher > backup.sql

# Restore from backup
docker exec -i govwatcher-postgres psql -U govwatcher govwatcher < backup.sql
```

---

## 📋 Post-Deployment Checklist

### Immediate Validation
- [ ] Health endpoint returns 200 OK
- [ ] Dashboard loads without errors
- [ ] AI analysis is functional
- [ ] Database connections work
- [ ] All Docker containers are healthy

### Security Checklist
- [ ] JWT secrets are properly configured
- [ ] Database passwords are secure
- [ ] API keys are not exposed in logs
- [ ] HTTPS is enabled (production)
- [ ] Firewall rules are configured

### Performance Checklist
- [ ] Response times are acceptable (<2s)
- [ ] Database queries are optimized
- [ ] Caching is working
- [ ] Resource usage is reasonable
- [ ] Error rates are low

### Monitoring Setup
- [ ] Health monitoring is active
- [ ] Log aggregation is configured
- [ ] Alerts are set up
- [ ] Backup procedures are tested
- [ ] Documentation is updated

---

## 🎉 Success!

Your Cosmos Governance Risk & Compliance Co-Pilot is now deployed and operational. 

### What's Next?
1. **Configure organization policies** in the dashboard
2. **Set up governance monitoring** for your chains
3. **Test AI recommendations** with real proposals
4. **Invite team members** to use the platform
5. **Monitor system health** and performance

### Support Resources
- **Documentation**: See `docs/` folder for detailed guides
- **Validation**: Run `python scripts/hackathon_check.py` anytime
- **Troubleshooting**: Check logs and use monitoring scripts
- **Updates**: Follow deployment procedures for updates

**🌌 Your governance platform is ready to transform how you participate in the Cosmos ecosystem!** 