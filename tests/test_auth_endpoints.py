"""Tests for authentication endpoints."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from litestar.testing import TestClient
from src.cellophanemail.app import create_app


@pytest.fixture
def test_client():
    """Create test client for the app."""
    app = create_app()
    return TestClient(app=app)


class TestUserRegistration:
    """Test user registration endpoint."""
    
    def test_register_user_success(self, test_client):
        """Test successful user registration."""
        with patch('src.cellophanemail.routes.auth.validate_email_unique', new=AsyncMock(return_value=True)):
            with patch('src.cellophanemail.routes.auth.create_user', new=AsyncMock()) as mock_create:
                # Mock user object
                mock_user = MagicMock()
                mock_user.id = "test-uuid"
                mock_user.email = "test@example.com"
                mock_user.username = "test123"
                mock_user.is_verified = False
                mock_user.verification_token = "test-token"
                mock_create.return_value = mock_user
                
                response = test_client.post(
                    "/auth/register",
                    json={
                        "email": "test@example.com",
                        "password": "TestPass123!",
                        "first_name": "Test",
                        "last_name": "User"
                    }
                )
                
                assert response.status_code == 201
                data = response.json()
                assert data["status"] == "registered"
                assert data["email"] == "test@example.com"
                assert data["shield_address"].endswith("@cellophanemail.com")
                assert "test" in data["shield_address"]
                assert data["email_verified"] is False
                
    def test_register_user_duplicate_email(self, test_client):
        """Test registration with duplicate email."""
        with patch('src.cellophanemail.routes.auth.validate_email_unique', new=AsyncMock(return_value=False)):
            response = test_client.post(
                "/auth/register",
                json={
                    "email": "existing@example.com",
                    "password": "TestPass123!",
                    "first_name": "Test",
                    "last_name": "User"
                }
            )
            
            assert response.status_code == 400
            data = response.json()
            assert data["error"] == "Email already registered"
            assert data["field"] == "email"
            
    def test_register_user_weak_password(self, test_client):
        """Test registration with weak password."""
        response = test_client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "weak",  # Too short, no uppercase, no digit
                "first_name": "Test",
                "last_name": "User"
            }
        )
        
        assert response.status_code == 422  # Validation error
        
    def test_register_user_invalid_email(self, test_client):
        """Test registration with invalid email format."""
        response = test_client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "password": "TestPass123!",
                "first_name": "Test",
                "last_name": "User"
            }
        )
        
        assert response.status_code == 422  # Validation error