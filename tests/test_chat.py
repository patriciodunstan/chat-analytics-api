"""Tests for chat endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Conversation, Message, MessageRole


@pytest.mark.asyncio
async def test_send_message_new_conversation(client: AsyncClient, auth_headers):
    """Test sending a message creates new conversation."""
    response = await client.post(
        "/chat/message",
        headers=auth_headers,
        json={"message": "Hello, this is a test message"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
    assert data["user_message"]["content"] == "Hello, this is a test message"
    assert data["user_message"]["role"] == "user"
    assert "assistant_message" in data


@pytest.mark.asyncio
async def test_send_message_with_pdf_flag(client: AsyncClient, auth_headers):
    """Test sending message with generate_pdf flag includes pdf_url in response."""
    response = await client.post(
        "/chat/message",
        headers=auth_headers,
        json={"message": "Hello", "generate_pdf": True},
    )

    assert response.status_code == 200
    data = response.json()
    # pdf_url puede ser None si no hay resultados de query
    assert "pdf_url" in data


@pytest.mark.asyncio
async def test_send_message_existing_conversation(
    client: AsyncClient, auth_headers, test_session: AsyncSession, test_user
):
    """Test sending a message to existing conversation."""
    # Create a conversation first
    conv = Conversation(user_id=test_user.id, title="Test Conv")
    test_session.add(conv)
    await test_session.commit()
    await test_session.refresh(conv)

    response = await client.post(
        "/chat/message",
        headers=auth_headers,
        json={"message": "Follow-up message", "conversation_id": conv.id},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["conversation_id"] == conv.id


@pytest.mark.asyncio
async def test_send_message_unauthorized(client: AsyncClient):
    """Test sending message without auth fails."""
    response = await client.post(
        "/chat/message",
        json={"message": "Hello"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_conversations_empty(client: AsyncClient, auth_headers):
    """Test listing conversations when empty."""
    response = await client.get("/chat/conversations", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_list_conversations_with_data(
    client: AsyncClient, auth_headers, test_session: AsyncSession, test_user
):
    """Test listing conversations with data."""
    # Create conversations
    for i in range(3):
        conv = Conversation(user_id=test_user.id, title=f"Conv {i}")
        test_session.add(conv)
    await test_session.commit()

    response = await client.get("/chat/conversations", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_get_conversation(
    client: AsyncClient, auth_headers, test_session: AsyncSession, test_user
):
    """Test getting a specific conversation."""
    # Create conversation with messages
    conv = Conversation(user_id=test_user.id, title="Test Conv")
    test_session.add(conv)
    await test_session.commit()
    await test_session.refresh(conv)

    msg = Message(
        conversation_id=conv.id,
        role=MessageRole.USER,
        content="Test message",
    )
    test_session.add(msg)
    await test_session.commit()

    response = await client.get(
        f"/chat/conversations/{conv.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == conv.id
    assert data["title"] == "Test Conv"
    assert len(data["messages"]) == 1


@pytest.mark.asyncio
async def test_get_conversation_not_found(client: AsyncClient, auth_headers):
    """Test getting non-existent conversation."""
    response = await client.get(
        "/chat/conversations/99999",
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_conversation(client: AsyncClient, auth_headers):
    """Test creating a new conversation."""
    response = await client.post(
        "/chat/conversations",
        headers=auth_headers,
        json={"title": "New Conversation"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Conversation"
    assert "id" in data


@pytest.mark.asyncio
async def test_download_pdf_invalid_extension(client: AsyncClient, auth_headers):
    """Test downloading PDF with invalid extension."""
    response = await client.get(
        "/chat/pdf/document.txt",
        headers=auth_headers,
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_download_pdf_not_found(client: AsyncClient, auth_headers):
    """Test downloading non-existent PDF."""
    response = await client.get(
        "/chat/pdf/nonexistent.pdf",
        headers=auth_headers,
    )

    assert response.status_code == 404
