"""Unit tests for services and utilities."""
import pytest
from datetime import datetime, timedelta

from app.auth.jwt_handler import create_access_token, decode_access_token
from app.auth.service import hash_password, verify_password
from app.db.models import UserRole, MessageRole, ReportType, ReportStatus


class TestJwtHandler:
    """Tests for JWT token handling."""
    
    def test_create_access_token(self):
        """Test creating an access token."""
        data = {"sub": "test@example.com", "role": "analyst"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_decode_access_token(self):
        """Test decoding a valid token."""
        data = {"sub": "test@example.com", "role": "analyst"}
        token = create_access_token(data)
        
        decoded = decode_access_token(token)
        
        assert decoded is not None
        assert decoded["sub"] == "test@example.com"
        assert decoded["role"] == "analyst"
    
    def test_decode_invalid_token(self):
        """Test decoding an invalid token returns None."""
        result = decode_access_token("invalid.token.here")
        
        assert result is None
    
    def test_token_with_expiry(self):
        """Test token with custom expiry."""
        data = {"sub": "test@example.com"}
        token = create_access_token(data, expires_delta=timedelta(minutes=5))
        
        decoded = decode_access_token(token)
        
        assert decoded is not None
        assert "exp" in decoded


class TestPasswordHashing:
    """Tests for password hashing."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "mysecretpassword"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
    
    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "mysecretpassword"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "mysecretpassword"
        hashed = hash_password(password)
        
        assert verify_password("wrongpassword", hashed) is False


class TestEnums:
    """Tests for model enums."""
    
    def test_user_role_values(self):
        """Test UserRole enum values."""
        assert UserRole.VIEWER.value == "viewer"
        assert UserRole.ANALYST.value == "analyst"
        assert UserRole.ADMIN.value == "admin"
    
    def test_message_role_values(self):
        """Test MessageRole enum values."""
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.SYSTEM.value == "system"
    
    def test_report_type_values(self):
        """Test ReportType enum values."""
        assert ReportType.COST_VS_EXPENSE.value == "cost_vs_expense"
        assert ReportType.MONTHLY_SUMMARY.value == "monthly_summary"
    
    def test_report_status_values(self):
        """Test ReportStatus enum values."""
        assert ReportStatus.PENDING.value == "pending"
        assert ReportStatus.PROCESSING.value == "processing"
        assert ReportStatus.COMPLETED.value == "completed"
        assert ReportStatus.FAILED.value == "failed"
