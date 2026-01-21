"""Chat service layer with NL2SQL integration."""
import logging
import os
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
from app.chat.nl2sql.schemas import QueryResult

# PDF generation
from app.reports.generator import report_generator

logger = logging.getLogger(__name__)

# Modo económico: desactiva LLM en detección y usa formateo simple
# Setea ECONOMICAL_MODE=true en variables de entorno para activar
ECONOMICAL_MODE = os.getenv("ECONOMICAL_MODE", "false").lower() == "true"

# Inicializar componentes NL2SQL
query_detector = QueryDetector()
schema_discovery = SchemaDiscovery(include_internal_tables=False)
intent_parser = IntentParser()
sql_generator = SQLGenerator()
query_executor = QueryExecutor()

# Modo económico: desactiva LLM en detección y formateo
# Setea ECONOMICAL_MODE=true en variables de entorno
import os
ECONOMICAL_MODE = os.getenv("ECONOMICAL_MODE", "false").lower() == "true"


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
    conversation_id: int | None = None,
    generate_pdf: bool = False,
) -> tuple[Conversation, Message, Message, str | None]:
    """Process a chat message with NL2SQL support.

    Returns:
        tuple with conversation, user_msg, assistant_msg, pdf_url
    """
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
    response_text, query_result, sql_description = await _process_with_nl2sql(
        db=db,
        user_message=user_message,
        conversation_history=history[:-1],
    )

    # Add assistant message
    assistant_msg = await add_message(
        db, conversation.id, MessageRole.ASSISTANT, response_text
    )

    # Generate PDF if requested and we have query results
    pdf_url = None
    if generate_pdf and query_result is not None:
        pdf_url = await _generate_query_pdf(
            user_message=user_message,
            response_text=response_text,
            query_result=query_result,
            sql_description=sql_description or "Consulta de datos",
        )

    return conversation, user_msg, assistant_msg, pdf_url


async def _generate_query_pdf(
    user_message: str,
    response_text: str,
    query_result: QueryResult,
    sql_description: str,
) -> str | None:
    """Generate PDF from query results."""
    try:
        # Crear resumen de datos para el PDF
        data_summary = {
            "Consulta": user_message,
            "Descripción": sql_description,
            "Total registros": query_result.row_count,
            "Columnas": ", ".join(query_result.column_names),
        }

        # Agregar algunos datos de muestra
        for idx, row in enumerate(query_result.data[:5]):
            row_data = {
                f"Fila {idx + 1}": ", ".join(str(v) for v in row.values())
            }
            data_summary.update(row_data)

        # Generar PDF
        filepath = report_generator.generate_summary_report(
            title=f"Reporte: {user_message[:50]}",
            data_summary=data_summary,
            analysis_text=response_text,
        )

        # Retornar ruta relativa para descargar
        if os.path.exists(filepath):
            return f"/api/chat/pdf/{os.path.basename(filepath)}"

        logger.warning(f"PDF file not found after generation: {filepath}")
        return None

    except Exception as e:
        logger.error(f"Error generating PDF: {e}", exc_info=True)
        return None


async def _process_with_nl2sql(
    db: AsyncSession,
    user_message: str,
    conversation_history: list[dict],
) -> tuple[str, QueryResult | None, str]:
    """Process message with NL2SQL if it's a data query.

    Returns:
        tuple[str, QueryResult | None, str]: response_text, query_result, sql_description
    """
    try:
        # Paso 1: Detectar si es query de datos (SIN LLM en modo económico)
        use_llm_detection = not ECONOMICAL_MODE
        is_data_query, confidence, reasoning = await query_detector.is_data_query(
            user_message,
            use_llm=use_llm_detection,
        )

        logger.info(
            f"Query detection: is_data={is_data_query}, "
            f"confidence={confidence:.2f}, reasoning={reasoning}, "
            f"econ_mode={ECONOMICAL_MODE}"
        )

        if not is_data_query or confidence < 0.6:
            response = await llm_client.generate_response(
                user_message=user_message,
                conversation_history=conversation_history,
            )
            return response, None, ""

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
            error_msg = (
                f"No pude ejecutar la consulta correctamente. "
                f"Error: {result.error_message}\n\n"
                f"Por favor, intenta reformular tu pregunta."
            )
            return error_msg, None, sql_query.description

        # Paso 6: Generar respuesta (SIN LLM en modo económico o resultados grandes)
        if ECONOMICAL_MODE or result.row_count > 100:
            formatted_results = query_executor.format_results_as_markdown_table(result)
            response_text = f"""## Resultados ({result.row_count} registros)

{formatted_results}

**Resumen:** Se encontraron {result.row_count} registros."""
            return response_text, result, sql_query.description

        # Para resultados pequeños, usar LLM para mejor interpretación
        formatted_results = query_executor.format_results_as_markdown_table(result)

        response_prompt = DATA_RESPONSE_PROMPT.format(
            user_message=user_message,
            query_description=sql_query.description,
            query_results=formatted_results,
            row_count=result.row_count,
            columns=", ".join(result.column_names),
        )

        response = await llm_client.generate_response(
            user_message=response_prompt,
            conversation_history=[],
        )
        return response, result, sql_query.description

    except NL2QLError as e:
        logger.error(f"NL2SQL error: {e}")
        response = await llm_client.generate_response(
            user_message=user_message,
            conversation_history=conversation_history,
            context_data={"error_context": str(e)},
        )
        return response, None, ""

    except Exception as e:
        logger.error(f"Unexpected error in NL2SQL: {e}", exc_info=True)
        response = await llm_client.generate_response(
            user_message=user_message,
            conversation_history=conversation_history,
        )
        return response, None, ""