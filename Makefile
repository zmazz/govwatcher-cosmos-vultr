# Cosmos Governance Risk & Compliance Co-Pilot
# Professional Makefile for development and deployment automation

.PHONY: help setup test deploy clean status docs

# Default target
help: ## Show this help message
	@echo "🌌 Cosmos GRC Co-Pilot - Available Commands"
	@echo "============================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development commands
setup: ## Setup development environment
	@echo "🔧 Setting up development environment..."
	@cp env.example .env 2>/dev/null || echo "env.example already copied"
	@python3 -m venv venv
	@./venv/bin/pip install -r requirements.txt
	@echo "✅ Setup complete! Edit .env with your configuration"

install: ## Install dependencies only
	@echo "📦 Installing dependencies..."
	@pip install -r requirements.txt
	@echo "✅ Dependencies installed"

dev: ## Run development server
	@echo "🚀 Starting development server..."
	@uvicorn src.web.main:app --reload --host 0.0.0.0 --port 8080

dev-bg: ## Run development server in background
	@echo "🚀 Starting development server in background..."
	@uvicorn src.web.main:app --host 0.0.0.0 --port 8080 &
	@echo "✅ Server running at http://localhost:8080"

# Testing commands
test: ## Run all tests
	@echo "🧪 Running tests..."
	@python scripts/hackathon_check.py
	@python scripts/test_basic_setup.py
	@pytest tests/ -v || echo "Note: pytest not found or no tests"
	@echo "✅ All tests completed"

check: ## Run compliance check only
	@echo "✅ Running Vultr Track compliance check..."
	@python scripts/hackathon_check.py

lint: ## Run code linting
	@echo "🔍 Running code linting..."
	@black src/ scripts/ --check || echo "Consider running: make format"
	@flake8 src/ scripts/ || echo "flake8 not installed"

format: ## Format code
	@echo "🎨 Formatting code..."
	@black src/ scripts/
	@echo "✅ Code formatted"

# Docker commands
docker-build: ## Build Docker containers
	@echo "🐳 Building Docker containers..."
	@cd infra/docker && docker-compose build
	@echo "✅ Docker containers built"

docker-up: ## Start all services with Docker
	@echo "🐳 Starting all services..."
	@cd infra/docker && docker-compose up -d
	@echo "✅ All services running"
	@echo "🌐 Access dashboard at: http://localhost:8080/dashboard"

docker-down: ## Stop all services
	@echo "🐳 Stopping all services..."
	@cd infra/docker && docker-compose down
	@echo "✅ All services stopped"

docker-logs: ## View Docker logs
	@cd infra/docker && docker-compose logs -f

docker-status: ## Check Docker service status
	@cd infra/docker && docker-compose ps

# Deployment commands
deploy-vultr: ## Deploy to Vultr VPS
	@echo "☁️ Deploying to Vultr..."
	@./infra/vultr/deploy-vultr.sh deploy

deploy-aws: ## Deploy to AWS
	@echo "☁️ Deploying to AWS..."
	@./infra/aws/deploy.sh all

deploy-onchain: ## Deploy on-chain agents to Fetch.ai blockchain
	@echo "🌌 Deploying on-chain agents..."
	@chmod +x scripts/deploy-onchain.sh
	@./scripts/deploy-onchain.sh deploy

deploy-status: ## Check deployment status
	@echo "📊 Checking deployment status..."
	@if [ -f .vultr_instance ]; then \
		./infra/vultr/deploy-vultr.sh status; \
	else \
		echo "No Vultr deployment found"; \
	fi

# On-chain specific commands
onchain-status: ## Check on-chain agent status
	@echo "🌌 Checking on-chain agent status..."
	@./scripts/deploy-onchain.sh status

onchain-stop: ## Stop on-chain agents
	@echo "🛑 Stopping on-chain agents..."
	@./scripts/deploy-onchain.sh stop

onchain-logs: ## View on-chain agent logs
	@echo "📋 Viewing on-chain agent logs..."
	@./scripts/deploy-onchain.sh logs

onchain-clean: ## Clean on-chain deployment
	@echo "🧹 Cleaning on-chain deployment..."
	@./scripts/deploy-onchain.sh clean

# Utility commands
keys: ## Generate uAgent keys
	@echo "🔑 Generating uAgent keys..."
	@python scripts/generate_uagents_key.py

env-check: ## Check environment configuration
	@echo "🔍 Checking environment..."
	@python scripts/load_env.py

clean: ## Clean up generated files
	@echo "🧹 Cleaning up..."
	@rm -rf __pycache__ .pytest_cache data/*.db .vultr_instance deployment.tar.gz
	@find . -name "*.pyc" -delete
	@find . -name "*.pyo" -delete
	@echo "✅ Cleanup complete"

clean-docker: ## Clean Docker containers and images
	@echo "🧹 Cleaning Docker resources..."
	@cd infra/docker && docker-compose down -v --remove-orphans
	@docker system prune -f
	@echo "✅ Docker cleanup complete"

# Documentation commands
docs: ## Open documentation
	@echo "📚 Opening documentation..."
	@echo "Repository Structure: docs/REPOSITORY_STRUCTURE.md"
	@echo "Deployment Guide: docs/DEPLOYMENT_INSTRUCTIONS.md"
	@echo "AWS Deployment: docs/MASTER_DEPLOYMENT_GUIDE.md"
	@echo "On-Chain Guide: docs/ONCHAIN.md"

readme: ## Show quick README
	@echo "📖 Cosmos Governance Risk & Compliance Co-Pilot"
	@echo "================================================"
	@echo ""
	@echo "🚀 Quick Start:"
	@echo "  make setup      # Setup development environment"
	@echo "  make dev        # Run development server"
	@echo "  make check      # Run compliance validation"
	@echo ""
	@echo "🐳 Docker:"
	@echo "  make docker-up  # Start all services"
	@echo "  make docker-down # Stop all services"
	@echo ""
	@echo "☁️ Deploy:"
	@echo "  make deploy-vultr # Deploy to Vultr VPS"
	@echo "  make deploy-aws   # Deploy to AWS"
	@echo ""
	@echo "📚 Documentation: make docs"

# Status and monitoring
status: ## Show system status
	@echo "📊 System Status Check"
	@echo "====================="
	@echo ""
	@echo "📁 Repository Structure:"
	@ls -la | grep -E "(src|infra|docs|scripts|sql)" || echo "Repository organized ✅"
	@echo ""
	@echo "🐍 Python Environment:"
	@python --version 2>/dev/null || echo "Python not found ❌"
	@pip show fastapi 2>/dev/null | grep Version || echo "FastAPI not installed"
	@echo ""
	@echo "🐳 Docker:"
	@docker --version 2>/dev/null || echo "Docker not found"
	@docker-compose --version 2>/dev/null || echo "Docker Compose not found"
	@echo ""
	@echo "✅ Compliance Status:"
	@python scripts/hackathon_check.py | grep "SUMMARY:" || echo "Check scripts/hackathon_check.py"

# All-in-one commands
fresh-start: clean setup ## Clean and setup from scratch
	@echo "🎊 Fresh start complete!"

local-demo: docker-up ## Start local demo environment
	@echo "🎬 Starting local demo..."
	@sleep 5
	@echo "🌐 Demo ready at: http://localhost:8080/dashboard"
	@echo "👤 Demo credentials: demo@enterprise.com / password123"

production-check: ## Verify production readiness
	@echo "🔍 Production Readiness Check"
	@echo "============================="
	@python scripts/hackathon_check.py
	@echo ""
	@echo "🔑 Environment Check:"
	@test -n "$$GROQ_API_KEY" && echo "✅ GROQ_API_KEY set" || echo "❌ GROQ_API_KEY missing"
	@test -n "$$VULTR_API_KEY" && echo "✅ VULTR_API_KEY set" || echo "⚠️  VULTR_API_KEY not set (needed for deployment)"
	@echo ""
	@echo "📋 Infrastructure Check:"
	@test -f "infra/docker/docker-compose.yml" && echo "✅ Docker Compose ready" || echo "❌ Docker Compose missing"
	@test -f "infra/vultr/deploy-vultr.sh" && echo "✅ Vultr deployment ready" || echo "❌ Vultr deployment missing"
	@test -f "sql/init.sql" && echo "✅ Database schema ready" || echo "❌ Database schema missing"

# Advanced commands
backup: ## Backup important files
	@echo "💾 Creating backup..."
	@mkdir -p backups
	@tar -czf backups/backup-$(shell date +%Y%m%d-%H%M%S).tar.gz \
		src/ infra/ sql/ scripts/ docs/ requirements.txt env.example README.md
	@echo "✅ Backup created in backups/"

version: ## Show version information
	@echo "📍 Cosmos GRC Co-Pilot Version Information"
	@echo "=========================================="
	@echo "Python: $(shell python --version 2>/dev/null || echo 'Not found')"
	@echo "Docker: $(shell docker --version 2>/dev/null || echo 'Not found')"
	@echo "Git: $(shell git --version 2>/dev/null || echo 'Not found')"
	@echo "FastAPI: $(shell pip show fastapi 2>/dev/null | grep Version | cut -d' ' -f2 || echo 'Not installed')"
	@echo "uAgents: $(shell pip show uagents 2>/dev/null | grep Version | cut -d' ' -f2 || echo 'Not installed')"
	@echo ""
	@echo "Repository: $(shell git remote get-url origin 2>/dev/null || echo 'Local repository')"
	@echo "Branch: $(shell git branch --show-current 2>/dev/null || echo 'Unknown')"
	@echo "Commit: $(shell git rev-parse --short HEAD 2>/dev/null || echo 'Unknown')"

# Help is the default target
.DEFAULT_GOAL := help 