#!/bin/bash

# RAG Chatbot Backend Services Startup Script
echo "🚀 Starting RAG Chatbot Backend Services..."

# Function to check if a service is running
check_service() {
    local port=$1
    local service_name=$2
    
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "✅ $service_name (port $port) is running"
        return 0
    else
        echo "❌ $service_name (port $port) is not running"
        return 1
    fi
}

# Check if virtual environment exists and activate it
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run 'uv venv' first."
    exit 1
fi

source .venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    uv pip install -r requirements.txt
fi

# Check if Qdrant is running
echo "🔍 Checking Qdrant vector database..."
if ! curl -s "http://localhost:6333" > /dev/null 2>&1; then
    echo "🐳 Starting Qdrant vector database..."
    docker run -d --name qdrant -p 6333:6333 qdrant/qdrant:latest
    echo "⏳ Waiting for Qdrant to start..."
    sleep 5
else
    echo "✅ Qdrant is already running"
fi

# Start services in background
echo "🚀 Starting microservices..."

# Storage Service (8001)
cd services/storage
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8001 > ../../logs/storage.log 2>&1 &
cd ../..

# Retriever Service (8002)
cd services/retriever
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8002 > ../../logs/retriever.log 2>&1 &
cd ../..

# Query Enhancement Service (8003)
cd services/query_enhancement
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8003 > ../../logs/query_enhancement.log 2>&1 &
cd ../..

# Generation Service (8004)
cd services/generation
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8004 > ../../logs/generation.log 2>&1 &
cd ../..

# API Gateway (8000)
cd services/gateway
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8000 > ../../logs/gateway.log 2>&1 &
cd ../..

# Create logs directory
mkdir -p logs

echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."
check_service 8001 "Storage Service"
check_service 8002 "Retriever Service"  
check_service 8003 "Query Enhancement Service"
check_service 8004 "Generation Service"
check_service 8000 "API Gateway"

# Overall health check
echo ""
echo "📊 Overall System Health:"
if curl -s "http://localhost:8000/health/all" | python -m json.tool; then
    echo ""
    echo "🎉 All services are running successfully!"
    echo ""
    echo "🌐 Access points:"
    echo "   • API Gateway: http://localhost:8000"
    echo "   • API Documentation: http://localhost:8000/docs"
    echo "   • Health Check: http://localhost:8000/health/all"
    echo ""
    echo "📝 Logs are available in the 'logs/' directory"
    echo ""
    echo "🛑 To stop all services, run: ./stop_services.sh"
else
    echo "⚠️  Some services may not be fully operational. Check logs for details."
fi