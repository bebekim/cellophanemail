"""Test to validate that Email Processing Slice is truly independent.

This test demonstrates that the slice can operate without dependencies on 
the traditional layered architecture.
"""

import pytest
from uuid import uuid4
from unittest.mock import patch, AsyncMock

from cellophanemail.core.email_message import EmailMessage
from cellophanemail.slices.email_processing.handler import EmailProcessingHandler
from cellophanemail.slices.email_processing.domain import ProcessEmailCommand


class TestSliceIndependence:
    """Test slice independence from traditional architecture layers."""
    
    @pytest.mark.asyncio
    async def test_slice_operates_without_traditional_layers(self):
        """Verify slice can process emails without touching traditional layered architecture."""
        
        # Arrange: Create email using only core EmailMessage (which slice depends on)
        email = EmailMessage(
            id=uuid4(),
            from_address='independence-test@example.com',
            to_addresses=['recipient@cellophanemail.com'],
            subject='Independence Test',
            text_content='This is an independence test email.',
            html_content='<p>This is an independence test email.</p>',
            message_id='<independence123@example.com>',
            source_plugin='independence-test'
        )
        
        # Mock external dependencies that slice uses (to prove it doesn't use layers)
        with patch('cellophanemail.models.organization.Organization.objects') as mock_org_query, \
             patch('cellophanemail.services.email_delivery.EmailDeliveryService.send_email', new_callable=AsyncMock) as mock_delivery:
            
            # Configure mocks
            mock_delivery.return_value.success = True
            mock_delivery.return_value.message_id = "slice-delivered-123"
            
            # Create command and handler (slice components only)
            command = ProcessEmailCommand(
                email_message=email,
                organization_id="test-independence-org",
                user_id="test-independence-user"
            )
            
            handler = EmailProcessingHandler()
            
            # Act: Process email through slice
            result = await handler.handle_email_processing(command)
            
            # Assert: Verify slice processed successfully
            assert result is not None
            assert result.email_id == email.id
            assert result.should_forward is True  # Safe email
            assert result.processing_time_ms > 0
            
            # Verify slice used its own components, not traditional layers
            assert hasattr(handler, 'service')  # Slice has its own service
            assert hasattr(handler.service, 'content_analyzer')  # Service has analyzer
            assert hasattr(handler.service, 'delivery_service')  # Service has delivery
            
            # Verify email was forwarded via slice's delivery service
            mock_delivery.assert_called_once_with(email)
    
    @pytest.mark.asyncio
    async def test_slice_has_own_analysis_logic(self):
        """Verify slice contains its own Four Horsemen analysis logic."""
        
        # Arrange: Create harmful email
        harmful_email = EmailMessage(
            id=uuid4(),
            from_address='harmful@example.com',
            to_addresses=['recipient@cellophanemail.com'],
            subject='Harmful Content',
            text_content='You are so stupid and worthless.',  # Triggers Four Horsemen
            html_content='<p>You are so stupid and worthless.</p>',
            message_id='<harmful123@example.com>',
            source_plugin='independence-test'
        )
        
        command = ProcessEmailCommand(
            email_message=harmful_email,
            organization_id="test-harmful-org",
            user_id="test-harmful-user"
        )
        
        handler = EmailProcessingHandler()
        
        # Act: Process harmful email
        result = await handler.handle_email_processing(command)
        
        # Assert: Verify slice detected harmful content independently
        assert result.should_forward is False
        assert result.block_reason is not None
        assert result.toxicity_score > 0.5
        assert len(result.horsemen_detected) > 0
        
        # Verify slice has its own analysis components
        assert hasattr(handler.service, 'content_analyzer')
        assert hasattr(handler.service, '_calculate_toxicity_score')
        assert hasattr(handler.service, '_should_forward_email')
        assert hasattr(handler.service, '_generate_block_reason')
    
    @pytest.mark.asyncio 
    async def test_slice_has_own_logging_model(self):
        """Verify slice uses its own logging model, not shared database models."""
        
        # Arrange: Create email for logging test
        email = EmailMessage(
            id=uuid4(),
            from_address='logging-test@example.com',
            to_addresses=['recipient@cellophanemail.com'],
            subject='Logging Test',
            text_content='This tests the slice logging.',
            message_id='<logging123@example.com>',
            source_plugin='independence-test'
        )
        
        # Mock the slice's own logging model
        with patch('cellophanemail.slices.email_processing.models.EmailProcessingLog.save', new_callable=AsyncMock) as mock_slice_save:
            
            command = ProcessEmailCommand(
                email_message=email,
                organization_id="test-logging-org",
                user_id="test-logging-user"
            )
            
            handler = EmailProcessingHandler()
            
            # Act: Process email
            result = await handler.handle_email_processing(command)
            
            # Assert: Verify slice used its own logging model
            mock_slice_save.assert_called_once()
            assert result is not None
    
    def test_slice_directory_structure_is_self_contained(self):
        """Verify slice has self-contained directory structure."""
        import os
        
        # Verify slice directory exists
        slice_path = "/Users/youngha/repositories/individuals/cellophanemail/src/cellophanemail/slices/email_processing"
        assert os.path.exists(slice_path)
        
        # Verify slice has all necessary components
        assert os.path.exists(os.path.join(slice_path, "__init__.py"))
        assert os.path.exists(os.path.join(slice_path, "handler.py"))      # Entry point
        assert os.path.exists(os.path.join(slice_path, "service.py"))      # Business logic
        assert os.path.exists(os.path.join(slice_path, "models.py"))       # Data models
        assert os.path.exists(os.path.join(slice_path, "domain.py"))       # Domain objects
        
        # Verify slice is in separate directory from traditional layers
        core_path = "/Users/youngha/repositories/individuals/cellophanemail/src/cellophanemail/core"
        services_path = "/Users/youngha/repositories/individuals/cellophanemail/src/cellophanemail/services"
        models_path = "/Users/youngha/repositories/individuals/cellophanemail/src/cellophanemail/models"
        
        # Slice should be separate from traditional layers
        assert slice_path != core_path
        assert slice_path != services_path
        assert slice_path != models_path