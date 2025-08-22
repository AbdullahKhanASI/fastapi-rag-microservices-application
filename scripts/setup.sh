#!/bin/bash

# Setup script for RAG Chatbot Microservices

echo "Setting up RAG Chatbot Microservices..."

# Create necessary directories
mkdir -p uploads
mkdir -p logs

# Copy environment file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file from .env.example"
    echo "Please update the .env file with your API keys"
else
    echo ".env file already exists"
fi

# Set permissions
chmod +x scripts/*.sh

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env file with your API keys"
echo "2. Run 'make build' to build Docker images"
echo "3. Run 'make start' to start all services"
echo "4. Access the API at http://localhost:8000"