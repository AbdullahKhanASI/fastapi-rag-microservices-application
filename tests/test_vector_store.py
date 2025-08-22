import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

from services.storage.services.vector_store import VectorStore
from shared.models import DocumentChunk


class TestVectorStore:
    """Test suite for VectorStore."""
    
    @pytest.fixture
    def vector_store(self, mock_qdrant_client, test_settings):
        """Create VectorStore instance with mocked Qdrant client."""
        with patch('services.storage.services.vector_store.settings', test_settings):
            store = VectorStore()
            store.client = mock_qdrant_client
        return store
    
    @pytest.mark.asyncio
    async def test_initialize_new_collection(self, vector_store, mock_qdrant_client):
        """Test initialization with new collection creation."""
        # Mock empty collections response
        mock_qdrant_client.get_collections.return_value = MagicMock(collections=[])
        
        await vector_store.initialize()
        
        mock_qdrant_client.get_collections.assert_called_once()
        mock_qdrant_client.create_collection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_existing_collection(self, vector_store, mock_qdrant_client):
        """Test initialization with existing collection."""
        # Mock existing collection
        existing_collection = MagicMock()
        existing_collection.name = "test_documents"
        mock_qdrant_client.get_collections.return_value = MagicMock(
            collections=[existing_collection]
        )
        
        await vector_store.initialize()
        
        mock_qdrant_client.get_collections.assert_called_once()
        mock_qdrant_client.create_collection.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_store_chunks(self, vector_store, sample_chunks, mock_qdrant_client):
        """Test storing document chunks."""
        await vector_store.store_chunks(sample_chunks)
        
        mock_qdrant_client.upsert.assert_called_once()
        
        # Verify the call arguments
        call_args = mock_qdrant_client.upsert.call_args
        assert call_args[1]["collection_name"] == "test_documents"
        assert len(call_args[1]["points"]) == len(sample_chunks)
    
    @pytest.mark.asyncio
    async def test_search_similar(self, vector_store, mock_qdrant_client, sample_search_results):
        """Test similarity search."""
        # Mock search response
        mock_hit1 = MagicMock()
        mock_hit1.id = "chunk_1"
        mock_hit1.score = 0.95
        mock_hit1.payload = sample_search_results[0]
        
        mock_hit2 = MagicMock()
        mock_hit2.id = "chunk_2"
        mock_hit2.score = 0.85
        mock_hit2.payload = sample_search_results[1]
        
        mock_qdrant_client.search.return_value = [mock_hit1, mock_hit2]
        
        query_vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        results = await vector_store.search_similar(query_vector, top_k=5)
        
        assert len(results) == 2
        assert results[0]["id"] == "chunk_1"
        assert results[0]["score"] == 0.95
        assert results[1]["id"] == "chunk_2"
        assert results[1]["score"] == 0.85
        
        mock_qdrant_client.search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_similar_with_filters(self, vector_store, mock_qdrant_client):
        """Test similarity search with filters."""
        mock_qdrant_client.search.return_value = []
        
        query_vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        filters = {"source_file": "test.pdf"}
        
        await vector_store.search_similar(
            query_vector, 
            top_k=5, 
            filters=filters
        )
        
        # Verify that search was called with filters
        call_args = mock_qdrant_client.search.call_args
        assert call_args[1]["query_filter"] is not None
    
    @pytest.mark.asyncio
    async def test_delete_by_file_id(self, vector_store, mock_qdrant_client):
        """Test deleting chunks by file ID."""
        file_id = "test_file_123"
        
        await vector_store.delete_by_file_id(file_id)
        
        mock_qdrant_client.delete.assert_called_once()
        call_args = mock_qdrant_client.delete.call_args
        assert call_args[1]["collection_name"] == "test_documents"
    
    @pytest.mark.asyncio
    async def test_list_files(self, vector_store, mock_qdrant_client):
        """Test listing unique source files."""
        # Mock scroll response
        mock_point1 = MagicMock()
        mock_point1.payload = {"source_file": "file1.pdf"}
        mock_point2 = MagicMock()
        mock_point2.payload = {"source_file": "file2.pdf"}
        mock_point3 = MagicMock()
        mock_point3.payload = {"source_file": "file1.pdf"}  # Duplicate
        
        mock_qdrant_client.scroll.return_value = ([mock_point1, mock_point2, mock_point3], None)
        
        files = await vector_store.list_files()
        
        assert len(files) == 2
        assert "file1.pdf" in files
        assert "file2.pdf" in files
        
        mock_qdrant_client.scroll.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_collection_info(self, vector_store, mock_qdrant_client):
        """Test getting collection information."""
        # Mock collection info
        mock_config = MagicMock()
        mock_config.name = "test_documents"
        
        mock_info = MagicMock()
        mock_info.config = mock_config
        mock_info.vectors_count = 100
        mock_info.indexed_vectors_count = 95
        mock_info.status = "green"
        
        mock_qdrant_client.get_collection.return_value = mock_info
        
        info = await vector_store.get_collection_info()
        
        assert info["name"] == "test_documents"
        assert info["vectors_count"] == 100
        assert info["indexed_vectors_count"] == 95
        assert info["status"] == "green"
        
        mock_qdrant_client.get_collection.assert_called_once_with("test_documents")
    
    @pytest.mark.asyncio
    async def test_initialization_error_handling(self, test_settings):
        """Test error handling during initialization."""
        with patch('services.storage.services.vector_store.settings', test_settings):
            with patch('services.storage.services.vector_store.QdrantClient', side_effect=Exception("Connection failed")):
                store = VectorStore()
                
                with pytest.raises(Exception, match="Error initializing vector store"):
                    await store.initialize()
    
    @pytest.mark.asyncio
    async def test_store_chunks_error_handling(self, vector_store, sample_chunks, mock_qdrant_client):
        """Test error handling when storing chunks fails."""
        mock_qdrant_client.upsert.side_effect = Exception("Storage failed")
        
        with pytest.raises(Exception, match="Error storing chunks in vector database"):
            await vector_store.store_chunks(sample_chunks)
    
    @pytest.mark.asyncio
    async def test_search_similar_error_handling(self, vector_store, mock_qdrant_client):
        """Test error handling when search fails."""
        mock_qdrant_client.search.side_effect = Exception("Search failed")
        
        query_vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        with pytest.raises(Exception, match="Error searching vector database"):
            await vector_store.search_similar(query_vector)
    
    @pytest.mark.asyncio
    async def test_delete_error_handling(self, vector_store, mock_qdrant_client):
        """Test error handling when delete fails."""
        mock_qdrant_client.delete.side_effect = Exception("Delete failed")
        
        with pytest.raises(Exception, match="Error deleting file chunks"):
            await vector_store.delete_by_file_id("test_file")
    
    @pytest.mark.asyncio
    async def test_list_files_error_handling(self, vector_store, mock_qdrant_client):
        """Test error handling when listing files fails."""
        mock_qdrant_client.scroll.side_effect = Exception("Scroll failed")
        
        with pytest.raises(Exception, match="Error listing files"):
            await vector_store.list_files()
    
    @pytest.mark.asyncio
    async def test_collection_info_error_handling(self, vector_store, mock_qdrant_client):
        """Test error handling when getting collection info fails."""
        mock_qdrant_client.get_collection.side_effect = Exception("Info failed")
        
        with pytest.raises(Exception, match="Error getting collection info"):
            await vector_store.get_collection_info()
    
    @pytest.mark.asyncio
    async def test_empty_chunks_storage(self, vector_store, mock_qdrant_client):
        """Test storing empty chunks list."""
        await vector_store.store_chunks([])
        
        mock_qdrant_client.upsert.assert_called_once()
        call_args = mock_qdrant_client.upsert.call_args
        assert len(call_args[1]["points"]) == 0
    
    @pytest.mark.asyncio
    async def test_search_threshold_filtering(self, vector_store, mock_qdrant_client):
        """Test that search threshold is properly applied."""
        query_vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        threshold = 0.8
        
        await vector_store.search_similar(
            query_vector, 
            top_k=5, 
            score_threshold=threshold
        )
        
        call_args = mock_qdrant_client.search.call_args
        assert call_args[1]["score_threshold"] == threshold