from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.models import (
    ChatRequest, ChatResponse, UploadFileResponse, 
    SearchQuery, RetrievalResponse, HealthCheck
)
from shared.config import settings
from shared.utils import setup_logging, generate_id

from services.orchestrator import RAGOrchestrator

app = FastAPI(
    title="RAG Chatbot API Gateway",
    version="1.0.0",
    description="API Gateway for RAG Chatbot Microservices"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = setup_logging("api-gateway")

# Initialize orchestrator
orchestrator = RAGOrchestrator()


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    try:
        await orchestrator.initialize()
        logger.info("API Gateway started successfully")
    except Exception as e:
        logger.error(f"Failed to start API Gateway: {e}")
        raise


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    return HealthCheck(service="api-gateway", status="healthy")


@app.get("/health/all")
async def health_check_all():
    """Check health of all services."""
    try:
        health_status = await orchestrator.check_all_services_health()
        return health_status
    except Exception as e:
        logger.error(f"Error checking service health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# File Upload Endpoints
@app.post("/upload", response_model=UploadFileResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload and process a file through the storage service."""
    try:
        logger.info(f"Uploading file: {file.filename}")
        response = await orchestrator.upload_file(file)
        logger.info(f"File uploaded successfully: {file.filename}")
        return response
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """Delete a file and its chunks."""
    try:
        response = await orchestrator.delete_file(file_id)
        return response
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/files")
async def list_files():
    """List all uploaded files."""
    try:
        files = await orchestrator.list_files()
        return files
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Search Endpoints
@app.post("/search", response_model=RetrievalResponse)
async def search(query: SearchQuery):
    """Search for documents."""
    try:
        logger.info(f"Searching for: {query.query}")
        results = await orchestrator.search_documents(query)
        logger.info(f"Search completed with {len(results.results)} results")
        return results
    except Exception as e:
        logger.error(f"Error during search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Chat Endpoints
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message through the full RAG pipeline."""
    try:
        logger.info(f"Processing chat message: {request.message}")
        
        response = await orchestrator.process_chat_message(request)
        
        logger.info("Chat message processed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Individual Service Endpoints (for debugging/testing)
@app.post("/enhance-query")
async def enhance_query(query: str):
    """Enhance a query (for testing)."""
    try:
        enhanced = await orchestrator.enhance_query(query)
        return enhanced
    except Exception as e:
        logger.error(f"Error enhancing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-response")
async def generate_response(enhanced_query: str, retrieved_docs: list):
    """Generate response (for testing)."""
    try:
        from shared.models import SearchResult, GenerationRequest
        
        # Convert dict results to SearchResult objects
        search_results = [
            SearchResult(**doc) if isinstance(doc, dict) else doc
            for doc in retrieved_docs
        ]
        
        generation_request = GenerationRequest(
            enhanced_query=enhanced_query,
            retrieved_docs=search_results
        )
        
        response = await orchestrator.generate_response(generation_request)
        return response
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)