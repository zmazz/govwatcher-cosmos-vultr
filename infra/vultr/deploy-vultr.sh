#!/bin/bash

# Vultr Deployment Script for Cosmos Governance Risk & Compliance Co-Pilot
# This script provisions a Vultr VPS and deploys the enterprise GRC application

set -e

# Get the root directory (two levels up from this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Configuration
VULTR_API_KEY=${VULTR_API_KEY:-""}
VPS_LABEL="govwatcher-grc-copilot"
VPS_REGION="ewr"  # New Jersey (change as needed)
VPS_PLAN="vc2-1c-1gb"  # $6/month plan (cheapest with good specs)
VPS_OS="1743"  # Ubuntu 22.04 LTS x64 (updated from 387)
DOMAIN_NAME=${DOMAIN_NAME:-""}
SSL_EMAIL=${SSL_EMAIL:-"admin@govwatcher.com"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

check_dependencies() {
    log_info "Checking deployment dependencies..."
    
    # Check if curl is installed
    if ! command -v curl &> /dev/null; then
        log_error "curl is required but not installed"
        exit 1
    fi
    
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        log_error "jq is required but not installed. Install with: sudo apt-get install jq"
        exit 1
    fi
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is required but not installed"
        exit 1
    fi
    
    # Check if Docker Compose is installed (either standalone or plugin)
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is required but not installed"
        exit 1
    fi
    
    log_success "All dependencies are available"
}

validate_environment() {
    log_info "Validating environment variables..."
    
    if [ -z "$VULTR_API_KEY" ]; then
        log_error "VULTR_API_KEY is required but not set"
        echo "Get your API key from: https://my.vultr.com/settings/#settingsapi"
        exit 1
    fi
    
    if [ -z "$GROQ_API_KEY" ]; then
        log_warning "GROQ_API_KEY is not set. Get one from: https://console.groq.com/keys"
    fi
    
    if [ -z "$OPENAI_API_KEY" ]; then
        log_warning "OPENAI_API_KEY is not set as fallback"
    fi
    
    log_success "Environment validation complete"
}

provision_vps() {
    log_info "Provisioning Vultr VPS..."
    
    # Create VPS
    RESPONSE=$(curl -s -X POST "https://api.vultr.com/v2/instances" \
        -H "Authorization: Bearer $VULTR_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{
            "region": "'$VPS_REGION'",
            "plan": "'$VPS_PLAN'",
            "os_id": '$VPS_OS',
            "label": "'$VPS_LABEL'",
            "tag": "govwatcher-grc",
            "hostname": "govwatcher-grc",
            "enable_ipv6": false,
            "enable_private_network": false,
            "enable_ddos_protection": false,
            "enable_backups": false
        }')
    
    # Extract instance ID
    INSTANCE_ID=$(echo $RESPONSE | jq -r '.instance.id')
    
    if [ "$INSTANCE_ID" == "null" ]; then
        log_error "Failed to create VPS. Response: $RESPONSE"
        exit 1
    fi
    
    log_success "VPS created with ID: $INSTANCE_ID"
    
    # Wait for VPS to be ready
    log_info "Waiting for VPS to be ready..."
    while true; do
        STATUS=$(curl -s -X GET "https://api.vultr.com/v2/instances/$INSTANCE_ID" \
            -H "Authorization: Bearer $VULTR_API_KEY" | jq -r '.instance.status')
        
        if [ "$STATUS" == "active" ]; then
            break
        fi
        
        log_info "VPS status: $STATUS. Waiting 30 seconds..."
        sleep 30
    done
    
    # Get VPS IP
    VPS_IP=$(curl -s -X GET "https://api.vultr.com/v2/instances/$INSTANCE_ID" \
        -H "Authorization: Bearer $VULTR_API_KEY" | jq -r '.instance.main_ip')
    
    log_success "VPS is ready! IP: $VPS_IP"
    
    # Save instance info to root directory
    echo "INSTANCE_ID=$INSTANCE_ID" > "$ROOT_DIR/.vultr_instance"
    echo "VPS_IP=$VPS_IP" >> "$ROOT_DIR/.vultr_instance"
    
    log_info "Instance details saved to .vultr_instance"
}

setup_vps() {
    log_info "Setting up VPS environment..."
    
    # Load instance info
    source "$ROOT_DIR/.vultr_instance"
    
    # Wait for SSH to be ready
    log_info "Waiting for SSH to be ready..."
    while ! ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no root@$VPS_IP exit 2>/dev/null; do
        log_info "SSH not ready, waiting 10 seconds..."
        sleep 10
    done
    
    log_success "SSH is ready"
    
    # Setup script
    cat > /tmp/setup_vps.sh << 'EOF'
#!/bin/bash
set -e

# Update system
apt-get update -y
apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl start docker
systemctl enable docker

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install other dependencies
apt-get install -y nginx certbot python3-certbot-nginx jq curl

# Create application directory
mkdir -p /opt/govwatcher
cd /opt/govwatcher

# Create nginx configuration
cat > /etc/nginx/sites-available/govwatcher << 'NGINX_CONF'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /status {
        proxy_pass http://localhost:8080/status;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
NGINX_CONF

# Enable nginx site
ln -sf /etc/nginx/sites-available/govwatcher /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
systemctl reload nginx

# Configure firewall
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "VPS setup complete!"
EOF

    # Copy and run setup script
    scp -o StrictHostKeyChecking=no /tmp/setup_vps.sh root@$VPS_IP:/tmp/
    ssh -o StrictHostKeyChecking=no root@$VPS_IP 'chmod +x /tmp/setup_vps.sh && /tmp/setup_vps.sh'
    
    log_success "VPS setup complete"
}

deploy_application() {
    log_info "Deploying application to VPS..."
    
    # Load instance info
    source "$ROOT_DIR/.vultr_instance"
    
    # Create deployment package from root directory
    cd "$ROOT_DIR"
    
    # Ensure all required files exist
    if [[ ! -f "infra/docker/docker-compose.yml" ]]; then
        log_error "Missing docker-compose.yml file"
        exit 1
    fi
    
    # Create deployment package with only necessary files
    tar -czf deployment.tar.gz \
        infra/docker/docker-compose.yml \
        infra/docker/Dockerfile* \
        infra/nginx/nginx.conf \
        src/ \
        requirements.txt \
        sql/ \
        env.example
    
    # Upload deployment package
    scp -o StrictHostKeyChecking=no deployment.tar.gz root@$VPS_IP:/opt/govwatcher/
    
    # Create .env file
    cat > .env.production << EOF
# Production Environment Configuration
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-$(openssl rand -hex 16)}
GROQ_API_KEY=${GROQ_API_KEY:-}
LLAMA_API_KEY=${LLAMA_API_KEY:-}
OPENAI_API_KEY=${OPENAI_API_KEY:-}
JWT_SECRET=${JWT_SECRET:-$(openssl rand -hex 32)}
FROM_EMAIL=${FROM_EMAIL:-noreply@govwatcher.com}
SMTP_SERVER=${SMTP_SERVER:-}
SMTP_PORT=${SMTP_PORT:-587}
SMTP_USERNAME=${SMTP_USERNAME:-}
SMTP_PASSWORD=${SMTP_PASSWORD:-}
UAGENTS_PRIVATE_KEY=${UAGENTS_PRIVATE_KEY:-}
LOG_LEVEL=${LOG_LEVEL:-INFO}
EOF
    
    # Upload environment file
    scp -o StrictHostKeyChecking=no .env.production root@$VPS_IP:/opt/govwatcher/.env
    
    # Deploy application
    ssh -o StrictHostKeyChecking=no root@$VPS_IP << 'EOF'
cd /opt/govwatcher
tar -xzf deployment.tar.gz

# Check if files exist before copying
if [ -d "infra/docker" ]; then
    cp infra/docker/docker-compose.yml .
    cp infra/docker/Dockerfile* .
    cp infra/nginx/nginx.conf .
    
    # Clean up extracted structure
    rm -rf infra/
else
    echo "Error: infra/docker directory not found after extraction"
    ls -la
    exit 1
fi

# Start services
docker compose down || true
docker compose up -d --build
EOF
    
    log_success "Application deployed successfully"
    log_info "Application URL: http://$VPS_IP"
    
    if [ -n "$DOMAIN_NAME" ]; then
        log_info "Don't forget to point your domain $DOMAIN_NAME to IP: $VPS_IP"
        log_info "Then run: $SCRIPT_DIR/deploy-vultr.sh setup_ssl"
    fi
}

setup_ssl() {
    log_info "Setting up SSL certificate..."
    
    if [ -z "$DOMAIN_NAME" ]; then
        log_error "DOMAIN_NAME is required for SSL setup"
        exit 1
    fi
    
    # Load instance info
    source "$ROOT_DIR/.vultr_instance"
    
    # Setup SSL
    ssh -o StrictHostKeyChecking=no root@$VPS_IP << EOF
# Update nginx configuration for domain
sed -i 's/server_name _;/server_name $DOMAIN_NAME;/' /etc/nginx/sites-available/govwatcher
systemctl reload nginx

# Get SSL certificate
certbot --nginx -d $DOMAIN_NAME --non-interactive --agree-tos --email $SSL_EMAIL
EOF
    
    log_success "SSL certificate configured for $DOMAIN_NAME"
}

cleanup() {
    log_info "Cleaning up local files..."
    rm -f /tmp/setup_vps.sh "$ROOT_DIR/deployment.tar.gz" "$ROOT_DIR/.env.production"
    log_success "Cleanup complete"
}

destroy_vps() {
    log_warning "This will destroy the VPS and all data. Are you sure? (y/N)"
    read -r confirm
    
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        log_info "Deployment cancelled"
        exit 0
    fi
    
    if [ ! -f "$ROOT_DIR/.vultr_instance" ]; then
        log_error "No instance file found. Cannot destroy VPS."
        exit 1
    fi
    
    source "$ROOT_DIR/.vultr_instance"
    
    log_info "Destroying VPS with ID: $INSTANCE_ID"
    
    curl -s -X DELETE "https://api.vultr.com/v2/instances/$INSTANCE_ID" \
        -H "Authorization: Bearer $VULTR_API_KEY"
    
    rm -f "$ROOT_DIR/.vultr_instance"
    log_success "VPS destroyed"
}

show_status() {
    if [ ! -f "$ROOT_DIR/.vultr_instance" ]; then
        log_info "No VPS instance found"
        return
    fi
    
    source "$ROOT_DIR/.vultr_instance"
    
    log_info "VPS Status:"
    echo "Instance ID: $INSTANCE_ID"
    echo "IP Address: $VPS_IP"
    echo "Application URL: http://$VPS_IP"
    
    if [ -n "$DOMAIN_NAME" ]; then
        echo "Domain: https://$DOMAIN_NAME"
    fi
    
    # Check if services are running
    log_info "Checking service health..."
    if curl -s -f "http://$VPS_IP/status" > /dev/null; then
        log_success "Application is running"
    else
        log_error "Application is not responding"
    fi
}

show_help() {
    echo "Vultr Deployment Script for Cosmos Governance Risk & Compliance Co-Pilot"
    echo
    echo "Usage: $0 [command]"
    echo
    echo "Commands:"
    echo "  deploy       - Full deployment (provision + setup + deploy)"
    echo "  provision    - Provision new VPS"
    echo "  setup        - Setup VPS environment"
    echo "  deploy_app   - Deploy application to existing VPS"
    echo "  setup_ssl    - Setup SSL certificate (requires DOMAIN_NAME)"
    echo "  status       - Show deployment status"
    echo "  destroy      - Destroy VPS"
    echo "  help         - Show this help message"
    echo
    echo "Required Environment Variables:"
    echo "  VULTR_API_KEY - Your Vultr API key"
    echo "  GROQ_API_KEY  - Your Groq API key"
    echo
    echo "Optional Environment Variables:"
    echo "  DOMAIN_NAME   - Your domain name"
    echo "  SSL_EMAIL     - Email for SSL certificate"
    echo "  SMTP_SERVER   - SMTP server for email"
    echo "  SMTP_USERNAME - SMTP username"
    echo "  SMTP_PASSWORD - SMTP password"
    echo
    echo "Note: Run this script from anywhere - it automatically finds the project root."
}

# Main execution
case "${1:-deploy}" in
    deploy)
        check_dependencies
        validate_environment
        provision_vps
        setup_vps
        deploy_application
        cleanup
        show_status
        ;;
    provision)
        check_dependencies
        validate_environment
        provision_vps
        ;;
    setup)
        setup_vps
        ;;
    deploy_app)
        deploy_application
        cleanup
        ;;
    setup_ssl)
        setup_ssl
        ;;
    status)
        show_status
        ;;
    destroy)
        destroy_vps
        ;;
    help)
        show_help
        ;;
    *)
        log_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac 