"""Chat API router."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import User
from app.auth.dependencies import get_current_user
from app.chat.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationResponse,
    ConversationWithMessages,
    MessageResponse,
)
from app.chat import service


router = APIRouter()


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChatResponse:
    """Send a message and get LLM response."""
    try:
        conversation, user_msg, assistant_msg = await service.process_chat_message(
            db=db,
            user=current_user,
            user_message=request.message,
            conversation_id=request.conversation_id,
        )
        
        return ChatResponse(
            conversation_id=conversation.id,
            user_message=MessageResponse.model_validate(user_msg),
            assistant_message=MessageResponse.model_validate(assistant_msg),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}",
        )


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 20,
) -> list[ConversationResponse]:
    """List user's conversations."""
    conversations, total = await service.get_user_conversations(
        db, current_user, skip, limit
    )

    return [
        ConversationResponse(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=getattr(conv, "_message_count", 0),
        )
        for conv in conversations
    ]


@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConversationWithMessages:
    """Get a conversation with all messages."""
    conversation = await service.get_conversation(db, conversation_id, current_user)
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    
    return ConversationWithMessages(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=len(conversation.messages),
        messages=[
            MessageResponse.model_validate(msg)
            for msg in conversation.messages
        ],
    )


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    data: ConversationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConversationResponse:
    """Create a new conversation."""
    conversation = await service.create_conversation(db, current_user, data)
    
    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=0,
    )
