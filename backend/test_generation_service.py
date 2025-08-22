#!/usr/bin/env python3
"""
Test script for the generation service.
"""

import json
import asyncio
import aiohttp

# Test data with mock retrieved documents
TEST_GENERATION_REQUEST = {
    "enhanced_query": "How does low-rank adaptation work for fine-tuning large language models?",
    "retrieved_docs": [
        {
            "chunk_id": "doc1_chunk1",
            "content": "Low-Rank Adaptation (LoRA) is a parameter-efficient fine-tuning technique that reduces the number of trainable parameters by learning pairs of rank-decomposition weight matrices while keeping the original model weights frozen. This approach significantly reduces GPU memory requirements and training time.",
            "metadata": {
                "source": "lora_review.pdf",
                "page": 3,
                "chunk_index": 15
            },
            "score": 0.92,
            "source_file": "lora_review.pdf"
        },
        {
            "chunk_id": "doc1_chunk2", 
            "content": "LoRA works by decomposing the weight updates into two smaller matrices A and B, where the original weight matrix W is updated as W + BA. The rank r of these matrices is typically much smaller than the dimensions of W, making the adaptation very parameter-efficient.",
            "metadata": {
                "source": "lora_review.pdf",
                "page": 4,
                "chunk_index": 22
            },
            "score": 0.89,
            "source_file": "lora_review.pdf"
        },
        {
            "chunk_id": "doc1_chunk3",
            "content": "Experimental results show that LoRA achieves comparable or better performance than full fine-tuning on various tasks while using only 0.1% of the original parameters. This makes it particularly valuable for adapting large models like GPT-3 and T5.",
            "metadata": {
                "source": "lora_review.pdf", 
                "page": 7,
                "chunk_index": 45
            },
            "score": 0.85,
            "source_file": "lora_review.pdf"
        }
    ],
    "conversation_history": [],
    "max_tokens": 500,
    "temperature": 0.7
}

async def test_generation_service():
    """Test the generation service API endpoints."""
    print("🚀 Testing Generation Service")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Test /generate endpoint
        print("\n📝 Testing /generate endpoint...")
        try:
            async with session.post(
                "http://localhost:8004/generate",
                json=TEST_GENERATION_REQUEST
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ Generation Response:")
                    print(f"   📊 Query: {result.get('query', 'N/A')[:80]}...")
                    print(f"   💬 Response: {result.get('response', 'N/A')[:200]}...")
                    print(f"   📚 Sources: {result.get('sources', [])}")
                    print(f"   🎯 Confidence: {result.get('confidence', 0)}")
                    print(f"   🔢 Token Usage: {result.get('token_usage', {})}")
                else:
                    text = await response.text()
                    print(f"❌ Generation failed: {response.status} - {text}")
        except Exception as e:
            print(f"❌ Generation error: {e}")
        
        # Test /summarize endpoint
        print("\n📋 Testing /summarize endpoint...")
        summarize_request = {
            "enhanced_query": "Summarize these LoRA documents",
            "retrieved_docs": TEST_GENERATION_REQUEST["retrieved_docs"][:2],
            "conversation_history": [],
            "max_tokens": 200,
            "temperature": 0.7
        }
        
        try:
            async with session.post(
                "http://localhost:8004/summarize",
                json=summarize_request
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ Summarization Response:")
                    print(f"   📝 Summary: {result.get('summary', 'N/A')[:200]}...")
                    print(f"   🔢 Token Usage: {result.get('token_usage', {})}")
                else:
                    text = await response.text()
                    print(f"❌ Summarization failed: {response.status} - {text}")
        except Exception as e:
            print(f"❌ Summarization error: {e}")
    
    print(f"\n🎉 Generation Service Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_generation_service())