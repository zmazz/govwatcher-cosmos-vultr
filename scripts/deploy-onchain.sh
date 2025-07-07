#!/bin/bash

# 🌌 Cosmos GRC Co-Pilot - On-Chain Deployment Script
# Deploy on-chain agents to Fetch.ai blockchain and integrate with web dashboard

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ONCHAIN_DIR="$PROJECT_ROOT/src/onchain"
CONFIG_FILE="$ONCHAIN_DIR/onchain-config.json"

# Default values
NETWORK=${NETWORK:-"fetchai-mainnet"}
FUND_AMOUNT=${FUND_AMOUNT:-"100"}
SKIP_FUNDING=${SKIP_FUNDING:-"false"}

# Functions
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

print_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                    🌌 Cosmos GRC Co-Pilot - On-Chain Deployment             ║"
    echo "║                                  Vultr Track                                 ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is required but not installed"
    fi
    
    # Check uAgents
    if ! python3 -c "import uagents" &> /dev/null; then
        error "uAgents package not installed. Run: pip install uagents"
    fi
    
    # Check fetchd (optional)
    if ! command -v fetchd &> /dev/null; then
        warn "fetchd not found. Some features may be limited"
    fi
    
    # Check configuration file
    if [[ ! -f "$CONFIG_FILE" ]]; then
        error "Configuration file not found: $CONFIG_FILE"
    fi
    
    # Check environment variables
    if [[ -z "$GROQ_API_KEY" ]]; then
        warn "GROQ_API_KEY not set. AI analysis may be limited"
    fi
    
    log "Prerequisites check completed"
}

setup_environment() {
    log "Setting up environment..."
    
    # Create necessary directories
    mkdir -p "$ONCHAIN_DIR/logs"
    mkdir -p "$ONCHAIN_DIR/data"
    
    # Install Python dependencies
    pip install -q structlog requests asyncio
    
    log "Environment setup completed"
}

generate_agent_keys() {
    log "Generating agent keys..."
    
    python3 << 'EOF'
import json
import os
from uagents.crypto import Identity

config_file = os.path.join(os.environ.get('ONCHAIN_DIR'), 'onchain-config.json')
with open(config_file, 'r') as f:
    config = json.load(f)

# Generate keys for each agent
for agent_name, agent_config in config['agents'].items():
    # Generate identity
    identity = Identity.generate()
    
    # Update config with generated address and private key
    config['agents'][agent_name]['address'] = str(identity.address)
    config['agents'][agent_name]['private_key'] = identity.private_key_hex
    
    print(f"Generated keys for {agent_name}: {identity.address}")

# Save updated config
with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print("Agent keys generated successfully")
EOF
    
    log "Agent keys generated"
}

update_config_for_deployment() {
    log "Updating configuration for deployment..."
    
    # Get deployment URL from environment or prompt
    if [[ -z "$DEPLOYMENT_URL" ]]; then
        echo -n "Enter your deployment URL (e.g., https://your-vultr-ip): "
        read DEPLOYMENT_URL
    fi
    
    # Update config file with actual deployment URL
    python3 << EOF
import json
import os

config_file = os.path.join('$ONCHAIN_DIR', 'onchain-config.json')
with open(config_file, 'r') as f:
    config = json.load(f)

# Update URLs
deployment_url = '$DEPLOYMENT_URL'
config['integration']['dashboard_url'] = f'{deployment_url}/dashboard'
config['integration']['api_base_url'] = deployment_url
config['integration']['health_check_url'] = f'{deployment_url}/status'

# Update agent endpoints
for agent_name, agent_config in config['agents'].items():
    if 'endpoints' in agent_config:
        port = agent_config['port']
        config['agents'][agent_name]['endpoints'] = [f'{deployment_url}:{port}/submit']

with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print(f'Configuration updated for deployment: {deployment_url}')
EOF
    
    log "Configuration updated"
}

fund_agents() {
    if [[ "$SKIP_FUNDING" == "true" ]]; then
        log "Skipping agent funding (SKIP_FUNDING=true)"
        return
    fi
    
    log "Funding agents..."
    
    python3 << 'EOF'
import json
import os
from uagents.setup import fund_agent_if_low

config_file = os.path.join(os.environ.get('ONCHAIN_DIR'), 'onchain-config.json')
with open(config_file, 'r') as f:
    config = json.load(f)

for agent_name, agent_config in config['agents'].items():
    if 'address' in agent_config:
        address = agent_config['address']
        print(f"Funding agent {agent_name} ({address})...")
        try:
            fund_agent_if_low(address)
            print(f"✓ {agent_name} funded successfully")
        except Exception as e:
            print(f"✗ Failed to fund {agent_name}: {e}")
EOF
    
    log "Agent funding completed"
}

test_dashboard_connection() {
    log "Testing dashboard connection..."
    
    python3 << 'EOF'
import json
import requests
import os

config_file = os.path.join(os.environ.get('ONCHAIN_DIR'), 'onchain-config.json')
with open(config_file, 'r') as f:
    config = json.load(f)

health_url = config['integration']['health_check_url']

try:
    response = requests.get(health_url, timeout=10)
    if response.status_code == 200:
        print(f"✓ Dashboard accessible at {health_url}")
        print(f"Response: {response.json()}")
    else:
        print(f"✗ Dashboard not accessible: HTTP {response.status_code}")
except Exception as e:
    print(f"✗ Dashboard connection failed: {e}")
EOF
}

deploy_payment_agent() {
    log "Deploying payment agent..."
    
    cd "$ONCHAIN_DIR"
    nohup python3 payment_agent.py > logs/payment_agent.log 2>&1 &
    PAYMENT_PID=$!
    echo $PAYMENT_PID > data/payment_agent.pid
    
    sleep 3
    if kill -0 $PAYMENT_PID 2>/dev/null; then
        log "Payment agent deployed successfully (PID: $PAYMENT_PID)"
    else
        error "Payment agent failed to start"
    fi
}

register_agentverse() {
    log "Registering agents on AgentVerse..."
    
    python3 << 'EOF'
import json
import os
import requests

config_file = os.path.join(os.environ.get('ONCHAIN_DIR'), 'onchain-config.json')
with open(config_file, 'r') as f:
    config = json.load(f)

if not config.get('agentverse', {}).get('enabled', False):
    print("AgentVerse registration disabled in config")
    exit(0)

# This would integrate with AgentVerse API
# For now, just print registration info
print("AgentVerse Registration Information:")
print("=" * 50)

for agent_name, agent_config in config['agents'].items():
    print(f"Agent: {agent_name}")
    print(f"  Address: {agent_config.get('address', 'N/A')}")
    print(f"  Description: {agent_config.get('description', 'N/A')}")
    print(f"  Categories: {', '.join(config['agentverse']['categories'])}")
    print(f"  Tags: {', '.join(config['agentverse']['tags'])}")
    print()

print("To complete AgentVerse registration:")
print("1. Visit https://agentverse.ai")
print("2. Login with your Fetch.ai wallet")
print("3. Register each agent using the addresses above")
EOF
    
    log "AgentVerse registration information displayed"
}

update_web_config() {
    log "Updating web application configuration..."
    
    # Update environment variables for web application
    ENV_FILE="$PROJECT_ROOT/.env"
    
    python3 << EOF
import json
import os

config_file = os.path.join('$ONCHAIN_DIR', 'onchain-config.json')
with open(config_file, 'r') as f:
    config = json.load(f)

env_updates = []
env_updates.append(f"BLOCKCHAIN_ENABLED=true")
env_updates.append(f"PAYMENT_AGENT_ADDRESS={config['agents']['payment']['address']}")
env_updates.append(f"INTEGRATION_AGENT_ADDRESS={config['agents']['integration']['address']}")
env_updates.append(f"ONCHAIN_PAYMENT_SUPPORT=true")

# Read existing .env
env_content = ""
env_file = '$ENV_FILE'
if os.path.exists(env_file):
    with open(env_file, 'r') as f:
        env_content = f.read()

# Add new variables
for update in env_updates:
    key = update.split('=')[0]
    # Remove existing line if present
    lines = env_content.split('\n')
    lines = [line for line in lines if not line.startswith(f'{key}=')]
    lines.append(update)
    env_content = '\n'.join(lines)

# Write updated .env
with open(env_file, 'w') as f:
    f.write(env_content)

print("Web application configuration updated")
EOF
    
    log "Web configuration updated"
}

create_monitoring_script() {
    log "Creating monitoring script..."
    
    cat > "$ONCHAIN_DIR/monitor_agents.py" << 'EOF'
#!/usr/bin/env python3
"""
Agent monitoring script for Cosmos GRC Co-Pilot
"""

import json
import os
import time
import requests
import psutil
from datetime import datetime

def load_config():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(script_dir, 'onchain-config.json')
    with open(config_file, 'r') as f:
        return json.load(f)

def check_agent_process(agent_name):
    """Check if agent process is running"""
    pid_file = f"data/{agent_name}_agent.pid"
    if not os.path.exists(pid_file):
        return False, "No PID file"
    
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        if psutil.pid_exists(pid):
            return True, f"Running (PID: {pid})"
        else:
            return False, f"Process not found (PID: {pid})"
    except Exception as e:
        return False, f"Error: {e}"

def check_dashboard_connectivity(config):
    """Check dashboard connectivity"""
    try:
        health_url = config['integration']['health_check_url']
        response = requests.get(health_url, timeout=5)
        if response.status_code == 200:
            return True, "Connected"
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, f"Error: {e}"

def main():
    config = load_config()
    
    print("🌌 Cosmos GRC Co-Pilot - Agent Monitor")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Check agent processes
    print("Agent Status:")
    for agent_name in config['agents'].keys():
        running, status = check_agent_process(agent_name)
        status_icon = "✅" if running else "❌"
        print(f"  {status_icon} {agent_name}: {status}")
    
    print()
    
    # Check dashboard connectivity
    connected, status = check_dashboard_connectivity(config)
    status_icon = "✅" if connected else "❌"
    print(f"Dashboard Connectivity: {status_icon} {status}")
    
    print()
    
    # Agent addresses
    print("Agent Addresses:")
    for agent_name, agent_config in config['agents'].items():
        address = agent_config.get('address', 'Not generated')
        print(f"  {agent_name}: {address}")

if __name__ == "__main__":
    main()
EOF
    
    chmod +x "$ONCHAIN_DIR/monitor_agents.py"
    log "Monitoring script created"
}

print_deployment_summary() {
    log "Deployment completed successfully!"
    
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                          🎉 DEPLOYMENT SUMMARY                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    python3 << 'EOF'
import json
import os

config_file = os.path.join(os.environ.get('ONCHAIN_DIR'), 'onchain-config.json')
with open(config_file, 'r') as f:
    config = json.load(f)

print("🌐 Access URLs:")
print(f"  Dashboard:    {config['integration']['dashboard_url']}")
print(f"  Health Check: {config['integration']['health_check_url']}")
print(f"  API Base:     {config['integration']['api_base_url']}")
print()

print("🤖 Agent Addresses:")
for agent_name, agent_config in config['agents'].items():
    address = agent_config.get('address', 'Not generated')
    port = agent_config.get('port', 'N/A')
    print(f"  {agent_name:20} {address} (Port: {port})")
print()

print("💰 Payment Information:")
print(f"  Basic Plan:      {config['pricing']['annual_subscription_fet']} FET/year")
print(f"  Enterprise Plan: {config['pricing']['enterprise_tier_fet']} FET/year")
print(f"  Additional Chain: {config['pricing']['additional_chain_fet']} FET/year")
print()

print("📊 Next Steps:")
print("  1. Test the dashboard and payment flows")
print("  2. Register agents on AgentVerse (optional)")
print("  3. Monitor agent health with: python3 src/onchain/monitor_agents.py")
print("  4. Check logs in: src/onchain/logs/")
EOF
    
    echo -e "${BLUE}For support and documentation, see: docs/ONCHAIN.md${NC}"
}

# Main deployment function
deploy() {
    local action=${1:-"deploy"}
    
    case $action in
        "deploy")
            print_banner
            check_prerequisites
            setup_environment
            generate_agent_keys
            update_config_for_deployment
            fund_agents
            test_dashboard_connection
            deploy_payment_agent
            register_agentverse
            update_web_config
            create_monitoring_script
            print_deployment_summary
            ;;
        "status")
            if [[ -f "$ONCHAIN_DIR/monitor_agents.py" ]]; then
                python3 "$ONCHAIN_DIR/monitor_agents.py"
            else
                error "Monitoring script not found. Run deploy first."
            fi
            ;;
        "stop")
            log "Stopping agents..."
            pkill -f "payment_agent.py" || true
            rm -f "$ONCHAIN_DIR/data/*.pid"
            log "Agents stopped"
            ;;
        "logs")
            if [[ -d "$ONCHAIN_DIR/logs" ]]; then
                log "Recent agent logs:"
                tail -n 50 "$ONCHAIN_DIR/logs/"*.log 2>/dev/null || log "No logs found"
            else
                error "Logs directory not found"
            fi
            ;;
        "clean")
            log "Cleaning deployment..."
            rm -rf "$ONCHAIN_DIR/logs"
            rm -rf "$ONCHAIN_DIR/data"
            log "Deployment cleaned"
            ;;
        *)
            echo "Usage: $0 {deploy|status|stop|logs|clean}"
            echo ""
            echo "Commands:"
            echo "  deploy  - Deploy all on-chain agents"
            echo "  status  - Check agent status"
            echo "  stop    - Stop all agents"
            echo "  logs    - Show recent logs"
            echo "  clean   - Clean deployment files"
            exit 1
            ;;
    esac
}

# Export environment variables for child processes
export ONCHAIN_DIR
export CONFIG_FILE

# Run main function
deploy "$@" 