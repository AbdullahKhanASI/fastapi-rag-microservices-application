import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from services.storage.services.embedding_service import EmbeddingService
from shared.config import Settings


class TestEmbeddingService:
    """Test suite for EmbeddingService."""
    
    @pytest.fixture
    def embedding_service_with_openai(self, test_settings):
        """Create EmbeddingService with OpenAI configuration."""
        with patch('services.storage.services.embedding_service.settings', test_settings):
            service = EmbeddingService()
        return service
    
    @pytest.fixture 
    def embedding_service_without_openai(self):
        """Create EmbeddingService without OpenAI (fallback to sentence transformers)."""
        settings_no_openai = Settings(openai_api_key=None)
        with patch('services.storage.services.embedding_service.settings', settings_no_openai):
            with patch('services.storage.services.embedding_service.SentenceTransformer') as mock_st:
                mock_model = MagicMock()
                mock_st.return_value = mock_model
                service = EmbeddingService()
                service.sentence_transformer = mock_model
        return service
    
    @pytest.mark.asyncio
    async def test_generate_openai_embeddings(self, embedding_service_with_openai, mock_openai_embeddings):
        """Test OpenAI embedding generation."""
        with patch.object(embedding_service_with_openai.openai_client.embeddings, 'create', return_value=mock_openai_embeddings):
            texts = ["This is test text 1.", "This is test text 2."]
            embeddings = await embedding_service_with_openai.generate_embeddings(texts)
            
            assert len(embeddings) == 2
            assert embeddings[0] == [0.1, 0.2, 0.3, 0.4, 0.5]
            assert embeddings[1] == [0.2, 0.3, 0.4, 0.5, 0.6]
    
    @pytest.mark.asyncio
    async def test_generate_sentence_transformer_embeddings(self, embedding_service_without_openai):
        """Test sentence transformer embedding generation."""
        # Mock sentence transformer encode method
        mock_embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        embedding_service_without_openai.sentence_transformer.encode.return_value = MagicMock()
        embedding_service_without_openai.sentence_transformer.encode.return_value.tolist.return_value = mock_embeddings
        
        texts = ["Test text 1", "Test text 2"]
        embeddings = await embedding_service_without_openai.generate_embeddings(texts)
        
        assert embeddings == mock_embeddings
        embedding_service_without_openai.sentence_transformer.encode.assert_called_once_with(texts)
    
    @pytest.mark.asyncio
    async def test_generate_single_embedding(self, embedding_service_with_openai):
        """Test single embedding generation."""
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3, 0.4, 0.5])]
        
        with patch.object(embedding_service_with_openai.openai_client.embeddings, 'create', return_value=mock_response):
            text = "Single test text."
            embedding = await embedding_service_with_openai.generate_single_embedding(text)
            
            assert embedding == [0.1, 0.2, 0.3, 0.4, 0.5]
    
    @pytest.mark.asyncio
    async def test_openai_api_error_handling(self, embedding_service_with_openai):
        """Test error handling when OpenAI API fails."""
        with patch.object(embedding_service_with_openai.openai_client.embeddings, 'create', side_effect=Exception("API Error")):
            texts = ["Test text"]
            
            with pytest.raises(Exception, match="Error generating OpenAI embeddings"):
                await embedding_service_with_openai.generate_embeddings(texts)
    
    @pytest.mark.asyncio
    async def test_sentence_transformer_error_handling(self, embedding_service_without_openai):
        """Test error handling when sentence transformer fails."""
        embedding_service_without_openai.sentence_transformer.encode.side_effect = Exception("Model Error")
        
        texts = ["Test text"]
        
        with pytest.raises(Exception, match="Error generating sentence transformer embeddings"):
            await embedding_service_without_openai.generate_embeddings(texts)
    
    @pytest.mark.asyncio
    async def test_empty_text_list(self, embedding_service_with_openai):
        """Test handling of empty text list."""
        mock_response = MagicMock()
        mock_response.data = []
        
        with patch.object(embedding_service_with_openai.openai_client.embeddings, 'create', return_value=mock_response):
            embeddings = await embedding_service_with_openai.generate_embeddings([])
            assert embeddings == []
    
    @pytest.mark.asyncio
    async def test_large_text_batch(self, embedding_service_with_openai):
        """Test handling of large text batches."""
        # Create mock response for large batch
        large_batch_size = 100
        mock_embeddings = [MagicMock(embedding=[i/100.0] * 5) for i in range(large_batch_size)]
        mock_response = MagicMock()
        mock_response.data = mock_embeddings
        
        with patch.object(embedding_service_with_openai.openai_client.embeddings, 'create', return_value=mock_response):
            texts = [f"Text {i}" for i in range(large_batch_size)]
            embeddings = await embedding_service_with_openai.generate_embeddings(texts)
            
            assert len(embeddings) == large_batch_size
            assert all(len(embedding) == 5 for embedding in embeddings)
    
    @pytest.mark.asyncio
    async def test_setup_embedding_service_with_openai_key(self):
        """Test service initialization with OpenAI key."""
        settings_with_key = Settings(openai_api_key="test-key")
        
        with patch('services.storage.services.embedding_service.settings', settings_with_key):
            with patch('services.storage.services.embedding_service.openai.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                
                service = EmbeddingService()
                
                assert service.openai_client == mock_client
                assert service.sentence_transformer is None
                mock_openai.assert_called_once_with(api_key="test-key")
    
    @pytest.mark.asyncio
    async def test_setup_embedding_service_without_openai_key(self):
        """Test service initialization without OpenAI key (fallback)."""
        settings_no_key = Settings(openai_api_key=None)
        
        with patch('services.storage.services.embedding_service.settings', settings_no_key):
            with patch('services.storage.services.embedding_service.SentenceTransformer') as mock_st:
                mock_model = MagicMock()
                mock_st.return_value = mock_model
                
                service = EmbeddingService()
                
                assert service.openai_client is None
                assert service.sentence_transformer == mock_model
                mock_st.assert_called_once_with('all-MiniLM-L6-v2')
    
    @pytest.mark.asyncio
    async def test_openai_embedding_model_configuration(self, embedding_service_with_openai, test_settings):
        """Test that the correct embedding model is used."""
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        
        with patch.object(embedding_service_with_openai.openai_client.embeddings, 'create', return_value=mock_response) as mock_create:
            texts = ["Test text"]
            await embedding_service_with_openai.generate_embeddings(texts)
            
            mock_create.assert_called_once_with(
                model=test_settings.embedding_model,
                input=texts
            )
    
    @pytest.mark.asyncio
    async def test_embedding_dimension_consistency(self, embedding_service_with_openai):
        """Test that embeddings have consistent dimensions."""
        # Mock embeddings with consistent dimensions
        embedding_dim = 1536
        mock_embeddings = [
            MagicMock(embedding=[i/1000.0] * embedding_dim) 
            for i in range(3)
        ]
        mock_response = MagicMock()
        mock_response.data = mock_embeddings
        
        with patch.object(embedding_service_with_openai.openai_client.embeddings, 'create', return_value=mock_response):
            texts = ["Text 1", "Text 2", "Text 3"]
            embeddings = await embedding_service_with_openai.generate_embeddings(texts)
            
            assert len(embeddings) == 3
            assert all(len(embedding) == embedding_dim for embedding in embeddings)
    
    @pytest.mark.asyncio
    async def test_unicode_text_handling(self, embedding_service_with_openai):
        """Test handling of unicode text."""
        unicode_texts = ["Hello 世界", "Café résumé", "🚀 rocket emoji"]
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3]) for _ in unicode_texts]
        
        with patch.object(embedding_service_with_openai.openai_client.embeddings, 'create', return_value=mock_response):
            embeddings = await embedding_service_with_openai.generate_embeddings(unicode_texts)
            
            assert len(embeddings) == len(unicode_texts)
            assert all(isinstance(embedding, list) for embedding in embeddings)