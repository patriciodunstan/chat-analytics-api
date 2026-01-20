"""Database models."""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Enum, ForeignKey, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class UserRole(str, enum.Enum):
    """User roles for access control."""
    VIEWER = "viewer"
    ANALYST = "analyst"
    ADMIN = "admin"


class User(Base):
    """User model for authentication."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.VIEWER)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="user")
    reports: Mapped[list["Report"]] = relationship(back_populates="user")


class Conversation(Base):
    """Conversation/chat session model."""
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(255), default="Nueva conversación")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )


class MessageRole(str, enum.Enum):
    """Message sender role."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(Base):
    """Chat message model."""
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"))
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


class ReportType(str, enum.Enum):
    """Types of reports that can be generated."""
    DATA_SUMMARY = "data_summary"
    TREND_ANALYSIS = "trend_analysis"
    CUSTOM = "custom"


class ReportStatus(str, enum.Enum):
    """Report generation status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Report(Base):
    """Generated report model."""
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(255))
    report_type: Mapped[ReportType] = mapped_column(Enum(ReportType))
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus), default=ReportStatus.PENDING
    )
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    analysis_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="reports")


# ============================================================
# MINING DOMAIN MODELS (Dataset 1)
# ============================================================

class Equipment(Base):
    """Equipment/machinery model for maintenance tracking."""
    __tablename__ = "equipment"

    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    tipo_maquina: Mapped[str] = mapped_column(String(50))
    marca: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    modelo: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ano: Mapped[Optional[int]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    maintenance_events: Mapped[list["MaintenanceEvent"]] = relationship(
        back_populates="equipment", cascade="all, delete-orphan"
    )
    failure_events: Mapped[list["FailureEvent"]] = relationship(
        back_populates="equipment", cascade="all, delete-orphan"
    )


class MaintenanceEvent(Base):
    """Maintenance event model."""
    __tablename__ = "maintenance_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[str] = mapped_column(String(20), ForeignKey("equipment.equipment_id"))
    fecha: Mapped[datetime] = mapped_column(DateTime)
    tipo_intervencion: Mapped[str] = mapped_column(String(20))
    descripcion_tarea: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    horas_operacion: Mapped[Optional[int]] = mapped_column(nullable=True)
    costo_total: Mapped[Optional[float]] = mapped_column(nullable=True)
    duracion_horas: Mapped[Optional[int]] = mapped_column(nullable=True)
    responsable: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ubicacion_gps: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    equipment: Mapped["Equipment"] = relationship(back_populates="maintenance_events")


class FailureEvent(Base):
    """Failure/breakdown event model."""
    __tablename__ = "failure_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[str] = mapped_column(String(20), ForeignKey("equipment.equipment_id"))
    fecha: Mapped[datetime] = mapped_column(DateTime)
    codigo_falla: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    descripcion_falla: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    causa_raiz: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    horas_operacion: Mapped[Optional[int]] = mapped_column(nullable=True)
    costo_total: Mapped[Optional[float]] = mapped_column(nullable=True)
    duracion_horas: Mapped[Optional[int]] = mapped_column(nullable=True)
    responsable: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ubicacion_gps: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    impacto: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    equipment: Mapped["Equipment"] = relationship(back_populates="failure_events")


class SupportTicket(Base):
    """Customer support ticket model."""
    __tablename__ = "support_tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(unique=True, index=True)
    customer_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    customer_email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    customer_age: Mapped[Optional[int]] = mapped_column(nullable=True)
    customer_gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    product_purchased: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    date_of_purchase: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ticket_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ticket_subject: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ticket_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ticket_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ticket_priority: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    ticket_channel: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    first_response_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    time_to_resolution: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    customer_satisfaction_rating: Mapped[Optional[float]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
