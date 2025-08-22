#!/bin/bash

# RAG Chatbot Backend Services Stop Script
echo "🛑 Stopping RAG Chatbot Backend Services..."

# Function to stop processes on a specific port
stop_service() {
    local port=$1
    local service_name=$2
    
    local pids=$(lsof -ti:$port)
    if [ -n "$pids" ]; then
        echo "🛑 Stopping $service_name (port $port)..."
        echo $pids | xargs kill -15
        sleep 2
        # Force kill if still running
        local remaining_pids=$(lsof -ti:$port)
        if [ -n "$remaining_pids" ]; then
            echo $remaining_pids | xargs kill -9
        fi
        echo "✅ $service_name stopped"
    else
        echo "ℹ️  $service_name (port $port) is not running"
    fi
}

# Stop all services
stop_service 8000 "API Gateway"
stop_service 8001 "Storage Service"
stop_service 8002 "Retriever Service"
stop_service 8003 "Query Enhancement Service"
stop_service 8004 "Generation Service"

# Optionally stop Qdrant (uncomment if you want to stop the database)
# echo "🛑 Stopping Qdrant database..."
# docker stop qdrant 2>/dev/null || echo "ℹ️  Qdrant container not running"

echo ""
echo "✅ All backend services have been stopped!"
echo ""
echo "ℹ️  Note: Qdrant database is still running. To stop it:"
echo "   docker stop qdrant && docker rm qdrant"