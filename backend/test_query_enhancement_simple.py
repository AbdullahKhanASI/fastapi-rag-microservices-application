#!/usr/bin/env python3
"""
Simple test script for query enhancement service without spaCy dependency issues.
"""

import asyncio
import sys
import os
from pathlib import Path
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Test queries
TEST_QUERIES = [
    "How does low-rank adaptation work for fine-tuning large language models?",
    "What are the key capabilities of frontier AI models in 2025?", 
    "parameter efficient tuning methods comparison",
    "Which AI models should I use for text generation tasks?"
]

def simple_intent_classifier(query: str) -> str:
    """Simple rule-based intent classification without spaCy."""
    query_lower = query.lower()
    
    # Intent keywords mapping
    intent_keywords = {
        "factual": ["what", "when", "where", "who", "which", "define", "explain"],
        "procedural": ["how", "steps", "process", "procedure", "method"],
        "comparative": ["compare", "difference", "versus", "vs", "better", "best", "comparison"],
        "analytical": ["analyze", "analysis", "why", "reason", "cause", "effect"],
        "creative": ["generate", "create", "write", "compose", "design"],
        "troubleshooting": ["error", "problem", "issue", "fix", "solve", "troubleshoot"]
    }
    
    # Count keyword matches for each intent
    scores = {}
    for intent, keywords in intent_keywords.items():
        scores[intent] = sum(1 for keyword in keywords if keyword in query_lower)
    
    # Return intent with highest score, default to factual
    if max(scores.values()) == 0:
        return "factual"
    
    return max(scores, key=scores.get)

def simple_query_expansion(query: str) -> list:
    """Simple query expansion without complex NLP."""
    expansions = []
    query_lower = query.lower()
    
    # Define synonym/expansion mappings
    expansions_map = {
        "lora": ["low-rank adaptation", "parameter efficient fine-tuning", "PEFT"],
        "llm": ["large language model", "language model", "neural language model"],
        "ai": ["artificial intelligence", "machine learning", "ML"],
        "model": ["neural network", "algorithm", "system"],
        "tuning": ["fine-tuning", "adaptation", "training", "optimization"],
        "frontier": ["advanced", "cutting-edge", "state-of-the-art", "latest"],
        "capabilities": ["features", "abilities", "functions", "performance"],
        "generation": ["text generation", "content creation", "synthesis"]
    }
    
    # Find expansions
    for key, values in expansions_map.items():
        if key in query_lower:
            expansions.extend([v for v in values if v not in query_lower])
    
    return list(set(expansions))

def simple_query_cleaner(query: str) -> str:
    """Simple query cleaning."""
    # Remove extra whitespace
    query = ' '.join(query.split())
    
    # Normalize punctuation
    query = query.replace('?', '').replace('!', '').strip()
    
    return query

async def test_query_enhancement():
    """Test query enhancement with simple implementations."""
    print("🚀 Testing Query Enhancement Service (Simple Version)")
    print("=" * 60)
    
    results = []
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n📝 Test Query {i}: {query}")
        print("-" * 50)
        
        # 1. Clean query
        cleaned = simple_query_cleaner(query)
        print(f"🧹 Cleaned: {cleaned}")
        
        # 2. Classify intent
        intent = simple_intent_classifier(query)
        print(f"🎯 Intent: {intent}")
        
        # 3. Expand query
        expansions = simple_query_expansion(query)
        print(f"🔄 Expansions: {expansions[:5]}")  # Show first 5
        
        # 4. Create enhanced query structure
        enhanced = {
            "original_query": query,
            "cleaned_query": cleaned,
            "intent": intent,
            "expansions": expansions,
            "enhanced_terms": expansions[:3],  # Top 3 expansions
            "search_optimized": f"{cleaned} {' '.join(expansions[:2])}"
        }
        
        results.append(enhanced)
        
        print(f"✨ Search Optimized: {enhanced['search_optimized']}")
    
    print(f"\n🎉 Enhancement Complete! Processed {len(results)} queries")
    
    # Summary
    print("\n📊 Enhancement Summary:")
    print("-" * 30)
    intents = [r['intent'] for r in results]
    from collections import Counter
    intent_counts = Counter(intents)
    
    for intent, count in intent_counts.items():
        print(f"   {intent}: {count} queries")
    
    # Show example enhanced result
    print(f"\n💡 Example Enhanced Query:")
    example = results[0]
    print(json.dumps(example, indent=2))
    
    return results

if __name__ == "__main__":
    results = asyncio.run(test_query_enhancement())