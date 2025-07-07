#!/bin/bash

# Cosmos Gov-Watcher SaaS Deployment Script
# Automates Docker build, ECR push, and CloudFormation deployment

set -e  # Exit on any error

# Configuration
STACK_NAME="${STACK_NAME:-govwatcher}"
AWS_REGION="${AWS_REGION:-us-east-1}"
STAGE="${STAGE:-prod}"
DOMAIN_NAME="${DOMAIN_NAME:-govwatcher.com}"
FROM_EMAIL="${FROM_EMAIL:-noreply@govwatcher.com}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Help function
show_help() {
    cat << EOF
Cosmos Gov-Watcher SaaS Deployment Script

Usage: $0 [OPTIONS] COMMAND

Commands:
    build       Build Docker image
    push        Push image to ECR
    deploy      Deploy CloudFormation stack
    all         Build, push, and deploy (default)
    status      Check deployment status
    logs        View Lambda logs
    cleanup     Delete stack and resources

Options:
    -s, --stack-name NAME    CloudFormation stack name (default: govwatcher)
    -r, --region REGION      AWS region (default: us-east-1)
    -t, --stage STAGE        Deployment stage (default: prod)
    -d, --domain DOMAIN      Domain name (default: govwatcher.com)
    -e, --email EMAIL        From email address (default: noreply@govwatcher.com)
    -h, --help              Show this help message

Environment Variables:
    OPENAI_API_KEY          Required: OpenAI API key
    UAGENTS_PRIVATE_KEY     Required: uAgents private key
    SKIP_TESTS             Optional: Skip running tests (default: false)

Examples:
    $0 all                                    # Full deployment
    $0 --stack-name dev-govwatcher deploy     # Deploy to dev stack
    $0 --stage dev --region eu-west-1 all    # Deploy to EU region

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -s|--stack-name)
                STACK_NAME="$2"
                shift 2
                ;;
            -r|--region)
                AWS_REGION="$2"
                shift 2
                ;;
            -t|--stage)
                STAGE="$2"
                shift 2
                ;;
            -d|--domain)
                DOMAIN_NAME="$2"
                shift 2
                ;;
            -e|--email)
                FROM_EMAIL="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            build|push|deploy|all|status|logs|cleanup)
                COMMAND="$1"
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # Default command
    COMMAND="${COMMAND:-all}"
}

# Validate prerequisites
validate_prerequisites() {
    log_info "Validating prerequisites..."

    # Check required commands
    local required_commands=("docker" "aws" "jq")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            log_error "$cmd is required but not installed"
            exit 1
        fi
    done

    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured. Run 'aws configure' first."
        exit 1
    fi

    # Check required environment variables
    if [[ -z "$OPENAI_API_KEY" ]]; then
        log_error "OPENAI_API_KEY environment variable is required"
        exit 1
    fi

    if [[ -z "$UAGENTS_PRIVATE_KEY" ]]; then
        log_error "UAGENTS_PRIVATE_KEY environment variable is required"
        exit 1
    fi

    # Check Docker daemon with timeout (can be skipped with SKIP_DOCKER_CHECK=true)
    if [[ "${SKIP_DOCKER_CHECK:-false}" != "true" ]]; then
        if ! timeout 10 docker info &> /dev/null; then
            log_warning "Docker daemon check failed or timed out. Trying alternative check..."
            if ! timeout 5 docker version --format '{{.Server.Version}}' &> /dev/null; then
                log_error "Docker daemon is not running or not accessible"
                log_info "To skip this check, run with: SKIP_DOCKER_CHECK=true ./deploy.sh all"
                exit 1
            fi
        fi
    else
        log_warning "Skipping Docker daemon check (SKIP_DOCKER_CHECK=true)"
    fi

    log_success "Prerequisites validated"
}

# Get AWS account ID
get_account_id() {
    aws sts get-caller-identity --query 'Account' --output text
}

# Get ECR repository URI
get_ecr_uri() {
    local account_id=$(get_account_id)
    echo "${account_id}.dkr.ecr.${AWS_REGION}.amazonaws.com/${STACK_NAME}-govwatcher"
}

# Run tests
run_tests() {
    if [[ "${SKIP_TESTS:-false}" == "true" ]]; then
        log_warning "Skipping tests (SKIP_TESTS=true)"
        return 0
    fi

    log_info "Running tests..."
    
    if [[ -f "requirements.txt" ]]; then
        # Install test dependencies
        python3 -m pip install -r requirements.txt --quiet
        
        # Run tests if they exist
        if [[ -d "tests" ]]; then
            python3 -m pytest tests/ -v
        else
            log_warning "No tests directory found, skipping tests"
        fi
    else
        log_warning "No requirements.txt found, skipping tests"
    fi

    log_success "Tests completed"
}

# Build Docker image
build_image() {
    log_info "Building Docker image..."

    local ecr_uri=$(get_ecr_uri)
    local image_tag="${ecr_uri}:latest"

    # Build the image with verbose output for linux/amd64 platform (required for AWS Lambda)
    # Use buildx with --provenance=false to generate Docker v2 manifest format (Lambda compatible)
    docker buildx build --platform linux/amd64 --provenance=false --load -t govwatcher:latest . --progress=plain --no-cache

    # Tag for ECR
    docker tag govwatcher:latest "$image_tag"

    # Show image size
    local image_size=$(docker images govwatcher:latest --format "table {{.Size}}" | tail -n1)
    log_success "Docker image built successfully (Size: $image_size)"
    
    # Check if image is close to target size
    local size_mb=$(echo "$image_size" | sed 's/MB//' | cut -d'.' -f1)
    if [[ "$size_mb" -gt 200 ]]; then
        log_warning "Image size (${image_size}) is larger than target (~180MB)"
    fi
}

# Push image to ECR
push_image() {
    log_info "Pushing image to ECR..."

    local ecr_uri=$(get_ecr_uri)
    local repository_name="${STACK_NAME}-govwatcher"

    # Create ECR repository if it doesn't exist
    if ! aws ecr describe-repositories --repository-names "$repository_name" --region "$AWS_REGION" &> /dev/null; then
        log_info "Creating ECR repository: $repository_name"
        aws ecr create-repository --repository-name "$repository_name" --region "$AWS_REGION" > /dev/null
    fi

    # Login to ECR
    aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ecr_uri"

    # Push the image
    docker push "${ecr_uri}:latest"

    log_success "Image pushed to ECR: ${ecr_uri}:latest"
}

# Deploy CloudFormation stack
deploy_stack() {
    log_info "Deploying CloudFormation stack: $STACK_NAME"

    # Validate template
    aws cloudformation validate-template --template-body file://infra/stack.yml --region "$AWS_REGION" > /dev/null

    # Deploy stack
    aws cloudformation deploy \
        --template-file infra/stack.yml \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --capabilities CAPABILITY_NAMED_IAM \
        --parameter-overrides \
            "DomainName=$DOMAIN_NAME" \
            "FromEmail=$FROM_EMAIL" \
            "OpenAIKey=$OPENAI_API_KEY" \
            "PrivateKey=$UAGENTS_PRIVATE_KEY" \
            "Stage=$STAGE" \
        --tags \
            Application=GovWatcher \
            Stage="$STAGE" \
            ManagedBy=deploy-script

    log_success "CloudFormation stack deployed successfully"

    # Get stack outputs
    log_info "Getting stack outputs..."
    aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query 'Stacks[0].Outputs' \
        --output table
}

# Check deployment status
check_status() {
    log_info "Checking deployment status for stack: $STACK_NAME"

    # Check stack status
    local stack_status=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query 'Stacks[0].StackStatus' \
        --output text 2>/dev/null || echo "NOT_FOUND")

    if [[ "$stack_status" == "NOT_FOUND" ]]; then
        log_warning "Stack '$STACK_NAME' not found"
        return 1
    fi

    echo "Stack Status: $stack_status"

    # Check Lambda functions
    log_info "Checking Lambda functions..."
    local functions=$(aws lambda list-functions \
        --region "$AWS_REGION" \
        --query "Functions[?starts_with(FunctionName, '$STACK_NAME')].{Name:FunctionName,State:State,LastModified:LastModified}" \
        --output table)

    if [[ -n "$functions" ]]; then
        echo "$functions"
    else
        log_warning "No Lambda functions found for stack"
    fi
}

# View Lambda logs
view_logs() {
    log_info "Viewing recent Lambda logs for stack: $STACK_NAME"

    local log_group="/aws/lambda/${STACK_NAME}-govwatcher"
    
    # Check if log group exists
    if aws logs describe-log-groups \
        --log-group-name-prefix "$log_group" \
        --region "$AWS_REGION" \
        --query 'logGroups[0].logGroupName' \
        --output text 2>/dev/null | grep -q "$log_group"; then
        
        log_info "Fetching logs from $log_group"
        aws logs filter-log-events \
            --log-group-name "$log_group" \
            --region "$AWS_REGION" \
            --start-time $(date -d '1 hour ago' +%s)000 \
            --query 'events[*].[timestamp,message]' \
            --output text | head -50
    else
        log_warning "Log group not found: $log_group"
    fi
}

# Cleanup resources
cleanup_stack() {
    log_warning "This will delete the entire stack and all resources!"
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Cleanup cancelled"
        return 0
    fi

    log_info "Deleting CloudFormation stack: $STACK_NAME"

    # Empty S3 bucket first (if it exists)
    local bucket_name=$(aws cloudformation describe-stack-resources \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --logical-resource-id LogBucket \
        --query 'StackResources[0].PhysicalResourceId' \
        --output text 2>/dev/null || echo "")

    if [[ -n "$bucket_name" && "$bucket_name" != "None" ]]; then
        log_info "Emptying S3 bucket: $bucket_name"
        aws s3 rm "s3://$bucket_name" --recursive --region "$AWS_REGION" || true
    fi

    # Delete stack
    aws cloudformation delete-stack \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION"

    log_info "Stack deletion initiated. This may take several minutes..."
    
    # Wait for deletion to complete
    aws cloudformation wait stack-delete-complete \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION"

    log_success "Stack deleted successfully"
}

# Main execution
main() {
    parse_args "$@"

    log_info "Cosmos Gov-Watcher SaaS Deployment"
    log_info "Stack: $STACK_NAME | Region: $AWS_REGION | Stage: $STAGE"
    log_info "Command: $COMMAND"
    echo

    case "$COMMAND" in
        build)
            validate_prerequisites
            run_tests
            build_image
            ;;
        push)
            validate_prerequisites
            push_image
            ;;
        deploy)
            validate_prerequisites
            deploy_stack
            ;;
        all)
            validate_prerequisites
            run_tests
            build_image
            push_image
            deploy_stack
            ;;
        status)
            check_status
            ;;
        logs)
            view_logs
            ;;
        cleanup)
            cleanup_stack
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            show_help
            exit 1
            ;;
    esac

    log_success "Deployment script completed successfully!"
}

# Run main function with all arguments
main "$@" 