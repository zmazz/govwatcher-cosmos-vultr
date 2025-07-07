-- PostgreSQL initialization script for Cosmos GRC Co-Pilot
-- This script creates the database schema and initial data

-- Create database extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Organizations table
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    policy_template JSONB DEFAULT '{}',
    subscription_tier VARCHAR(50) DEFAULT 'basic',
    is_active BOOLEAN DEFAULT true,
    contact_email VARCHAR(255) NOT NULL,
    UNIQUE(domain)
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    organization_id UUID REFERENCES organizations(id),
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Proposal history table
CREATE TABLE IF NOT EXISTS proposal_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chain_id VARCHAR(50) NOT NULL,
    proposal_id VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL,
    voting_start TIMESTAMP,
    voting_end TIMESTAMP,
    ai_analysis JSONB,
    organization_votes JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chain_id, proposal_id)
);

-- User preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    preference_vector JSONB,
    approval_history JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id),
    chains TEXT[] DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    payment_method VARCHAR(50) DEFAULT 'credit_card',
    payment_tx_hash VARCHAR(255),
    sender_address VARCHAR(255)
);

-- Audit logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    organization_id UUID REFERENCES organizations(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255),
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_organization ON users(organization_id);
CREATE INDEX IF NOT EXISTS idx_proposals_chain ON proposal_history(chain_id);
CREATE INDEX IF NOT EXISTS idx_proposals_status ON proposal_history(status);
CREATE INDEX IF NOT EXISTS idx_proposals_voting_end ON proposal_history(voting_end);
CREATE INDEX IF NOT EXISTS idx_subscriptions_org ON subscriptions(organization_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_org ON audit_logs(organization_id);

-- Insert demo organization and user with proper UUIDs
INSERT INTO organizations (id, name, domain, contact_email, policy_template, subscription_tier)
VALUES (
    '550e8400-e29b-41d4-a716-446655440000',
    'Demo Enterprise',
    'demo.enterprise.com',
    'demo@enterprise.com',
    '{"name": "Conservative Strategy", "risk_tolerance": "LOW", "security_weight": 0.4}',
    'enterprise'
) ON CONFLICT (domain) DO NOTHING;

-- Insert demo user (password: 'password123')
INSERT INTO users (id, email, hashed_password, organization_id, role)
VALUES (
    '550e8400-e29b-41d4-a716-446655440001',
    'demo@enterprise.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewlKtJ3lOewKnSsi', -- password123
    '550e8400-e29b-41d4-a716-446655440000',
    'admin'
) ON CONFLICT (email) DO NOTHING;

-- Insert demo subscription
INSERT INTO subscriptions (id, organization_id, chains, status, expires_at, payment_method)
VALUES (
    '550e8400-e29b-41d4-a716-446655440002',
    '550e8400-e29b-41d4-a716-446655440000',
    '{"cosmoshub-4", "osmosis-1", "juno-1", "fetchhub-4"}',
    'active',
    CURRENT_TIMESTAMP + INTERVAL '1 year',
    'demo'
) ON CONFLICT (id) DO NOTHING;

-- Insert sample proposals for demo
INSERT INTO proposal_history (id, chain_id, proposal_id, title, description, status, voting_start, voting_end, ai_analysis)
VALUES
(
    '550e8400-e29b-41d4-a716-446655440003',
    'cosmoshub-4',
    'prop_123',
    'Community Pool Spend: IBC Upgrade',
    'Proposal to upgrade IBC infrastructure using community pool funds for enhanced security and performance.',
    'voting',
    CURRENT_TIMESTAMP - INTERVAL '1 day',
    CURRENT_TIMESTAMP + INTERVAL '6 days',
    '{"recommendation": "APPROVE", "confidence": 85, "reasoning": "Aligns with infrastructure investment policy"}'
),
(
    '550e8400-e29b-41d4-a716-446655440004',
    'osmosis-1',
    'prop_456',
    'Parameter Change: Minimum Commission Rate',
    'Increase minimum validator commission rate to 5% to ensure sustainable validator operations.',
    'voting',
    CURRENT_TIMESTAMP - INTERVAL '2 days',
    CURRENT_TIMESTAMP + INTERVAL '4 days',
    '{"recommendation": "REJECT", "confidence": 72, "reasoning": "May negatively impact validator economics per risk policy"}'
) ON CONFLICT (chain_id, proposal_id) DO NOTHING;

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions to govwatcher user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO govwatcher;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO govwatcher;

-- Display initialization status
SELECT 'Database initialized successfully!' as status; 