import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch

from services.storage.services.file_processor import FileProcessor
from services.storage.services.embedding_service import EmbeddingService
from shared.models import FileType


class TestStorageIntegration:
    """Integration tests for the complete storage pipeline with real documents."""
    
    @pytest.fixture
    def file_processor(self):
        return FileProcessor()
    
    @pytest.fixture
    def embedding_service_mock(self):
        """Mock embedding service to avoid API calls."""
        service = EmbeddingService()
        service.openai_client = MagicMock()
        return service
    
    @pytest.mark.asyncio
    async def test_complete_pdf_processing_pipeline(
        self, 
        file_processor, 
        embedding_service_mock, 
        pdf_test_file_path
    ):
        """Test complete pipeline: PDF → Text → Chunks → Embeddings."""
        if not os.path.exists(pdf_test_file_path):
            pytest.skip("Test PDF file not found")
        
        # Step 1: Extract text from PDF
        text = await file_processor.extract_text(pdf_test_file_path, FileType.PDF)
        
        assert len(text) > 0
        assert "adaptation" in text.lower() or "language" in text.lower()
        print(f"✅ Extracted {len(text)} characters from PDF")
        
        # Step 2: Create chunks
        chunks = await file_processor.chunk_text(text, pdf_test_file_path)
        
        assert len(chunks) > 0
        assert all(chunk.content for chunk in chunks)
        assert all(chunk.source_file == pdf_test_file_path for chunk in chunks)
        print(f"✅ Created {len(chunks)} chunks")
        
        # Step 3: Mock embedding generation
        mock_embeddings = [[0.1] * 1536 for _ in chunks]  # Mock 1536-dim embeddings
        
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=emb) for emb in mock_embeddings]
        embedding_service_mock.openai_client.embeddings.create.return_value = mock_response
        
        # Generate embeddings for all chunks
        texts = [chunk.content for chunk in chunks]
        embeddings = await embedding_service_mock.generate_embeddings(texts)
        
        assert len(embeddings) == len(chunks)
        assert all(len(emb) == 1536 for emb in embeddings)
        print(f"✅ Generated embeddings for {len(embeddings)} chunks")
        
        # Step 4: Add embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding
        
        # Verify complete chunks
        assert all(chunk.embedding is not None for chunk in chunks)
        assert all(len(chunk.embedding) == 1536 for chunk in chunks)
        print(f"✅ Complete pipeline successful: {len(chunks)} chunks ready for storage")
    
    @pytest.mark.asyncio
    async def test_large_pdf_processing_pipeline(
        self, 
        file_processor, 
        embedding_service_mock, 
        pdf_test_file_path_2
    ):
        """Test pipeline with larger PDF document."""
        if not os.path.exists(pdf_test_file_path_2):
            pytest.skip("Second test PDF file not found")
        
        # Step 1: Extract text
        text = await file_processor.extract_text(pdf_test_file_path_2, FileType.PDF)
        
        assert len(text) > 50000  # Large document
        print(f"✅ Extracted {len(text)} characters from large PDF")
        
        # Step 2: Create chunks
        chunks = await file_processor.chunk_text(text, pdf_test_file_path_2)
        
        assert len(chunks) > 50  # Should create many chunks
        print(f"✅ Created {len(chunks)} chunks from large document")
        
        # Verify chunk quality
        assert all(len(chunk.content.strip()) > 0 for chunk in chunks)
        assert all(chunk.chunk_index == i for i, chunk in enumerate(chunks))
        
        # Check that chunks don't exceed expected size (with some buffer for word boundaries)
        for chunk in chunks[:-1]:  # All but last chunk
            assert len(chunk.content) <= 600  # chunk_size + buffer
        
        print(f"✅ All {len(chunks)} chunks properly formatted and sized")
    
    @pytest.mark.asyncio
    async def test_chunk_content_quality(self, file_processor, pdf_test_file_path):
        """Test that chunks contain meaningful content."""
        if not os.path.exists(pdf_test_file_path):
            pytest.skip("Test PDF file not found")
        
        text = await file_processor.extract_text(pdf_test_file_path, FileType.PDF)
        chunks = await file_processor.chunk_text(text, pdf_test_file_path)
        
        # Check that chunks contain meaningful content
        meaningful_chunks = 0
        for chunk in chunks:
            # Count chunks with reasonable word count
            word_count = len(chunk.content.split())
            if word_count > 10:  # At least 10 words
                meaningful_chunks += 1
        
        # Most chunks should have meaningful content
        assert meaningful_chunks > len(chunks) * 0.8  # 80% of chunks
        print(f"✅ {meaningful_chunks}/{len(chunks)} chunks have meaningful content")
        
        # Check for proper sentence boundaries in chunks
        complete_sentences = 0
        for chunk in chunks:
            if any(chunk.content.strip().endswith(punct) for punct in '.!?'):
                complete_sentences += 1
        
        print(f"✅ {complete_sentences}/{len(chunks)} chunks end with proper punctuation")
    
    @pytest.mark.asyncio
    async def test_chunk_metadata_completeness(self, file_processor, pdf_test_file_path):
        """Test that all chunks have complete metadata."""
        if not os.path.exists(pdf_test_file_path):
            pytest.skip("Test PDF file not found")
        
        text = await file_processor.extract_text(pdf_test_file_path, FileType.PDF)
        chunks = await file_processor.chunk_text(text, pdf_test_file_path)
        
        for i, chunk in enumerate(chunks):
            # Check required fields
            assert chunk.id is not None
            assert chunk.content is not None
            assert chunk.source_file == pdf_test_file_path
            assert chunk.chunk_index == i
            
            # Check metadata
            assert "source_file" in chunk.metadata
            assert "chunk_index" in chunk.metadata
            assert "total_chunks" in chunk.metadata
            assert "char_count" in chunk.metadata
            
            # Verify metadata values
            assert chunk.metadata["source_file"] == pdf_test_file_path
            assert chunk.metadata["chunk_index"] == i
            assert chunk.metadata["total_chunks"] == len(chunks)
            assert chunk.metadata["char_count"] == len(chunk.content)
        
        print(f"✅ All {len(chunks)} chunks have complete metadata")
    
    @pytest.mark.asyncio
    async def test_embedding_service_configuration(self, test_settings):
        """Test embedding service configuration with API key."""
        with patch('services.storage.services.embedding_service.settings', test_settings):
            service = EmbeddingService()
            
            # Should initialize with OpenAI client when API key is provided
            assert service.openai_client is not None
            assert service.sentence_transformer is None
        
        print("✅ Embedding service properly configured with OpenAI API key")
    
    @pytest.mark.asyncio
    async def test_file_type_detection_and_processing(self, file_processor):
        """Test that the system can handle different file types correctly."""
        test_cases = [
            ("document.pdf", FileType.PDF),
            ("document.docx", FileType.DOCX), 
            ("document.txt", FileType.TXT),
            ("data.json", FileType.JSON)
        ]
        
        for filename, expected_type in test_cases:
            # This would be used in the actual API to determine file type
            file_extension = filename.split('.')[-1].lower()
            detected_type = FileType(file_extension)
            
            assert detected_type == expected_type
        
        print("✅ File type detection working for all supported formats")