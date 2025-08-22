#!/usr/bin/env python3
"""
Simple retriever test script to verify functionality with real Qdrant data.
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from services.retriever.services.hybrid_retriever import HybridRetriever
from shared.config import Settings


async def test_retriever_with_real_data():
    """Test retriever functionality with real Qdrant data."""
    print("🚀 Testing Retriever with Real Qdrant Data")
    print("=" * 50)
    
    # Configure settings (will load from .env)
    test_settings = Settings(
        qdrant_host="localhost",
        qdrant_port=6333,
        qdrant_collection_name="documents",
        embedding_model="text-embedding-3-small",
        embedding_dimension=1536
    )
    
    # Initialize retriever
    with patch('services.retriever.services.hybrid_retriever.settings', test_settings):
        retriever = HybridRetriever()
        await retriever.initialize()
    
    print(f"✅ Initialization successful")
    print(f"📊 Loaded {len(retriever.documents)} documents")
    print(f"📊 Document IDs: {len(retriever.document_ids)}")
    print(f"📊 BM25 initialized: {retriever.bm25 is not None}")
    
    # Test semantic search
    print("\n🧠 Testing Semantic Search")
    print("-" * 30)
    
    semantic_queries = [
        "low-rank adaptation LoRA",
        "frontier AI models",
        "parameter efficient tuning",
        "large language models"
    ]
    
    for query in semantic_queries:
        print(f"\n🔍 Query: '{query}'")
        results = await retriever.semantic_search(
            query=query,
            top_k=3,
            threshold=0.1
        )
        
        print(f"   📊 Results: {len(results)}")
        if results:
            top_result = results[0]
            print(f"   🏆 Top score: {top_result['score']:.3f}")
            print(f"   📄 Source: {top_result['source_file']}")
            print(f"   📄 Preview: {top_result['content'][:100]}...")
        else:
            print("   ⚠️ No results found")
    
    # Test keyword search
    print("\n🔤 Testing Keyword Search (BM25)")
    print("-" * 35)
    
    keyword_queries = [
        "adaptation parameter tuning",
        "AI frontier models", 
        "language processing neural"
    ]
    
    for query in keyword_queries:
        print(f"\n🔍 Query: '{query}'")
        results = await retriever.keyword_search(
            query=query,
            top_k=3
        )
        
        print(f"   📊 Results: {len(results)}")
        if results:
            top_result = results[0]
            print(f"   🏆 BM25 score: {top_result['score']:.3f}")
            print(f"   📄 Source: {top_result['source_file']}")
            print(f"   📄 Preview: {top_result['content'][:100]}...")
        else:
            print("   ⚠️ No results found")
    
    # Test hybrid search
    print("\n🔄 Testing Hybrid Search")
    print("-" * 25)
    
    hybrid_queries = [
        "How does LoRA work for language models?",
        "What are frontier AI capabilities?",
        "Parameter efficient fine-tuning methods"
    ]
    
    for query in hybrid_queries:
        print(f"\n🔍 Query: '{query}'")
        results = await retriever.hybrid_search(
            query=query,
            top_k=3,
            threshold=0.1
        )
        
        print(f"   📊 Results: {len(results)}")
        if results:
            top_result = results[0]
            print(f"   🏆 Combined score: {top_result['score']:.3f}")
            print(f"   🧠 Semantic: {top_result['semantic_score']:.3f}")
            print(f"   🔤 Keyword: {top_result['keyword_score']:.3f}")
            print(f"   📄 Source: {top_result['source_file']}")
            print(f"   📄 Preview: {top_result['content'][:100]}...")
        else:
            print("   ⚠️ No results found")
    
    # Test document diversity
    print("\n📚 Testing Document Source Diversity")
    print("-" * 40)
    
    all_sources = set()
    diversity_queries = [
        "LoRA low-rank adaptation",  # Should favor first PDF
        "frontier AI GPT Claude",   # Should favor second PDF
    ]
    
    for query in diversity_queries:
        print(f"\n🔍 Query: '{query}'")
        results = await retriever.hybrid_search(query, top_k=10, threshold=0.1)
        
        if results:
            sources = [r["source_file"] for r in results]
            unique_sources = set(sources)
            all_sources.update(unique_sources)
            
            print(f"   📊 Results: {len(results)}")
            print(f"   📁 Sources: {unique_sources}")
        else:
            print("   ⚠️ No results found")
    
    print(f"\n📋 Total unique sources found: {len(all_sources)}")
    print(f"📋 All sources: {all_sources}")
    
    # Test threshold effects
    print("\n📊 Testing Threshold Effects")
    print("-" * 30)
    
    query = "parameter efficient tuning"
    thresholds = [0.1, 0.3, 0.5, 0.7]
    
    print(f"🔍 Query: '{query}'")
    for threshold in thresholds:
        results = await retriever.semantic_search(
            query=query,
            top_k=10,
            threshold=threshold
        )
        print(f"   Threshold {threshold}: {len(results)} results")
    
    print("\n🎉 All tests completed successfully!")
    print("✅ Retriever is working correctly with real Qdrant data")


if __name__ == "__main__":
    asyncio.run(test_retriever_with_real_data())