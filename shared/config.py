import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # Vector Database
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "documents"
    
    # Service URLs
    storage_service_url: str = "http://localhost:8001"
    retriever_service_url: str = "http://localhost:8002"
    query_enhancement_service_url: str = "http://localhost:8003"
    generation_service_url: str = "http://localhost:8004"
    
    # Embedding Configuration
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536
    
    # Generation Configuration
    llm_model: str = "gpt-4o-mini"
    max_tokens: int = 2000
    temperature: float = 0.7
    
    # Chunking Configuration
    chunk_size: int = 500
    chunk_overlap: int = 50
    
    # File Upload
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    upload_dir: str = "uploads"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()