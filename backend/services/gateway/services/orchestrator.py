import aiohttp
from typing import Dict, Any, List
from datetime import datetime
from fastapi import UploadFile
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from shared.models import (
    ChatRequest, ChatResponse, SearchQuery, RetrievalResponse,
    GenerationRequest, GenerationResponse, UploadFileResponse,
    EnhancedQuery, SearchResult
)
from shared.config import settings
from shared.utils import generate_id, make_http_request


class RAGOrchestrator:
    """Orchestrates the RAG pipeline by coordinating all microservices."""
    
    def __init__(self):
        self.storage_url = settings.storage_service_url
        self.retriever_url = settings.retriever_service_url
        self.query_enhancement_url = settings.query_enhancement_service_url
        self.generation_url = settings.generation_service_url
        
        # Store conversation sessions (in production, use Redis or database)
        self.conversations = {}
    
    async def initialize(self):
        """Initialize the orchestrator."""
        pass
    
    async def check_all_services_health(self) -> Dict[str, Any]:
        """Check health status of all services."""
        services = {
            "storage": f"{self.storage_url}/health",
            "retriever": f"{self.retriever_url}/health",
            "query_enhancement": f"{self.query_enhancement_url}/health",
            "generation": f"{self.generation_url}/health"
        }
        
        health_status = {"gateway": "healthy", "services": {}}
        
        async with aiohttp.ClientSession() as session:
            for service_name, health_url in services.items():
                try:
                    async with session.get(health_url, timeout=5) as response:
                        if response.status == 200:
                            health_status["services"][service_name] = "healthy"
                        else:
                            health_status["services"][service_name] = "unhealthy"
                except Exception:
                    health_status["services"][service_name] = "unreachable"
        
        return health_status
    
    async def upload_file(self, file: UploadFile) -> UploadFileResponse:
        """Upload file to storage service."""
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('file', await file.read(), filename=file.filename)
            
            async with session.post(f"{self.storage_url}/upload", data=data) as response:
                response.raise_for_status()
                result = await response.json()
                return UploadFileResponse(**result)
    
    async def delete_file(self, file_id: str) -> Dict[str, Any]:
        """Delete file from storage service."""
        return await make_http_request(
            f"{self.storage_url}/files/{file_id}",
            method="DELETE"
        )
    
    async def list_files(self) -> Dict[str, Any]:
        """List files from storage service."""
        return await make_http_request(f"{self.storage_url}/files")
    
    async def enhance_query(self, query: str, context: str = "") -> EnhancedQuery:
        """Enhance query using query enhancement service."""
        data = {"query": query, "context": context}
        result = await make_http_request(
            f"{self.query_enhancement_url}/enhance",
            method="POST",
            json_data=data
        )
        return EnhancedQuery(**result)
    
    async def search_documents(self, query: SearchQuery) -> RetrievalResponse:
        """Search documents using retriever service."""
        result = await make_http_request(
            f"{self.retriever_url}/search",
            method="POST",
            json_data=query.dict()
        )
        return RetrievalResponse(**result)
    
    async def generate_response(self, request: GenerationRequest) -> GenerationResponse:
        """Generate response using generation service."""
        result = await make_http_request(
            f"{self.generation_url}/generate",
            method="POST",
            json_data=request.dict()
        )
        return GenerationResponse(**result)
    
    async def process_chat_message(self, request: ChatRequest) -> ChatResponse:
        """Process a complete chat message through the RAG pipeline."""
        try:
            # Generate conversation ID if not provided
            conversation_id = request.conversation_id or generate_id()
            
            # Get or create conversation history
            conversation_history = self.conversations.get(conversation_id, [])
            
            # Step 1: Enhance the query
            enhanced_query = await self.enhance_query(request.message)
            
            # Step 2: Search for relevant documents
            search_query = SearchQuery(
                query=enhanced_query.enhanced_query,
                top_k=getattr(request, 'retrieval_params', None) and getattr(request.retrieval_params, 'top_k', None) or request.top_k,
                threshold=getattr(request, 'retrieval_params', None) and getattr(request.retrieval_params, 'threshold', None) or 0.1
            )
            retrieval_response = await self.search_documents(search_query)
            
            # Step 3: Generate response
            generation_request = GenerationRequest(
                enhanced_query=enhanced_query.enhanced_query,
                retrieved_docs=retrieval_response.results,
                conversation_history=conversation_history,
                temperature=getattr(request, 'generation_params', None) and getattr(request.generation_params, 'temperature', None) or request.temperature,
                max_tokens=getattr(request, 'generation_params', None) and getattr(request.generation_params, 'max_tokens', None) or 1000
            )
            generation_response = await self.generate_response(generation_request)
            
            # Step 4: Update conversation history
            conversation_history.append({
                "human": request.message,
                "assistant": generation_response.response
            })
            
            # Keep only last 5 exchanges to manage memory
            if len(conversation_history) > 5:
                conversation_history = conversation_history[-5:]
            
            self.conversations[conversation_id] = conversation_history
            
            # Step 5: Return chat response
            return ChatResponse(
                conversation_id=conversation_id,
                response=generation_response.response,
                sources=generation_response.sources,
                confidence=generation_response.confidence,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            raise Exception(f"Error in RAG pipeline: {e}")
    
    async def get_conversation_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a given conversation ID."""
        return self.conversations.get(conversation_id, [])
    
    async def clear_conversation(self, conversation_id: str) -> Dict[str, str]:
        """Clear conversation history for a given conversation ID."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return {"message": f"Conversation {conversation_id} cleared successfully"}
        else:
            return {"message": f"Conversation {conversation_id} not found"}
    
    async def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """Get a summary of the conversation."""
        history = self.conversations.get(conversation_id, [])
        
        if not history:
            return {"conversation_id": conversation_id, "message_count": 0, "summary": "No messages"}
        
        message_count = len(history)
        last_message_time = datetime.now()  # In a real implementation, store timestamps
        
        return {
            "conversation_id": conversation_id,
            "message_count": message_count,
            "last_activity": last_message_time.isoformat(),
            "summary": f"Conversation with {message_count} message exchanges"
        }