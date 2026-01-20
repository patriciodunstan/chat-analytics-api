"""Chat service layer with NL2SQL integration."""
import logging
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Conversation, Message, MessageRole, User
from app.chat.schemas import MessageCreate, ConversationCreate
from app.chat.llm.client import llm_client

# NL2SQL imports
from app.chat.nl2sql.detector import QueryDetector
from app.chat.nl2sql.schema_discovery import SchemaDiscovery
from app.chat.nl2sql.intent_parser import IntentParser
from app.chat.nl2sql.sql_generator import SQLGenerator
from app.chat.nl2sql.query_executor import QueryExecutor
from app.chat.nl2sql.prompts import DATA_RESPONSE_PROMPT
from app.chat.nl2sql.exceptions import NL2QLError

logger = logging.getLogger(__name__)

# Inicializar componentes NL2SQL
query_detector = QueryDetector()
schema_discovery = SchemaDiscovery(include_internal_tables=False)
intent_parser = IntentParser()
sql_generator = SQLGenerator()
query_executor = QueryExecutor()


async def create_conversation(
    db: AsyncSession, user: User, data: ConversationCreate
) -> Conversation:
    """Create a new conversation."""
    conversation = Conversation(
        user_id=user.id,
        title=data.title or "Nueva conversación",
    )
    db.add(conversation)
    await db.flush()
    await db.refresh(conversation)
    return conversation


async def get_conversation(
    db: AsyncSession, conversation_id: int, user: User
) -> Optional[Conversation]:
    """Get a conversation by ID for a specific user."""
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id
        )
    )
    return result.scalar_one_or_none()


async def get_user_conversations(
    db: AsyncSession, user: User, skip: int = 0, limit: int = 20
) -> tuple[list[Conversation], int]:
    """Get all conversations for a user with pagination."""
    # Subquery para contar mensajes por conversación
    msg_count = (
        select(func.count(Message.id))
        .where(Message.conversation_id == Conversation.id)
        .correlate(Conversation)
        .scalar_subquery()
    )

    count_result = await db.execute(
        select(func.count(Conversation.id)).where(Conversation.user_id == user.id)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(Conversation, msg_count.label("message_count"))
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )

    # Adjuntar message_count a cada conversación
    conversations = []
    for row in result.all():
        conv = row[0]
        conv._message_count = row[1]  # type: ignore
        conversations.append(conv)

    return conversations, total


async def add_message(
    db: AsyncSession,
    conversation_id: int,
    role: MessageRole,
    content: str
) -> Message:
    """Add a message to a conversation."""
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
    )
    db.add(message)
    await db.flush()
    await db.refresh(message)
    return message


async def get_conversation_history(
    db: AsyncSession, conversation_id: int, limit: int = 10
) -> list[dict]:
    """Get recent conversation history."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    messages = list(result.scalars().all())
    messages.reverse()

    return [
        {"role": msg.role.value, "content": msg.content}
        for msg in messages
    ]


async def process_chat_message(
    db: AsyncSession,
    user: User,
    user_message: str,
    conversation_id: Optional[int] = None,
) -> tuple[Conversation, Message, Message]:
    """Process a chat message with NL2SQL support."""
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

    # Get conversation history
    history = await get_conversation_history(db, conversation.id)

    # Process with NL2SQL or standard chat
    response_text = await _process_with_nl2sql(
        db=db,
        user_message=user_message,
        conversation_history=history[:-1],
    )

    # Add assistant message
    assistant_msg = await add_message(
        db, conversation.id, MessageRole.ASSISTANT, response_text
    )

    return conversation, user_msg, assistant_msg


async def _process_with_nl2sql(
    db: AsyncSession,
    user_message: str,
    conversation_history: list[dict],
) -> str:
    """Process message with NL2SQL if it's a data query."""
    try:
        # Paso 1: Detectar si es query de datos
        is_data_query, confidence, reasoning = await query_detector.is_data_query(
            user_message
        )

        logger.info(
            f"Query detection: is_data={is_data_query}, "
            f"confidence={confidence:.2f}, reasoning={reasoning}"
        )

        if not is_data_query or confidence < 0.6:
            return await llm_client.generate_response(
                user_message=user_message,
                conversation_history=conversation_history,
            )

        # Paso 2: Descubrir esquema
        schema = await schema_discovery.discover(db)
        schema_prompt = schema_discovery.get_schema_prompt(schema)

        logger.info(f"Discovered {len(schema.tables)} tables")

        # Paso 3: Parsear intención
        intent = await intent_parser.parse(user_message, schema, schema_prompt)

        logger.info(
            f"Parsed intent: tables={intent.tables}, "
            f"aggregations={len(intent.aggregations)}, "
            f"filters={len(intent.filters)}"
        )

        # Paso 4: Generar SQL
        sql_query = sql_generator.generate(intent, schema)

        logger.info(f"Generated SQL: {sql_query.description}")
        logger.debug(f"SQL: {sql_query.sql}")

        # Paso 5: Ejecutar query
        result = await query_executor.execute(db, sql_query)

        if not result.success:
            logger.warning(f"Query execution failed: {result.error_message}")
            return (
                f"No pude ejecutar la consulta correctamente. "
                f"Error: {result.error_message}\n\n"
                f"Por favor, intenta reformular tu pregunta."
            )

        # Paso 6: Generar respuesta natural
        formatted_results = query_executor.format_results_as_markdown_table(result)

        response_prompt = DATA_RESPONSE_PROMPT.format(
            user_message=user_message,
            query_description=sql_query.description,
            query_results=formatted_results,
            row_count=result.row_count,
            columns=", ".join(result.column_names),
        )

        return await llm_client.generate_response(
            user_message=response_prompt,
            conversation_history=[],
        )

    except NL2QLError as e:
        logger.error(f"NL2SQL error: {e}")
        return await llm_client.generate_response(
            user_message=user_message,
            conversation_history=conversation_history,
            context_data={"error_context": str(e)},
        )

    except Exception as e:
        logger.error(f"Unexpected error in NL2SQL: {e}", exc_info=True)
        return await llm_client.generate_response(
            user_message=user_message,
            conversation_history=conversation_history,
        )