"""Fixed unit tests for Postmark webhook handler using Litestar TestClient."""

import pytest
from unittest.mock import AsyncMock, patch
from litestar.testing import create_test_client
from litestar.status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from cellophanemail.routes.webhooks import WebhookController
from cellophanemail.models.user import User
from cellophanemail.core.email_processor import ProcessingResult


class TestPostmarkWebhookHandlerFixed:
    """Test cases for Postmark webhook endpoint using proper Litestar testing."""
    
    @pytest.fixture
    def sample_postmark_payload(self):
        """Sample Postmark webhook payload for testing."""
        return {
            "From": "sender@example.com",
            "To": "a1b2c3d4e5f6789012345678901234567@cellophanemail.com",
            "Subject": "Test email",
            "MessageID": "msg-123456",
            "Date": "2025-08-12T12:00:00Z",
            "TextBody": "This is a test email",
            "HtmlBody": "<p>This is a test email</p>",
            "Headers": [
                {"Name": "X-Test", "Value": "test-value"}
            ],
            "Attachments": []
        }
    
    def test_valid_email_forwarded(self, sample_postmark_payload):
        """Test that valid email is processed and forwarded."""
        # Setup mocks
        mock_user = {
            "id": "user-uuid-123",
            "email": "real.user@gmail.com",
            "organization": None,
            "is_active": True
        }
        
        mock_result = ProcessingResult(
            email_id="test-id",
            should_forward=True,
            toxicity_score=0.1,
            horsemen_detected=[],
            processing_time_ms=250.0
        )
        
        with patch('cellophanemail.routes.webhooks.UserService.get_user_by_shield_address', new_callable=AsyncMock) as mock_user_service, \
             patch('cellophanemail.routes.webhooks.EmailProcessor') as mock_processor_class:
            
            # Setup mocks
            mock_user_service.return_value = mock_user
            mock_processor = AsyncMock()
            mock_processor.process.return_value = mock_result
            mock_processor_class.return_value = mock_processor
            
            # Create test client with the controller
            with create_test_client(route_handlers=[WebhookController]) as client:
                # Act
                response = client.post("/webhooks/postmark", json=sample_postmark_payload)
                
                # Assert
                assert response.status_code == HTTP_200_OK
                response_data = response.json()
                assert response_data["status"] == "accepted"
                assert response_data["processing"] == "forwarded"
                assert response_data["message_id"] == "msg-123456"
                assert response_data["user_id"] == "user-uuid-123"
                assert response_data["toxicity_score"] == 0.1
    
    def test_toxic_email_blocked(self, sample_postmark_payload):
        """Test that toxic email is blocked."""
        mock_user = {
            "id": "user-uuid-123",
            "email": "real.user@gmail.com",
            "organization": None,
            "is_active": True
        }
        
        mock_result = ProcessingResult(
            email_id="test-id",
            should_forward=False,
            block_reason="Four Horsemen detected",
            toxicity_score=0.9,
            horsemen_detected=["contempt", "criticism"],
            processing_time_ms=320.0
        )
        
        with patch('cellophanemail.routes.webhooks.UserService.get_user_by_shield_address', new_callable=AsyncMock) as mock_user_service, \
             patch('cellophanemail.routes.webhooks.EmailProcessor') as mock_processor_class:
            
            mock_user_service.return_value = mock_user
            mock_processor = AsyncMock()
            mock_processor.process.return_value = mock_result
            mock_processor_class.return_value = mock_processor
            
            with create_test_client(route_handlers=[WebhookController]) as client:
                response = client.post("/webhooks/postmark", json=sample_postmark_payload)
                
                assert response.status_code == HTTP_200_OK
                response_data = response.json()
                assert response_data["status"] == "accepted"
                assert response_data["processing"] == "blocked"
                assert response_data["block_reason"] == "Four Horsemen detected"
                assert response_data["toxicity_score"] == 0.9
                assert response_data["horsemen_detected"] == ["contempt", "criticism"]
    
    def test_invalid_domain_rejected(self):
        """Test that emails to invalid domains are rejected."""
        payload_data = {
            "From": "sender@example.com",
            "To": "user@wrong-domain.com",  # Wrong domain
            "Subject": "Test",
            "MessageID": "msg-123",
            "Date": "2025-08-12T12:00:00Z"
        }
        
        with create_test_client(route_handlers=[WebhookController]) as client:
            response = client.post("/webhooks/postmark", json=payload_data)
            
            assert response.status_code == HTTP_400_BAD_REQUEST
            response_data = response.json()
            assert response_data["error"] == "Invalid domain"
            assert response_data["message_id"] == "msg-123"
    
    def test_shield_address_not_found(self, sample_postmark_payload):
        """Test handling when shield address has no associated user."""
        with patch('cellophanemail.routes.webhooks.UserService.get_user_by_shield_address', new_callable=AsyncMock) as mock_user_service:
            mock_user_service.return_value = None
            
            with create_test_client(route_handlers=[WebhookController]) as client:
                response = client.post("/webhooks/postmark", json=sample_postmark_payload)
                
                assert response.status_code == HTTP_404_NOT_FOUND
                response_data = response.json()
                assert response_data["error"] == "Shield address not found"
                assert response_data["message_id"] == "msg-123456"