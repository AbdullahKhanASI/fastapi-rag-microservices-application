from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class FileType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    JSON = "json"


class DocumentChunk(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    source_file: str
    chunk_index: int


class UploadFileRequest(BaseModel):
    file_name: str
    file_type: FileType
    metadata: Optional[Dict[str, Any]] = {}


class UploadFileResponse(BaseModel):
    file_id: str
    file_name: str
    chunks_count: int
    status: str
    message: str


class SearchQuery(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    filters: Optional[Dict[str, Any]] = None


class SearchResult(BaseModel):
    chunk_id: str
    content: str
    score: float
    metadata: Dict[str, Any]
    source_file: str


class RetrievalResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int


class EnhancedQuery(BaseModel):
    original_query: str
    enhanced_query: str
    expansion_terms: List[str]
    intent: str
    confidence: float


class GenerationRequest(BaseModel):
    enhanced_query: str
    retrieved_docs: List[SearchResult]
    conversation_history: Optional[List[Dict[str, str]]] = []
    max_tokens: int = Field(default=1000, ge=100, le=4000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class GenerationResponse(BaseModel):
    query: str
    response: str
    sources: List[str]
    confidence: float
    token_usage: Dict[str, int]


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=20)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class ChatResponse(BaseModel):
    conversation_id: str
    response: str
    sources: List[str]
    confidence: float
    timestamp: datetime = Field(default_factory=datetime.now)


class HealthCheck(BaseModel):
    service: str
    status: str
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0"