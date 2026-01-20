"""Pydantic schemas for chat module."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.db.models import MessageRole


class MessageCreate(BaseModel):
    """Schema for creating a new message."""
    content: str
    conversation_id: Optional[int] = None


class MessageResponse(BaseModel):
    """Schema for message response."""
    id: int
    conversation_id: int
    role: MessageRole
    content: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""
    title: Optional[str] = "Nueva conversación"


class ConversationResponse(BaseModel):
    """Schema for conversation response."""
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    model_config = ConfigDict(from_attributes=True)


class ConversationWithMessages(ConversationResponse):
    """Conversation with its messages."""
    messages: list[MessageResponse] = []


class ChatRequest(BaseModel):
    """Schema for chat request."""
    message: str
    conversation_id: Optional[int] = None


class ChatResponse(BaseModel):
    """Schema for chat response."""
    conversation_id: int
    user_message: MessageResponse
    assistant_message: MessageResponse


class AnalysisRequest(BaseModel):
    """Schema for analysis request."""
    analysis_type: str
    service_id: Optional[int] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
