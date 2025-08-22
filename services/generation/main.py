from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.models import GenerationRequest, GenerationResponse, HealthCheck
from shared.config import settings
from shared.utils import setup_logging

from services.response_generator import ResponseGenerator

app = FastAPI(title="Generation Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = setup_logging("generation-service")

# Initialize response generator
response_generator = ResponseGenerator()


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    try:
        await response_generator.initialize()
        logger.info("Generation service started successfully")
    except Exception as e:
        logger.error(f"Failed to start generation service: {e}")
        raise


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    return HealthCheck(service="generation", status="healthy")


@app.post("/generate", response_model=GenerationResponse)
async def generate_response(request: GenerationRequest):
    """Generate a response based on enhanced query and retrieved documents."""
    try:
        logger.info(f"Generating response for query: {request.enhanced_query}")
        
        response = await response_generator.generate_response(
            enhanced_query=request.enhanced_query,
            retrieved_docs=request.retrieved_docs,
            conversation_history=request.conversation_history,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        logger.info("Response generated successfully")
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/summarize")
async def summarize_documents(request: GenerationRequest):
    """Summarize the retrieved documents."""
    try:
        logger.info("Summarizing retrieved documents")
        
        summary = await response_generator.summarize_documents(
            retrieved_docs=request.retrieved_docs,
            max_tokens=request.max_tokens
        )
        
        return {"summary": summary}
        
    except Exception as e:
        logger.error(f"Error summarizing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)