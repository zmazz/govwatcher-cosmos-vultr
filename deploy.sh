#!/bin/bash

# =============================================================================
# Cosmos Governance Risk & Compliance Co-Pilot - Main Deployment Script
# Enterprise-ready multi-deployment orchestrator for Vultr Track
# =============================================================================

set -e

# Get the script directory (works regardless of where it's called from)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Configuration
DEFAULT_DEPLOYMENT="vultr"
DEPLOYMENT_TYPE="${DEPLOYMENT_TYPE:-$DEFAULT_DEPLOYMENT}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "${PURPLE}[HEADER]${NC} $1"
}

print_banner() {
    echo -e "${CYAN}"
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════════════════════╗
║                 🌌 Cosmos GRC Co-Pilot - Deployment Manager                 ║
║                                Vultr Track                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

show_help() {
    print_banner
    cat << EOF
${GREEN}Enterprise-Ready Governance Risk & Compliance Co-Pilot${NC}

${CYAN}USAGE:${NC}
    $0 [DEPLOYMENT_TYPE] [COMMAND] [OPTIONS]

${CYAN}DEPLOYMENT TYPES:${NC}
    ${GREEN}vultr${NC}      Deploy to Vultr VPS (Recommended for Vultr Track)
    ${GREEN}aws${NC}        Deploy to AWS Lambda/CloudFormation
    ${GREEN}local${NC}      Deploy locally with Docker Compose
    ${GREEN}onchain${NC}    Deploy on-chain agents to Fetch.ai blockchain
    ${GREEN}hybrid${NC}     Deploy both cloud and on-chain components

${CYAN}COMMANDS:${NC}
    ${GREEN}deploy${NC}     Full deployment (default)
    ${GREEN}setup${NC}      Environment setup and validation
    ${GREEN}test${NC}       Run validation tests
    ${GREEN}status${NC}     Check deployment status
    ${GREEN}logs${NC}       View deployment logs
    ${GREEN}cleanup${NC}    Clean up deployment
    ${GREEN}help${NC}       Show this help message

${CYAN}EXAMPLES:${NC}
    $0 vultr deploy              # Deploy to Vultr (recommended)
    $0 aws deploy                # Deploy to AWS
    $0 local deploy              # Deploy locally
    $0 onchain deploy            # Deploy on-chain agents
    $0 vultr status              # Check Vultr deployment status
    $0 hybrid deploy             # Deploy both cloud and on-chain

${CYAN}ENVIRONMENT SETUP:${NC}
    1. Copy env.example to .env and configure your settings
    2. Run: $0 setup
    3. Run: $0 [deployment_type] deploy

${CYAN}REQUIRED ENVIRONMENT VARIABLES:${NC}
    For Vultr:    VULTR_API_KEY, GROQ_API_KEY
    For AWS:      AWS credentials, OPENAI_API_KEY, UAGENTS_PRIVATE_KEY
    For On-chain: GROQ_API_KEY, DEPLOYMENT_URL

${CYAN}VULTR TRACK FEATURES:${NC}
    ✅ Groq API integration for AI analysis
    ✅ Llama model support for hybrid analysis
    ✅ Enterprise web dashboard with FastAPI
    ✅ Multi-chain Cosmos governance monitoring
    ✅ Autonomous agent architecture
    ✅ Health monitoring endpoints

EOF
}

validate_environment() {
    log_info "Validating environment..."
    
    # Check if .env file exists
    if [[ ! -f "$PROJECT_ROOT/.env" ]]; then
        log_warning ".env file not found. Checking env.example..."
        if [[ -f "$PROJECT_ROOT/env.example" ]]; then
            log_info "Found env.example. You should copy it to .env and configure it:"
            echo "    cp env.example .env"
            echo "    # Edit .env with your configuration"
        else
            log_error "No environment configuration found"
            exit 1
        fi
    else
        log_success ".env file found"
        # Load environment variables
        set -a
        source "$PROJECT_ROOT/.env"
        set +a
    fi
    
    # Check for required tools
    local required_tools=("docker" "curl" "jq")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool is required but not installed"
            exit 1
        fi
    done
    
    log_success "Environment validation completed"
}

run_setup() {
    log_header "Setting up deployment environment..."
    
    # Create necessary directories
    mkdir -p "$PROJECT_ROOT/data"
    mkdir -p "$PROJECT_ROOT/logs"
    
    # Copy environment template if needed
    if [[ ! -f "$PROJECT_ROOT/.env" && -f "$PROJECT_ROOT/env.example" ]]; then
        log_info "Creating .env file from template..."
        cp "$PROJECT_ROOT/env.example" "$PROJECT_ROOT/.env"
        log_warning "Please edit .env file with your configuration before deploying"
    fi
    
    # Generate uAgents key if needed
    if [[ -f "$PROJECT_ROOT/scripts/generate_uagents_key.py" ]]; then
        log_info "Checking uAgents key..."
        python3 "$PROJECT_ROOT/scripts/generate_uagents_key.py"
    fi
    
    # Run basic setup tests
    if [[ -f "$PROJECT_ROOT/scripts/test_basic_setup.py" ]]; then
        log_info "Running basic setup validation..."
        python3 "$PROJECT_ROOT/scripts/test_basic_setup.py"
    fi
    
    log_success "Setup completed successfully"
}

run_tests() {
    log_header "Running deployment validation tests..."
    
    # Run compliance check
    if [[ -f "$PROJECT_ROOT/scripts/hackathon_check.py" ]]; then
        log_info "Running Vultr Track compliance check..."
        python3 "$PROJECT_ROOT/scripts/hackathon_check.py"
    fi
    
    # Run basic setup tests
    if [[ -f "$PROJECT_ROOT/scripts/test_basic_setup.py" ]]; then
        log_info "Running basic setup tests..."
        python3 "$PROJECT_ROOT/scripts/test_basic_setup.py"
    fi
    
    log_success "All tests completed"
}

deploy_vultr() {
    log_header "Deploying to Vultr VPS..."
    
    local vultr_script="$PROJECT_ROOT/infra/vultr/deploy-vultr.sh"
    if [[ -f "$vultr_script" ]]; then
        cd "$PROJECT_ROOT"
        bash "$vultr_script" "$@"
    else
        log_error "Vultr deployment script not found: $vultr_script"
        exit 1
    fi
}

deploy_aws() {
    log_header "Deploying to AWS..."
    
    local aws_script="$PROJECT_ROOT/infra/aws/deploy.sh"
    if [[ -f "$aws_script" ]]; then
        cd "$PROJECT_ROOT"
        bash "$aws_script" "$@"
    else
        log_error "AWS deployment script not found: $aws_script"
        exit 1
    fi
}

deploy_local() {
    log_header "Deploying locally with Docker Compose..."
    
    cd "$PROJECT_ROOT"
    
    # Use the docker-compose file
    local compose_file="$PROJECT_ROOT/infra/docker/docker-compose.yml"
    if [[ -f "$compose_file" ]]; then
        log_info "Starting services with Docker Compose..."
        docker compose -f "$compose_file" up -d --build
        
        log_info "Waiting for services to start..."
        sleep 10
        
        # Check health
        if curl -s http://localhost:8080/status > /dev/null; then
            log_success "Local deployment successful!"
            log_info "Dashboard: http://localhost:8080"
            log_info "Health: http://localhost:8080/status"
            log_info "API Docs: http://localhost:8080/docs"
        else
            log_error "Health check failed"
            exit 1
        fi
    else
        log_error "Docker Compose file not found: $compose_file"
        exit 1
    fi
}

deploy_onchain() {
    log_header "Deploying on-chain agents..."
    
    local onchain_script="$PROJECT_ROOT/scripts/deploy-onchain.sh"
    if [[ -f "$onchain_script" ]]; then
        cd "$PROJECT_ROOT"
        bash "$onchain_script" "$@"
    else
        log_error "On-chain deployment script not found: $onchain_script"
        exit 1
    fi
}

deploy_hybrid() {
    log_header "Deploying hybrid (cloud + on-chain) architecture..."
    
    # First deploy to cloud
    case "${CLOUD_PROVIDER:-vultr}" in
        "vultr")
            deploy_vultr "$@"
            ;;
        "aws")
            deploy_aws "$@"
            ;;
        *)
            log_warning "Unknown cloud provider, defaulting to Vultr"
            deploy_vultr "$@"
            ;;
    esac
    
    # Then deploy on-chain components
    deploy_onchain "$@"
    
    log_success "Hybrid deployment completed"
}

show_status() {
    log_header "Checking deployment status..."
    
    case "$DEPLOYMENT_TYPE" in
        "vultr")
            if [[ -f "$PROJECT_ROOT/infra/vultr/deploy-vultr.sh" ]]; then
                bash "$PROJECT_ROOT/infra/vultr/deploy-vultr.sh" status
            fi
            ;;
        "aws")
            if [[ -f "$PROJECT_ROOT/infra/aws/deploy.sh" ]]; then
                bash "$PROJECT_ROOT/infra/aws/deploy.sh" status
            fi
            ;;
        "local")
            log_info "Checking local Docker services..."
            if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
                docker compose -f "$PROJECT_ROOT/infra/docker/docker-compose.yml" ps
            fi
            ;;
        "onchain")
            if [[ -f "$PROJECT_ROOT/scripts/deploy-onchain.sh" ]]; then
                bash "$PROJECT_ROOT/scripts/deploy-onchain.sh" status
            fi
            ;;
        *)
            log_error "Unknown deployment type: $DEPLOYMENT_TYPE"
            ;;
    esac
}

cleanup_deployment() {
    log_header "Cleaning up deployment..."
    
    case "$DEPLOYMENT_TYPE" in
        "vultr")
            if [[ -f "$PROJECT_ROOT/infra/vultr/deploy-vultr.sh" ]]; then
                bash "$PROJECT_ROOT/infra/vultr/deploy-vultr.sh" destroy
            fi
            ;;
        "aws")
            if [[ -f "$PROJECT_ROOT/infra/aws/deploy.sh" ]]; then
                bash "$PROJECT_ROOT/infra/aws/deploy.sh" cleanup
            fi
            ;;
        "local")
            log_info "Stopping local Docker services..."
            if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
                docker compose -f "$PROJECT_ROOT/infra/docker/docker-compose.yml" down -v
            fi
            ;;
        "onchain")
            if [[ -f "$PROJECT_ROOT/scripts/deploy-onchain.sh" ]]; then
                bash "$PROJECT_ROOT/scripts/deploy-onchain.sh" clean
            fi
            ;;
        *)
            log_error "Unknown deployment type: $DEPLOYMENT_TYPE"
            ;;
    esac
}

# Parse arguments
parse_arguments() {
    if [[ $# -eq 0 ]]; then
        show_help
        exit 0
    fi
    
    # Check if first argument is a deployment type
    case "$1" in
        "vultr"|"aws"|"local"|"onchain"|"hybrid")
            DEPLOYMENT_TYPE="$1"
            shift
            ;;
    esac
    
    # Parse command
    case "${1:-deploy}" in
        "deploy")
            COMMAND="deploy"
            shift
            ;;
        "setup")
            COMMAND="setup"
            shift
            ;;
        "test")
            COMMAND="test"
            shift
            ;;
        "status")
            COMMAND="status"
            shift
            ;;
        "logs")
            COMMAND="logs"
            shift
            ;;
        "cleanup")
            COMMAND="cleanup"
            shift
            ;;
        "help"|"-h"|"--help")
            show_help
            exit 0
            ;;
        *)
            COMMAND="deploy"
            ;;
    esac
    
    # Store remaining arguments
    EXTRA_ARGS="$@"
}

# Main execution
main() {
    print_banner
    
    parse_arguments "$@"
    
    log_info "Deployment Type: $DEPLOYMENT_TYPE"
    log_info "Command: $COMMAND"
    
    # Validate environment for most commands
    if [[ "$COMMAND" != "help" && "$COMMAND" != "setup" ]]; then
        validate_environment
    fi
    
    # Execute command
    case "$COMMAND" in
        "setup")
            run_setup
            ;;
        "test")
            run_tests
            ;;
        "deploy")
            case "$DEPLOYMENT_TYPE" in
                "vultr")
                    deploy_vultr $EXTRA_ARGS
                    ;;
                "aws")
                    deploy_aws $EXTRA_ARGS
                    ;;
                "local")
                    deploy_local $EXTRA_ARGS
                    ;;
                "onchain")
                    deploy_onchain $EXTRA_ARGS
                    ;;
                "hybrid")
                    deploy_hybrid $EXTRA_ARGS
                    ;;
                *)
                    log_error "Unknown deployment type: $DEPLOYMENT_TYPE"
                    show_help
                    exit 1
                    ;;
            esac
            ;;
        "status")
            show_status
            ;;
        "cleanup")
            cleanup_deployment
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            show_help
            exit 1
            ;;
    esac
    
    log_success "Operation completed successfully!"
}

# Run main function
main "$@" 