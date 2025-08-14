"""Unit tests for Postmark webhook handler."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from litestar.status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from cellophanemail.routes.webhooks import WebhookController, PostmarkWebhookPayload
from cellophanemail.models.user import User, SubscriptionStatus
from cellophanemail.models.shield_address import ShieldAddress
from cellophanemail.core.email_processor import ProcessingResult


class TestPostmarkWebhookHandler:
    """Test cases for Postmark webhook endpoint."""
    
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
    
    @pytest.fixture
    def mock_user(self):
        """Mock user for testing."""
        user = Mock(spec=User)
        user.id = "user-uuid-123"
        user.email = "real.user@gmail.com"
        user.organization = None
        user.is_active = True
        return user
    
    @pytest.fixture
    def mock_processing_result_safe(self):
        """Mock processing result for safe email."""
        result = Mock(spec=ProcessingResult)
        result.should_forward = True
        result.block_reason = None
        result.toxicity_score = 0.1
        result.horsemen_detected = []
        result.processing_time_ms = 250.0
        return result
    
    @pytest.fixture
    def mock_processing_result_blocked(self):
        """Mock processing result for blocked email."""
        result = Mock(spec=ProcessingResult)
        result.should_forward = False
        result.block_reason = "Four Horsemen detected"
        result.toxicity_score = 0.9
        result.horsemen_detected = ["contempt", "criticism"]
        result.processing_time_ms = 320.0
        return result
    
    @pytest.mark.asyncio
    async def test_valid_email_forwarded(self, sample_postmark_payload, mock_user, mock_processing_result_safe):
        """Test that valid email is processed and forwarded."""
        # Arrange
        controller = WebhookController()
        payload = PostmarkWebhookPayload(**sample_postmark_payload)
        mock_request = Mock()
        
        with patch('cellophanemail.routes.webhooks.UserService.get_user_by_shield_address', new_callable=AsyncMock) as mock_user_service, \
             patch('cellophanemail.routes.webhooks.EmailProcessor') as mock_processor_class:
            
            # Setup mocks
            mock_user_service.return_value = mock_user
            mock_processor = AsyncMock()
            mock_processor.process.return_value = mock_processing_result_safe
            mock_processor_class.return_value = mock_processor
            
            # Act
            response = await controller.handle_postmark_inbound(mock_request, payload)
            
            # Assert
            assert response.status_code == HTTP_200_OK
            response_data = response.content
            assert response_data["status"] == "accepted"
            assert response_data["processing"] == "forwarded"
            assert response_data["message_id"] == "msg-123456"
            assert response_data["user_id"] == "user-uuid-123"
            assert response_data["toxicity_score"] == 0.1
            
            # Verify UserService was called with correct shield address
            mock_user_service.assert_called_once_with("a1b2c3d4e5f6789012345678901234567@cellophanemail.com")
            
            # Verify EmailProcessor was called
            mock_processor.process.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_toxic_email_blocked(self, sample_postmark_payload, mock_user, mock_processing_result_blocked):
        """Test that toxic email is processed and blocked."""
        # Arrange
        controller = WebhookController()
        payload = PostmarkWebhookPayload(**sample_postmark_payload)
        mock_request = Mock()
        
        with patch('cellophanemail.routes.webhooks.UserService.get_user_by_shield_address', new_callable=AsyncMock) as mock_user_service, \
             patch('cellophanemail.routes.webhooks.EmailProcessor') as mock_processor_class:
            
            # Setup mocks
            mock_user_service.return_value = mock_user
            mock_processor = AsyncMock()
            mock_processor.process.return_value = mock_processing_result_blocked
            mock_processor_class.return_value = mock_processor
            
            # Act
            response = await controller.handle_postmark_inbound(mock_request, payload)
            
            # Assert
            assert response.status_code == HTTP_200_OK
            response_data = response.content
            assert response_data["status"] == "accepted"
            assert response_data["processing"] == "blocked"
            assert response_data["block_reason"] == "Four Horsemen detected"
            assert response_data["toxicity_score"] == 0.9
            assert response_data["horsemen_detected"] == ["contempt", "criticism"]
            
            # Verify UserService was called
            mock_user_service.assert_called_once()
            
            # Verify EmailProcessor was called
            mock_processor.process.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_invalid_domain_rejected(self):
        """Test that emails to invalid domains are rejected."""
        # Arrange
        controller = WebhookController()
        mock_request = Mock()
        payload_data = {
            "From": "sender@example.com",
            "To": "user@wrong-domain.com",  # Wrong domain
            "Subject": "Test",
            "MessageID": "msg-123",
            "Date": "2025-08-12T12:00:00Z"
        }
        payload = PostmarkWebhookPayload(**payload_data)
        
        # Act
        response = await controller.handle_postmark_inbound(mock_request, payload)
        
        # Assert
        assert response.status_code == HTTP_400_BAD_REQUEST
        response_data = response.content
        assert response_data["error"] == "Invalid domain"
        assert response_data["message_id"] == "msg-123"
    
    @pytest.mark.asyncio
    async def test_shield_address_not_found(self, sample_postmark_payload):
        """Test handling when shield address has no associated user."""
        # Arrange
        controller = WebhookController()
        mock_request = Mock()
        payload = PostmarkWebhookPayload(**sample_postmark_payload)
        
        with patch('cellophanemail.routes.webhooks.UserService.get_user_by_shield_address', new_callable=AsyncMock) as mock_user_service:
            # Setup mock to return None (no user found)
            mock_user_service.return_value = None
            
            # Act
            response = await controller.handle_postmark_inbound(mock_request, payload)
            
            # Assert
            assert response.status_code == HTTP_404_NOT_FOUND
            response_data = response.content
            assert response_data["error"] == "Shield address not found"
            assert response_data["message_id"] == "msg-123456"
    
    @pytest.mark.asyncio
    async def test_user_context_set_correctly(self, sample_postmark_payload, mock_user, mock_processing_result_safe):
        """Test that user context is correctly set in EmailMessage."""
        # Arrange
        controller = WebhookController()
        mock_request = Mock()
        payload = PostmarkWebhookPayload(**sample_postmark_payload)
        
        with patch('cellophanemail.routes.webhooks.UserService.get_user_by_shield_address', new_callable=AsyncMock) as mock_user_service, \
             patch('cellophanemail.routes.webhooks.EmailProcessor') as mock_processor_class, \
             patch('cellophanemail.routes.webhooks.EmailMessage.from_postmark_webhook') as mock_email_message:
            
            # Setup mocks
            mock_user_service.return_value = mock_user
            mock_processor = AsyncMock()
            mock_processor.process.return_value = mock_processing_result_safe
            mock_processor_class.return_value = mock_processor
            
            # Create mock email message
            mock_message = Mock()
            mock_email_message.return_value = mock_message
            
            # Act
            await controller.handle_postmark_inbound(mock_request, payload)
            
            # Assert that user context was set on the EmailMessage
            assert mock_message.user_id == "user-uuid-123"
            assert mock_message.organization_id is None
            assert mock_message.to_addresses == ["real.user@gmail.com"]
            
            # Verify EmailMessage.from_postmark_webhook was called with correct data
            mock_email_message.assert_called_once_with(payload.model_dump())
    
    @pytest.mark.asyncio
    async def test_user_with_organization(self, sample_postmark_payload, mock_processing_result_safe):
        """Test handling user with organization context."""
        # Arrange
        controller = WebhookController()
        mock_request = Mock()
        payload = PostmarkWebhookPayload(**sample_postmark_payload)
        
        # Create user with organization
        mock_user = Mock(spec=User)
        mock_user.id = "user-uuid-123"
        mock_user.email = "user@company.com"
        mock_user.organization = "org-uuid-456"
        mock_user.is_active = True
        
        with patch('cellophanemail.routes.webhooks.UserService.get_user_by_shield_address', new_callable=AsyncMock) as mock_user_service, \
             patch('cellophanemail.routes.webhooks.EmailProcessor') as mock_processor_class, \
             patch('cellophanemail.routes.webhooks.EmailMessage.from_postmark_webhook') as mock_email_message:
            
            # Setup mocks
            mock_user_service.return_value = mock_user
            mock_processor = AsyncMock()
            mock_processor.process.return_value = mock_processing_result_safe
            mock_processor_class.return_value = mock_processor
            
            mock_message = Mock()
            mock_email_message.return_value = mock_message
            
            # Act
            await controller.handle_postmark_inbound(mock_request, payload)
            
            # Assert that organization context was set
            assert mock_message.user_id == "user-uuid-123"
            assert mock_message.organization_id == "org-uuid-456"
    
    @pytest.mark.asyncio
    async def test_exception_handling(self, sample_postmark_payload):
        """Test proper exception handling in webhook."""
        # Arrange
        controller = WebhookController()
        mock_request = Mock()
        payload = PostmarkWebhookPayload(**sample_postmark_payload)
        
        with patch('cellophanemail.routes.webhooks.UserService.get_user_by_shield_address', new_callable=AsyncMock) as mock_user_service:
            # Setup mock to raise exception
            mock_user_service.side_effect = Exception("Database error")
            
            # Act
            response = await controller.handle_postmark_inbound(mock_request, payload)
            
            # Assert
            assert response.status_code == HTTP_400_BAD_REQUEST
            response_data = response.content
            assert response_data["error"] == "Internal processing error"
            assert response_data["message_id"] == "msg-123456"