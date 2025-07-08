# 📁 Repository Structure Guide

This document provides a comprehensive overview of the organized repository structure for the Cosmos Governance Risk & Compliance Co-Pilot (GovWatcher).

## 🗂️ Directory Overview

```
govwatcher-cosmos-vultr/
├── README.md                      # Main project documentation & demo links
├── requirements.txt               # Python dependencies
├── env.example                   # Environment template
├── deploy.sh                     # Legacy deployment script
├── Makefile                      # Project automation commands
├── .gitignore                    # Git ignore rules
├── .dockerignore                 # Docker ignore rules
│
├── 📁 src/                        # Source Code
│   ├── __init__.py               # Python package initialization
│   ├── models.py                 # Data models and schemas (SQLAlchemy)
│   ├── ai_adapters.py           # AI integration (Groq, OpenAI, Llama)
│   │
│   ├── web/                     # Web Application (FastAPI)
│   │   ├── main.py              # Main FastAPI application entry point
│   │   ├── templates/           # Jinja2 HTML templates
│   │   │   ├── index.html       # Landing page with auth options
│   │   │   ├── dashboard.html   # Enterprise dashboard interface
│   │   │   └── settings.html    # Policy configuration interface
│   │   └── static/              # Static assets (CSS, JS, images)
│   │
│   ├── agents/                  # Autonomous uAgent Implementations
│   │   ├── __init__.py          # Agent package initialization
│   │   ├── subscription_agent.py # Subscription management agent
│   │   ├── watcher_agent.py     # Governance proposal monitoring
│   │   ├── analysis_agent.py    # AI-powered proposal analysis
│   │   └── mail_agent.py        # Email notification system
│   │
│   ├── onchain/                 # Blockchain Integration
│   │   ├── payment_agent.py     # FET token payment processing
│   │   └── onchain-config.json  # Blockchain configuration
│   │
│   ├── utils/                   # Utility Modules
│   │   ├── __init__.py          # Utils package initialization
│   │   ├── logging.py           # Centralized logging configuration
│   │   ├── cosmos_client.py     # Cosmos blockchain client
│   │   └── aws_clients.py       # AWS service integrations
│   │
│   └── data/                    # Data processing modules
│
├── 📁 infra/                     # Infrastructure & Deployment
│   ├── docker/                  # Docker Configurations
│   │   ├── docker-compose.yml   # Multi-service orchestration
│   │   ├── Dockerfile           # Main application container
│   │   ├── Dockerfile.web       # Web application container
│   │   ├── Dockerfile.agents    # Agent services container
│   │   └── Dockerfile.simple    # Simple deployment option
│   │
│   ├── nginx/                   # Nginx Configuration
│   │   ├── nginx.conf           # Production nginx config
│   │   └── ssl/                 # SSL certificates directory
│   │
│   ├── vultr/                   # Vultr VPS Deployment
│   │   └── deploy-vultr.sh      # Vultr deployment automation
│   │
│   └── aws/                     # AWS CloudFormation Deployment
│       ├── deploy.sh            # AWS deployment script
│       └── stack.yml            # CloudFormation template
│
├── 📁 sql/                       # Database Schema
│   └── init.sql                 # PostgreSQL schema & demo data
│
├── 📁 scripts/                   # Utility & Automation Scripts
│   ├── hackathon_check.py       # Vultr Track compliance validator
│   ├── generate_uagents_key.py  # uAgent key generator
│   ├── load_env.py              # Environment loader utility
│   ├── test_basic_setup.py      # Basic setup testing
│   ├── validate_data_models.py  # Data model validation
│   ├── generate_governance_data.py # Governance data generator
│   ├── generate_test_data.py    # Test data generator
│   ├── generate_env_values.py   # Environment value generator
│   ├── deploy-onchain.sh        # Blockchain deployment automation
│   ├── get_vultr_password.py    # Vultr server password retrieval
│   ├── get_vultr_root_password.py # Vultr root password retrieval
│   ├── check_vultr_os.py        # Vultr OS verification
│   └── setup_ssh_key.py         # SSH key setup automation
│
├── 📁 tests/                     # Test Suite
│   ├── __init__.py              # Test package initialization
│   ├── conftest.py              # Pytest configuration
│   ├── test_models.py           # Data model tests
│   ├── test_business_logic.py   # Business logic tests
│   ├── test_watcher_agent.py    # Watcher agent tests
│   ├── test_analysis_agent.py   # Analysis agent tests
│   ├── test_subscription_agent.py # Subscription agent tests
│   ├── test_mail_agent.py       # Mail agent tests
│   └── test_aws_helpers.py      # AWS integration tests
│
├── 📁 docs/                      # Comprehensive Documentation
│   ├── README.md                # Documentation index & navigation
│   ├── MASTER_DEPLOYMENT_GUIDE.md # Complete deployment guide (all options)
│   ├── MASTER_DEPLOYMENT_GUIDE_HACKATHON.md # Quick Vultr deployment (60min)
│   ├── ONCHAIN.md               # Fetch.ai blockchain integration guide
│   ├── DATA_MODEL_SUMMARY.md    # Database schemas & API reference
│   ├── INTEGRATION_SUMMARY.md   # Multi-auth & payment architecture
│   └── REPOSITORY_STRUCTURE.md  # This file - codebase organization
│
├── 📁 data/                      # Local Development Data (git-ignored)
│   └── govwatcher.db            # Local SQLite database
│
└── 📁 .cursor/                   # Cursor IDE Configuration
    ├── scratchpad.md            # Development notes & planning
    └── instructions.md          # Development instructions
```

## 🎯 Key Architectural Decisions

### 1. **Infrastructure Separation**
- **`infra/`**: All deployment configurations isolated from source code
- **Platform-specific subdirectories**: `vultr/`, `aws/`, `docker/`, `nginx/`
- **Environment independence**: Same source code deploys to multiple platforms

### 2. **Source Code Organization**
- **`src/web/`**: Modern FastAPI web application with enterprise dashboard
- **`src/agents/`**: Autonomous uAgent implementations for governance automation
- **`src/onchain/`**: Blockchain integration with Fetch.ai payment processing
- **`src/utils/`**: Shared utilities for logging, blockchain clients, AWS integration
- **Clear separation of concerns** between web interface, agents, and utilities

### 3. **Database & Configuration**
- **`sql/`**: Version-controlled PostgreSQL schema with demo data
- **`data/`**: Local development data (git-ignored SQLite)
- **Environment templates**: `env.example` with comprehensive configuration options

### 4. **Documentation & Automation**
- **`docs/`**: Complete documentation suite with deployment guides
- **`scripts/`**: Comprehensive automation for deployment, testing, and validation
- **`tests/`**: Full test coverage for all components

### 5. **Enterprise Features**
- **Multi-tenant architecture**: Organization-based data isolation
- **AI-powered analysis**: Groq + OpenAI integration with custom adapters
- **Payment processing**: Both traditional (Stripe) and blockchain (FET tokens)
- **Compliance features**: Audit trails, policy templates, reporting

## 🚀 Quick Start Commands

### Local Development
```bash
# Setup environment
cp env.example .env
# Edit .env with your API keys and configuration

# Install dependencies
pip install -r requirements.txt

# Run web application
uvicorn src.web.main:app --reload --host 0.0.0.0 --port 8080

# Run compliance check
python scripts/hackathon_check.py

# Generate test data
python scripts/generate_test_data.py
```

### Docker Development
```bash
# Start all services locally
cd infra/docker
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f web
docker-compose logs -f analysis-agent
```

### Production Deployment

#### Vultr VPS (Recommended - 60 minutes)
```bash
export VULTR_API_KEY=your_api_key
export GROQ_API_KEY=your_groq_key
./infra/vultr/deploy-vultr.sh deploy
```

#### AWS CloudFormation (Enterprise)
```bash
aws configure  # Set up AWS credentials
./infra/aws/deploy.sh all
```

#### Blockchain Integration
```bash
# Deploy on-chain payment agents
./scripts/deploy-onchain.sh deploy

# Check agent status
./scripts/deploy-onchain.sh status
```

## 📋 Configuration Management

### Environment Variables
The system uses environment variables for configuration across all deployment targets:

- **`env.example`**: Comprehensive template with all configuration options
- **`infra/docker/.env`**: Docker Compose specific environment
- **Production**: Environment variables injected during deployment

### Key Configuration Categories

#### **AI Integration**
```bash
# Primary AI provider (required)
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-70b-versatile

# Fallback providers
OPENAI_API_KEY=your_openai_key
LLAMA_API_KEY=your_llama_key

# AI Configuration
AI_TEMPERATURE=0.3
AI_MAX_TOKENS=2000
```

#### **Database**
```bash
# Production PostgreSQL
DATABASE_URL=postgresql://user:pass@host:5432/db
POSTGRES_DB=govwatcher
POSTGRES_USER=govwatcher
POSTGRES_PASSWORD=secure_password

# Development SQLite
SQLITE_DATABASE_PATH=data/govwatcher.db
```

#### **Authentication & Security**
```bash
JWT_SECRET=your_jwt_secret_here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Admin credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure_admin_password
```

#### **Payment Processing**
```bash
# Traditional payments
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...

# Blockchain payments
BLOCKCHAIN_ENABLED=true
PAYMENT_AGENT_ADDRESS=agent1payment...
FET_PAYMENT_TIMEOUT=600
```

#### **Email & Notifications**
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=noreply@yourdomain.com
```

#### **Deployment Configuration**
```bash
# Vultr VPS
VULTR_API_KEY=your_vultr_api_key
VPS_REGION=ewr  # New York
VPS_PLAN=vc2-2c-4gb

# AWS Configuration
AWS_REGION=us-east-1
AWS_PROFILE=default
```

## 🛠️ Development Workflow

### 1. **Local Development Setup**
```bash
# Clone and setup
git clone https://github.com/zmazz/govwatcher-cosmos-vultr.git
cd govwatcher-cosmos-vultr
cp env.example .env

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
python scripts/test_basic_setup.py

# Run locally
uvicorn src.web.main:app --reload --host 0.0.0.0 --port 8080
```

### 2. **Testing & Validation**
```bash
# Run comprehensive compliance check
python scripts/hackathon_check.py

# Validate data models
python scripts/validate_data_models.py

# Run unit tests
pytest tests/ -v

# Test basic setup
python scripts/test_basic_setup.py

# Generate test data
python scripts/generate_test_data.py
```

### 3. **Docker Development**
```bash
# Build and test locally
cd infra/docker
docker-compose build
docker-compose up -d

# Check health
curl http://localhost:8080/api/status
curl http://localhost:8080/dashboard

# View logs
docker-compose logs -f web
docker-compose logs -f analysis-agent
```

### 4. **Production Deployment**
```bash
# Quick Vultr deployment (recommended)
./infra/vultr/deploy-vultr.sh deploy

# Full AWS deployment
./infra/aws/deploy.sh all

# Blockchain integration
./scripts/deploy-onchain.sh deploy
```

## 📊 Monitoring & Maintenance

### Health Checks
```bash
# Web Application Health
curl https://your-deployment/api/status

# Docker Services Health
docker-compose ps
docker-compose logs web

# VPS System Health
./infra/vultr/deploy-vultr.sh status

# Agent Health
./scripts/deploy-onchain.sh status
```

### Log Management
```bash
# Local development logs
tail -f logs/govwatcher.log

# Docker logs
docker-compose logs -f web
docker-compose logs -f analysis-agent

# VPS logs (production)
ssh root@your_vps_ip
docker logs govwatcher-web
docker logs govwatcher-postgres
```

### Database Management
```bash
# Local SQLite (development)
sqlite3 data/govwatcher.db
.tables
.schema organizations

# Production PostgreSQL
docker exec -it govwatcher-postgres psql -U govwatcher -d govwatcher
\dt
\d organizations
```

## 🔒 Security Considerations

### Environment Security
- **`.env` files**: Never committed to git, use `env.example` as template
- **API keys**: Stored as environment variables only
- **Database passwords**: Auto-generated during deployment
- **JWT secrets**: Cryptographically secure random generation

### Network Security
- **Nginx reverse proxy**: Production SSL termination and security headers
- **Firewall configuration**: Automated during VPS setup with minimal open ports
- **SSL certificates**: Automated Let's Encrypt certificate provisioning
- **Database access**: Restricted to application containers only

### Application Security
- **JWT Authentication**: Secure session management with expiration
- **Input Validation**: FastAPI automatic validation and sanitization
- **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries
- **CORS Configuration**: Restricted to allowed origins only
- **Rate Limiting**: API endpoint protection against abuse

## 🎓 Contributing Guidelines

### Code Organization Principles
1. **Source code** belongs in `src/` with clear module separation
2. **Infrastructure configurations** belong in `infra/` by platform
3. **Documentation** belongs in `docs/` with cross-references
4. **Automation scripts** belong in `scripts/` with clear naming
5. **Tests** mirror the `src/` structure in `tests/`

### Adding New Features
1. **Web features**: Extend `src/web/main.py` and add templates
2. **Agent features**: Create new agents in `src/agents/`
3. **AI integrations**: Extend `src/ai_adapters.py` with new providers
4. **Deployment options**: Add platform-specific configs in `infra/`
5. **Database changes**: Update `sql/init.sql` and `src/models.py`

### Testing Requirements
1. **Unit tests**: Add corresponding test files in `tests/`
2. **Integration tests**: Include docker-compose testing scenarios
3. **Compliance validation**: Ensure `scripts/hackathon_check.py` passes
4. **Documentation updates**: Update relevant docs when changing functionality

### Documentation Standards
- **Clear section headers** with emoji for visual organization
- **Code examples** with proper syntax highlighting and explanations
- **Step-by-step instructions** for complex procedures with verification steps
- **Cross-references** between related documents with relative links
- **Status indicators** (✅ Working, 🟡 Ready, 🔴 Planned) for feature clarity

## 📞 Support & Resources

### Getting Help
- **[Main README](../README.md)**: Project overview and live demo links
- **[Documentation Index](README.md)**: Complete documentation navigation
- **[Quick Deployment](MASTER_DEPLOYMENT_GUIDE_HACKATHON.md)**: Get running in 60 minutes
- **[Master Deployment Guide](MASTER_DEPLOYMENT_GUIDE.md)**: All deployment scenarios
- **[Compliance Check](../scripts/hackathon_check.py)**: Validation and troubleshooting

### Common Operations
```bash
# System validation
python scripts/hackathon_check.py

# Environment setup
python scripts/generate_env_values.py

# Agent key generation
python scripts/generate_uagents_key.py

# Test data generation
python scripts/generate_test_data.py

# Vultr deployment
./infra/vultr/deploy-vultr.sh deploy

# AWS deployment
./infra/aws/deploy.sh all

# Blockchain deployment
./scripts/deploy-onchain.sh deploy
```

### External Resources
- **Live Demo**: [Dashboard](http://207.148.31.84:8080/dashboard) | [API](http://207.148.31.84:8080/api/proposals)
- **GitHub Repository**: [govwatcher-cosmos-vultr](https://github.com/zmazz/govwatcher-cosmos-vultr)
- **Health Check**: [System Status](http://207.148.31.84:8080/api/status)
- **Documentation**: [Complete Docs Index](README.md)

---

**🌌 This organized, enterprise-ready structure enables professional development, seamless deployment, and maintainable code for the Cosmos Governance Risk & Compliance Co-Pilot (GovWatcher).** 