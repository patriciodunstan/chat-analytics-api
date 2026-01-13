"""Chat service layer."""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Conversation, Message, MessageRole, User
from app.chat.schemas import MessageCreate, ConversationCreate
from app.chat.llm import gemini_client


async def create_conversation(
    db: AsyncSession,
    user: User,
    data: ConversationCreate,
) -> Conversation:
    """Create a new conversation."""
    conversation = Conversation(
        user_id=user.id,
        title=data.title,
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


async def get_conversation(
    db: AsyncSession,
    conversation_id: int,
    user: User,
) -> Conversation | None:
    """Get a conversation by ID with messages."""
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id,
        )
    )
    return result.scalar_one_or_none()


async def get_user_conversations(
    db: AsyncSession,
    user: User,
    skip: int = 0,
    limit: int = 20,
) -> list[Conversation]:
    """Get all conversations for a user."""
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def add_message(
    db: AsyncSession,
    conversation_id: int,
    role: MessageRole,
    content: str,
) -> Message:
    """Add a message to a conversation."""
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def get_conversation_history(
    db: AsyncSession,
    conversation_id: int,
    limit: int = 10,
) -> list[dict]:
    """Get recent messages for LLM context."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    messages = list(result.scalars().all())
    messages.reverse()  # Oldest first for context
    
    return [
        {"role": msg.role.value, "content": msg.content}
        for msg in messages
    ]


async def process_chat_message(
    db: AsyncSession,
    user: User,
    user_message: str,
    conversation_id: int | None = None,
) -> tuple[Conversation, Message, Message]:
    """Process a chat message and get LLM response."""
    # Create or get conversation
    if conversation_id:
        conversation = await get_conversation(db, conversation_id, user)
        if not conversation:
            raise ValueError("Conversation not found")
    else:
        conversation = await create_conversation(
            db, user, ConversationCreate(title=user_message[:50])
        )
    
    # Add user message
    user_msg = await add_message(
        db, conversation.id, MessageRole.USER, user_message
    )
    
    # Get conversation history for context
    history = await get_conversation_history(db, conversation.id)
    
    # Generate LLM response
    response_text = await gemini_client.generate_response(
        user_message=user_message,
        conversation_history=history[:-1],  # Exclude current message
    )
    
    # Add assistant message
    assistant_msg = await add_message(
        db, conversation.id, MessageRole.ASSISTANT, response_text
    )
    
    return conversation, user_msg, assistant_msg
