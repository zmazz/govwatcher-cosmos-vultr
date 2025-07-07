# 📁 Repository Structure Guide

This document provides a comprehensive overview of the organized repository structure for the Cosmos Governance Risk & Compliance Co-Pilot.

## 🗂️ Directory Overview

```
/
├── README.md                 # Main project documentation
├── requirements.txt          # Python dependencies
├── env.example              # Environment template
├── .gitignore               # Git ignore rules
├── .dockerignore            # Docker ignore rules
│
├── 📁 src/                   # Source Code
│   ├── web/                 # Web application (FastAPI)
│   │   ├── main.py          # Main application entry point
│   │   ├── templates/       # Jinja2 HTML templates
│   │   │   ├── index.html   # Landing page
│   │   │   ├── dashboard.html # Enterprise dashboard
│   │   │   └── settings.html  # Policy configuration
│   │   └── static/          # Static assets (CSS, JS, images)
│   ├── agents/              # uAgent implementations
│   │   ├── subscription_agent.py
│   │   ├── watcher_agent.py
│   │   ├── analysis_agent.py
│   │   └── mail_agent.py
│   ├── ai_adapters.py       # AI integration (Groq, Llama, OpenAI)
│   ├── models.py            # Data models and schemas
│   └── legacy_handler.py    # Legacy AWS Lambda handler
│
├── 📁 infra/                 # Infrastructure & Deployment
│   ├── docker/              # Docker configurations
│   │   ├── docker-compose.yml # Multi-service orchestration
│   │   ├── Dockerfile.web   # Web application container
│   │   ├── Dockerfile.agents # Agent services container
│   │   └── Dockerfile.simple # Simple deployment option
│   ├── nginx/               # Nginx configuration
│   │   ├── nginx.conf       # Production nginx config
│   │   └── ssl/             # SSL certificates directory
│   ├── vultr/               # Vultr VPS deployment
│   │   └── deploy-vultr.sh  # Vultr deployment automation
│   └── aws/                 # AWS deployment
│       ├── deploy.sh        # AWS deployment script
│       └── stack.yml        # CloudFormation template
│
├── 📁 sql/                   # Database
│   └── init.sql             # PostgreSQL schema & demo data
│
├── 📁 scripts/              # Utility Scripts
│   ├── hackathon_check.py   # Vultr Track compliance validator
│   ├── generate_uagents_key.py # uAgent key generator
│   ├── load_env.py          # Environment loader utility
│   └── test_basic_setup.py  # Basic setup testing
│
├── 📁 tests/                 # Test Suite
│   └── [test files]         # Unit and integration tests
│
├── 📁 docs/                  # Documentation
│   ├── DEPLOYMENT.md        # AWS deployment guide
│   ├── DEPLOYMENT_INSTRUCTIONS.md # Complete deployment guide
│   └── ONCHAIN.md           # Blockchain deployment guide
│
└── 📁 data/                  # Local Data (ignored by git)
    └── govwatcher.db        # Local SQLite database
```

## 🎯 Key Architectural Decisions

### 1. **Infrastructure Separation**
- **`infra/`**: All deployment configurations isolated from source code
- **Platform-specific subdirectories**: `vultr/`, `aws/`, `docker/`, `nginx/`
- **Environment independence**: Same source code deploys everywhere

### 2. **Source Code Organization**
- **`src/web/`**: Modern FastAPI web application
- **`src/agents/`**: Autonomous uAgent implementations
- **`src/ai_adapters.py`**: Unified AI integration layer
- **Clear separation of concerns** between web interface and agents

### 3. **Database & Configuration**
- **`sql/`**: Version-controlled database schema
- **`data/`**: Local development data (git-ignored)
- **Environment templates**: `env.example` for easy setup

### 4. **Documentation & Scripts**
- **`docs/`**: Comprehensive deployment guides
- **`scripts/`**: Development and validation utilities
- **`tests/`**: Complete test suite

## 🚀 Quick Start Commands

### Local Development
```bash
# Setup environment
cp env.example .env
# Edit .env with your configuration

# Install dependencies
pip install -r requirements.txt

# Run web application
uvicorn src.web.main:app --reload --host 0.0.0.0 --port 8080

# Run compliance check
python scripts/hackathon_check.py
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
```

### Production Deployment

#### Vultr VPS (Recommended)
```bash
export VULTR_API_KEY=your_api_key
export GROQ_API_KEY=your_groq_key
./infra/vultr/deploy-vultr.sh deploy
```

#### AWS CloudFormation
```bash
aws configure  # Set up AWS credentials
./infra/aws/deploy.sh all
```

## 📋 Configuration Management

### Environment Variables
The system uses environment variables for configuration. Key files:

- **`env.example`**: Template with all available options
- **`infra/docker/.env`**: Docker Compose environment
- **Production**: Environment variables set during deployment

### Key Configuration Categories

#### **AI Integration**
```bash
GROQ_API_KEY=your_groq_api_key     # Required
LLAMA_API_KEY=your_llama_key       # Optional
OPENAI_API_KEY=your_openai_key     # Fallback
```

#### **Database**
```bash
DATABASE_URL=postgresql://user:pass@host:5432/db
POSTGRES_PASSWORD=secure_password
```

#### **Authentication**
```bash
JWT_SECRET=your_jwt_secret_here
JWT_ALGORITHM=HS256
```

#### **Email**
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=noreply@yourdomain.com
```

## 🛠️ Development Workflow

### 1. **Local Development**
```bash
# Clone and setup
git clone <repository>
cd uagents-govwatcher
cp env.example .env

# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run locally
uvicorn src.web.main:app --reload
```

### 2. **Testing**
```bash
# Run compliance check
python scripts/hackathon_check.py

# Run basic tests
python scripts/test_basic_setup.py

# Run full test suite
pytest tests/ -v
```

### 3. **Docker Testing**
```bash
# Build and test locally
cd infra/docker
docker-compose up --build

# Check health
curl http://localhost:8080/status
```

### 4. **Production Deployment**
```bash
# Choose your platform
./infra/vultr/deploy-vultr.sh deploy    # Vultr VPS
./infra/aws/deploy.sh all               # AWS CloudFormation
```

## 📊 Monitoring & Maintenance

### Health Checks
- **Web Application**: `GET /status`
- **Docker Services**: `docker-compose ps`
- **VPS Status**: `./infra/vultr/deploy-vultr.sh status`

### Log Management
```bash
# Docker logs
docker-compose logs -f web
docker-compose logs -f analysis-agent

# VPS logs
ssh root@your_vps_ip
docker logs govwatcher-web
```

### Database Maintenance
```bash
# Local SQLite (development)
sqlite3 data/govwatcher.db

# Production PostgreSQL
docker exec -it govwatcher-postgres psql -U govwatcher -d govwatcher
```

## 🔒 Security Considerations

### Environment Security
- **`.env` files**: Never commit to git
- **API keys**: Use environment variables only
- **Database passwords**: Generated automatically in production

### Network Security
- **Nginx**: Production reverse proxy with security headers
- **Firewall**: Configured automatically during VPS setup
- **SSL**: Automated Let's Encrypt certificate setup

### Application Security
- **JWT Authentication**: Secure session management
- **Input Validation**: FastAPI automatic validation
- **SQL Injection**: SQLAlchemy ORM protection

## 🎓 Contributing Guidelines

### Code Organization
1. **Source code** goes in `src/`
2. **Infrastructure** configurations in `infra/`
3. **Documentation** in `docs/`
4. **Utilities** in `scripts/`

### Adding New Features
1. **Web features**: Add to `src/web/`
2. **Agent features**: Add to `src/agents/`
3. **AI integrations**: Extend `src/ai_adapters.py`
4. **Deployment**: Update appropriate `infra/` configurations

### Testing Requirements
1. **Unit tests**: Add to `tests/`
2. **Integration tests**: Include docker-compose testing
3. **Compliance**: Ensure `scripts/hackathon_check.py` passes
4. **Documentation**: Update relevant docs

## 📞 Support & Resources

### Getting Help
- **README.md**: Main project documentation
- **docs/**: Comprehensive deployment guides
- **scripts/hackathon_check.py**: Validation and troubleshooting

### Common Operations
```bash
# Check compliance
python scripts/hackathon_check.py

# Generate uAgent keys
python scripts/generate_uagents_key.py

# Validate environment
python scripts/load_env.py

# Deploy to Vultr
./infra/vultr/deploy-vultr.sh deploy

# Deploy to AWS
./infra/aws/deploy.sh all
```

---

**🌌 This organized structure enables professional development, easy deployment, and maintainable code for the Cosmos Governance Risk & Compliance Co-Pilot.** 