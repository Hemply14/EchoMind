# app/main.py
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from typing import Optional, List

from app.core.enhanced_ai_engine import EnhancedPrivacyAI
from app.models.schemas import (
    TeachRequest, AskRequest, RuleRequest, ResearchRequest,
    FeedbackRequest, AskContextRequest,
    AIResponse, HealthResponse, PerformanceResponse,
    UserProfileResponse, ConversationHistoryResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Privacy-First AI API",
    description="Fully offline, privacy-first AI assistant with web research and comprehensive auto-learning capabilities",
    version="2.3.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize enhanced AI engine
ai_engine = EnhancedPrivacyAI()

@app.on_event("startup")
async def startup_event():
    """Initialize the AI engine on startup"""
    logger.info("🚀 Enhanced Privacy-First AI starting up...")
    try:
        # Health check to ensure everything is loaded
        health = ai_engine.get_health()
        logger.info(f"✅ AI Engine initialized successfully")
        logger.info(f"📊 Initial stats: {health['memory_count']} memories, {health['rule_count']} rules")
        
        # 🎯 START COMPREHENSIVE AUTO-LEARNING
        auto_learning_result = ai_engine.enable_auto_learning(
            comprehensive_knowledge=True,  # This loads ALL 200+ topics!
            current_events=True
        )
        logger.info(f"🌐 {auto_learning_result['message']}")
        logger.info("📚 Loading MASSIVE knowledge base with 200+ topics across all categories!")
        
        # Log the categories being loaded
        categories = auto_learning_result.get('categories', [])
        for category in categories:
            logger.info(f"   📖 {category}")
            
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Enhanced Privacy-First AI shutting down...")
    # Stop auto-learning gracefully
    ai_engine.disable_auto_learning()

# ===== CORE AI ENDPOINTS =====

@app.post("/teach", response_model=dict)
async def teach_endpoint(request: TeachRequest):
    """
    Teach the AI new knowledge
    
    - **input_text**: The question or input pattern
    - **output_text**: The desired response  
    - **context**: Optional context for the memory
    - **category**: Category for organization
    """
    try:
        logger.info(f"📚 Teaching new memory: {request.input_text[:50]}...")
        
        result = ai_engine.teach(
            input_text=request.input_text,
            output_text=request.output_text,
            context=request.context,
            category=request.category
        )
        
        logger.info(f"✅ Successfully taught memory ID: {result.get('memory_id')}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error in /teach: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Teaching failed: {str(e)}"
        )

@app.post("/ask", response_model=AIResponse)
async def ask_endpoint(request: AskRequest):
    """
    Query the AI based on learned knowledge
    
    - **query**: The question to ask
    - **threshold**: Similarity threshold (0.0-1.0)
    """
    try:
        logger.info(f"🤔 Asking: {request.query[:50]}...")
        
        response = ai_engine.ask(request.query, request.threshold)
        
        logger.info(f"✅ Response confidence: {response['confidence']:.2f}, source: {response['source']}")
        return AIResponse(**response)
        
    except Exception as e:
        logger.error(f"❌ Error in /ask: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )

@app.post("/rules", response_model=dict)
async def add_rule_endpoint(request: RuleRequest):
    """
    Add a behavior rule
    
    - **pattern**: Text pattern to match
    - **action**: Response when pattern matches
    - **priority**: Rule priority (1-10)
    """
    try:
        logger.info(f"📝 Adding rule: {request.pattern[:50]}...")
        
        result = ai_engine.add_rule(
            pattern=request.pattern,
            action=request.action,
            priority=request.priority
        )
        
        logger.info(f"✅ Rule added with ID: {result.get('rule_id')}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error in /rules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rule addition failed: {str(e)}"
        )

# ===== ENHANCED ENDPOINTS =====

@app.post("/ask-context", response_model=AIResponse)
async def ask_with_context_endpoint(request: AskContextRequest):
    """
    Ask with conversation context and optional web research
    
    - **query**: The question to ask
    - **user_id**: User identifier for conversation tracking
    - **threshold**: Similarity threshold (0.0-1.0) 
    - **enable_research**: Whether to search online for unknown topics
    """
    try:
        logger.info(f"🧠 Contextual ask from {request.user_id}: {request.query[:50]}...")
        logger.info(f"🔍 Research enabled: {request.enable_research}")
        
        response = ai_engine.ask_with_context(
            query=request.query, 
            user_id=request.user_id, 
            threshold=request.threshold, 
            enable_research=request.enable_research
        )
        
        enhancement = response.get('enhancement', 'none')
        logger.info(f"✅ Response enhanced with: {enhancement}, confidence: {response['confidence']:.2f}")
        
        return AIResponse(**response)
        
    except Exception as e:
        logger.error(f"❌ Error in /ask-context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Contextual query failed: {str(e)}"
        )

@app.post("/research", response_model=dict)
async def research_endpoint(request: ResearchRequest):
    """
    Research a topic online and learn from it
    
    - **topic**: The topic to research
    - **depth**: Research depth (basic/comprehensive)
    """
    try:
        logger.info(f"🔬 Researching topic: {request.topic}")
        
        result = ai_engine.research_topic(request.topic)
        
        if result["status"] == "success":
            logger.info(f"✅ Research successful: {result['learned_items']} items learned")
        else:
            logger.warning(f"⚠️ Research completed with status: {result['status']}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error in /research: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Research failed: {str(e)}"
        )

# ===== AUTO-LEARNING ENDPOINTS =====

@app.post("/auto-learning/enable", response_model=dict)
async def enable_auto_learning_endpoint(
    comprehensive_knowledge: bool = True,
    current_events: bool = True,
    fundamental_knowledge: bool = False,  # Legacy parameter
    programming_skills: bool = False      # Legacy parameter
):
    """
    Enable automatic learning from the internet
    
    - **comprehensive_knowledge**: Learn ALL categories (200+ topics)
    - **current_events**: Learn about recent developments
    - **fundamental_knowledge**: Legacy - use comprehensive_knowledge instead
    - **programming_skills**: Legacy - use comprehensive_knowledge instead
    """
    try:
        logger.info("🚀 Enabling comprehensive auto-learning via API")
        
        result = ai_engine.enable_auto_learning(
            comprehensive_knowledge=comprehensive_knowledge,
            current_events=current_events,
            fundamental_knowledge=fundamental_knowledge,
            programming_skills=programming_skills
        )
        
        logger.info(f"✅ {result['message']}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error enabling auto-learning: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Auto-learning enable failed: {str(e)}"
        )

@app.post("/auto-learning/disable", response_model=dict)
async def disable_auto_learning_endpoint():
    """Disable automatic learning"""
    try:
        logger.info("🛑 Disabling auto-learning via API")
        
        result = ai_engine.disable_auto_learning()
        
        logger.info(f"✅ {result['message']}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error disabling auto-learning: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Auto-learning disable failed: {str(e)}"
        )

@app.post("/auto-learning/topics", response_model=dict)
async def add_auto_learning_topic_endpoint(topic: str, interval_hours: int = 24):
    """
    Add a custom topic for auto-learning
    
    - **topic**: Topic to research automatically
    - **interval_hours**: How often to research (default: 24 hours)
    """
    try:
        logger.info(f"📚 Adding auto-learning topic: {topic} (every {interval_hours}h)")
        
        result = ai_engine.add_auto_learning_topic(topic, interval_hours)
        
        logger.info(f"✅ {result['message']}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error adding auto-learning topic: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Add auto-learning topic failed: {str(e)}"
        )

@app.delete("/auto-learning/topics/{topic}", response_model=dict)
async def remove_auto_learning_topic_endpoint(topic: str):
    """
    Remove a topic from auto-learning
    
    - **topic**: Topic to remove
    """
    try:
        logger.info(f"🗑️ Removing auto-learning topic: {topic}")
        
        result = ai_engine.remove_auto_learning_topic(topic)
        
        logger.info(f"✅ {result['message']}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error removing auto-learning topic: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Remove auto-learning topic failed: {str(e)}"
        )

@app.get("/auto-learning/topics", response_model=dict)
async def get_auto_learning_topics_endpoint():
    """Get all auto-learning topics"""
    try:
        logger.info("📖 Getting auto-learning topics")
        
        result = ai_engine.get_auto_learning_topics()
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error getting auto-learning topics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Get auto-learning topics failed: {str(e)}"
        )

@app.get("/auto-learning/stats", response_model=dict)
async def get_auto_learning_stats_endpoint():
    """Get auto-learning statistics"""
    try:
        logger.info("📊 Getting auto-learning stats")
        
        result = ai_engine.get_auto_learning_stats()
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error getting auto-learning stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Get auto-learning stats failed: {str(e)}"
        )

@app.post("/auto-learning/research-now", response_model=dict)
async def research_topic_now_endpoint(topic: str):
    """
    Research a topic immediately
    
    - **topic**: Topic to research now
    """
    try:
        logger.info(f"🎯 Immediate research requested for: {topic}")
        
        result = ai_engine.research_topic_now(topic)
        
        if result["status"] == "success":
            logger.info(f"✅ Immediate research successful: {result['learned_items']} items learned")
        else:
            logger.warning(f"⚠️ Immediate research completed with status: {result['status']}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error in immediate research: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Immediate research failed: {str(e)}"
        )

# ===== DYNAMIC TOPIC DISCOVERY ENDPOINTS =====

@app.get("/auto-learning/discovered-topics", response_model=dict)
async def get_discovered_topics_endpoint():
    """Get topics discovered from conversations"""
    try:
        logger.info("🔍 Getting discovered topics")
        
        result = ai_engine.get_discovered_topics()
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error getting discovered topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auto-learning/discover-from-query", response_model=dict)
async def discover_topics_from_query_endpoint(query: str):
    """
    Manually discover topics from a query
    
    - **query**: Query to analyze for topic discovery
    """
    try:
        logger.info(f"🔍 Manually discovering topics from query: {query}")
        
        ai_engine.discover_topics_from_conversation(query)
        
        stats = ai_engine.get_auto_learning_stats()
        discovered_count = stats.get("auto_learning", {}).get("discovery_stats", {}).get("total_discovered", 0)
        
        return {
            "status": "success",
            "message": f"Discovered topics from query. Now tracking {discovered_count} topics.",
            "query_analyzed": query
        }
        
    except Exception as e:
        logger.error(f"❌ Error discovering topics from query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback", response_model=dict)
async def submit_feedback_endpoint(request: FeedbackRequest):
    """
    Submit feedback to help AI learn
    
    - **query**: Original user query
    - **response**: AI response that was given
    - **rating**: Rating 1-5 (1=bad, 5=excellent)
    - **comment**: Optional comment explaining the rating
    """
    try:
        if not 1 <= request.rating <= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rating must be between 1-5"
            )
        
        logger.info(f"⭐ Feedback received: rating {request.rating} for query: {request.query[:50]}...")
        
        ai_engine.learn_from_feedback(request.query, request.response, request.rating, request.comment)
        
        return {
            "status": "feedback_received", 
            "message": "Thank you for the feedback! This helps me learn and improve.",
            "rating_received": request.rating
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in /feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feedback submission failed: {str(e)}"
        )

# ===== DATA MANAGEMENT ENDPOINTS =====

@app.get("/memories", response_model=list)
async def get_memories_endpoint(
    category: Optional[str] = None, 
    limit: int = 100
):
    """
    Get memories with optional filtering
    
    - **category**: Filter by category
    - **limit**: Maximum number of memories to return
    """
    try:
        logger.info(f"📖 Fetching memories (category: {category}, limit: {limit})")
        
        memories = ai_engine.get_memories(category, limit)
        
        logger.info(f"✅ Retrieved {len(memories)} memories")
        return memories
        
    except Exception as e:
        logger.error(f"❌ Error in /memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve memories: {str(e)}"
        )

@app.delete("/memories/{memory_id}", response_model=dict)
async def delete_memory_endpoint(memory_id: int):
    """
    Delete a specific memory
    
    - **memory_id**: ID of the memory to delete
    """
    try:
        logger.info(f"🗑️ Deleting memory ID: {memory_id}")
        
        result = ai_engine.delete_memory(memory_id)
        
        if result["status"] == "deleted":
            logger.info(f"✅ Memory {memory_id} deleted successfully")
        else:
            logger.warning(f"⚠️ Memory deletion failed: {result.get('message')}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error deleting memory {memory_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete memory: {str(e)}"
        )

# ===== SYSTEM & MONITORING ENDPOINTS =====

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Get system health information"""
    try:
        health = ai_engine.get_health()
        logger.debug(f"Health check: {health['status']}")
        return HealthResponse(**health)
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service unhealthy"
        )

@app.get("/performance", response_model=PerformanceResponse)
async def performance_stats():
    """Get performance statistics and system metrics"""
    try:
        stats = ai_engine.get_performance_stats()
        logger.debug("Performance stats retrieved")
        return PerformanceResponse(**stats)
        
    except Exception as e:
        logger.error(f"❌ Error getting performance stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user-profile", response_model=UserProfileResponse)
async def get_user_profile(user_id: str = "default"):
    """Get user profile and conversation insights"""
    try:
        profile = ai_engine.get_user_profile(user_id)
        logger.info(f"📊 User profile retrieved for {user_id}")
        return UserProfileResponse(**profile)
        
    except Exception as e:
        logger.error(f"❌ Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversation-history", response_model=ConversationHistoryResponse)
async def get_conversation_history(limit: int = 10):
    """Get recent conversation history"""
    try:
        history = ai_engine.conversation_history[-limit:]
        logger.info(f"💬 Retrieved {len(history)} conversation entries")
        return ConversationHistoryResponse(conversations=history)
        
    except Exception as e:
        logger.error(f"❌ Error getting conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/force-update", response_model=dict)
async def force_update():
    """Force a complete knowledge base update"""
    try:
        logger.info("🔄 Forcing knowledge base update...")
        
        result = ai_engine.force_update()
        
        logger.info(f"✅ Knowledge base updated: {result['memory_count']} memories loaded")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error forcing update: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== UTILITY ENDPOINTS =====

@app.get("/")
async def root():
    """Root endpoint with API information"""
    auto_learning_stats = ai_engine.get_auto_learning_stats()
    discovered_topics = ai_engine.get_discovered_topics()
    
    knowledge_categories = discovered_topics.get("knowledge_categories", {})
    
    return {
        "message": "🤖 Super AI - Comprehensive Knowledge Assistant", 
        "status": "running",
        "version": "2.3.0",
        "features": [
            "web_research", 
            "conversation_memory", 
            "user_profiling",
            "adaptive_learning",
            "feedback_system",
            "comprehensive_auto_learning",
            "dynamic_topic_discovery"
        ],
        "endpoints": {
            "chat": "/ask, /ask-context",
            "learning": "/teach, /research", 
            "auto_learning": "/auto-learning/*",
            "topic_discovery": "/auto-learning/discovered-topics, /auto-learning/discover-from-query",
            "management": "/memories, /rules",
            "insights": "/user-profile, /conversation-history",
            "system": "/health, /performance"
        },
        "knowledge_base": {
            "total_topics": auto_learning_stats.get("auto_learning", {}).get("active_topics", 0),
            "topics_learned": auto_learning_stats.get("auto_learning", {}).get("total_topics_learned", 0),
            "categories": {
                "programming": knowledge_categories.get("programming", 0),
                "pop_culture": knowledge_categories.get("pop_culture", 0),
                "science": knowledge_categories.get("science", 0),
                "lifestyle": knowledge_categories.get("lifestyle", 0),
                "random": knowledge_categories.get("random", 0),
                "current_events": knowledge_categories.get("current_events", 0)
            }
        },
        "topic_discovery": {
            "discovered_topics": discovered_topics.get("discovery_stats", {}).get("total_discovered", 0),
            "min_mentions_threshold": discovered_topics.get("discovery_stats", {}).get("min_mentions_threshold", 2)
        },
        "documentation": "/docs",
        "notice": "AI with comprehensive knowledge in programming, pop culture, science, lifestyle, and more!"
    }

@app.get("/stats", response_model=dict)
async def get_stats():
    """Comprehensive statistics endpoint"""
    try:
        health = ai_engine.get_health()
        profile = ai_engine.get_user_profile()
        performance = ai_engine.get_performance_stats()
        auto_learning = ai_engine.get_auto_learning_stats()
        discovered_topics = ai_engine.get_discovered_topics()
        
        return {
            "system_health": health,
            "user_insights": profile,
            "performance": performance,
            "auto_learning": auto_learning,
            "discovered_topics": discovered_topics,
            "timestamp": ai_engine._last_full_update.isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== ERROR HANDLERS =====

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint not found",
            "available_endpoints": [
                "/docs - API documentation",
                "/health - System health",
                "/ask - Chat with AI", 
                "/teach - Teach new knowledge",
                "/research - Research topics online",
                "/auto-learning/* - Auto-learning controls",
                "/auto-learning/discovered-topics - Discovered topics"
            ]
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "Something went wrong on our end. Please try again later.",
            "support": "Check the logs for more details."
        }
    )

# ===== SIMPLE RUNNER =====
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )