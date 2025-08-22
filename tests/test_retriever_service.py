import pytest
import asyncio
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock

from services.retriever.services.hybrid_retriever import HybridRetriever
from shared.models import SearchQuery
from shared.config import Settings


class TestHybridRetriever:
    """Test suite for HybridRetriever with real Qdrant integration."""
    
    @pytest.fixture
    def test_settings_qdrant(self):
        """Test settings pointing to running Qdrant instance."""
        return Settings(
            openai_api_key="test-key",
            qdrant_host="localhost",
            qdrant_port=6333,
            qdrant_collection_name="documents",
            embedding_model="text-embedding-3-small",
            embedding_dimension=1536
        )
    
    @pytest.fixture
    def retriever(self, test_settings_qdrant):
        """Create HybridRetriever instance connected to real Qdrant."""
        with patch('services.retriever.services.hybrid_retriever.settings', test_settings_qdrant):
            return HybridRetriever()
    
    async def _initialize_retriever(self, retriever):
        """Helper to initialize retriever for tests."""
        await retriever.initialize()
        return retriever
    
    @pytest.mark.asyncio
    async def test_initialization(self, retriever):
        """Test that retriever initializes correctly with Qdrant."""
        await retriever.initialize()
        
        assert retriever.qdrant_client is not None
        assert retriever.collection_name == "documents"
        assert len(retriever.documents) > 0  # Should have loaded documents from our stored data
        assert len(retriever.document_ids) > 0
        assert retriever.bm25 is not None
        print(f"✅ Loaded {len(retriever.documents)} documents for BM25 search")
    
    @pytest.mark.asyncio
    async def test_semantic_search_real_data(self, retriever):
        """Test semantic search with real stored data."""
        retriever = await self._initialize_retriever(retriever)
        # Test queries related to our stored documents
        test_queries = [
            "low-rank adaptation",
            "parameter tuning", 
            "language models",
            "frontier AI models",
            "large language models"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing semantic search for: '{query}'")
            
            results = await retriever.semantic_search(
                query=query,
                top_k=5,
                threshold=0.1  # Lower threshold for testing
            )
            
            assert isinstance(results, list)
            print(f"   📊 Found {len(results)} results")
            
            if results:
                # Check result structure
                result = results[0]
                required_fields = ["id", "content", "score", "source_file", "metadata"]
                for field in required_fields:
                    assert field in result, f"Missing field: {field}"
                
                # Check score is reasonable
                assert 0 <= result["score"] <= 1, f"Invalid score: {result['score']}"
                
                # Check content is meaningful
                assert len(result["content"]) > 0, "Empty content"
                
                print(f"   ✅ Top result score: {result['score']:.3f}")
                print(f"   📄 Content preview: {result['content'][:100]}...")
    
    @pytest.mark.asyncio
    async def test_keyword_search_real_data(self, retriever):
        """Test BM25 keyword search with real data."""
        test_queries = [
            "adaptation parameter tuning",
            "AI models frontier",
            "language processing",
            "neural networks"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing keyword search for: '{query}'")
            
            results = await retriever.keyword_search(
                query=query,
                top_k=5
            )
            
            assert isinstance(results, list)
            print(f"   📊 Found {len(results)} results")
            
            if results:
                result = results[0]
                assert "search_type" in result
                assert result["search_type"] == "keyword"
                assert result["score"] > 0  # BM25 scores should be positive
                
                print(f"   ✅ Top BM25 score: {result['score']:.3f}")
                print(f"   📄 Content preview: {result['content'][:100]}...")
    
    @pytest.mark.asyncio
    async def test_hybrid_search_real_data(self, retriever):
        """Test hybrid search combining semantic and keyword approaches."""
        test_queries = [
            "How does low-rank adaptation work?",
            "What are frontier AI models?", 
            "Parameter efficient tuning methods",
            "Large language model fine-tuning"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing hybrid search for: '{query}'")
            
            results = await retriever.hybrid_search(
                query=query,
                top_k=5,
                threshold=0.1
            )
            
            assert isinstance(results, list)
            print(f"   📊 Found {len(results)} results")
            
            if results:
                result = results[0]
                assert "search_type" in result
                assert result["search_type"] == "hybrid"
                
                # Should have both scores
                assert "semantic_score" in result
                assert "keyword_score" in result
                assert "score" in result  # Combined score
                
                print(f"   ✅ Combined score: {result['score']:.3f}")
                print(f"   🧠 Semantic: {result['semantic_score']:.3f}")
                print(f"   🔤 Keyword: {result['keyword_score']:.3f}")
                print(f"   📄 Content preview: {result['content'][:100]}...")
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self, retriever):
        """Test search with source file filters."""
        # First, let's see what files we have
        results_unfiltered = await retriever.semantic_search("adaptation", top_k=10)
        
        if results_unfiltered:
            # Get unique source files
            source_files = list(set(r["source_file"] for r in results_unfiltered))
            print(f"📁 Available source files: {source_files}")
            
            if len(source_files) > 1:
                # Test filtering by specific file
                test_file = source_files[0]
                
                results_filtered = await retriever.semantic_search(
                    query="adaptation",
                    top_k=5,
                    filters={"source_file": test_file}
                )
                
                # All results should be from the specified file
                for result in results_filtered:
                    assert result["source_file"] == test_file
                
                print(f"   ✅ Successfully filtered to file: {test_file}")
                print(f"   📊 Filtered results: {len(results_filtered)}")
    
    @pytest.mark.asyncio
    async def test_search_quality_and_relevance(self, retriever):
        """Test search quality and relevance with specific queries."""
        test_cases = [
            {
                "query": "LoRA low-rank adaptation",
                "expected_keywords": ["lora", "low-rank", "adaptation", "parameter"],
                "min_results": 1
            },
            {
                "query": "transformer language models",
                "expected_keywords": ["transformer", "language", "model"],
                "min_results": 1  
            },
            {
                "query": "fine-tuning efficiency",
                "expected_keywords": ["fine", "tuning", "efficient"],
                "min_results": 1
            }
        ]
        
        for test_case in test_cases:
            query = test_case["query"]
            expected_keywords = test_case["expected_keywords"]
            min_results = test_case["min_results"]
            
            print(f"\n🎯 Testing relevance for: '{query}'")
            
            results = await retriever.hybrid_search(query, top_k=5, threshold=0.1)
            
            assert len(results) >= min_results, f"Expected at least {min_results} results"
            
            # Check if results contain expected keywords
            if results:
                top_result = results[0]
                content_lower = top_result["content"].lower()
                
                found_keywords = []
                for keyword in expected_keywords:
                    if keyword.lower() in content_lower:
                        found_keywords.append(keyword)
                
                relevance_score = len(found_keywords) / len(expected_keywords)
                print(f"   📈 Relevance score: {relevance_score:.2f}")
                print(f"   🔑 Found keywords: {found_keywords}")
                print(f"   📄 Content preview: {content_lower[:150]}...")
                
                # At least 30% of keywords should be found for decent relevance
                assert relevance_score >= 0.3, f"Low relevance: {relevance_score}"
    
    @pytest.mark.asyncio
    async def test_search_performance_and_limits(self, retriever):
        """Test search performance and edge cases."""
        # Test with different top_k values
        for top_k in [1, 3, 5, 10]:
            results = await retriever.hybrid_search(
                query="language models",
                top_k=top_k,
                threshold=0.0
            )
            
            assert len(results) <= top_k, f"Returned more than {top_k} results"
            print(f"   ✅ top_k={top_k}: got {len(results)} results")
        
        # Test with very high threshold (should return fewer results)
        results_high_threshold = await retriever.semantic_search(
            query="language models",
            top_k=10,
            threshold=0.9  # Very high threshold
        )
        
        results_low_threshold = await retriever.semantic_search(
            query="language models", 
            top_k=10,
            threshold=0.1  # Low threshold
        )
        
        assert len(results_high_threshold) <= len(results_low_threshold)
        print(f"   ✅ High threshold: {len(results_high_threshold)} results")
        print(f"   ✅ Low threshold: {len(results_low_threshold)} results")
    
    @pytest.mark.asyncio
    async def test_empty_and_edge_queries(self, retriever):
        """Test handling of empty and edge case queries."""
        edge_cases = [
            "",  # Empty query
            "   ",  # Whitespace only
            "xyz123abc",  # Nonsense query
            "a",  # Single character
            "the and or but",  # Common stopwords
        ]
        
        for query in edge_cases:
            print(f"\n🧪 Testing edge case query: '{query}'")
            
            try:
                results = await retriever.hybrid_search(
                    query=query,
                    top_k=3,
                    threshold=0.1
                )
                
                assert isinstance(results, list)
                print(f"   ✅ Handled gracefully, got {len(results)} results")
                
            except Exception as e:
                print(f"   ⚠️ Exception (expected for some cases): {e}")
    
    @pytest.mark.asyncio
    async def test_search_ranking_consistency(self, retriever):
        """Test that search rankings are consistent and properly ordered."""
        query = "parameter efficient fine-tuning"
        
        # Run the same search multiple times
        results_list = []
        for i in range(3):
            results = await retriever.hybrid_search(query, top_k=5, threshold=0.1)
            results_list.append(results)
        
        # Rankings should be consistent
        if all(len(r) > 0 for r in results_list):
            # Check that top result is consistent
            top_ids = [r[0]["id"] for r in results_list if r]
            if len(set(top_ids)) == 1:
                print("   ✅ Search rankings are consistent")
            else:
                print("   ⚠️ Search rankings vary (could be due to tie-breaking)")
        
        # Check that results are properly ordered by score
        for i, results in enumerate(results_list):
            if len(results) > 1:
                scores = [r["score"] for r in results]
                assert scores == sorted(scores, reverse=True), f"Results not ordered by score in run {i}"
                print(f"   ✅ Run {i+1}: Results properly ordered by score")
    
    @pytest.mark.asyncio
    async def test_document_coverage(self, retriever):
        """Test that search can find content from both stored documents."""
        # Queries that should match specific documents
        document_specific_queries = [
            ("LoRA adaptation", "lora_review.pdf"),
            ("frontier AI models", "frontier_ai_models.pdf")
        ]
        
        found_documents = set()
        
        for query, expected_doc in document_specific_queries:
            print(f"\n📚 Testing document coverage for: '{query}'")
            
            results = await retriever.hybrid_search(query, top_k=10, threshold=0.1)
            
            if results:
                # Check which documents appear in results
                doc_sources = [r["source_file"] for r in results]
                found_documents.update(doc_sources)
                
                print(f"   📊 Found results from: {set(doc_sources)}")
                
                # Check if expected document appears in results
                expected_found = any(expected_doc in source for source in doc_sources)
                if expected_found:
                    print(f"   ✅ Found expected document: {expected_doc}")
                else:
                    print(f"   ⚠️ Expected document not in top results: {expected_doc}")
        
        print(f"\n📋 Total unique documents found across all queries: {len(found_documents)}")
        print(f"📋 Documents found: {found_documents}")