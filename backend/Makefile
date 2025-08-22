# RAG Chatbot Microservices Makefile

.PHONY: help build start stop restart logs clean test

# Default target
help:
	@echo "Available commands:"
	@echo "  build     - Build all Docker images"
	@echo "  start     - Start all services"
	@echo "  stop      - Stop all services"
	@echo "  restart   - Restart all services"
	@echo "  logs      - Show logs from all services"
	@echo "  clean     - Remove all containers and images"
	@echo "  test      - Run tests"
	@echo "  dev       - Start services for development"

# Build all services
build:
	docker-compose build

# Start all services
start:
	docker-compose up -d

# Stop all services
stop:
	docker-compose down

# Restart all services
restart: stop start

# Show logs
logs:
	docker-compose logs -f

# Clean up
clean:
	docker-compose down -v --rmi all --remove-orphans

# Run tests
test:
	@echo "Running tests..."
	# Add test commands here

# Development mode (with logs)
dev:
	docker-compose up

# Individual service commands
start-storage:
	docker-compose up -d storage-service

start-retriever:
	docker-compose up -d retriever-service

start-query-enhancement:
	docker-compose up -d query-enhancement-service

start-generation:
	docker-compose up -d generation-service

start-gateway:
	docker-compose up -d api-gateway

# Health check
health:
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health/all | python -m json.tool