#!/usr/bin/env python3
"""
Test script for query enhancement service API endpoints.
"""

import asyncio
import json
import aiohttp

# Test queries
TEST_QUERIES = [
    "How does low-rank adaptation work for fine-tuning large language models?",
    "What are the key capabilities of frontier AI models in 2025?", 
    "parameter efficient tuning methods comparison",
    "Which AI models should I use for text generation tasks?"
]

SERVICE_URL = "http://localhost:8003"

async def test_query_enhancement_api():
    """Test query enhancement service API."""
    print("🚀 Testing Query Enhancement Service API")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        for i, query in enumerate(TEST_QUERIES, 1):
            print(f"\n📝 Test Query {i}: {query}")
            print("-" * 50)
            
            # Test 1: Full Enhancement
            try:
                payload = {"query": query, "context": ""}
                async with session.post(f"{SERVICE_URL}/enhance", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        print("✅ Full Enhancement:")
                        print(f"   🧹 Cleaned: {result.get('cleaned_query', 'N/A')}")
                        print(f"   🎯 Intent: {result.get('intent', 'N/A')}")
                        print(f"   🔍 Entities: {result.get('entities', [])}")
                        print(f"   🔄 Expansions: {result.get('expansions', [])[:5]}")  
                        print(f"   ✨ Search Optimized: {result.get('search_optimized', 'N/A')}")
                    else:
                        print(f"❌ Enhancement failed: {response.status}")
            except Exception as e:
                print(f"❌ Enhancement error: {e}")
            
            # Test 2: Query Expansion
            try:
                payload = {"query": query}
                async with session.post(f"{SERVICE_URL}/expand", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        print("✅ Query Expansion:")
                        print(f"   🔄 Terms: {result.get('expansion_terms', [])[:5]}")
                    else:
                        print(f"❌ Expansion failed: {response.status}")
            except Exception as e:
                print(f"❌ Expansion error: {e}")
            
            # Test 3: Intent Classification
            try:
                payload = {"query": query}
                async with session.post(f"{SERVICE_URL}/classify-intent", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        print("✅ Intent Classification:")
                        print(f"   🎯 Result: {result}")
                    else:
                        print(f"❌ Intent classification failed: {response.status}")
            except Exception as e:
                print(f"❌ Intent classification error: {e}")
    
    print(f"\n🎉 API Testing Complete!")

if __name__ == "__main__":
    asyncio.run(test_query_enhancement_api())