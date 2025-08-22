import re
import spacy
import openai
from typing import List, Dict, Any
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from shared.models import EnhancedQuery
from shared.config import settings


class QueryEnhancer:
    """Service for enhancing user queries for better retrieval."""
    
    def __init__(self):
        self.nlp = None
        self.openai_client = None
        self.intent_keywords = {
            "factual": ["what", "when", "where", "who", "which", "define", "explain"],
            "procedural": ["how", "steps", "process", "procedure", "method"],
            "comparative": ["compare", "difference", "versus", "vs", "better", "best"],
            "analytical": ["analyze", "analysis", "why", "reason", "cause", "effect"],
            "creative": ["generate", "create", "write", "compose", "design"],
            "troubleshooting": ["error", "problem", "issue", "fix", "solve", "troubleshoot"]
        }
    
    async def initialize(self):
        """Initialize NLP models and services."""
        try:
            # Load spaCy model
            self.nlp = spacy.load("en_core_web_sm")
            
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
            
            # Extract key entities and terms
            entities = self._extract_entities(cleaned_query)
            
            # Classify intent
            intent_result = await self.classify_intent(cleaned_query)
            intent = intent_result["intent"]
            confidence = intent_result["confidence"]
            
            # Generate expansion terms
            expansion_terms = await self.expand_query(cleaned_query)
            
            # Create enhanced query
            enhanced_query = await self._create_enhanced_query(
                cleaned_query, entities, expansion_terms, intent, context
            )
            
            return EnhancedQuery(
                original_query=query,
                enhanced_query=enhanced_query,
                expansion_terms=expansion_terms,
                intent=intent,
                confidence=confidence
            )
            
        except Exception as e:
            raise Exception(f"Error enhancing query: {e}")
    
    def _clean_query(self, query: str) -> str:
        """Clean and normalize the query."""
        # Remove extra whitespace
        query = re.sub(r'\s+', ' ', query.strip())
        
        # Remove common stop patterns for search
        stop_patterns = [
            r'^(can you|could you|please|help me|i want to|i need to)\s+',
            r'\?$',
            r'^(what is|what are|tell me about)\s+'
        ]
        
        for pattern in stop_patterns:
            query = re.sub(pattern, '', query, flags=re.IGNORECASE).strip()
        
        return query
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract named entities and important terms from the query."""
        if not self.nlp:
            return []
        
        doc = self.nlp(query)
        entities = []
        
        # Extract named entities
        for ent in doc.ents:
            entities.append(ent.text)
        
        # Extract important nouns and adjectives
        for token in doc:
            if (token.pos_ in ['NOUN', 'ADJ', 'PROPN'] and 
                len(token.text) > 2 and 
                not token.is_stop and 
                token.text.lower() not in [e.lower() for e in entities]):
                entities.append(token.text)
        
        return entities[:10]  # Limit to top 10 entities
    
    async def expand_query(self, query: str) -> List[str]:
        """Generate expansion terms for the query."""
        if self.openai_client:
            return await self._expand_with_llm(query)
        else:
            return await self._expand_with_nlp(query)
    
    async def _expand_with_llm(self, query: str) -> List[str]:
        """Use LLM to generate query expansion terms."""
        try:
            prompt = f"""
            Given the search query: "{query}"
            
            Generate 5-7 related terms, synonyms, or alternative phrasings that would help find relevant documents. 
            Focus on terms that maintain the same intent but use different vocabulary.
            
            Return only the terms, separated by commas, without explanations.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.3
            )
            
            expansion_text = response.choices[0].message.content.strip()
            expansion_terms = [term.strip() for term in expansion_text.split(',')]
            
            return expansion_terms[:7]
            
        except Exception as e:
            print(f"Error in LLM expansion: {e}")
            return await self._expand_with_nlp(query)
    
    async def _expand_with_nlp(self, query: str) -> List[str]:
        """Use NLP techniques to generate expansion terms."""
        if not self.nlp:
            return []
        
        doc = self.nlp(query)
        expansion_terms = []
        
        # Extract lemmas and related forms
        for token in doc:
            if token.pos_ in ['NOUN', 'VERB', 'ADJ'] and not token.is_stop:
                # Add lemma if different from original
                if token.lemma_ != token.text.lower():
                    expansion_terms.append(token.lemma_)
        
        # Simple synonym expansion (basic implementation)
        synonym_map = {
            "document": ["file", "paper", "text", "record"],
            "information": ["data", "details", "facts", "content"],
            "process": ["procedure", "method", "workflow", "steps"],
            "issue": ["problem", "challenge", "trouble", "difficulty"],
            "solution": ["answer", "resolution", "fix", "remedy"]
        }
        
        for word in doc:
            word_lower = word.text.lower()
            if word_lower in synonym_map:
                expansion_terms.extend(synonym_map[word_lower])
        
        return list(set(expansion_terms))[:7]
    
    async def classify_intent(self, query: str) -> Dict[str, Any]:
        """Classify the intent of the query."""
        query_lower = query.lower()
        intent_scores = {}
        
        # Calculate scores based on keyword matching
        for intent, keywords in self.intent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                intent_scores[intent] = score
        
        if not intent_scores:
            return {"intent": "general", "confidence": 0.5}
        
        # Get the intent with highest score
        best_intent = max(intent_scores, key=intent_scores.get)
        max_score = intent_scores[best_intent]
        
        # Calculate confidence (normalized by query length and keyword matches)
        confidence = min(0.9, max_score / (len(query.split()) + 1) + 0.3)
        
        return {
            "intent": best_intent,
            "confidence": confidence,
            "all_scores": intent_scores
        }
    
    async def _create_enhanced_query(
        self,
        original_query: str,
        entities: List[str],
        expansion_terms: List[str],
        intent: str,
        context: str
    ) -> str:
        """Create an enhanced version of the query."""
        enhanced_parts = [original_query]
        
        # Add important entities if not already in query
        for entity in entities[:3]:  # Limit to top 3 entities
            if entity.lower() not in original_query.lower():
                enhanced_parts.append(entity)
        
        # Add expansion terms selectively
        for term in expansion_terms[:3]:  # Limit to top 3 expansion terms
            if (term.lower() not in original_query.lower() and 
                term not in enhanced_parts):
                enhanced_parts.append(term)
        
        # Join with spaces
        enhanced_query = " ".join(enhanced_parts)
        
        return enhanced_query