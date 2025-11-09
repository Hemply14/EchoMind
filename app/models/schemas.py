# app/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class TeachRequest(BaseModel):
    input_text: str = Field(..., min_length=1, max_length=1000, description="The question or input pattern")
    output_text: str = Field(..., min_length=1, max_length=2000, description="The desired response")
    context: Optional[str] = Field(None, max_length=1000, description="Optional context for the memory")
    category: str = Field("general", max_length=50, description="Category for organization")

class AskRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="The question to ask")
    threshold: float = Field(0.7, ge=0.0, le=1.0, description="Similarity threshold (0.0-1.0)")

class AskContextRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    user_id: str = Field("default", description="User identifier for conversation tracking")
    threshold: float = Field(0.7, ge=0.0, le=1.0)
    enable_research: bool = Field(False, description="Whether to search online for unknown topics")

class RuleRequest(BaseModel):
    pattern: str = Field(..., min_length=1, max_length=500, description="Text pattern to match")
    action: str = Field(..., min_length=1, max_length=1000, description="Response when pattern matches")
    priority: int = Field(1, ge=1, le=10, description="Rule priority (1-10)")

class ResearchRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=500, description="Topic to research online")
    depth: str = Field("basic", description="Research depth: basic or comprehensive")

class FeedbackRequest(BaseModel):
    query: str = Field(..., description="Original user query")
    response: str = Field(..., description="AI response that was given")
    rating: int = Field(..., ge=1, le=5, description="Rating 1-5 (1=bad, 5=excellent)")
    comment: Optional[str] = Field(None, description="Optional comment explaining the rating")

# ===== RESPONSE MODELS =====

class AIResponse(BaseModel):
    response: str = Field(..., description="The AI's response")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score of the response")
    source: str = Field(..., description="Source of the response: memory, rule, web_research, unknown")
    memory_id: Optional[int] = Field(None, description="ID of the memory used, if applicable")
    rule_id: Optional[int] = Field(None, description="ID of the rule used, if applicable")
    match_rank: Optional[int] = Field(None, description="Rank of the match if multiple were considered")
    enhancement: Optional[str] = Field(None, description="Type of enhancement applied: common_sense, personalization, context, web_research")
    research_used: Optional[bool] = Field(None, description="Whether web research was used")
    sources: Optional[List[str]] = Field(None, description="Sources used for research")

class TeachResponse(BaseModel):
    status: str = Field(..., description="Status of the teaching operation")
    memory_id: int = Field(..., description="ID of the created memory")
    category: str = Field(..., description="Category of the memory")
    pending_updates: Optional[int] = Field(None, description="Number of pending knowledge base updates")

class RuleResponse(BaseModel):
    status: str = Field(..., description="Status of the rule operation")
    rule_id: int = Field(..., description="ID of the created rule")

class ResearchResponse(BaseModel):
    status: str = Field(..., description="Status of the research: success, no_results, error")
    learned_items: int = Field(..., description="Number of items learned from research")
    sources: List[str] = Field(..., description="Sources used for research")
    message: str = Field(..., description="Human-readable result message")

class FeedbackResponse(BaseModel):
    status: str = Field(..., description="Status of the feedback submission")
    message: str = Field(..., description="Acknowledgement message")
    rating_received: int = Field(..., description="The rating that was received")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall system health status")
    memory_count: int = Field(..., description="Number of active memories")
    rule_count: int = Field(..., description="Number of active rules")
    model_loaded: bool = Field(..., description="Whether the AI model is loaded")
    knowledge_base_ready: bool = Field(..., description="Whether the knowledge base is ready")
    cache_size: int = Field(..., description="Number of items in memory cache")
    pending_updates: int = Field(..., description="Number of pending knowledge base updates")
    last_update: str = Field(..., description="Timestamp of last knowledge base update")

class PerformanceResponse(BaseModel):
    memory_cache_size: int = Field(..., description="Number of memories in cache")
    embedding_cache_size: int = Field(..., description="Size of embedding cache")
    pending_updates: int = Field(..., description="Number of pending updates")
    last_full_update: str = Field(..., description="Timestamp of last full update")
    update_threshold: int = Field(..., description="Update threshold setting")
    conversation_history: int = Field(..., description="Number of conversation entries")
    user_interests: int = Field(..., description="Number of learned user interests")
    successful_responses: int = Field(..., description="Number of successful responses tracked")
    total_feedback_ratings: int = Field(..., description="Total number of feedback ratings received")

class UserProfileResponse(BaseModel):
    interests: List[str] = Field(..., description="User's learned interests")
    topics_discussed: List[str] = Field(..., description="Topics discussed with the user")
    conversation_count: int = Field(..., description="Number of conversations with the user")
    last_interaction: Optional[str] = Field(None, description="Timestamp of last interaction")
    conversation_style: str = Field(..., description="Detected conversation style")

class ConversationHistoryResponse(BaseModel):
    conversations: List[Dict[str, Any]] = Field(..., description="List of conversation entries")

class MemoryResponse(BaseModel):
    id: int = Field(..., description="Memory ID")
    input_text: str = Field(..., description="Input text/question")
    output_text: str = Field(..., description="Output text/response")
    context: Optional[str] = Field(None, description="Context for the memory")
    category: str = Field(..., description="Memory category")
    confidence: float = Field(..., description="Confidence score")
    created_at: datetime = Field(..., description="Creation timestamp")
    is_active: bool = Field(..., description="Whether the memory is active")

class ForceUpdateResponse(BaseModel):
    status: str = Field(..., description="Update status")
    memory_count: int = Field(..., description="Number of memories after update")

class DeleteResponse(BaseModel):
    status: str = Field(..., description="Deletion status")
    memory_id: int = Field(..., description="ID of the deleted memory")
    message: Optional[str] = Field(None, description="Additional message")

class StatsResponse(BaseModel):
    system_health: HealthResponse = Field(..., description="System health information")
    user_insights: UserProfileResponse = Field(..., description="User profile insights")
    performance: PerformanceResponse = Field(..., description="Performance statistics")
    timestamp: str = Field(..., description="Timestamp of the stats snapshot")

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")

class RootResponse(BaseModel):
    message: str = Field(..., description="Welcome message")
    status: str = Field(..., description="API status")
    version: str = Field(..., description="API version")
    features: List[str] = Field(..., description="Available features")
    endpoints: Dict[str, str] = Field(..., description="Available endpoints")
    documentation: str = Field(..., description="Documentation URL")
    notice: str = Field(..., description="Privacy notice")