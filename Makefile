.PHONY: help install dev test build deploy clean

help:
	@echo "Viral Video SaaS - Available commands:"
	@echo "  make install       - Install all dependencies"
	@echo "  make dev          - Start development environment (Docker)"
	@echo "  make test         - Run tests"
	@echo "  make build        - Build Docker images"
	@echo "  make deploy       - Deploy to AWS (requires Terraform)"
	@echo "  make clean        - Clean up Docker containers and volumes"

install:
	@echo "Installing dependencies..."
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

dev:
	@echo "Starting development environment..."
	docker-compose up -d
	@echo "Frontend: http://localhost:3000"
	@echo "Backend API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"

dev-logs:
	docker-compose logs -f

stop:
	docker-compose down

dev-full:
	@echo "Starting full development with Celery..."
	docker-compose -f docker-compose.yml -f docker-compose.override.yml up

test:
	@echo "Running tests..."
	cd backend && pytest tests/

test-coverage:
	cd backend && pytest tests/ --cov=app

build:
	@echo "Building Docker images..."
	docker-compose build

build-no-cache:
	docker-compose build --no-cache

deploy-tf-init:
	cd infrastructure && terraform init

deploy-tf-plan:
	cd infrastructure && terraform plan

deploy-tf-apply:
	cd infrastructure && terraform apply

logs-backend:
	docker-compose logs backend -f

logs-celery:
	docker-compose logs celery-worker -f

logs-redis:
	docker-compose logs redis -f

logs-postgres:
	docker-compose logs postgres -f

ps:
	docker-compose ps

clean:
	@echo "Cleaning up..."
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true

backend-shell:
	docker-compose exec backend bash

frontend-shell:
	docker-compose exec backend sh

db-shell:
	docker-compose exec postgres psql -U postgres -d viral_db

redis-cli:
	docker-compose exec redis redis-cli

format:
	@echo "Formatting code..."
	cd backend && black app/
	cd frontend && prettier --write src/

lint:
	@echo "Linting code..."
	cd backend && pylint app/
	cd frontend && npm run lint

type-check:
	cd frontend && npm run type-check

.DEFAULT_GOAL := help
