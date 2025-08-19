"""Test-Driven Development tests for Email Processing Vertical Slice Architecture.

These tests define the expected behavior of the email processing slice BEFORE implementation.
Following strict TDD Red-Green-Refactor methodology.

RED PHASE: These tests MUST FAIL initially to drive the implementation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

# These imports will FAIL initially - that's the RED phase of TDD
try:
    from cellophanemail.slices.email_processing.handler import EmailProcessingHandler
    from cellophanemail.slices.email_processing.service import EmailProcessingService
    from cellophanemail.slices.email_processing.models import EmailProcessingLog
    from cellophanemail.slices.email_processing.domain import ProcessEmailCommand, EmailProcessingResult
except ImportError:
    # Expected to fail initially - this drives our implementation
    pass

from cellophanemail.core.email_message import EmailMessage


class TestEmailProcessingSlice:
    """Test Email Processing Vertical Slice - TDD Style."""
    
    @pytest.fixture
    def sample_email_message(self):
        """Create a sample email message for testing."""
        return EmailMessage(
            id=uuid4(),
            from_address='friend@example.com',
            to_addresses=['yh.kim@cellophanemail.com'],
            subject='Hello from friend',
            text_content='This is a friendly email message.',
            html_content='<p>This is a friendly email message.</p>',
            message_id='<friend123@example.com>',
            source_plugin='smtp'
        )
    
    @pytest.fixture
    def harmful_email_message(self):
        """Create a harmful email message for testing."""
        return EmailMessage(
            id=uuid4(),
            from_address='abusive@example.com',
            to_addresses=['yh.kim@cellophanemail.com'],
            subject='You are incompetent',
            text_content='You are so stupid and worthless. You never do anything right.',
            html_content='<p>You are so stupid and worthless. You never do anything right.</p>',
            message_id='<abuse123@example.com>',
            source_plugin='smtp'
        )
    
    @pytest.mark.asyncio
    async def test_email_processing_slice_handler_exists(self):
        """RED: Test that EmailProcessingHandler exists as entry point to the slice."""
        # This test MUST FAIL initially to drive implementation
        
        # Arrange: Setup test data
        handler = EmailProcessingHandler()
        
        # Act & Assert: Verify handler exists and has expected interface
        assert handler is not None
        assert hasattr(handler, 'handle_email_processing')
        assert callable(handler.handle_email_processing)
    
    @pytest.mark.asyncio
    async def test_email_processing_slice_processes_safe_email(self, sample_email_message):
        """RED: Test that slice can process safe emails independently."""
        # This test MUST FAIL initially
        
        # Arrange: Create command for email processing
        command = ProcessEmailCommand(
            email_message=sample_email_message,
            organization_id="test-org-123",
            user_id="test-user-456"
        )
        
        handler = EmailProcessingHandler()
        
        # Act: Process the email through the slice
        result = await handler.handle_email_processing(command)
        
        # Assert: Verify expected behavior
        assert isinstance(result, EmailProcessingResult)
        assert result.should_forward is True
        assert result.block_reason is None
        assert result.email_id == sample_email_message.id
        assert result.toxicity_score >= 0.0
        assert result.toxicity_score <= 1.0
        assert isinstance(result.horsemen_detected, list)
        assert result.processing_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_email_processing_slice_blocks_harmful_email(self, harmful_email_message):
        """RED: Test that slice blocks harmful emails independently."""
        # This test MUST FAIL initially
        
        # Arrange: Create command for harmful email processing
        command = ProcessEmailCommand(
            email_message=harmful_email_message,
            organization_id="test-org-123",
            user_id="test-user-456"
        )
        
        handler = EmailProcessingHandler()
        
        # Act: Process the harmful email through the slice
        result = await handler.handle_email_processing(command)
        
        # Assert: Verify harmful email is blocked
        assert isinstance(result, EmailProcessingResult)
        assert result.should_forward is False
        assert result.block_reason is not None
        assert "harmful" in result.block_reason.lower() or "blocked" in result.block_reason.lower() or "filtered" in result.block_reason.lower()
        assert result.toxicity_score > 0.5  # Should be high for harmful content
        assert len(result.horsemen_detected) > 0  # Should detect some horsemen
        assert result.processing_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_email_processing_slice_is_self_contained(self, sample_email_message):
        """RED: Test that slice works without dependencies on other layers."""
        # This test MUST FAIL initially
        
        # Arrange: Create minimal command
        command = ProcessEmailCommand(
            email_message=sample_email_message,
            organization_id="test-org",
            user_id="test-user"
        )
        
        # Act: Process without any external layer dependencies
        # The slice should handle its own models, services, and business logic
        handler = EmailProcessingHandler()
        result = await handler.handle_email_processing(command)
        
        # Assert: Verify slice processed independently
        assert result is not None
        assert hasattr(result, 'should_forward')
        assert hasattr(result, 'email_id')
        assert hasattr(result, 'processing_time_ms')
    
    @pytest.mark.asyncio
    async def test_email_processing_service_exists_within_slice(self):
        """RED: Test that slice contains its own service layer."""
        # This test MUST FAIL initially
        
        # Arrange & Act: Try to create service within slice
        service = EmailProcessingService()
        
        # Assert: Verify service exists and has expected methods
        assert service is not None
        assert hasattr(service, 'analyze_email_content')
        assert hasattr(service, 'check_organization_limits')
        assert hasattr(service, 'forward_email')
        assert callable(service.analyze_email_content)
        assert callable(service.check_organization_limits)
        assert callable(service.forward_email)
    
    @pytest.mark.asyncio
    async def test_email_processing_models_exist_within_slice(self):
        """RED: Test that slice contains its own domain models."""
        # This test MUST FAIL initially
        
        # Arrange & Act: Try to create slice-specific models
        log_entry = EmailProcessingLog(
            organization_id="test-org",
            user_id="test-user", 
            email_id=uuid4(),
            from_address="test@example.com",
            to_addresses=["recipient@example.com"],
            subject="Test Subject",
            status="processed",
            toxicity_score=0.1,
            horsemen_detected=["none"],
            processing_time_ms=150.5
        )
        
        # Assert: Verify model exists and has expected attributes
        assert log_entry is not None
        assert hasattr(log_entry, 'organization_id')
        assert hasattr(log_entry, 'user_id')
        assert hasattr(log_entry, 'email_id')
        assert hasattr(log_entry, 'status')
        assert hasattr(log_entry, 'toxicity_score')
        assert hasattr(log_entry, 'horsemen_detected')
        assert hasattr(log_entry, 'processing_time_ms')
    
    @pytest.mark.asyncio
    async def test_email_processing_command_and_result_domain_objects(self):
        """RED: Test that slice has proper domain objects for commands and results."""
        # This test MUST FAIL initially
        
        # Arrange: Create sample email message
        email_msg = EmailMessage(
            id=uuid4(),
            from_address='test@example.com',
            to_addresses=['recipient@example.com'],
            subject='Test',
            text_content='Test content',
            message_id='<test123@example.com>',
            source_plugin='smtp'
        )
        
        # Act: Create command domain object
        command = ProcessEmailCommand(
            email_message=email_msg,
            organization_id="test-org",
            user_id="test-user"
        )
        
        # Assert: Verify command has expected structure
        assert command is not None
        assert command.email_message == email_msg
        assert command.organization_id == "test-org"
        assert command.user_id == "test-user"
        
        # Act: Create result domain object
        result = EmailProcessingResult(
            email_id=email_msg.id,
            should_forward=True,
            block_reason=None,
            toxicity_score=0.1,
            horsemen_detected=[],
            ai_analysis={},
            processing_time_ms=100.0
        )
        
        # Assert: Verify result has expected structure
        assert result is not None
        assert result.email_id == email_msg.id
        assert result.should_forward is True
        assert result.block_reason is None
        assert result.toxicity_score == 0.1
        assert result.horsemen_detected == []
        assert result.ai_analysis == {}
        assert result.processing_time_ms == 100.0


class TestEmailProcessingSliceIntegration:
    """Integration tests for Email Processing Slice - TDD Style."""
    
    @pytest.fixture
    def sample_email_message(self):
        """Create a sample email message for testing."""
        return EmailMessage(
            id=uuid4(),
            from_address='friend@example.com',
            to_addresses=['yh.kim@cellophanemail.com'],
            subject='Hello from friend',
            text_content='This is a friendly email message.',
            html_content='<p>This is a friendly email message.</p>',
            message_id='<friend123@example.com>',
            source_plugin='smtp'
        )
    
    @pytest.mark.asyncio
    async def test_slice_integration_with_existing_email_message(self, sample_email_message):
        """RED: Test that slice integrates properly with existing EmailMessage."""
        # This test MUST FAIL initially
        
        # Arrange: Use existing EmailMessage from current codebase
        command = ProcessEmailCommand(
            email_message=sample_email_message,
            organization_id="integration-test-org",
            user_id="integration-test-user"
        )
        
        handler = EmailProcessingHandler()
        
        # Act: Process through slice
        result = await handler.handle_email_processing(command)
        
        # Assert: Verify integration works
        assert result.email_id == sample_email_message.id
        assert result.processing_time_ms > 0
        # Should work with existing EmailMessage structure
    
    @pytest.mark.asyncio 
    async def test_slice_logs_to_its_own_model(self, sample_email_message):
        """RED: Test that slice uses its own logging model, not shared layers."""
        # This test MUST FAIL initially
        
        # Arrange: Mock the slice's own database operations
        with patch('cellophanemail.slices.email_processing.models.EmailProcessingLog.save', new_callable=AsyncMock) as mock_save:
            command = ProcessEmailCommand(
                email_message=sample_email_message,
                organization_id="log-test-org", 
                user_id="log-test-user"
            )
            
            handler = EmailProcessingHandler()
            
            # Act: Process email
            result = await handler.handle_email_processing(command)
            
            # Assert: Verify slice used its own logging model
            mock_save.assert_called_once()
            assert result is not None


# TDD_HANDOFF_3: Test cases specified - convert to executable tests following Red-Green-Refactor
# 
# These failing tests now define the exact behavior we want from our Email Processing Vertical Slice:
# 
# 1. EmailProcessingHandler as the slice entry point
# 2. ProcessEmailCommand and EmailProcessingResult as domain objects  
# 3. EmailProcessingService with analysis, limits checking, and forwarding
# 4. EmailProcessingLog as slice-specific model
# 5. Self-contained behavior without cross-slice dependencies
# 6. Integration with existing EmailMessage structure
#
# NEXT STEP: Run these tests to confirm they FAIL (RED phase)
# THEN: Implement minimal code to make them pass (GREEN phase)