from typing import List, Dict, Any, Optional
import openai
import tiktoken
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from shared.models import SearchResult, GenerationResponse
from shared.config import settings


class ResponseGenerator:
    """Service for generating responses using OpenAI."""
    
    def __init__(self):
        self.openai_client = None
        self.tokenizer = None
        
    async def initialize(self):
        """Initialize OpenAI client."""
        try:
            if settings.openai_api_key:
                self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
                try:
                    self.tokenizer = tiktoken.encoding_for_model(settings.llm_model)
                except KeyError:
                    # Fallback to cl100k_base encoding for newer models
                    self.tokenizer = tiktoken.get_encoding("cl100k_base")
            else:
                raise Exception("OpenAI API key is required")
                
        except Exception as e:
            raise Exception(f"Error initializing response generator: {e}")
    
    async def generate_response(
        self,
        enhanced_query: str,
        retrieved_docs: List[SearchResult],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> GenerationResponse:
        """Generate a response based on the enhanced query and retrieved documents."""
        try:
            # Prepare context from retrieved documents
            context = self._prepare_context(retrieved_docs)
            
            # Build the prompt
            prompt = self._build_prompt(enhanced_query, context, conversation_history)
            
            # Generate response using OpenAI
            if self.openai_client:
                response_text, token_usage = await self._generate_with_openai(
                    prompt, max_tokens, temperature
                )
            else:
                raise Exception("OpenAI client not initialized")
            
            # Extract source files (filter out empty sources)
            sources = list(set(doc.source_file for doc in retrieved_docs if doc.source_file.strip()))
            
            # Calculate confidence based on retrieved document scores
            confidence = self._calculate_confidence(retrieved_docs)
            
            return GenerationResponse(
                query=enhanced_query,
                response=response_text,
                sources=sources,
                confidence=confidence,
                token_usage=token_usage
            )
            
        except Exception as e:
            raise Exception(f"Error generating response: {e}")
    
    def _prepare_context(self, retrieved_docs: List[SearchResult]) -> str:
        """Prepare context from retrieved documents."""
        if not retrieved_docs:
            return "No relevant documents found."
        
        context_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            context_parts.append(
                f"Document {i} (Score: {doc.score:.3f}):\n{doc.content}\n"
            )
        
        return "\n".join(context_parts)
    
    def _build_prompt(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Build the prompt for the LLM."""
        system_prompt = """You are a helpful assistant that answers questions based on provided context documents. 

Instructions:
1. Use only the information from the provided context documents to answer the question
2. If the context doesn't contain enough information to answer the question, say so clearly
3. Cite specific documents when making claims (e.g., "According to Document 1...")
4. Be concise but comprehensive in your response
5. If multiple documents contain conflicting information, acknowledge this and present both views
6. Do not make up information that isn't in the context"""

        user_prompt = f"""Context Documents:
{context}

Question: {query}

Please provide a helpful and accurate answer based on the context documents above."""

        if conversation_history:
            history_text = "\n".join([
                f"Human: {msg.get('human', '')}\nAssistant: {msg.get('assistant', '')}"
                for msg in conversation_history[-3:]  # Include last 3 exchanges
            ])
            user_prompt = f"Conversation History:\n{history_text}\n\n{user_prompt}"
        
        return f"{system_prompt}\n\n{user_prompt}"
    
    async def _generate_with_openai(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> tuple[str, Dict[str, int]]:
        """Generate response using OpenAI."""
        try:
            response = self.openai_client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            response_text = response.choices[0].message.content
            token_usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            return response_text, token_usage
            
        except Exception as e:
            raise Exception(f"Error with OpenAI generation: {e}")
    
    
    def _calculate_confidence(self, retrieved_docs: List[SearchResult]) -> float:
        """Calculate confidence score based on retrieved document scores."""
        if not retrieved_docs:
            return 0.0
        
        # Use the average score of top documents as confidence
        top_scores = [doc.score for doc in retrieved_docs[:3]]  # Top 3 documents
        avg_score = sum(top_scores) / len(top_scores)
        
        # Normalize to 0-1 range (assuming scores are already normalized)
        confidence = min(0.95, max(0.1, avg_score))
        
        return confidence
    
    async def summarize_documents(
        self,
        retrieved_docs: List[SearchResult],
        max_tokens: int = 500
    ) -> str:
        """Generate a summary of the retrieved documents."""
        try:
            if not retrieved_docs:
                return "No documents to summarize."
            
            context = self._prepare_context(retrieved_docs)
            
            prompt = f"""Please provide a concise summary of the following documents:

{context}

Summary:"""
            
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=settings.llm_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0.3
                )
                return response.choices[0].message.content
            else:
                return "OpenAI client not available for summarization."
                
        except Exception as e:
            raise Exception(f"Error summarizing documents: {e}")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Rough estimation: 4 characters per token
            return len(text) // 4