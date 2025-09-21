# AI Research Paper Intelligence System - Makefile

.PHONY: help setup start stop clean test lint format docs

help: ## Show this help message
	@echo "AI Research Paper Intelligence System"
	@echo "===================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development Environment
setup: ## Setup development environment
	@echo "🚀 Setting up development environment..."
	@cp .env.example .env
	@echo "📝 Please edit .env with your API keys"
	@echo "🐳 Starting services..."
	@docker-compose up -d
	@echo "⏳ Waiting for services to be ready..."
	@sleep 15
	@echo "🗄️ Running database migrations..."
	@docker-compose exec backend alembic upgrade head
	@echo "✅ Setup complete!"
	@echo ""
	@echo "🌐 Access points:"
	@echo "  Backend API: http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Jupyter: http://localhost:8888 (token: research-papers-dev)"
	@echo "  Neo4j: http://localhost:7474 (neo4j/password)"
	@echo "  Grafana: http://localhost:3001 (admin/admin)"

start: ## Start all services
	@echo "🚀 Starting all services..."
	@docker-compose up -d

stop: ## Stop all services
	@echo "🛑 Stopping all services..."
	@docker-compose down

restart: ## Restart all services
	@echo "🔄 Restarting all services..."
	@docker-compose restart

clean: ## Clean up containers and volumes
	@echo "🧹 Cleaning up..."
	@docker-compose down -v
	@docker system prune -f

# Database Management
db-migrate: ## Run database migrations
	@echo "🗄️ Running database migrations..."
	@docker-compose exec backend alembic upgrade head

db-reset: ## Reset database (WARNING: destroys all data)
	@echo "⚠️  Resetting database (this will destroy all data)..."
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		docker-compose up -d postgres redis neo4j; \
		sleep 10; \
		docker-compose exec backend alembic upgrade head; \
		echo "✅ Database reset complete"; \
	else \
		echo "❌ Database reset cancelled"; \
	fi

db-shell: ## Access database shell
	@docker-compose exec postgres psql -U postgres -d research_papers

# Development Tools
logs: ## Show logs from all services
	@docker-compose logs -f

logs-backend: ## Show backend logs
	@docker-compose logs -f backend

logs-db: ## Show database logs
	@docker-compose logs -f postgres

shell-backend: ## Access backend shell
	@docker-compose exec backend bash

shell-db: ## Access database shell
	@docker-compose exec postgres psql -U postgres -d research_papers

# Testing
test: ## Run all tests
	@echo "🧪 Running tests..."
	@docker-compose exec backend pytest -v

test-coverage: ## Run tests with coverage
	@echo "🧪 Running tests with coverage..."
	@docker-compose exec backend pytest --cov=. --cov-report=html

test-agents: ## Run agent-specific tests
	@echo "🤖 Running agent tests..."
	@docker-compose exec backend pytest tests/test_agents.py -v

# Code Quality
lint: ## Run linting
	@echo "🔍 Running linters..."
	@docker-compose exec backend black --check .
	@docker-compose exec backend flake8 .
	@docker-compose exec backend isort --check-only .

format: ## Format code
	@echo "✨ Formatting code..."
	@docker-compose exec backend black .
	@docker-compose exec backend isort .

# Monitoring
health: ## Check system health
	@echo "🏥 Checking system health..."
	@curl -s http://localhost:8000/health | jq '.'

metrics: ## Show system metrics
	@echo "📊 System metrics:"
	@curl -s http://localhost:8000/metrics

status: ## Show service status
	@echo "📋 Service status:"
	@docker-compose ps

# Data Management
seed-papers: ## Seed database with sample papers
	@echo "📚 Seeding sample papers..."
	@docker-compose exec backend python scripts/seed_papers.py

create-agent: ## Create a sample agent (requires paper_id)
	@echo "🤖 Creating sample agent..."
	@curl -X POST http://localhost:8000/api/v1/agents/ \
		-H "Content-Type: application/json" \
		-d '{"paper_id": "$(PAPER_ID)", "agent_type": "interactive", "model_name": "gpt-3.5-turbo"}'

# Documentation
docs: ## Generate documentation
	@echo "📖 Generating documentation..."
	@echo "API documentation available at: http://localhost:8000/docs"

docs-serve: ## Serve documentation locally
	@echo "📖 Serving documentation..."
	@cd docs && python -m http.server 8080

# Production
build: ## Build production images
	@echo "🏗️ Building production images..."
	@docker build -t research-papers/backend:latest ./backend
	@docker build -t research-papers/frontend:latest ./frontend

deploy-staging: ## Deploy to staging (requires AWS setup)
	@echo "🚀 Deploying to staging..."
	@echo "⚠️  This requires AWS credentials and infrastructure setup"

# Utilities
backup: ## Backup database
	@echo "💾 Creating database backup..."
	@docker-compose exec postgres pg_dump -U postgres research_papers > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backup created: backup_$(shell date +%Y%m%d_%H%M%S).sql"

restore: ## Restore database from backup (requires BACKUP_FILE)
	@echo "📥 Restoring database from $(BACKUP_FILE)..."
	@docker-compose exec -T postgres psql -U postgres research_papers < $(BACKUP_FILE)

update: ## Update dependencies
	@echo "🔄 Updating dependencies..."
	@docker-compose pull
	@docker-compose build --no-cache

# Quick Actions
quick-start: ## Quick start for first-time users
	@echo "⚡ Quick start setup..."
	@make setup
	@echo ""
	@echo "🎉 Quick start complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Edit .env with your OpenAI API key"
	@echo "2. Visit http://localhost:8000/docs to explore the API"
	@echo "3. Run 'make seed-papers' to add sample data"
	@echo "4. Create your first agent with the API"

demo: ## Run demo scenario
	@echo "🎬 Running demo scenario..."
	@echo "Creating sample paper and agent..."
	@curl -X POST http://localhost:8000/api/v1/papers/ \
		-H "Content-Type: application/json" \
		-d '{"title": "Sample Paper", "abstract": "A sample research paper for demonstration", "authors": ["Demo Author"], "categories": ["cs.AI"]}'
	@echo "✅ Demo setup complete. Check http://localhost:8000/docs for API exploration"

# Development Helpers
dev-reset: ## Reset development environment
	@echo "🔄 Resetting development environment..."
	@make clean
	@make setup

install-dev: ## Install development dependencies locally
	@echo "📦 Installing development dependencies..."
	@cd backend && pip install -r requirements.txt
	@cd frontend && npm install

check-env: ## Check environment configuration
	@echo "🔍 Checking environment configuration..."
	@docker-compose config

# Troubleshooting
troubleshoot: ## Run troubleshooting checks
	@echo "🔧 Running troubleshooting checks..."
	@echo "Docker version:"
	@docker --version
	@echo "Docker Compose version:"
	@docker-compose --version
	@echo "Available ports:"
	@netstat -tulpn | grep -E ':(3000|8000|5432|6379|7474|7687)' || echo "Ports are available"
	@echo "Docker system info:"
	@docker system df
	@echo "Service status:"
	@make status