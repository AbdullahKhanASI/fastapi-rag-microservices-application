from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.models import UploadFileResponse, HealthCheck, FileType
from shared.config import settings
from shared.utils import setup_logging, generate_id, sanitize_filename

from services.file_processor import FileProcessor
from services.embedding_service import EmbeddingService
from services.vector_store import VectorStore

app = FastAPI(title="Storage Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = setup_logging("storage-service")

# Initialize services
file_processor = FileProcessor()
embedding_service = EmbeddingService()
vector_store = VectorStore()


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    try:
        await vector_store.initialize()
        logger.info("Storage service started successfully")
    except Exception as e:
        logger.error(f"Failed to start storage service: {e}")
        raise


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    return HealthCheck(service="storage", status="healthy")


@app.post("/upload", response_model=UploadFileResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload and process a file."""
    try:
        # Validate file type
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in ['pdf', 'docx', 'txt', 'json']:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_extension}"
            )
        
        # Generate file ID and sanitize filename
        file_id = generate_id()
        safe_filename = sanitize_filename(file.filename)
        
        # Save uploaded file
        upload_path = os.path.join(settings.upload_dir, f"{file_id}_{safe_filename}")
        os.makedirs(settings.upload_dir, exist_ok=True)
        
        with open(upload_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process file
        text_content = await file_processor.extract_text(upload_path, FileType(file_extension))
        chunks = await file_processor.chunk_text(text_content, source_file=safe_filename)
        
        # Generate embeddings
        embeddings = await embedding_service.generate_embeddings([chunk.content for chunk in chunks])
        
        # Add embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding
        
        # Store in vector database
        await vector_store.store_chunks(chunks)
        
        logger.info(f"Successfully processed file {file.filename} with {len(chunks)} chunks")
        
        return UploadFileResponse(
            file_id=file_id,
            file_name=file.filename,
            chunks_count=len(chunks),
            status="success",
            message=f"File processed and stored successfully with {len(chunks)} chunks"
        )
        
    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """Delete a file and its chunks from the vector store."""
    try:
        await vector_store.delete_by_file_id(file_id)
        logger.info(f"Successfully deleted file {file_id}")
        return {"message": f"File {file_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting file {file_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/files")
async def list_files():
    """List all stored files."""
    try:
        files = await vector_store.list_files()
        return {"files": files}
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)