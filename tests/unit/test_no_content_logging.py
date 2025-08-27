"""
TDD CYCLE 3 - RED PHASE: Test that NO email content is logged to database or files
This should fail initially because normal mode still logs content
"""
import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
from datetime import datetime

from cellophanemail.providers.contracts import EmailMessage
from cellophanemail.features.email_protection.models import ProtectionResult, AnalysisResult, ThreatLevel, HorsemanDetection
from cellophanemail.features.email_protection.storage import ProtectionLogStorage


class TestNoContentLogging:
    """Ensure NO email content is ever logged to files or database"""
    
    @pytest.mark.asyncio
    async def test_storage_never_logs_email_subjects(self):
        """
        RED TEST: storage.log_protection_decision should NEVER log email subjects
        """
        # Arrange - Create an email with sensitive subject
        email = EmailMessage(
            message_id="test-001",
            from_address="sender@example.com",
            to_addresses=["recipient@example.com"],
            subject="CONFIDENTIAL: Salary Review 2025",  # This should NEVER be logged
            text_body="This is private content",
            shield_address="shield@cellophanemail.com"
        )
        
        # Create a protection result
        analysis = AnalysisResult(
            safe=True,
            toxicity_score=0.1,
            threat_level=ThreatLevel.SAFE,
            horsemen_detected=[],
            reasoning="Test analysis",
            processing_time_ms=100
        )
        
        result = ProtectionResult(
            should_forward=True,
            analysis=analysis,
            block_reason=None,
            forwarded_to=None,
            logged_at=datetime.now(),
            message_id=email.message_id
        )
        
        # Create storage with temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = ProtectionLogStorage(log_dir=temp_dir)
            
            # Act - Log the protection decision
            await storage.log_protection_decision(email, result)
            
            # Assert - Check the log file
            log_files = list(Path(temp_dir).glob("*.jsonl"))
            assert len(log_files) == 1, "Should create one log file"
            
            with open(log_files[0], 'r') as f:
                log_content = f.read()
                log_entry = json.loads(log_content)
                
                # CRITICAL: Subject should NOT be in the log
                assert "subject" not in log_entry, "Email subject should NEVER be logged"
                assert "CONFIDENTIAL" not in log_content, "Sensitive content found in log"
                assert "Salary Review" not in log_content, "Private information leaked to log"
    
    @pytest.mark.asyncio
    async def test_storage_never_logs_email_addresses(self):
        """
        RED TEST: storage.log_protection_decision should NEVER log real email addresses
        """
        # Arrange
        email = EmailMessage(
            message_id="test-002",
            from_address="john.doe@company.com",  # PII - should not be logged
            to_addresses=["jane.smith@company.com"],  # PII - should not be logged
            subject="Meeting",
            text_body="Content",
            shield_address="shield123@cellophanemail.com"
        )
        
        analysis = AnalysisResult(
            safe=True,
            toxicity_score=0.1,
            threat_level=ThreatLevel.SAFE,
            horsemen_detected=[],
            reasoning="Test analysis",
            processing_time_ms=100
        )
        
        result = ProtectionResult(
            should_forward=True,
            analysis=analysis,
            block_reason=None,
            forwarded_to=None,
            logged_at=datetime.now(),
            message_id=email.message_id
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = ProtectionLogStorage(log_dir=temp_dir)
            
            # Act
            await storage.log_protection_decision(email, result)
            
            # Assert
            log_files = list(Path(temp_dir).glob("*.jsonl"))
            with open(log_files[0], 'r') as f:
                log_content = f.read()
                
                # CRITICAL: Real email addresses should NOT be in the log
                assert "john.doe@company.com" not in log_content, "Sender email leaked"
                assert "jane.smith@company.com" not in log_content, "Recipient email leaked"
                assert "john.doe" not in log_content, "Partial email leaked"
                assert "jane.smith" not in log_content, "Partial email leaked"
    
    @pytest.mark.asyncio
    async def test_storage_only_logs_metadata(self):
        """
        RED TEST: storage should only log privacy-safe metadata
        """
        email = EmailMessage(
            message_id="test-003",
            from_address="user@private.com",
            to_addresses=["recipient@private.com"],
            subject="Private Subject",
            text_body="Private email body content",
            html_body="<p>Private HTML content</p>",
            shield_address="shield@cellophanemail.com"
        )
        
        analysis = AnalysisResult(
            safe=False,
            toxicity_score=0.25,
            threat_level=ThreatLevel.MEDIUM,
            horsemen_detected=[],
            reasoning="Test analysis",
            processing_time_ms=200
        )
        
        result = ProtectionResult(
            should_forward=False,
            analysis=analysis,
            block_reason="Toxicity threshold exceeded",
            forwarded_to=None,
            logged_at=datetime.now(),
            message_id=email.message_id
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = ProtectionLogStorage(log_dir=temp_dir)
            
            # Act
            await storage.log_protection_decision(email, result)
            
            # Assert - Check what IS logged (only safe metadata)
            log_files = list(Path(temp_dir).glob("*.jsonl"))
            with open(log_files[0], 'r') as f:
                log_entry = json.loads(f.read())
                
                # These metadata fields SHOULD be present
                assert "timestamp" in log_entry
                assert "message_id" in log_entry
                assert "decision" in log_entry
                assert log_entry["decision"]["forwarded"] == False
                assert log_entry["decision"]["toxicity_score"] == 0.25
                
                # These content fields should NOT be present
                assert "subject" not in log_entry
                assert "from" not in log_entry
                assert "to" not in log_entry
                assert "text_body" not in log_entry
                assert "html_body" not in log_entry
                assert "Private" not in str(log_entry)
    
    @pytest.mark.asyncio
    async def test_storage_uses_hashed_identifiers(self):
        """
        RED TEST: storage should use hashed/anonymous identifiers instead of real data
        """
        email = EmailMessage(
            message_id="real-message-id-12345",
            from_address="realuser@realdomain.com",
            to_addresses=["realrecipient@realdomain.com"],
            subject="Real Subject Line",
            text_body="Real email content",
            shield_address="shield999@cellophanemail.com"
        )
        
        analysis = AnalysisResult(
            safe=True,
            toxicity_score=0.1,
            threat_level=ThreatLevel.SAFE,
            horsemen_detected=[],
            reasoning="Test analysis",
            processing_time_ms=100
        )
        
        result = ProtectionResult(
            should_forward=True,
            analysis=analysis,
            block_reason=None,
            forwarded_to=None,
            logged_at=datetime.now(),
            message_id=email.message_id
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = ProtectionLogStorage(log_dir=temp_dir)
            
            # Act
            await storage.log_protection_decision(email, result)
            
            # Assert
            log_files = list(Path(temp_dir).glob("*.jsonl"))
            with open(log_files[0], 'r') as f:
                log_entry = json.loads(f.read())
                
                # Message ID should be hashed or anonymized
                if "message_id" in log_entry:
                    # Should not contain the real message ID directly
                    assert log_entry["message_id"] != "real-message-id-12345", \
                        "Real message ID should be hashed"
                
                # No real domain names should appear
                assert "realdomain.com" not in str(log_entry)
                assert "realuser" not in str(log_entry)
                assert "realrecipient" not in str(log_entry)
    
    def test_protection_log_storage_has_privacy_mode(self):
        """
        RED TEST: ProtectionLogStorage should have privacy configuration
        """
        # This should be the new interface
        storage = ProtectionLogStorage(log_dir="logs", privacy_safe=True)
        assert storage.privacy_config.enable_content_logging == False
        assert storage.privacy_config.hash_identifiers == True
        
        # Default should be privacy-safe
        storage_default = ProtectionLogStorage(log_dir="logs")
        assert storage_default.privacy_config.enable_content_logging == False
        assert storage_default.privacy_config.hash_identifiers == True