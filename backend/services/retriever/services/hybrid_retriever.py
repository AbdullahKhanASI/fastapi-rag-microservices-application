from typing import List, Dict, Any, Optional
import openai
from qdrant_client import QdrantClient
from qdrant_client.http import models
from rank_bm25 import BM25Okapi
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from shared.config import settings


class HybridRetriever:
    """Service for hybrid search combining semantic and keyword search."""
    
    def __init__(self):
        self.qdrant_client = None
        self.openai_client = None
        self.sentence_transformer = None
        self.bm25 = None
        self.documents = []
        self.document_ids = []
        self.collection_name = settings.qdrant_collection_name
        
    async def initialize(self):
        """Initialize all components."""
        await self._setup_qdrant()
        await self._setup_embedding_service()
        await self._load_documents_for_bm25()
    
    async def _setup_qdrant(self):
        """Initialize Qdrant client."""
        try:
            self.qdrant_client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port
            )
        except Exception as e:
            raise Exception(f"Error connecting to Qdrant: {e}")
    
    async def _setup_embedding_service(self):
        """Initialize embedding service."""
        if settings.openai_api_key:
            self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        else:
            # Fallback to sentence transformers - import only when needed
            try:
                from sentence_transformers import SentenceTransformer
                self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
            except ImportError as e:
                raise Exception(f"sentence_transformers not available and no OpenAI API key provided: {e}")
    
    async def _load_documents_for_bm25(self):
        """Load documents from Qdrant for BM25 indexing."""
        try:
            # Scroll through all documents in the collection
            scroll_result = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                limit=10000,  # Adjust based on your collection size
                with_payload=True
            )
            
            self.documents = []
            self.document_ids = []
            
            for point in scroll_result[0]:
                content = point.payload.get("content", "")
                if content:
                    self.documents.append(content)
                    self.document_ids.append(point.id)
            
            # Initialize BM25 with the documents
            if self.documents:
                tokenized_docs = [doc.lower().split() for doc in self.documents]
                self.bm25 = BM25Okapi(tokenized_docs)
                
        except Exception as e:
            print(f"Warning: Could not load documents for BM25: {e}")
            self.documents = []
            self.document_ids = []
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        if self.openai_client:
            response = self.openai_client.embeddings.create(
                model=settings.embedding_model,
                input=text
            )
            return response.data[0].embedding
        else:
            embedding = self.sentence_transformer.encode([text])
            return embedding[0].tolist()
    
    async def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Perform semantic search using vector similarity."""
        try:
            # Generate query embedding
            query_embedding = await self._generate_embedding(query)
            
            # Build filter if provided
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
            
            # Search in Qdrant
            search_result = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                score_threshold=threshold,
                query_filter=search_filter
            )
            
            results = []
            for hit in search_result:
                result = {
                    "id": str(hit.id),
                    "content": hit.payload.get("content", ""),
                    "score": hit.score,
                    "source_file": hit.payload.get("source_file", ""),
                    "chunk_index": hit.payload.get("chunk_index", 0),
                    "metadata": hit.payload.get("metadata", {}),
                    "search_type": "semantic"
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            raise Exception(f"Error in semantic search: {e}")
    
    async def keyword_search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Perform keyword search using BM25."""
        try:
            if not self.bm25 or not self.documents:
                return []
            
            # Tokenize query
            tokenized_query = query.lower().split()
            
            # Get BM25 scores
            scores = self.bm25.get_scores(tokenized_query)
            
            # Get top-k results
            top_indices = np.argsort(scores)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                if scores[idx] > 0:  # Only include results with positive scores
                    # Get additional metadata from Qdrant
                    point = self.qdrant_client.retrieve(
                        collection_name=self.collection_name,
                        ids=[self.document_ids[idx]],
                        with_payload=True
                    )[0]
                    
                    result = {
                        "id": str(self.document_ids[idx]),
                        "content": self.documents[idx],
                        "score": float(scores[idx]),
                        "source_file": point.payload.get("source_file", ""),
                        "chunk_index": point.payload.get("chunk_index", 0),
                        "metadata": point.payload.get("metadata", {}),
                        "search_type": "keyword"
                    }
                    results.append(result)
            
            return results
            
        except Exception as e:
            raise Exception(f"Error in keyword search: {e}")
    
    async def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search combining semantic and keyword search."""
        try:
            # Get results from both search methods
            semantic_results = await self.semantic_search(
                query, top_k=top_k*2, threshold=threshold, filters=filters
            )
            keyword_results = await self.keyword_search(
                query, top_k=top_k*2, filters=filters
            )
            
            # Combine and rerank results
            combined_results = self._combine_and_rerank(
                semantic_results,
                keyword_results,
                semantic_weight,
                keyword_weight
            )
            
            # Return top-k results
            return combined_results[:top_k]
            
        except Exception as e:
            raise Exception(f"Error in hybrid search: {e}")
    
    def _combine_and_rerank(
        self,
        semantic_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        semantic_weight: float,
        keyword_weight: float
    ) -> List[Dict[str, Any]]:
        """Combine and rerank results from semantic and keyword search."""
        # Create a dictionary to store combined scores
        combined_scores = {}
        
        # Normalize semantic scores (already between 0-1 from cosine similarity)
        for result in semantic_results:
            doc_id = result["id"]
            combined_scores[doc_id] = {
                "result": result,
                "semantic_score": result["score"],
                "keyword_score": 0.0
            }
        
        # Normalize and add keyword scores
        if keyword_results:
            max_keyword_score = max(r["score"] for r in keyword_results) if keyword_results else 1.0
            for result in keyword_results:
                doc_id = result["id"]
                normalized_score = result["score"] / max_keyword_score if max_keyword_score > 0 else 0
                
                if doc_id in combined_scores:
                    combined_scores[doc_id]["keyword_score"] = normalized_score
                else:
                    combined_scores[doc_id] = {
                        "result": result,
                        "semantic_score": 0.0,
                        "keyword_score": normalized_score
                    }
        
        # Calculate combined scores
        final_results = []
        for doc_id, scores in combined_scores.items():
            combined_score = (
                semantic_weight * scores["semantic_score"] +
                keyword_weight * scores["keyword_score"]
            )
            
            result = scores["result"].copy()
            result["score"] = combined_score
            result["semantic_score"] = scores["semantic_score"]
            result["keyword_score"] = scores["keyword_score"]
            result["search_type"] = "hybrid"
            
            final_results.append(result)
        
        # Sort by combined score
        final_results.sort(key=lambda x: x["score"], reverse=True)
        
        return final_results