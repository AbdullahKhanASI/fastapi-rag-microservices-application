from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.models import EnhancedQuery, HealthCheck
from shared.config import settings
from shared.utils import setup_logging

from services.query_enhancer import QueryEnhancer

app = FastAPI(title="Query Enhancement Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = setup_logging("query-enhancement-service")

# Initialize query enhancer
query_enhancer = QueryEnhancer()


class QueryRequest(BaseModel):
    query: str
    context: str = ""


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    try:
        await query_enhancer.initialize()
        logger.info("Query enhancement service started successfully")
    except Exception as e:
        logger.error(f"Failed to start query enhancement service: {e}")
        raise


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    return HealthCheck(service="query-enhancement", status="healthy")


@app.post("/enhance", response_model=EnhancedQuery)
async def enhance_query(request: QueryRequest):
    """Enhance a user query for better retrieval."""
    try:
        logger.info(f"Enhancing query: {request.query}")
        
        enhanced_query = await query_enhancer.enhance_query(
            query=request.query,
            context=request.context
        )
        
        logger.info(f"Enhanced query generated: {enhanced_query.enhanced_query}")
        
        return enhanced_query
        
    except Exception as e:
        logger.error(f"Error enhancing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/expand")
async def expand_query(request: QueryRequest):
    """Expand query with synonyms and related terms."""
    try:
        logger.info(f"Expanding query: {request.query}")
        
        expansion_terms = await query_enhancer.expand_query(request.query)
        
        return {
            "original_query": request.query,
            "expansion_terms": expansion_terms,
            "expanded_query": f"{request.query} {' '.join(expansion_terms)}"
        }
        
    except Exception as e:
        logger.error(f"Error expanding query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/classify-intent")
async def classify_intent(request: QueryRequest):
    """Classify the intent of a user query."""
    try:
        logger.info(f"Classifying intent for: {request.query}")
        
        intent_result = await query_enhancer.classify_intent(request.query)
        
        return intent_result
        
    except Exception as e:
        logger.error(f"Error classifying intent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)