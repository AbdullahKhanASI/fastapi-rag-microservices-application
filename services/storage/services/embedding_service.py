from typing import List
import openai
from sentence_transformers import SentenceTransformer
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from shared.config import settings


class EmbeddingService:
    """Service for generating text embeddings."""
    
    def __init__(self):
        self.openai_client = None
        self.sentence_transformer = None
        self._setup_embedding_service()
    
    def _setup_embedding_service(self):
        """Initialize the embedding service based on configuration."""
        if settings.openai_api_key:
            openai.api_key = settings.openai_api_key
            self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        else:
            # Fallback to sentence transformers
            self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        if self.openai_client:
            return await self._generate_openai_embeddings(texts)
        else:
            return await self._generate_sentence_transformer_embeddings(texts)
    
    async def _generate_openai_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API."""
        try:
            response = self.openai_client.embeddings.create(
                model=settings.embedding_model,
                input=texts
            )
            return [embedding.embedding for embedding in response.data]
        except Exception as e:
            raise Exception(f"Error generating OpenAI embeddings: {e}")
    
    async def _generate_sentence_transformer_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using sentence transformers."""
        try:
            embeddings = self.sentence_transformer.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            raise Exception(f"Error generating sentence transformer embeddings: {e}")
    
    async def generate_single_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        embeddings = await self.generate_embeddings([text])
        return embeddings[0]