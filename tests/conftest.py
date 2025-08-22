import pytest
import asyncio
import tempfile
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Generator, AsyncGenerator

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.models import DocumentChunk, FileType
from shared.config import Settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings():
    """Test settings with mocked values."""
    return Settings(
        openai_api_key="test-openai-key",
        qdrant_host="localhost",
        qdrant_port=6333,
        qdrant_collection_name="test_documents",
        embedding_model="text-embedding-3-small",
        embedding_dimension=1536,
        chunk_size=500,
        chunk_overlap=50,
        upload_dir="test_uploads"
    )


@pytest.fixture
def temp_upload_dir():
    """Create a temporary upload directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_text():
    """Sample text for testing."""
    return """
    This is a sample document for testing purposes. It contains multiple sentences 
    that will be used to test the chunking functionality of our document processing system.
    
    The document discusses various topics including natural language processing,
    machine learning, and artificial intelligence. These are important concepts
    in modern computer science and technology.
    
    We use this text to verify that our system can properly extract, chunk,
    and process textual content from various document formats.
    """


@pytest.fixture
def sample_chunks():
    """Sample document chunks for testing."""
    return [
        DocumentChunk(
            id="chunk_1",
            content="This is the first chunk of text for testing.",
            metadata={"source_file": "test.pdf", "chunk_index": 0},
            source_file="test.pdf",
            chunk_index=0,
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5]
        ),
        DocumentChunk(
            id="chunk_2", 
            content="This is the second chunk of text for testing.",
            metadata={"source_file": "test.pdf", "chunk_index": 1},
            source_file="test.pdf",
            chunk_index=1,
            embedding=[0.2, 0.3, 0.4, 0.5, 0.6]
        )
    ]


@pytest.fixture
def mock_openai_embeddings():
    """Mock OpenAI embeddings response."""
    mock_response = MagicMock()
    mock_response.data = [
        MagicMock(embedding=[0.1, 0.2, 0.3, 0.4, 0.5]),
        MagicMock(embedding=[0.2, 0.3, 0.4, 0.5, 0.6])
    ]
    return mock_response


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client."""
    mock_client = AsyncMock()
    
    # Mock collection operations
    mock_client.get_collections.return_value = MagicMock(collections=[])
    mock_client.create_collection = AsyncMock()
    mock_client.upsert = AsyncMock()
    mock_client.search.return_value = []
    mock_client.delete = AsyncMock()
    mock_client.scroll.return_value = ([], None)
    mock_client.get_collection.return_value = MagicMock(
        config=MagicMock(name="test_documents"),
        vectors_count=0,
        indexed_vectors_count=0,
        status="green"
    )
    mock_client.retrieve.return_value = []
    
    return mock_client


@pytest.fixture
def pdf_test_file_path():
    """Path to the test PDF file."""
    return "/Users/abdullah/Repositories/learning/python/2-fastapi/4-fastapi-backend-microservices/test_docs/A_Comprehensive_Review_of_Low_Rank_Adaptation_in_Large_Language_Models_for_Efficient_Parameter_Tuning-1.pdf"


@pytest.fixture
def pdf_test_file_path_2():
    """Path to the second test PDF file."""
    return "/Users/abdullah/Repositories/learning/python/2-fastapi/4-fastapi-backend-microservices/test_docs/Frontier AI Models for Key Use Cases (2025).pdf"


@pytest.fixture
def mock_file_upload():
    """Mock file upload object."""
    mock_file = MagicMock()
    mock_file.filename = "test_document.pdf"
    mock_file.read = AsyncMock(return_value=b"mock file content")
    return mock_file


@pytest.fixture
def sample_search_results():
    """Sample search results for testing."""
    return [
        {
            "id": "chunk_1",
            "content": "This is the first search result.",
            "score": 0.95,
            "source_file": "test.pdf",
            "chunk_index": 0,
            "metadata": {"source_file": "test.pdf", "chunk_index": 0}
        },
        {
            "id": "chunk_2",
            "content": "This is the second search result.",
            "score": 0.85,
            "source_file": "test.pdf", 
            "chunk_index": 1,
            "metadata": {"source_file": "test.pdf", "chunk_index": 1}
        }
    ]