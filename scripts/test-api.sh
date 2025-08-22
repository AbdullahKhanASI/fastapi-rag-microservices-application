#!/bin/bash

# Test script for RAG Chatbot API

BASE_URL="http://localhost:8000"

echo "Testing RAG Chatbot API..."

# Test health check
echo "1. Testing health check..."
curl -s "$BASE_URL/health" | python -m json.tool

echo -e "\n2. Testing all services health..."
curl -s "$BASE_URL/health/all" | python -m json.tool

# Test file upload (if test file exists)
if [ -f "test.txt" ]; then
    echo -e "\n3. Testing file upload..."
    curl -X POST "$BASE_URL/upload" \
         -H "Content-Type: multipart/form-data" \
         -F "file=@test.txt" | python -m json.tool
fi

# Test search
echo -e "\n4. Testing search..."
curl -X POST "$BASE_URL/search" \
     -H "Content-Type: application/json" \
     -d '{"query": "test query", "top_k": 3}' | python -m json.tool

# Test chat
echo -e "\n5. Testing chat..."
curl -X POST "$BASE_URL/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Hello, can you help me?"}' | python -m json.tool

echo -e "\nAPI testing complete!"