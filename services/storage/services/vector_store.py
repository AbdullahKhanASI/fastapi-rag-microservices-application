from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from shared.models import DocumentChunk
from shared.config import settings


class VectorStore:
    """Service for managing vector database operations."""
    
    def __init__(self):
        self.client = None
        self.collection_name = settings.qdrant_collection_name
    
    async def initialize(self):
        """Initialize connection to Qdrant and create collection if needed."""
        try:
            self.client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port
            )
            
            # Check if collection exists
            collections = self.client.get_collections()
            collection_exists = any(
                collection.name == self.collection_name 
                for collection in collections.collections
            )
            
            if not collection_exists:
                # Create collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=settings.embedding_dimension,
                        distance=models.Distance.COSINE
                    )
                )
                
        except Exception as e:
            raise Exception(f"Error initializing vector store: {e}")
    
    async def store_chunks(self, chunks: List[DocumentChunk]):
        """Store document chunks in the vector database."""
        try:
            points = []
            for chunk in chunks:
                point = models.PointStruct(
                    id=chunk.id,
                    vector=chunk.embedding,
                    payload={
                        "content": chunk.content,
                        "source_file": chunk.source_file,
                        "chunk_index": chunk.chunk_index,
                        "metadata": chunk.metadata
                    }
                )
                points.append(point)
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
        except Exception as e:
            raise Exception(f"Error storing chunks in vector database: {e}")
    
    async def search_similar(
        self, 
        query_vector: List[float], 
        top_k: int = 5,
        score_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors in the database."""
        try:
            search_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                    )
                search_filter = models.Filter(must=conditions)
            
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                score_threshold=score_threshold,
                query_filter=search_filter
            )
            
            results = []
            for hit in search_result:
                result = {
                    "id": hit.id,
                    "score": hit.score,
                    "content": hit.payload.get("content", ""),
                    "source_file": hit.payload.get("source_file", ""),
                    "chunk_index": hit.payload.get("chunk_index", 0),
                    "metadata": hit.payload.get("metadata", {})
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            raise Exception(f"Error searching vector database: {e}")
    
    async def delete_by_file_id(self, file_id: str):
        """Delete all chunks belonging to a specific file."""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="source_file",
                                match=models.MatchText(text=file_id)
                            )
                        ]
                    )
                )
            )
        except Exception as e:
            raise Exception(f"Error deleting file chunks: {e}")
    
    async def list_files(self) -> List[str]:
        """List all unique source files in the database."""
        try:
            # This is a simplified implementation
            # In production, you might want to maintain a separate files index
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                limit=1000,  # Adjust based on your needs
                with_payload=["source_file"]
            )
            
            source_files = set()
            for point in scroll_result[0]:
                source_file = point.payload.get("source_file")
                if source_file:
                    source_files.add(source_file)
            
            return list(source_files)
            
        except Exception as e:
            raise Exception(f"Error listing files: {e}")
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": info.config.name,
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "status": info.status
            }
        except Exception as e:
            raise Exception(f"Error getting collection info: {e}")