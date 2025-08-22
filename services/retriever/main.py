from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.models import SearchQuery, RetrievalResponse, SearchResult, HealthCheck
from shared.config import settings
from shared.utils import setup_logging

from services.hybrid_retriever import HybridRetriever

app = FastAPI(title="Retriever Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = setup_logging("retriever-service")

# Initialize retriever service
hybrid_retriever = HybridRetriever()


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    try:
        await hybrid_retriever.initialize()
        logger.info("Retriever service started successfully")
    except Exception as e:
        logger.error(f"Failed to start retriever service: {e}")
        raise


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    return HealthCheck(service="retriever", status="healthy")


@app.post("/search", response_model=RetrievalResponse)
async def search_documents(query: SearchQuery):
    """Search for relevant documents using hybrid search."""
    try:
        logger.info(f"Searching for: {query.query}")
        
        results = await hybrid_retriever.hybrid_search(
            query=query.query,
            top_k=query.top_k,
            threshold=query.threshold,
            filters=query.filters
        )
        
        search_results = [
            SearchResult(
                chunk_id=result["id"],
                content=result["content"],
                score=result["score"],
                metadata=result["metadata"],
                source_file=result["source_file"]
            )
            for result in results
        ]
        
        logger.info(f"Found {len(search_results)} relevant documents")
        
        return RetrievalResponse(
            query=query.query,
            results=search_results,
            total_results=len(search_results)
        )
        
    except Exception as e:
        logger.error(f"Error during search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/semantic-search", response_model=RetrievalResponse)
async def semantic_search(query: SearchQuery):
    """Perform semantic search only."""
    try:
        logger.info(f"Performing semantic search for: {query.query}")
        
        results = await hybrid_retriever.semantic_search(
            query=query.query,
            top_k=query.top_k,
            threshold=query.threshold,
            filters=query.filters
        )
        
        search_results = [
            SearchResult(
                chunk_id=result["id"],
                content=result["content"],
                score=result["score"],
                metadata=result["metadata"],
                source_file=result["source_file"]
            )
            for result in results
        ]
        
        return RetrievalResponse(
            query=query.query,
            results=search_results,
            total_results=len(search_results)
        )
        
    except Exception as e:
        logger.error(f"Error during semantic search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/keyword-search", response_model=RetrievalResponse)
async def keyword_search(query: SearchQuery):
    """Perform keyword search only."""
    try:
        logger.info(f"Performing keyword search for: {query.query}")
        
        results = await hybrid_retriever.keyword_search(
            query=query.query,
            top_k=query.top_k,
            filters=query.filters
        )
        
        search_results = [
            SearchResult(
                chunk_id=result["id"],
                content=result["content"],
                score=result["score"],
                metadata=result["metadata"],
                source_file=result["source_file"]
            )
            for result in results
        ]
        
        return RetrievalResponse(
            query=query.query,
            results=search_results,
            total_results=len(search_results)
        )
        
    except Exception as e:
        logger.error(f"Error during keyword search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)