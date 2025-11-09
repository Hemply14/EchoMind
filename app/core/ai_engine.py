# app/core/ai_engine.py
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime, timezone

from app.config import settings
from app.core.memory_store import SupabaseMemoryStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PrivacyFirstAI:
    def __init__(self):
        self.memory_store = SupabaseMemoryStore()
        self.embedding_model = None
        self.knn_model = None
        
        # Performance optimizations
        self._memory_cache = []
        self._embedding_cache = np.array([])
        self._pending_updates = 0
        self._last_full_update = datetime.now(timezone.utc)
        self._update_threshold = 10  # Update after 10 new memories
        
        # Enhanced features placeholder
        self.conversation_history = []
        self.user_profile = {
            "interests": set(),
            "topics_discussed": set(),
            "conversation_style": "friendly",
            "last_interaction": None
        }
        self.response_ratings = {}
        self.successful_responses = {}
        
        self._load_models()
        
    def _load_models(self):
        """Load embedding model and initialize ML components"""
        try:
            logger.info("Loading embedding model...")
            self.embedding_model = SentenceTransformer(
                settings.embedding_model, 
                cache_folder=str(settings.model_cache_dir)
            )
            logger.info("Embedding model loaded successfully")
            
            # Initialize KNN model
            self.knn_model = NearestNeighbors(
                n_neighbors=5,  # Get top 5 matches
                metric='cosine', 
                algorithm='brute'
            )
            
            # Load initial knowledge base
            self._update_knowledge_base()
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise
    
    def _update_knowledge_base(self, incremental=False):
        """Update knowledge base with optional incremental updates"""
        try:
            if incremental and self._embedding_cache.size > 0:
                # Incremental update - only add new memories
                all_memories = self.memory_store.get_active_memories()
                current_ids = {mem['id'] for mem in self._memory_cache}
                new_memories = [mem for mem in all_memories if mem['id'] not in current_ids]
                
                if new_memories:
                    new_texts = [mem['input_text'] for mem in new_memories]
                    new_embeddings = self.embedding_model.encode(new_texts)
                    
                    # Add to existing cache
                    if self._embedding_cache.size == 0:
                        self._embedding_cache = new_embeddings
                    else:
                        self._embedding_cache = np.vstack([self._embedding_cache, new_embeddings])
                    
                    self._memory_cache.extend(new_memories)
                    self.knn_model.fit(self._embedding_cache)
                    logger.info(f"Incrementally added {len(new_memories)} memories")
            else:
                # Full update
                memories = self.memory_store.get_active_memories()
                self._memory_cache = memories
                
                if memories:
                    texts = [mem['input_text'] for mem in memories]
                    self._embedding_cache = self.embedding_model.encode(texts)
                    self.knn_model.fit(self._embedding_cache)
                    logger.info(f"Knowledge base updated with {len(memories)} memories")
                else:
                    self._embedding_cache = np.array([])
                    
                self._last_full_update = datetime.now(timezone.utc)
                
            self._pending_updates = 0
            
        except Exception as e:
            logger.error(f"Error updating knowledge base: {e}")
            # Fall back to full update
            self._update_knowledge_base(incremental=False)
    
    def teach(self, input_text: str, output_text: str, context: str = None, 
              category: str = "general") -> Dict:
        """Teach the AI new knowledge with performance optimizations"""
        try:
            # Store in database first
            memory_id = self.memory_store.add_memory(
                input_text=input_text,
                output_text=output_text,
                context=context,
                category=category,
                embedding=None  # Don't store embedding in DB for now
            )
            
            # Incremental update instead of full rebuild
            self._pending_updates += 1
            
            # Update knowledge base if we've accumulated enough changes
            # or if it's been a while since last full update
            time_since_update = (datetime.now(timezone.utc) - self._last_full_update).total_seconds()
            if (self._pending_updates >= self._update_threshold or 
                time_since_update > 300):  # 5 minutes
                self._update_knowledge_base(incremental=True)
            
            logger.info(f"Taught new memory (ID: {memory_id}) - Pending updates: {self._pending_updates}")
            return {
                "status": "learned", 
                "memory_id": memory_id,
                "category": category,
                "pending_updates": self._pending_updates
            }
            
        except Exception as e:
            logger.error(f"Error teaching AI: {e}")
            return {"status": "error", "message": str(e)}
    
    def ask(self, query: str, threshold: float = None) -> Dict:
        """Query the AI with performance optimizations"""
        if threshold is None:
            threshold = settings.similarity_threshold
        
        try:
            # Apply any pending updates before querying
            if self._pending_updates > 0:
                self._update_knowledge_base(incremental=True)
            
            # First check rules
            rule_response = self._check_rules(query)
            if rule_response:
                return rule_response
            
            # Then check memories if we have any
            if len(self._memory_cache) > 0:
                memory_response = self._check_memories(query, threshold)
                if memory_response:
                    return memory_response
            
            return {
                "response": "I'm not sure how to respond to that. Could you teach me?",
                "confidence": 0.0,
                "source": "unknown"
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "response": "I encountered an error while processing your request.",
                "confidence": 0.0,
                "source": "error"
            }
    
    def _check_rules(self, query: str) -> Optional[Dict]:
        """Check if any rules match the query"""
        rules = self.memory_store.get_active_rules()
        
        for rule in rules:
            if rule['pattern'].lower() in query.lower():
                return {
                    "response": rule['action'],
                    "confidence": 1.0,
                    "source": "rule",
                    "rule_id": rule['id']
                }
        return None
    
    def _check_memories(self, query: str, threshold: float) -> Optional[Dict]:
        """Check memories with multiple candidate matches"""
        query_embedding = self.embedding_model.encode([query])
        
        if len(self._embedding_cache) > 0:
            # Get top 5 matches instead of just 1
            distances, indices = self.knn_model.kneighbors(query_embedding, n_neighbors=min(5, len(self._embedding_cache)))
            
            for i, (distance, index) in enumerate(zip(distances[0], indices[0])):
                similarity = 1 - distance
                memory = self._memory_cache[index]
                
                # Return best match above threshold
                if similarity > threshold:
                    return {
                        "response": memory['output_text'],
                        "confidence": float(similarity),
                        "source": "memory",
                        "memory_id": memory['id'],
                        "match_rank": i + 1  # Show which rank this match was
                    }
        
        return None
    
    def add_rule(self, pattern: str, action: str, priority: int = 1) -> Dict:
        """Add a behavior rule"""
        try:
            rule_id = self.memory_store.add_rule(pattern, action, priority)
            logger.info(f"Added new rule (ID: {rule_id})")
            return {"status": "rule_added", "rule_id": rule_id}
        except Exception as e:
            logger.error(f"Error adding rule: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_memories(self, category: str = None, limit: int = 100) -> List[Dict]:
        """Get memories with optional filtering"""
        return self.memory_store.get_active_memories(category, limit)
    
    def delete_memory(self, memory_id: int) -> Dict:
        """Delete a memory"""
        try:
            success = self.memory_store.delete_memory(memory_id)
            if success:
                # Force full update since we removed a memory
                self._update_knowledge_base(incremental=False)
                return {"status": "deleted", "memory_id": memory_id}
            else:
                return {"status": "error", "message": "Memory not found"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def force_update(self):
        """Force a full knowledge base update"""
        self._update_knowledge_base(incremental=False)
        return {"status": "updated", "memory_count": len(self._memory_cache)}
    
    def get_health(self) -> Dict:
        """Get system health information"""
        stats = self.memory_store.get_stats()
        return {
            "status": "healthy",
            "memory_count": stats['memory_count'],
            "rule_count": stats['rule_count'],
            "model_loaded": self.embedding_model is not None,
            "knowledge_base_ready": len(self._memory_cache) > 0,
            "cache_size": len(self._memory_cache),
            "pending_updates": self._pending_updates,
            "last_update": self._last_full_update.isoformat()
        }
    
    # Enhanced methods for compatibility
    def get_user_profile(self, user_id: str = "default") -> Dict:
        """Get user profile - enhanced version placeholder"""
        return {
            "interests": list(self.user_profile["interests"]),
            "topics_discussed": list(self.user_profile["topics_discussed"]),
            "conversation_count": len(self.conversation_history),
            "last_interaction": self.user_profile["last_interaction"],
            "conversation_style": self.user_profile["conversation_style"]
        }
    
    def learn_from_feedback(self, query: str, response: str, rating: int, user_comment: str = None):
        """Learn from feedback - enhanced version placeholder"""
        pass
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        return {
            "memory_cache_size": len(self._memory_cache),
            "embedding_cache_size": self._embedding_cache.shape[0] if self._embedding_cache.size > 0 else 0,
            "pending_updates": self._pending_updates,
            "last_full_update": self._last_full_update.isoformat(),
            "update_threshold": self._update_threshold,
            "conversation_history": len(self.conversation_history),
            "user_interests": len(self.user_profile["interests"]),
            "successful_responses": len(self.successful_responses),
            "total_feedback_ratings": sum(len(ratings) for ratings in self.response_ratings.values())
        }