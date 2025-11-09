# app/core/enhanced_ai_engine.py
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Any
import logging

from app.core.ai_engine import PrivacyFirstAI
from app.core.web_searcher import AutoResearcher
from app.core.auto_learner import AutoLearner

logger = logging.getLogger(__name__)

class EnhancedPrivacyAI(PrivacyFirstAI):
    def __init__(self):
        super().__init__()
        
        # Conversation memory
        self.conversation_history = []
        self.user_profile = {
            "interests": set(),
            "topics_discussed": set(),
            "conversation_style": "friendly",
            "last_interaction": None
        }
        
        # Common sense knowledge base
        self.common_sense = self._load_common_sense()
        
        # Adaptive learning
        self.successful_responses = {}
        self.response_ratings = {}
        
        # Web research capability
        self.researcher = AutoResearcher(self.memory_store, self)
        self.research_topics = set()
        
        # Auto-learning capability
        self.auto_learner = AutoLearner(self)
    
    def _load_common_sense(self):
        """Load basic common sense rules"""
        return {
            "tired": ["Get some rest", "Take a break", "Drink water", "Sleep helps"],
            "stressed": ["Take deep breaths", "Break tasks into smaller pieces", "Prioritize"],
            "stuck": ["Take a walk", "Explain problem to someone", "Try different approach"],
            "happy": ["That's great!", "Celebrate small wins", "Share the joy"],
            "confused": ["Break it down step by step", "Ask for clarification", "Research basics"]
        }
    
    def ask_with_context(self, query: str, user_id: str = "default", threshold: float = None, 
                        enable_research: bool = False) -> Dict:
        """Enhanced ask with conversation memory and optional research"""
        # Update user profile
        self._update_user_profile(query, user_id)
        
        # 🔍 DISCOVER NEW TOPICS FROM CONVERSATION
        self.discover_topics_from_conversation(query)
        
        # First try to answer from existing knowledge
        base_response = super().ask(query, threshold)
        
        # If low confidence and research enabled, try to find information online
        if (enable_research and 
            base_response["confidence"] < 0.6 and 
            base_response["source"] == "unknown" and
            self._should_research(query)):
            
            logger.info(f"🔍 Research triggered for query: {query}")
            research_response = self._try_research_answer(query)
            if research_response and research_response.get("found", False):
                return research_response
        
        # Enhance with context and reasoning
        enhanced_response = self._enhance_response(query, base_response)
        
        # Store conversation
        self._store_conversation(user_id, query, enhanced_response)
        
        return enhanced_response
    
    def discover_topics_from_conversation(self, query: str):
        """Discover new learning topics from user conversations"""
        try:
            logger.info(f"🔍 Analyzing query for topic discovery: {query}")
            self.auto_learner.discover_topic_from_conversation(query)
            
            # Check if any topics reached threshold and need immediate research
            discovered_stats = self.auto_learner.get_learning_stats().get("discovery_stats", {})
            discovered_topics = discovered_stats.get("total_discovered", 0)
            
            if discovered_topics > 0:
                logger.info(f"📝 Currently tracking {discovered_topics} discovered topics")
                
        except Exception as e:
            logger.error(f"❌ Topic discovery failed: {e}")
    
    def _should_research(self, query: str) -> bool:
        """Determine if a query should trigger research"""
        # Don't research personal questions
        personal_keywords = ["you", "your", "i ", "my ", "me ", "us ", "we "]
        if any(keyword in query.lower() for keyword in personal_keywords):
            return False
        
        # Don't research very short queries
        if len(query.strip()) < 5:
            return False
        
        # Research factual questions
        research_keywords = [
            "what is", "how to", "why is", "when did", "where is", 
            "explain", "define", "tell me about", "information about",
            "who invented", "how does", "what are", "history of"
        ]
        if any(keyword in query.lower() for keyword in research_keywords):
            return True
        
        # Research questions with question marks
        if "?" in query:
            return True
        
        return len(query.split()) > 3  # Research longer queries
    
    def _try_research_answer(self, query: str) -> Optional[Dict]:
        """Try to answer by researching online"""
        try:
            logger.info(f"🔍 Researching query: {query}")
            
            # Use quick search for immediate answers
            search_result = self.researcher.quick_search(query)
            
            if search_result.get("found", False):
                logger.info(f"✅ Research found answer for: {query}")
                
                # Also learn this permanently if it's good
                if len(search_result["answer"]) > 50:  # Substantial answer
                    try:
                        self.memory_store.add_memory(
                            input_text=query,
                            output_text=search_result["answer"],
                            context=f"Researched from web: {', '.join(search_result['sources'])}",
                            category="researched_knowledge"
                        )
                        logger.debug("💾 Also saved research to permanent memory")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to save research to memory: {e}")
                
                return {
                    "response": search_result["answer"],
                    "confidence": search_result.get("confidence", 0.7),
                    "source": "web_research",
                    "research_used": True,
                    "sources": search_result["sources"],
                    "enhancement": "web_research"
                }
            else:
                logger.info(f"❌ Research found no answer for: {query}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Research failed for query '{query}': {e}")
            return None
    
    def research_topic(self, topic: str) -> Dict:
        """Research a topic and learn from it"""
        logger.info(f"🎯 Starting dedicated research on: {topic}")
        return self.researcher.research_and_learn(topic)
    
    # ===== AUTO-LEARNING METHODS =====
    
    def enable_auto_learning(self, comprehensive_knowledge: bool = True, 
                           current_events: bool = True,
                           fundamental_knowledge: bool = False,  # Deprecated - kept for compatibility
                           programming_skills: bool = False) -> Dict:  # Deprecated - kept for compatibility
        """Enable automatic learning from the internet with comprehensive knowledge"""
        logger.info("🚀 Enabling comprehensive auto-learning from internet")
        
        topics_added = 0
        
        if comprehensive_knowledge:
            self.auto_learner.learn_comprehensive_knowledge()
            topics_added = 207  # Total from your list: 40 + 30 + 40 + 30 + 60 + 7
            
        if current_events:
            self.auto_learner.learn_current_events()
            topics_added += 7
            
        # Legacy support for old parameters
        if fundamental_knowledge and not comprehensive_knowledge:
            self.auto_learner.learn_common_knowledge_base()
            topics_added += 15
            
        if programming_skills and not comprehensive_knowledge:
            self.auto_learner.learn_programming_skills()
            topics_added += 10
            
        success = self.auto_learner.start_continuous_learning()
        
        if success:
            return {
                "status": "auto_learning_enabled", 
                "message": f"AI will now automatically learn from the internet with {topics_added} topics across all categories!",
                "topics_added": topics_added,
                "comprehensive_knowledge": comprehensive_knowledge,
                "current_events": current_events,
                "categories": [
                    "Programming & Development (40 topics)",
                    "Pop Culture & Entertainment (30 topics)", 
                    "Science & Math (40 topics)",
                    "Lifestyle & Self-Improvement (30 topics)",
                    "Random/Fun/Miscellaneous (60 topics)",
                    "Current Events (7 topics)"
                ] if comprehensive_knowledge else ["Custom selection"]
            }
        else:
            return {
                "status": "auto_learning_already_running",
                "message": "Auto-learning is already enabled"
            }
        
    def disable_auto_learning(self) -> Dict:
        """Disable automatic learning"""
        self.auto_learner.stop_continuous_learning()
        return {
            "status": "auto_learning_disabled",
            "message": "Auto-learning has been stopped"
        }
        
    def add_auto_learning_topic(self, topic: str, interval_hours: int = 24) -> Dict:
        """Add a custom topic for auto-learning"""
        success = self.auto_learner.add_learning_topic(topic, interval_hours)
        if success:
            return {
                "status": "topic_added", 
                "topic": topic, 
                "interval_hours": interval_hours,
                "message": f"Topic '{topic}' will be researched every {interval_hours} hours"
            }
        else:
            return {
                "status": "invalid_topic",
                "topic": topic,
                "message": f"Topic '{topic}' is invalid or too short"
            }
        
    def remove_auto_learning_topic(self, topic: str) -> Dict:
        """Remove a topic from auto-learning"""
        self.auto_learner.remove_learning_topic(topic)
        return {
            "status": "topic_removed",
            "topic": topic,
            "message": f"Topic '{topic}' removed from auto-learning"
        }
        
    def get_auto_learning_topics(self) -> Dict:
        """Get list of current auto-learning topics"""
        topics = self.auto_learner.get_learning_topics()
        return {
            "status": "success",
            "topics": topics,
            "total_topics": len(topics)
        }
        
    def get_auto_learning_stats(self) -> Dict:
        """Get auto-learning statistics"""
        stats = self.auto_learner.get_learning_stats()
        return {
            "status": "success",
            "auto_learning": stats
        }
        
    def research_topic_now(self, topic: str) -> Dict:
        """Research a topic immediately"""
        result = self.auto_learner.research_topic_now(topic)
        return result
    
    def get_discovered_topics(self) -> Dict:
        """Get topics discovered from conversations"""
        stats = self.auto_learner.get_learning_stats()
        discovered_topics = stats.get("discovered_topics", [])
        discovery_stats = stats.get("discovery_stats", {})
        knowledge_categories = stats.get("knowledge_categories", {})
        
        return {
            "status": "success",
            "discovered_topics": discovered_topics,
            "discovery_stats": discovery_stats,
            "knowledge_categories": knowledge_categories
        }
    
    def _update_user_profile(self, query: str, user_id: str):
        """Learn about user from their queries"""
        interest_keywords = {
            "coding": ["code", "program", "debug", "function", "algorithm", "python", "javascript", "java", "c++", "html", "css"],
            "pop_culture": ["movie", "tv", "series", "anime", "marvel", "dc", "star wars", "harry potter", "game of thrones"],
            "science": ["science", "physics", "chemistry", "biology", "math", "quantum", "space", "astronomy", "neuroscience"],
            "gaming": ["game", "gaming", "playstation", "xbox", "nintendo", "steam", "esports", "rpg", "fps"],
            "fitness": ["workout", "exercise", "fitness", "gym", "boxing", "cardio", "strength", "diet", "nutrition"],
            "technology": ["ai", "machine learning", "computer", "tech", "software", "hardware", "robot", "vr", "ar"]
        }
        
        for interest, keywords in interest_keywords.items():
            if any(keyword in query.lower() for keyword in keywords):
                self.user_profile["interests"].add(interest)
                self.user_profile["topics_discussed"].add(interest)
        
        self.user_profile["last_interaction"] = datetime.now(timezone.utc)
    
    def _enhance_response(self, query: str, base_response: Dict) -> Dict:
        """Enhance response with reasoning and context"""
        response = base_response["response"]
        confidence = base_response["confidence"]
        
        # Add common sense for low-confidence responses
        if confidence < 0.7:
            enhanced_response = self._apply_common_sense(query, response)
            if enhanced_response != response:
                base_response["response"] = enhanced_response
                base_response["enhancement"] = "common_sense"
                base_response["confidence"] = min(confidence + 0.1, 0.9)
        
        # Personalize based on user interests
        personalized_response = self._personalize_response(query, base_response["response"])
        if personalized_response != base_response["response"]:
            base_response["response"] = personalized_response
            base_response["enhancement"] = "personalization"
        
        # Add conversation continuity
        if self.conversation_history:
            contextual_response = self._add_conversation_context(query, base_response["response"])
            if contextual_response != base_response["response"]:
                base_response["response"] = contextual_response
                if "enhancement" not in base_response:
                    base_response["enhancement"] = "context"
        
        return base_response
    
    def _apply_common_sense(self, query: str, response: str) -> str:
        """Apply common sense reasoning to responses"""
        query_lower = query.lower()
        
        for situation, advice_list in self.common_sense.items():
            if situation in query_lower:
                if not any(advice.lower() in response.lower() for advice in advice_list):
                    additional_advice = np.random.choice(advice_list)
                    return f"{response} Also, {additional_advice.lower()}"
        
        return response
    
    def _personalize_response(self, query: str, response: str) -> str:
        """Personalize responses based on user interests"""
        user_interests = self.user_profile["interests"]
        
        additions = []
        
        if "coding" in user_interests and any(word in query.lower() for word in ["stuck", "problem", "debug", "error", "code"]):
            additions.append("Sometimes taking a break and coming back with fresh eyes helps solve coding problems!")
        
        if "pop_culture" in user_interests and any(word in query.lower() for word in ["movie", "tv", "series", "anime"]):
            additions.append("I love discussing entertainment - there's always so much to explore!")
        
        if "science" in user_interests and any(word in query.lower() for word in ["science", "physics", "research", "discovery"]):
            additions.append("The wonders of science never cease to amaze me!")
        
        if "fitness" in user_interests and any(word in query.lower() for word in ["workout", "exercise", "fitness", "health"]):
            additions.append("Remember to stay hydrated during your workouts!")
        
        if additions:
            return f"{response} {np.random.choice(additions)}"
        
        return response
    
    def _add_conversation_context(self, query: str, response: str) -> str:
        """Add continuity to conversations"""
        if len(self.conversation_history) < 2:
            return response
        
        last_exchange = self.conversation_history[-1]
        last_topic_words = set(last_exchange["query"].lower().split())
        current_topic_words = set(query.lower().split())
        common_words = last_topic_words.intersection(current_topic_words)
        
        if len(common_words) > 2:
            continuity_phrases = [
                "Continuing from our chat...",
                "Building on what we discussed...",
                "Like I mentioned before...",
                "As we were talking about..."
            ]
            return f"{np.random.choice(continuity_phrases)} {response}"
        
        return response
    
    def _store_conversation(self, user_id: str, query: str, response: Dict):
        """Store conversation for context"""
        self.conversation_history.append({
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc),
            "query": query,
            "response": response["response"],
            "confidence": response["confidence"],
            "source": response["source"]
        })
        
        if len(self.conversation_history) > 20:
            self.conversation_history.pop(0)
    
    def learn_from_feedback(self, query: str, response: str, rating: int, user_comment: str = None):
        """Learn from explicit user feedback"""
        key = f"{query[:50]}_{response[:50]}"
        
        if key not in self.response_ratings:
            self.response_ratings[key] = []
        
        self.response_ratings[key].append({
            "rating": rating,
            "comment": user_comment,
            "timestamp": datetime.now(timezone.utc)
        })
    
    def get_user_profile(self, user_id: str = "default") -> Dict:
        """Get insights about the user"""
        user_conversations = [c for c in self.conversation_history if c["user_id"] == user_id]
        
        return {
            "interests": list(self.user_profile["interests"]),
            "topics_discussed": list(self.user_profile["topics_discussed"]),
            "conversation_count": len(user_conversations),
            "last_interaction": self.user_profile["last_interaction"],
            "conversation_style": self.user_profile["conversation_style"]
        }
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics without exposing private attributes"""
        auto_learning_stats = self.auto_learner.get_learning_stats()
        
        return {
            "memory_cache_size": len(self._memory_cache),
            "embedding_cache_size": self._embedding_cache.shape[0] if self._embedding_cache.size > 0 else 0,
            "pending_updates": self._pending_updates,
            "last_full_update": self._last_full_update.isoformat(),
            "update_threshold": self._update_threshold,
            "conversation_history": len(self.conversation_history),
            "user_interests": len(self.user_profile["interests"]),
            "successful_responses": len(self.successful_responses),
            "total_feedback_ratings": sum(len(ratings) for ratings in self.response_ratings.values()),
            "auto_learning": auto_learning_stats
        }