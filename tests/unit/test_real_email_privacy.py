"""
Test privacy with REAL email examples to ensure no sensitive data leaks
"""
import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime

from cellophanemail.providers.contracts import EmailMessage
from cellophanemail.features.email_protection.models import ProtectionResult, AnalysisResult, ThreatLevel
from cellophanemail.features.email_protection.storage import ProtectionLogStorage


class TestRealEmailPrivacy:
    """Test privacy with realistic email content"""
    
    SENSITIVE_EMAILS = [
        {
            "subject": "CONFIDENTIAL: Salary Negotiation - $120,000 Offer",
            "from": "hr.director@company.com", 
            "to": "john.smith@company.com",
            "content": "Hi John, Following our discussion, we're pleased to offer you $120,000 annual salary with a $10,000 signing bonus. Please keep this confidential until we finalize the paperwork."
        },
        {
            "subject": "Medical Test Results - PRIVATE",
            "from": "dr.wilson@clinic.com",
            "to": "patient123@email.com", 
            "content": "Your recent blood work shows elevated cholesterol levels. Please schedule a follow-up appointment to discuss treatment options."
        },
        {
            "subject": "Legal Settlement - Attorney-Client Privilege",
            "from": "lawyer@lawfirm.com",
            "to": "client@example.com",
            "content": "The defendant has agreed to settle for $50,000. This communication is protected by attorney-client privilege and must remain confidential."
        },
        {
            "subject": "Credit Card Statement - Account ending 4567", 
            "from": "statements@bank.com",
            "to": "customer@email.com",
            "content": "Your credit card statement is ready. Current balance: $2,847.63. Recent transactions include: Target $156.78, Gas Station $45.23."
        }
    ]
    
    @pytest.mark.asyncio
    async def test_no_sensitive_content_in_logs(self):
        """Verify NO sensitive content appears in logs for realistic emails"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = ProtectionLogStorage(log_dir=temp_dir, privacy_safe=True)
            
            for i, email_data in enumerate(self.SENSITIVE_EMAILS):
                # Create realistic email
                email = EmailMessage(
                    message_id=f"real-email-{i:03d}",
                    from_address=email_data["from"],
                    to_addresses=[email_data["to"]],
                    subject=email_data["subject"],
                    text_body=email_data["content"],
                    shield_address=f"shield{i}@cellophanemail.com"
                )
                
                # Create protection result
                analysis = AnalysisResult(
                    safe=True,
                    toxicity_score=0.05,
                    threat_level=ThreatLevel.SAFE,
                    horsemen_detected=[],
                    reasoning="Clean email",
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
                
                # Log the decision
                await storage.log_protection_decision(email, result)
            
            # Check log files for sensitive data
            log_files = list(Path(temp_dir).glob("*.jsonl"))
            assert len(log_files) == 1, "Should create one log file"
            
            with open(log_files[0], 'r') as f:
                log_content = f.read()
            
            # Parse all log entries
            log_entries = [json.loads(line) for line in log_content.strip().split('\n')]
            assert len(log_entries) == len(self.SENSITIVE_EMAILS)
            
            # CRITICAL PRIVACY CHECKS
            self._assert_no_financial_data_leaked(log_content)
            self._assert_no_medical_data_leaked(log_content)
            self._assert_no_legal_data_leaked(log_content) 
            self._assert_no_personal_identifiers_leaked(log_content)
            self._assert_no_email_addresses_leaked(log_content)
            self._assert_no_subjects_leaked(log_content)
            
            # Verify only safe metadata is present
            for entry in log_entries:
                self._assert_only_safe_metadata(entry)
    
    def _assert_no_financial_data_leaked(self, log_content: str):
        """Ensure no financial information appears in logs"""
        financial_terms = [
            "$120,000", "$10,000", "salary", "bonus", "settlement", "$50,000",
            "$2,847.63", "$156.78", "$45.23", "credit card", "account", "4567"
        ]
        
        for term in financial_terms:
            assert term not in log_content, f"Financial data leaked: {term}"
    
    def _assert_no_medical_data_leaked(self, log_content: str):
        """Ensure no medical information appears in logs"""
        medical_terms = [
            "blood work", "cholesterol", "treatment", "clinic", "dr.wilson",
            "patient", "medical", "test results", "appointment"
        ]
        
        for term in medical_terms:
            assert term.lower() not in log_content.lower(), f"Medical data leaked: {term}"
    
    def _assert_no_legal_data_leaked(self, log_content: str):
        """Ensure no legal information appears in logs"""
        legal_terms = [
            "attorney-client", "privilege", "lawyer", "lawfirm", "defendant",
            "legal", "settlement", "confidential"  
        ]
        
        for term in legal_terms:
            assert term.lower() not in log_content.lower(), f"Legal data leaked: {term}"
    
    def _assert_no_personal_identifiers_leaked(self, log_content: str):
        """Ensure no personal identifiers appear in logs"""
        identifiers = [
            "john.smith", "patient123", "customer", "hr.director", "dr.wilson"
        ]
        
        for identifier in identifiers:
            assert identifier not in log_content.lower(), f"Personal identifier leaked: {identifier}"
    
    def _assert_no_email_addresses_leaked(self, log_content: str):
        """Ensure no email addresses appear in logs"""
        email_addresses = [
            "hr.director@company.com", "john.smith@company.com",
            "dr.wilson@clinic.com", "patient123@email.com",
            "lawyer@lawfirm.com", "client@example.com",
            "statements@bank.com", "customer@email.com"
        ]
        
        for email in email_addresses:
            assert email not in log_content, f"Email address leaked: {email}"
    
    def _assert_no_subjects_leaked(self, log_content: str):
        """Ensure no email subjects appear in logs"""
        subjects = [
            "CONFIDENTIAL", "Salary Negotiation", "Medical Test Results", 
            "PRIVATE", "Legal Settlement", "Attorney-Client Privilege",
            "Credit Card Statement", "Account ending 4567"
        ]
        
        for subject in subjects:
            assert subject not in log_content, f"Email subject leaked: {subject}"
    
    def _assert_only_safe_metadata(self, log_entry: dict):
        """Verify only safe metadata fields are present"""
        # Required safe fields
        required_fields = {"timestamp", "message_id", "decision"}
        assert all(field in log_entry for field in required_fields), \
            f"Missing required fields: {required_fields - log_entry.keys()}"
        
        # Forbidden content fields
        forbidden_fields = {"subject", "from", "to", "text_body", "html_body", "shield_address"}
        leaked_fields = forbidden_fields.intersection(log_entry.keys())
        assert not leaked_fields, f"Content fields leaked: {leaked_fields}"
        
        # Message ID should be hashed (not original)
        assert not log_entry["message_id"].startswith("real-email-"), \
            "Message ID should be hashed, not original"
        
        # Decision metadata should be present
        decision = log_entry["decision"]
        required_decision_fields = {"forwarded", "toxicity_score", "processing_time_ms"}
        assert all(field in decision for field in required_decision_fields), \
            f"Missing decision fields: {required_decision_fields - decision.keys()}"
    
    @pytest.mark.asyncio
    async def test_legacy_mode_shows_privacy_violations(self):
        """Verify that legacy mode DOES log content (for comparison)"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # EXPLICITLY disable privacy to show the difference
            storage = ProtectionLogStorage(log_dir=temp_dir, privacy_safe=False)
            
            email_data = self.SENSITIVE_EMAILS[0]  # Just test one
            email = EmailMessage(
                message_id="legacy-test-001",
                from_address=email_data["from"],
                to_addresses=[email_data["to"]],
                subject=email_data["subject"],
                text_body=email_data["content"],
                shield_address="shield@cellophanemail.com"
            )
            
            analysis = AnalysisResult(
                safe=True,
                toxicity_score=0.05,
                threat_level=ThreatLevel.SAFE,
                horsemen_detected=[],
                reasoning="Clean email",
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
            
            await storage.log_protection_decision(email, result)
            
            # Read log
            log_files = list(Path(temp_dir).glob("*.jsonl"))
            with open(log_files[0], 'r') as f:
                log_content = f.read()
            
            # In legacy mode, content SHOULD be leaked (this is why we need privacy mode)
            assert "CONFIDENTIAL" in log_content, "Legacy mode should log subjects"
            assert "hr.director@company.com" in log_content, "Legacy mode should log addresses"
            assert "Salary Negotiation" in log_content, "Legacy mode should log content"
            
            print("⚠️  Legacy mode privacy violations confirmed (this is why privacy mode exists!)")