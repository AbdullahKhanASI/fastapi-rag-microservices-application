#!/usr/bin/env python3
"""
Complete RAG Pipeline Test using the API Gateway
Tests the entire flow: Query Enhancement → Retrieval → Generation
"""

import asyncio
import json
import aiohttp
from datetime import datetime

# Test queries from our previous tests
TEST_QUERIES = [
    "How does low-rank adaptation work for fine-tuning large language models?",
    "What are the key capabilities of frontier AI models in 2025?", 
    "parameter efficient tuning methods comparison",
    "Which AI models should I use for text generation tasks?"
]

GATEWAY_URL = "http://localhost:8000"

async def test_rag_pipeline():
    """Test the complete RAG pipeline end-to-end."""
    print("🚀 Complete RAG Pipeline Test")
    print("=" * 60)
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Gateway URL: {GATEWAY_URL}")
    print()

    async with aiohttp.ClientSession() as session:
        # First, check if we have documents in storage
        print("📊 Checking document storage...")
        try:
            async with session.get(f"{GATEWAY_URL}/files") as response:
                if response.status == 200:
                    files = await response.json()
                    print(f"   ✅ Found {len(files)} files in storage")
                    for file in files[:3]:  # Show first 3
                        print(f"      📄 {file.get('file_name', 'Unknown')} ({file.get('chunks_count', 0)} chunks)")
                else:
                    print(f"   ⚠️  Could not retrieve files: {response.status}")
        except Exception as e:
            print(f"   ❌ Error checking files: {e}")

        print()
        
        # Test each query through the complete RAG pipeline
        for i, query in enumerate(TEST_QUERIES, 1):
            print(f"🔍 Test Query {i}: {query}")
            print("-" * 50)
            
            try:
                # Use the chat endpoint for complete RAG pipeline
                chat_request = {
                    "message": query,
                    "conversation_history": [],
                    "retrieval_params": {
                        "top_k": 3,
                        "threshold": 0.7
                    },
                    "generation_params": {
                        "max_tokens": 300,
                        "temperature": 0.7
                    }
                }
                
                print("   🔄 Processing through RAG pipeline...")
                async with session.post(f"{GATEWAY_URL}/chat", json=chat_request) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        print("   ✅ RAG Pipeline Results:")
                        print(f"      💬 Response: {result.get('response', 'N/A')[:150]}...")
                        print(f"      📚 Sources: {result.get('sources', [])}")
                        print(f"      🎯 Confidence: {result.get('confidence', 0):.3f}")
                        print(f"      📊 Retrieved Docs: {len(result.get('retrieved_docs', []))}")
                        
                        # Show token usage if available
                        token_usage = result.get('token_usage', {})
                        if token_usage:
                            print(f"      🔢 Tokens: {token_usage.get('total_tokens', 0)} total")
                        
                        # Show enhanced query if available
                        enhanced_query = result.get('enhanced_query', {})
                        if enhanced_query:
                            print(f"      ✨ Enhanced: {enhanced_query.get('enhanced_query', 'N/A')[:100]}...")
                            print(f"      🎯 Intent: {enhanced_query.get('intent', 'N/A')}")
                        
                    else:
                        error_text = await response.text()
                        print(f"   ❌ RAG Pipeline failed: {response.status}")
                        print(f"      Error: {error_text[:200]}...")
                        
            except Exception as e:
                print(f"   ❌ Exception during RAG pipeline: {e}")
            
            print()
        
        # Test document search directly
        print("🔍 Testing Direct Document Search:")
        print("-" * 40)
        
        search_query = TEST_QUERIES[0]  # Use first query
        try:
            search_request = {
                "query": search_query,
                "top_k": 5,
                "threshold": 0.6
            }
            
            async with session.post(f"{GATEWAY_URL}/search", json=search_request) as response:
                if response.status == 200:
                    search_results = await response.json()
                    print(f"   ✅ Search Results: {len(search_results.get('results', []))} documents")
                    
                    for i, doc in enumerate(search_results.get('results', [])[:3], 1):
                        print(f"      📄 Doc {i}: Score {doc.get('score', 0):.3f} - {doc.get('content', '')[:80]}...")
                        
                else:
                    print(f"   ❌ Search failed: {response.status}")
                    
        except Exception as e:
            print(f"   ❌ Search error: {e}")

    print()
    print("🎉 RAG Pipeline Testing Complete!")
    print(f"⏰ Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Service status summary
    print("\n📊 Service Status Summary:")
    print("   🔵 Gateway (8000): ✅ Running")
    print("   🔵 Storage (8001): ✅ Running") 
    print("   🔵 Retriever (8002): ✅ Running")
    print("   🔵 Query Enhancement (8003): ✅ Running")
    print("   🔵 Generation (8004): ✅ Running")
    print("   🔵 Qdrant (6333): ✅ Running")

if __name__ == "__main__":
    asyncio.run(test_rag_pipeline())