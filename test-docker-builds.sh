#!/bin/bash

# Test Docker builds for all services
# This script helps validate Docker configuration before pushing to CI/CD

set -e

echo "🐳 Testing Docker builds for all microservices..."

# Services to test
SERVICES=("storage" "retriever" "query_enhancement" "generation" "gateway")

# Counter for tracking results
PASSED=0
TOTAL=${#SERVICES[@]}

for SERVICE in "${SERVICES[@]}"; do
    echo ""
    echo "🔨 Building Docker image for $SERVICE service..."
    
    if docker build -t "rag-$SERVICE:test" "./backend/services/$SERVICE"; then
        echo "✅ $SERVICE service build successful"
        ((PASSED++))
        
        # Test that the image was created and has the expected labels
        echo "📋 Checking image details..."
        docker inspect "rag-$SERVICE:test" --format='{{.Config.Labels.service}}' || echo "No service label found"
        
        # Clean up the test image
        docker rmi "rag-$SERVICE:test" >/dev/null 2>&1 || true
        
    else
        echo "❌ $SERVICE service build failed"
    fi
done

# Also test frontend build
echo ""
echo "🔨 Building Docker image for frontend..."
if docker build -t "rag-frontend:test" "./frontend"; then
    echo "✅ Frontend build successful"
    ((PASSED++))
    ((TOTAL++))
    docker rmi "rag-frontend:test" >/dev/null 2>&1 || true
else
    echo "❌ Frontend build failed"
    ((TOTAL++))
fi

echo ""
echo "📊 Docker build test results: $PASSED/$TOTAL builds successful"

if [ $PASSED -eq $TOTAL ]; then
    echo "🎉 All Docker builds passed!"
    exit 0
else
    echo "⚠️ Some Docker builds failed"
    exit 1
fi