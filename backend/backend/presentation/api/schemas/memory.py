from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MemoryInsightsResponse(BaseModel):
    """Response schema for memory insights."""
    
    user_id: str = Field(description="The user's ID")
    status: str = Field(description="Status of the operation")
    insights: Dict[str, Any] = Field(description="Memory insights data")
    message: str = Field(description="Response message")


class MemoryConsolidationResponse(BaseModel):
    """Response schema for memory consolidation."""
    
    user_id: str = Field(description="The user's ID")
    status: str = Field(description="Status of the consolidation")
    consolidation_result: Dict[str, Any] = Field(description="Consolidation results")
    message: str = Field(description="Response message")


class MemoryInitializationResponse(BaseModel):
    """Response schema for memory initialization."""
    
    user_id: str = Field(description="The user's ID")
    status: str = Field(description="Status of the initialization")
    message: str = Field(description="Response message")


class RelevantMemoriesResponse(BaseModel):
    """Response schema for relevant memories."""
    
    user_id: str = Field(description="The user's ID")
    query: str = Field(description="The search query")
    status: str = Field(description="Status of the operation")
    memories: List[Dict[str, Any]] = Field(description="List of relevant memories")
    count: int = Field(description="Number of memories returned")
    message: str = Field(description="Response message")


class ProfileUpdateResponse(BaseModel):
    """Response schema for profile updates."""
    
    user_id: str = Field(description="The user's ID")
    status: str = Field(description="Status of the update")
    updated_fields: List[str] = Field(description="List of updated fields")
    message: str = Field(description="Response message")


class MemoryConsolidationScheduleResponse(BaseModel):
    """Response schema for memory consolidation scheduling."""
    
    user_id: str = Field(description="The user's ID")
    session_id: str = Field(description="The session ID")
    priority: int = Field(description="Priority level")
    status: str = Field(description="Status of the scheduling")
    message: str = Field(description="Response message")


