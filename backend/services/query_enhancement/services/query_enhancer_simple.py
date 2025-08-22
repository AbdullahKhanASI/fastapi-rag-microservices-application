import re
import openai
from typing import List, Dict, Any
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from shared.models import EnhancedQuery
from shared.config import settings


class QueryEnhancer:
    """Service for enhancing user queries for better retrieval (without spaCy)."""
    
    def __init__(self):
        self.openai_client = None
        self.intent_keywords = {
            "factual": ["what", "when", "where", "who", "which", "define", "explain"],
            "procedural": ["how", "steps", "process", "procedure", "method"],
            "comparative": ["compare", "difference", "versus", "vs", "better", "best", "comparison"],
            "analytical": ["analyze", "analysis", "why", "reason", "cause", "effect"],
            "creative": ["generate", "create", "write", "compose", "design"],
            "troubleshooting": ["error", "problem", "issue", "fix", "solve", "troubleshoot"]
        }
        
        # Expansion mappings
        self.expansions_map = {
            "lora": ["low-rank adaptation", "parameter efficient fine-tuning", "PEFT"],
            "llm": ["large language model", "language model", "neural language model"],
            "ai": ["artificial intelligence", "machine learning", "ML"],
            "model": ["neural network", "algorithm", "system"],
            "tuning": ["fine-tuning", "adaptation", "training", "optimization"],
            "frontier": ["advanced", "cutting-edge", "state-of-the-art", "latest"],
            "capabilities": ["features", "abilities", "functions", "performance"],
            "generation": ["text generation", "content creation", "synthesis"],
            "parameter": ["weight", "variable", "coefficient"],
            "efficient": ["optimized", "effective", "streamlined"]
        }
    
    async def initialize(self):
        """Initialize services (without spaCy)."""
        try:
            # Initialize OpenAI client if API key is available
            if settings.openai_api_key:
                self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
                
        except Exception as e:
            raise Exception(f"Error initializing query enhancer: {e}")
    
    async def enhance_query(self, query: str, context: str = "") -> EnhancedQuery:
        """Enhance a user query for better retrieval."""
        try:
            # Clean and preprocess the query
            cleaned_query = self._clean_query(query)
            
            # Extract key entities and terms (simple version)
            entities = self._extract_entities_simple(cleaned_query)
            
            # Classify intent
            intent = self._classify_intent(cleaned_query)
            
            # Generate query expansions
            expansions = self._expand_query_terms(cleaned_query)
            
            # Create enhanced search terms
            enhanced_terms = self._create_enhanced_terms(cleaned_query, expansions)
            
            return EnhancedQuery(
                original_query=query,
                enhanced_query=f"{cleaned_query} {' '.join(enhanced_terms[:3])}",
                expansion_terms=enhanced_terms,
                intent=intent,
                confidence=0.85  # Default confidence score
            )
            
        except Exception as e:
            # Fallback to basic enhancement
            return EnhancedQuery(
                original_query=query,
                enhanced_query=query.strip(),
                expansion_terms=[],
                intent="factual",
                confidence=0.5
            )
    
    def _clean_query(self, query: str) -> str:
        """Clean and normalize the query."""
        # Remove extra whitespace
        query = ' '.join(query.split())
        
        # Remove common punctuation but preserve important ones
        query = re.sub(r'[^\w\s\-\']', ' ', query)
        
        # Normalize spacing
        query = ' '.join(query.split())
        
        return query.strip()
    
    def _extract_entities_simple(self, query: str) -> List[str]:
        """Simple entity extraction without spaCy."""
        entities = []
        query_lower = query.lower()
        
        # Look for capitalized words (potential entities)
        words = query.split()
        for word in words:
            if len(word) > 2 and word[0].isupper():
                entities.append(word)
        
        # Look for known technical terms
        technical_terms = ["LoRA", "AI", "ML", "LLM", "GPT", "BERT", "API", "NLP"]
        for term in technical_terms:
            if term.lower() in query_lower:
                entities.append(term)
        
        return list(set(entities))
    
    def _classify_intent(self, query: str) -> str:
        """Classify the query intent based on keywords."""
        query_lower = query.lower()
        
        # Count keyword matches for each intent
        scores = {}
        for intent, keywords in self.intent_keywords.items():
            scores[intent] = sum(1 for keyword in keywords if keyword in query_lower)
        
        # Return intent with highest score, default to factual
        if max(scores.values()) == 0:
            return "factual"
        
        return max(scores, key=scores.get)
    
    def _expand_query_terms(self, query: str) -> List[str]:
        """Generate query expansions."""
        expansions = []
        query_lower = query.lower()
        
        # Find expansions from mapping
        for key, values in self.expansions_map.items():
            if key in query_lower:
                expansions.extend([v for v in values if v not in query_lower])
        
        return list(set(expansions))
    
    def _create_enhanced_terms(self, query: str, expansions: List[str]) -> List[str]:
        """Create enhanced terms for search optimization."""
        enhanced = []
        
        # Add top expansions
        enhanced.extend(expansions[:5])
        
        # Add query words that are longer than 3 characters
        query_words = [word for word in query.split() if len(word) > 3]
        enhanced.extend(query_words[:3])
        
        return list(set(enhanced))
    
    async def expand_query(self, query: str) -> List[str]:
        """Generate query expansions."""
        return self._expand_query_terms(query)
    
    async def classify_intent(self, query: str) -> str:
        """Classify query intent."""
        return self._classify_intent(query)