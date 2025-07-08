# Data Model Summary

## Overview

This document provides a quick reference for the data models used in the Cosmos Governance Risk & Compliance Co-Pilot. The system uses SQLAlchemy ORM with support for both PostgreSQL (production) and SQLite (development).

## Core Database Models

### Organization (`organizations` table)
```python
class Organization(Base):
    id: str                    # Primary key (UUID)
    name: str                  # Organization name
    domain: str               # Email domain (e.g., "company.com")
    policy_template: JSON     # Governance policy configuration
    subscription_tier: str    # "basic" or "enterprise"
    created_at: datetime      # Creation timestamp
    updated_at: datetime      # Last update timestamp
```

**Purpose**: Multi-tenant organization management with governance policies.

### User (`users` table)
```python
class User(Base):
    id: str                    # Primary key (UUID)
    email: str                 # User email (unique)
    password_hash: str         # Hashed password
    organization_id: str       # Foreign key to Organization
    role: str                  # "admin", "user", "super_admin"
    created_at: datetime       # Creation timestamp
    last_login: datetime       # Last login timestamp
    is_active: bool           # Account status
```

**Purpose**: User authentication and role-based access control.

### Subscription (`subscriptions` table)
```python
class Subscription(Base):
    id: str                    # Primary key (UUID)
    organization_id: str       # Foreign key to Organization
    tier: str                  # "basic", "enterprise"
    status: str                # "active", "cancelled", "expired"
    start_date: datetime       # Subscription start
    end_date: datetime         # Subscription end
    created_at: datetime       # Creation timestamp
```

**Purpose**: Subscription management and billing tracking.

### Payment (`payments` table)
```python
class Payment(Base):
    id: str                    # Primary key (UUID)
    subscription_id: str       # Foreign key to Subscription
    amount: float              # Payment amount
    currency: str              # "USD", "FET"
    payment_method: str        # "stripe", "crypto"
    payment_provider: str      # "stripe", "fetch_blockchain"
    transaction_id: str        # External transaction ID
    status: str                # "pending", "completed", "failed"
    created_at: datetime       # Payment timestamp
```

**Purpose**: Payment tracking for both traditional and cryptocurrency payments.

### WalletConnection (`wallet_connections` table)
```python
class WalletConnection(Base):
    id: str                    # Primary key (UUID)
    user_id: str               # Foreign key to User
    wallet_address: str        # Cosmos wallet address
    chain_id: str              # Chain identifier (e.g., "cosmoshub-4")
    wallet_type: str           # "keplr", "cosmostation"
    created_at: datetime       # Connection timestamp
    last_used: datetime        # Last usage timestamp
```

**Purpose**: Cosmos wallet integration for authentication and governance participation.

## AI Analysis Data Structures

### Governance Proposal (JSON format)
```json
{
  "id": "string",
  "chain_id": "string",
  "proposal_id": "integer",
  "title": "string",
  "description": "string",
  "status": "string",
  "voting_start_time": "datetime",
  "voting_end_time": "datetime",
  "deposit_end_time": "datetime",
  "total_deposit": "array",
  "submit_time": "datetime",
  "proposer": "string",
  "type": "string",
  "final_tally_result": {
    "yes": "string",
    "no": "string",
    "abstain": "string",
    "no_with_veto": "string"
  }
}
```

### AI Analysis Result (JSON format)
```json
{
  "proposal_id": "string",
  "chain_id": "string",
  "analysis_timestamp": "datetime",
  "analysis_provider": "string",
  "recommendation": "string",
  "confidence": "float",
  "reasoning": "string",
  "risk_assessment": "string",
  "policy_alignment": "string",
  "swot_analysis": {
    "strengths": ["string"],
    "weaknesses": ["string"],
    "opportunities": ["string"],
    "threats": ["string"]
  },
  "pestel_analysis": {
    "political": "string",
    "economic": "string",
    "social": "string",
    "technological": "string",
    "environmental": "string",
    "legal": "string"
  },
  "stakeholder_impact": {
    "validators": "string",
    "delegators": "string",
    "developers": "string",
    "users": "string",
    "institutions": "string"
  },
  "implementation_assessment": {
    "technical_complexity": "string",
    "timeline": "string",
    "resource_requirements": "string",
    "success_probability": "string"
  }
}
```

## Configuration Data Structures

### Organization Policy Template (JSON format)
```json
{
  "name": "string",
  "description": "string",
  "risk_tolerance": "string",
  "voting_criteria": {
    "security_weight": "float",
    "economic_impact_weight": "float",
    "community_support_weight": "float",
    "decentralization_weight": "float"
  },
  "auto_vote_threshold": "float",
  "notification_preferences": {
    "email": "boolean",
    "dashboard": "boolean"
  },
  "compliance_requirements": {
    "audit_required": "boolean",
    "approval_threshold": "float",
    "documentation_required": "boolean"
  }
}
```

### Chain Configuration (JSON format)
```json
{
  "chain_id": "string",
  "name": "string",
  "rpc_endpoint": "string",
  "rest_endpoint": "string",
  "enabled": "boolean",
  "polling_interval": "integer",
  "governance_module": "string",
  "native_token": {
    "symbol": "string",
    "decimals": "integer"
  }
}
```

## API Response Formats

### Health Check Response
```json
{
  "status": "string",
  "timestamp": "datetime",
  "version": "string",
  "services": {
    "database": "string",
    "ai_adapters": {
      "groq": "boolean",
      "llama": "boolean",
      "openai": "boolean"
    }
  }
}
```

### Proposals API Response
```json
{
  "count": "integer",
  "proposals": [
    {
      "id": "string",
      "chain_id": "string",
      "title": "string",
      "status": "string",
      "ai_recommendation": "string",
      "confidence": "float",
      "analysis_timestamp": "datetime"
    }
  ]
}
```

### Authentication Response
```json
{
  "access_token": "string",
  "token_type": "string",
  "expires_in": "integer",
  "user": {
    "id": "string",
    "email": "string",
    "role": "string",
    "organization_id": "string"
  }
}
```

## Database Schema Relationships

```
Organization (1) ←→ (N) User
Organization (1) ←→ (N) Subscription
Subscription (1) ←→ (N) Payment
User (1) ←→ (N) WalletConnection
```

## File Storage Locations

### Cache Files
- **Governance Data**: `/tmp/governance_updates.json`
- **AI Analysis Cache**: `/tmp/proposal_analysis_cache.json`
- **Organization Policies**: `/tmp/organization_policy.json`

### Database Files
- **SQLite (Development)**: `data/govwatcher.db`
- **PostgreSQL (Production)**: Configured via `DATABASE_URL`

## Environment Configuration

### Required Variables
```bash
# Database
DATABASE_URL=sqlite:///./data/govwatcher.db

# AI Services
GROQ_API_KEY=gsk_your_key_here
OPENAI_API_KEY=sk_your_key_here  # Optional

# Security
JWT_SECRET=your_secret_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Email (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### Optional Variables
```bash
# Demo Mode
DEMO_MODE=true

# Deployment
DEPLOYMENT_TYPE=local
VULTR_API_KEY=your_vultr_key
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret

# Blockchain Integration
UAGENTS_PRIVATE_KEY=your_private_key
FETCH_WALLET_ADDRESS=your_wallet_address
```

## Data Validation

The system includes validation scripts:

- **`scripts/validate_data_models.py`**: Validates database schema consistency
- **`scripts/hackathon_check.py`**: Validates compliance requirements
- **`scripts/test_basic_setup.py`**: Tests basic functionality

## Cache Management

The system uses three types of caching:

1. **File-based caching**: JSON files in `/tmp/` for governance data
2. **Database caching**: Stored analysis results in database
3. **Memory caching**: Runtime caching for frequently accessed data

## Security Considerations

- **Password hashing**: Uses bcrypt for secure password storage
- **JWT tokens**: Secure token-based authentication
- **Input validation**: All user inputs are validated and sanitized
- **SQL injection prevention**: SQLAlchemy ORM prevents SQL injection
- **API key protection**: Environment variables for sensitive data

This summary provides the essential data structures needed to understand and work with the Cosmos Governance Risk & Compliance Co-Pilot system. 