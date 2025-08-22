import pytest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock, mock_open

from services.storage.services.file_processor import FileProcessor
from shared.models import FileType, DocumentChunk


class TestFileProcessor:
    """Test suite for FileProcessor."""
    
    @pytest.fixture
    def file_processor(self):
        """Create FileProcessor instance."""
        return FileProcessor()
    
    @pytest.mark.asyncio
    async def test_extract_pdf_text_real_file(self, file_processor, pdf_test_file_path):
        """Test PDF text extraction with real PDF file."""
        if not os.path.exists(pdf_test_file_path):
            pytest.skip("Test PDF file not found")
        
        text = await file_processor.extract_text(pdf_test_file_path, FileType.PDF)
        
        assert isinstance(text, str)
        assert len(text) > 0
        assert "adaptation" in text.lower() or "language" in text.lower()
        print(f"Extracted text length: {len(text)} characters")
        print(f"First 200 characters: {text[:200]}")
    
    @pytest.mark.asyncio
    async def test_extract_pdf_text_second_file(self, file_processor, pdf_test_file_path_2):
        """Test PDF text extraction with second real PDF file."""
        if not os.path.exists(pdf_test_file_path_2):
            pytest.skip("Second test PDF file not found")
        
        text = await file_processor.extract_text(pdf_test_file_path_2, FileType.PDF)
        
        assert isinstance(text, str)
        assert len(text) > 0
        assert "ai" in text.lower() or "frontier" in text.lower()
        print(f"Extracted text length: {len(text)} characters")
        print(f"First 200 characters: {text[:200]}")
    
    @pytest.mark.asyncio
    async def test_extract_txt_text(self, file_processor, sample_text):
        """Test TXT file text extraction."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(sample_text)
            temp_path = f.name
        
        try:
            text = await file_processor.extract_text(temp_path, FileType.TXT)
            assert text.strip() == sample_text.strip()
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_extract_json_text(self, file_processor):
        """Test JSON file text extraction."""
        test_data = {
            "title": "Test Document",
            "content": "This is test content",
            "metadata": {
                "author": "Test Author",
                "tags": ["test", "document"]
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name
        
        try:
            text = await file_processor.extract_text(temp_path, FileType.JSON)
            assert "Test Document" in text
            assert "This is test content" in text
            assert "Test Author" in text
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_unsupported_file_type(self, file_processor):
        """Test handling of unsupported file types."""
        with pytest.raises(Exception, match="Error extracting text from xyz file"):
            await file_processor.extract_text("dummy.xyz", "xyz")
    
    @pytest.mark.asyncio
    async def test_chunk_text_basic(self, file_processor, sample_text):
        """Test basic text chunking functionality."""
        chunks = await file_processor.chunk_text(sample_text, "test.pdf")
        
        assert isinstance(chunks, list)
        assert len(chunks) > 0
        assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
        assert all(chunk.source_file == "test.pdf" for chunk in chunks)
        assert all(chunk.chunk_index == i for i, chunk in enumerate(chunks))
    
    @pytest.mark.asyncio
    async def test_chunk_text_with_real_pdf(self, file_processor, pdf_test_file_path):
        """Test chunking with real PDF content."""
        if not os.path.exists(pdf_test_file_path):
            pytest.skip("Test PDF file not found")
        
        # Extract text from real PDF
        text = await file_processor.extract_text(pdf_test_file_path, FileType.PDF)
        chunks = await file_processor.chunk_text(text, pdf_test_file_path)
        
        assert isinstance(chunks, list)
        assert len(chunks) > 0
        
        # Verify chunk properties
        for i, chunk in enumerate(chunks):
            assert chunk.id is not None
            assert len(chunk.content) > 0
            assert chunk.source_file == pdf_test_file_path
            assert chunk.chunk_index == i
            assert "source_file" in chunk.metadata
            assert "chunk_index" in chunk.metadata
            assert "total_chunks" in chunk.metadata
            assert "char_count" in chunk.metadata
        
        print(f"Created {len(chunks)} chunks from PDF")
        print(f"First chunk content: {chunks[0].content[:100]}")
    
    @pytest.mark.asyncio
    async def test_chunk_text_small_content(self, file_processor):
        """Test chunking with content smaller than chunk size."""
        small_text = "This is a small text."
        chunks = await file_processor.chunk_text(small_text, "small.txt")
        
        assert len(chunks) == 1
        assert chunks[0].content == small_text
        assert chunks[0].chunk_index == 0
    
    @pytest.mark.asyncio
    async def test_chunk_metadata(self, file_processor, sample_text):
        """Test that chunk metadata is correctly populated."""
        chunks = await file_processor.chunk_text(sample_text, "test.pdf")
        
        for chunk in chunks:
            assert "source_file" in chunk.metadata
            assert "chunk_index" in chunk.metadata
            assert "total_chunks" in chunk.metadata
            assert "char_count" in chunk.metadata
            
            assert chunk.metadata["source_file"] == "test.pdf"
            assert chunk.metadata["total_chunks"] == len(chunks)
            assert chunk.metadata["char_count"] == len(chunk.content)
    
    @pytest.mark.asyncio
    async def test_json_to_text_conversion(self, file_processor):
        """Test JSON to text conversion logic."""
        test_data = {
            "simple_key": "simple_value",
            "nested": {
                "key1": "value1",
                "key2": "value2"
            },
            "list_data": ["item1", "item2", "item3"]
        }
        
        text = file_processor._json_to_text(test_data)
        
        assert "simple_key: simple_value" in text
        assert "nested:" in text
        assert "key1: value1" in text
        assert "list_data:" in text
        assert "item1" in text
    
    @pytest.mark.asyncio
    async def test_error_handling_missing_file(self, file_processor):
        """Test error handling for missing files."""
        with pytest.raises(Exception):
            await file_processor.extract_text("nonexistent.pdf", FileType.PDF)
    
    @pytest.mark.asyncio
    async def test_chunk_id_generation(self, file_processor):
        """Test that chunk IDs are generated consistently."""
        text = "Test content for chunk ID generation."
        chunks1 = await file_processor.chunk_text(text, "test.pdf")
        chunks2 = await file_processor.chunk_text(text, "test.pdf")
        
        # Same content should generate same IDs
        assert chunks1[0].id == chunks2[0].id
        
        # Different source files should generate different IDs
        chunks3 = await file_processor.chunk_text(text, "different.pdf")
        assert chunks1[0].id != chunks3[0].id
    
    @pytest.mark.asyncio
    async def test_large_text_chunking(self, file_processor):
        """Test chunking of large text content."""
        # Create text larger than chunk size
        large_text = "This is a sentence. " * 100  # ~2000 characters
        chunks = await file_processor.chunk_text(large_text, "large.txt")
        
        assert len(chunks) > 1
        
        # Verify no chunk is empty
        assert all(len(chunk.content.strip()) > 0 for chunk in chunks)
        
        # Verify chunk size constraints
        for chunk in chunks[:-1]:  # All but last chunk
            assert len(chunk.content) <= 550  # chunk_size + some buffer for word boundaries
    
    @pytest.mark.asyncio 
    async def test_docx_extraction_mock(self, file_processor):
        """Test DOCX extraction with mocked Document."""
        with patch('services.storage.services.file_processor.Document') as mock_doc:
            # Mock document with paragraphs
            mock_paragraph1 = MagicMock()
            mock_paragraph1.text = "First paragraph text."
            mock_paragraph2 = MagicMock()
            mock_paragraph2.text = "Second paragraph text."
            
            mock_doc_instance = MagicMock()
            mock_doc_instance.paragraphs = [mock_paragraph1, mock_paragraph2]
            mock_doc.return_value = mock_doc_instance
            
            with tempfile.NamedTemporaryFile(suffix='.docx') as temp_file:
                text = await file_processor.extract_text(temp_file.name, FileType.DOCX)
                
                expected_text = "First paragraph text.\nSecond paragraph text."
                assert text == expected_text