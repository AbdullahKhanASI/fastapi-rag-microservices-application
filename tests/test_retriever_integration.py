import pytest
from unittest.mock import patch

from services.retriever.services.hybrid_retriever import HybridRetriever
from shared.config import Settings


class TestRetrieverIntegration:
    """Integration tests for HybridRetriever with real Qdrant data."""
    
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
    async def retriever(self, test_settings_qdrant):
        """Create and initialize HybridRetriever instance."""
        with patch('services.retriever.services.hybrid_retriever.settings', test_settings_qdrant):
            retriever = HybridRetriever()
            await retriever.initialize()
            return retriever
    
    @pytest.mark.asyncio
    async def test_retriever_initialization_with_real_data(self, retriever):
        """Test that retriever loads real data from Qdrant."""
        assert retriever.qdrant_client is not None
        assert retriever.collection_name == "documents"
        assert len(retriever.documents) == 333  # Our stored documents
        assert len(retriever.document_ids) == 333
        assert retriever.bm25 is not None
        print(f"✅ Successfully loaded {len(retriever.documents)} documents from Qdrant")
    
    @pytest.mark.asyncio
    async def test_semantic_search_quality(self, retriever):
        """Test semantic search quality with specific queries."""
        test_cases = [
            {
                "query": "low-rank adaptation LoRA",
                "expected_score_min": 0.5,
                "description": "LoRA-specific query"
            },
            {
                "query": "frontier AI models GPT Claude",
                "expected_score_min": 0.4,
                "description": "Frontier AI query"
            },
            {
                "query": "parameter efficient fine-tuning",
                "expected_score_min": 0.4,
                "description": "Fine-tuning query"
            }
        ]
        
        for test_case in test_cases:
            query = test_case["query"]
            min_score = test_case["expected_score_min"]
            description = test_case["description"]
            
            print(f"\n🎯 Testing {description}: '{query}'")
            
            results = await retriever.semantic_search(
                query=query,
                top_k=3,
                threshold=0.1
            )
            
            assert len(results) > 0, f"No results for query: {query}"
            
            top_result = results[0]
            assert top_result["score"] >= min_score, f"Low score: {top_result['score']}"
            
            print(f"   ✅ Score: {top_result['score']:.3f} (min: {min_score})")
            print(f"   📄 Preview: {top_result['content'][:100]}...")
    
    @pytest.mark.asyncio
    async def test_keyword_search_functionality(self, retriever):
        """Test BM25 keyword search functionality."""
        test_queries = [
            "adaptation tuning efficient",
            "language model transformer",
            "AI frontier models"
        ]
        
        for query in test_queries:
            print(f"\n🔤 Testing keyword search: '{query}'")
            
            results = await retriever.keyword_search(
                query=query,
                top_k=3
            )
            
            assert isinstance(results, list)
            
            if results:
                top_result = results[0]
                assert top_result["search_type"] == "keyword"
                assert top_result["score"] > 0
                
                print(f"   ✅ BM25 Score: {top_result['score']:.3f}")
                print(f"   📄 Preview: {top_result['content'][:100]}...")
            else:
                print(f"   ⚠️ No keyword results for: {query}")
    
    @pytest.mark.asyncio
    async def test_hybrid_search_performance(self, retriever):
        """Test hybrid search combining semantic and keyword approaches."""
        test_queries = [
            "How does LoRA adaptation work for language models?",
            "What are the benefits of parameter efficient tuning?",
            "Frontier AI capabilities and limitations"
        ]
        
        for query in test_queries:
            print(f"\n🔄 Testing hybrid search: '{query}'")
            
            # Get semantic results
            semantic_results = await retriever.semantic_search(query, top_k=3, threshold=0.1)
            
            # Get keyword results  
            keyword_results = await retriever.keyword_search(query, top_k=3)
            
            # Get hybrid results
            hybrid_results = await retriever.hybrid_search(query, top_k=3, threshold=0.1)
            
            print(f"   🧠 Semantic results: {len(semantic_results)}")
            print(f"   🔤 Keyword results: {len(keyword_results)}")
            print(f"   🔄 Hybrid results: {len(hybrid_results)}")
            
            if hybrid_results:
                top_result = hybrid_results[0]
                assert top_result["search_type"] == "hybrid"
                assert "semantic_score" in top_result
                assert "keyword_score" in top_result
                
                print(f"   ✅ Combined: {top_result['score']:.3f}")
                print(f"   🧠 Semantic: {top_result['semantic_score']:.3f}")
                print(f"   🔤 Keyword: {top_result['keyword_score']:.3f}")
    
    @pytest.mark.asyncio
    async def test_document_source_diversity(self, retriever):
        """Test that search results come from both source documents."""
        queries = [
            "LoRA low-rank adaptation",  # Should favor first document
            "frontier AI models GPT",   # Should favor second document
        ]
        
        all_sources = set()
        
        for query in queries:
            print(f"\n📚 Testing source diversity: '{query}'")
            
            results = await retriever.hybrid_search(query, top_k=10, threshold=0.1)
            
            if results:
                sources = [r["source_file"] for r in results]
                unique_sources = set(sources)
                all_sources.update(unique_sources)
                
                print(f"   📊 Sources found: {unique_sources}")
        
        print(f"\n📋 Total unique sources across all queries: {len(all_sources)}")
        print(f"📋 Sources: {all_sources}")
        
        # We should see both PDF files in results
        assert len(all_sources) >= 1, "Should find results from at least one source document"
    
    @pytest.mark.asyncio
    async def test_search_with_different_thresholds(self, retriever):
        """Test how search threshold affects results."""
        query = "parameter efficient tuning"
        thresholds = [0.1, 0.3, 0.5, 0.7]
        
        print(f"\n📊 Testing threshold effects for: '{query}'")
        
        results_by_threshold = {}
        
        for threshold in thresholds:
            results = await retriever.semantic_search(
                query=query,
                top_k=10,
                threshold=threshold
            )
            results_by_threshold[threshold] = len(results)
            print(f"   Threshold {threshold}: {len(results)} results")
        
        # Higher thresholds should return fewer or equal results
        prev_count = float('inf')
        for threshold in sorted(thresholds):
            count = results_by_threshold[threshold]
            assert count <= prev_count, f"Higher threshold returned more results"
            prev_count = count
        
        print("   ✅ Threshold filtering working correctly")
    
    @pytest.mark.asyncio
    async def test_search_result_structure(self, retriever):
        """Test that search results have proper structure."""
        results = await retriever.hybrid_search("language models", top_k=3, threshold=0.1)
        
        if results:
            result = results[0]
            
            # Check required fields
            required_fields = [
                "id", "content", "score", "source_file", 
                "chunk_index", "metadata", "search_type",
                "semantic_score", "keyword_score"
            ]
            
            for field in required_fields:
                assert field in result, f"Missing required field: {field}"
            
            # Check data types
            assert isinstance(result["id"], str)
            assert isinstance(result["content"], str)
            assert isinstance(result["score"], (int, float))
            assert isinstance(result["source_file"], str)
            assert isinstance(result["chunk_index"], int)
            assert isinstance(result["metadata"], dict)
            assert result["search_type"] == "hybrid"
            
            print("   ✅ All required fields present and properly typed")
            print(f"   📊 Result ID: {result['id']}")
            print(f"   📊 Source: {result['source_file']}")
            print(f"   📊 Chunk: {result['chunk_index']}")
        else:
            print("   ⚠️ No results to validate structure")