"""
TDD CYCLE 6 - RED PHASE: Component contract tests
This should fail initially because contracts aren't formally defined
"""
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

from cellophanemail.features.email_protection.memory_manager import MemoryManager
from cellophanemail.features.email_protection.ephemeral_email import EphemeralEmail
from cellophanemail.features.email_protection.in_memory_processor import InMemoryProcessor, ProcessingResult
from cellophanemail.features.email_protection.immediate_delivery import ImmediateDeliveryManager, DeliveryResult
from cellophanemail.features.email_protection.graduated_decision_maker import ProtectionAction


# Contract Interfaces (should be defined formally)
@runtime_checkable
class MemoryStorageContract(Protocol):
    """Contract for memory storage components."""
    
    async def store_email_safe(self, email: EphemeralEmail) -> bool:
        """Store email safely in memory."""
        ...
    
    async def get_email_safe(self, message_id: str) -> EphemeralEmail:
        """Retrieve email safely from memory."""
        ...
    
    async def get_all_emails(self) -> list[EphemeralEmail]:
        """Get all emails from memory."""
        ...
    
    async def remove_email(self, message_id: str) -> bool:
        """Remove email from memory."""
        ...
    
    def get_stats(self) -> dict:
        """Get memory usage statistics."""
        ...


@runtime_checkable
class EmailProcessorContract(Protocol):
    """Contract for email processing components."""
    
    async def process_email(self, email: EphemeralEmail) -> ProcessingResult:
        """Process email and return result."""
        ...


@runtime_checkable
class DeliveryManagerContract(Protocol):
    """Contract for email delivery components."""
    
    async def deliver_email(self, processing_result: ProcessingResult, email: EphemeralEmail) -> DeliveryResult:
        """Deliver processed email."""
        ...


@runtime_checkable
class LLMAnalyzerContract(Protocol):
    """Contract for LLM analysis components."""
    
    def analyze_toxicity(self, content: str) -> dict:
        """Analyze content for toxicity."""
        ...


class TestComponentContracts:
    """Test contracts between privacy pipeline components"""
    
    def test_memory_manager_implements_storage_contract(self):
        """
        RED TEST: MemoryManager should implement MemoryStorageContract
        """
        memory_manager = MemoryManager(capacity=100)
        
        # Contract compliance check
        assert isinstance(memory_manager, MemoryStorageContract), \
            "MemoryManager must implement MemoryStorageContract"
        
        # Verify all required methods exist
        required_methods = ['store_email_safe', 'get_email_safe', 'get_all_emails', 'remove_email', 'get_stats']
        for method_name in required_methods:
            assert hasattr(memory_manager, method_name), \
                f"MemoryManager missing required method: {method_name}"
    
    @pytest.mark.asyncio
    async def test_memory_manager_handles_ephemeral_email_contract(self):
        """
        RED TEST: MemoryManager must handle EphemeralEmail contract correctly
        """
        memory_manager = MemoryManager(capacity=100)
        
        # Create test email
        email = EphemeralEmail(
            message_id="contract-test-001",
            from_address="sender@example.com",
            to_addresses=["recipient@example.com"],
            subject="Contract Test",
            text_body="Testing contract compliance",
            user_email="user@example.com",
            ttl_seconds=300
        )
        
        # Contract: store_email_safe must accept EphemeralEmail and return bool
        result = await memory_manager.store_email_safe(email)
        assert isinstance(result, bool), "store_email_safe must return bool"
        assert result == True, "Storage should succeed for valid email"
        
        # Contract: get_email_safe must accept string ID and return EphemeralEmail or None
        retrieved = await memory_manager.get_email_safe("contract-test-001")
        assert retrieved is not None, "get_email_safe should retrieve stored email"
        assert isinstance(retrieved, EphemeralEmail), "get_email_safe must return EphemeralEmail"
        assert retrieved.message_id == "contract-test-001", "Retrieved email must match stored email"
        
        # Contract: get_all_emails must return list of EphemeralEmail
        all_emails = await memory_manager.get_all_emails()
        assert isinstance(all_emails, list), "get_all_emails must return list"
        assert len(all_emails) > 0, "get_all_emails should return stored emails"
        assert all(isinstance(e, EphemeralEmail) for e in all_emails), \
            "get_all_emails must return list of EphemeralEmail objects"
        
        # Contract: remove_email must accept string ID and return bool
        remove_result = await memory_manager.remove_email("contract-test-001")
        assert isinstance(remove_result, bool), "remove_email must return bool"
        assert remove_result == True, "Removal should succeed for existing email"
        
        # Contract: get_stats must return dict with specific fields
        stats = memory_manager.get_stats()
        assert isinstance(stats, dict), "get_stats must return dict"
        required_stats = ['current_emails', 'max_concurrent', 'available_slots']
        for stat in required_stats:
            assert stat in stats, f"get_stats missing required field: {stat}"
            assert isinstance(stats[stat], int), f"Stat {stat} must be integer"
    
    def test_in_memory_processor_implements_processor_contract(self):
        """
        RED TEST: InMemoryProcessor should implement EmailProcessorContract
        """
        processor = InMemoryProcessor()
        
        # Contract compliance check
        assert isinstance(processor, EmailProcessorContract), \
            "InMemoryProcessor must implement EmailProcessorContract"
        
        # Verify required methods exist
        assert hasattr(processor, 'process_email'), \
            "InMemoryProcessor missing required method: process_email"
    
    @pytest.mark.asyncio
    async def test_in_memory_processor_llm_analyzer_contract(self):
        """
        RED TEST: InMemoryProcessor must properly interface with LLM analyzer
        """
        # Mock LLM analyzer to test contract
        mock_analyzer = Mock()
        mock_analyzer.analyze_toxicity.return_value = {
            "toxicity_score": 0.15,
            "manipulation": False,
            "gaslighting": False,
            "stonewalling": False,
            "defensive": False,
            "action": "SAFE"
        }
        
        with patch('cellophanemail.features.email_protection.in_memory_processor.LlamaAnalyzer', 
                   return_value=mock_analyzer):
            processor = InMemoryProcessor(use_llm=True)
            
            # Create test email
            email = EphemeralEmail(
                message_id="llm-contract-001",
                from_address="sender@example.com",
                to_addresses=["recipient@example.com"],
                subject="LLM Contract Test",
                text_body="Testing LLM analyzer contract",
                user_email="user@example.com",
                ttl_seconds=300
            )
            
            # Contract: process_email must accept EphemeralEmail and return ProcessingResult
            result = await processor.process_email(email)
            
            assert isinstance(result, ProcessingResult), \
                "process_email must return ProcessingResult"
            
            # Contract: ProcessingResult must have required fields
            required_fields = ['action', 'toxicity_score', 'requires_delivery', 
                             'delivery_targets', 'processed_content', 'processing_time_ms']
            for field in required_fields:
                assert hasattr(result, field), f"ProcessingResult missing field: {field}"
            
            # Contract: action must be ProtectionAction enum
            assert isinstance(result.action, ProtectionAction), \
                "ProcessingResult.action must be ProtectionAction enum"
            
            # Contract: toxicity_score must be float between 0.0 and 1.0
            assert isinstance(result.toxicity_score, float), \
                "ProcessingResult.toxicity_score must be float"
            assert 0.0 <= result.toxicity_score <= 1.0, \
                "toxicity_score must be between 0.0 and 1.0"
            
            # Contract: requires_delivery must be bool
            assert isinstance(result.requires_delivery, bool), \
                "ProcessingResult.requires_delivery must be bool"
            
            # Contract: delivery_targets must be list of strings
            assert isinstance(result.delivery_targets, list), \
                "ProcessingResult.delivery_targets must be list"
            
            # Contract: LLM analyzer must be called with email content
            mock_analyzer.analyze_toxicity.assert_called_once()
            call_args = mock_analyzer.analyze_toxicity.call_args[0]
            assert "LLM Contract Test" in call_args[0], \
                "LLM analyzer must be called with email content"
    
    def test_immediate_delivery_implements_delivery_contract(self):
        """
        RED TEST: ImmediateDeliveryManager should implement DeliveryManagerContract
        """
        delivery_manager = ImmediateDeliveryManager()
        
        # Contract compliance check
        assert isinstance(delivery_manager, DeliveryManagerContract), \
            "ImmediateDeliveryManager must implement DeliveryManagerContract"
        
        # Verify required methods exist
        assert hasattr(delivery_manager, 'deliver_email'), \
            "ImmediateDeliveryManager missing required method: deliver_email"
    
    @pytest.mark.asyncio
    async def test_immediate_delivery_postmark_contract(self):
        """
        RED TEST: ImmediateDeliveryManager must handle delivery contract correctly
        """
        delivery_manager = ImmediateDeliveryManager(max_retries=2)
        
        # Create test processing result
        processing_result = ProcessingResult(
            action=ProtectionAction.FORWARD_CLEAN,
            toxicity_score=0.1,
            requires_delivery=True,
            delivery_targets=["user@example.com"],
            processed_content="Clean test content",
            processing_time_ms=150
        )
        
        # Create test email
        email = EphemeralEmail(
            message_id="delivery-contract-001",
            from_address="sender@example.com",
            to_addresses=["recipient@example.com"],
            subject="Delivery Contract Test",
            text_body="Testing delivery contract",
            user_email="user@example.com",
            ttl_seconds=300
        )
        
        # Contract: deliver_email must accept ProcessingResult and EphemeralEmail
        result = await delivery_manager.deliver_email(processing_result, email)
        
        # Contract: deliver_email must return DeliveryResult
        assert isinstance(result, DeliveryResult), \
            "deliver_email must return DeliveryResult"
        
        # Contract: DeliveryResult must have required fields
        required_fields = ['success', 'attempts', 'error_message', 'delivery_time_ms']
        for field in required_fields:
            assert hasattr(result, field), f"DeliveryResult missing field: {field}"
        
        # Contract: success must be bool
        assert isinstance(result.success, bool), \
            "DeliveryResult.success must be bool"
        
        # Contract: attempts must be positive integer
        assert isinstance(result.attempts, int), \
            "DeliveryResult.attempts must be int"
        assert result.attempts > 0, \
            "DeliveryResult.attempts must be positive"
    
    @pytest.mark.asyncio
    async def test_component_integration_contract_chain(self):
        """
        RED TEST: All components must work together following contracts
        """
        # Create component chain
        memory_manager = MemoryManager(capacity=100)
        processor = InMemoryProcessor(use_llm=False)  # Use heuristics for test
        delivery_manager = ImmediateDeliveryManager(max_retries=1)
        
        # Create test email
        email = EphemeralEmail(
            message_id="integration-contract-001",
            from_address="sender@example.com",
            to_addresses=["recipient@example.com"],
            subject="Integration Contract Test",
            text_body="Testing component integration contracts",
            user_email="user@example.com",
            ttl_seconds=300
        )
        
        # Contract Chain: Memory → Processor → Delivery
        
        # Step 1: Memory storage contract
        stored = await memory_manager.store_email_safe(email)
        assert stored, "Memory storage contract failed"
        
        # Step 2: Email retrieval contract
        retrieved_email = await memory_manager.get_email_safe("integration-contract-001")
        assert retrieved_email is not None, "Email retrieval contract failed"
        
        # Step 3: Processing contract
        processing_result = await processor.process_email(retrieved_email)
        assert isinstance(processing_result, ProcessingResult), "Processing contract failed"
        
        # Step 4: Delivery contract (if required)
        if processing_result.requires_delivery:
            delivery_result = await delivery_manager.deliver_email(processing_result, retrieved_email)
            assert isinstance(delivery_result, DeliveryResult), "Delivery contract failed"
        
        # Step 5: Cleanup contract
        removed = await memory_manager.remove_email("integration-contract-001")
        assert removed, "Cleanup contract failed"
        
        # Verify chain completed successfully
        final_email = await memory_manager.get_email_safe("integration-contract-001")
        assert final_email is None, "Email should be removed after processing"
    
    @pytest.mark.asyncio
    async def test_error_boundary_contracts(self):
        """
        RED TEST: Components must handle errors according to contracts
        """
        memory_manager = MemoryManager(capacity=1)  # Very small capacity
        
        # Create emails that will exceed capacity
        email1 = EphemeralEmail(
            message_id="boundary-001",
            from_address="sender@example.com",
            to_addresses=["recipient@example.com"],
            subject="Boundary Test 1",
            text_body="First email",
            user_email="user@example.com",
            ttl_seconds=300
        )
        
        email2 = EphemeralEmail(
            message_id="boundary-002",
            from_address="sender@example.com",
            to_addresses=["recipient@example.com"],
            subject="Boundary Test 2",
            text_body="Second email",
            user_email="user@example.com",
            ttl_seconds=300
        )
        
        # Contract: First storage should succeed
        result1 = await memory_manager.store_email_safe(email1)
        assert result1 == True, "First storage should succeed"
        
        # Contract: Second storage should fail gracefully (return False, not exception)
        result2 = await memory_manager.store_email_safe(email2)
        assert result2 == False, "Storage should fail gracefully when at capacity"
        
        # Contract: get_email_safe should handle non-existent emails gracefully
        non_existent = await memory_manager.get_email_safe("does-not-exist")
        assert non_existent is None, "get_email_safe should return None for non-existent emails"
        
        # Contract: remove_email should handle non-existent emails gracefully
        remove_non_existent = await memory_manager.remove_email("does-not-exist")
        assert remove_non_existent == False, "remove_email should return False for non-existent emails"
    
    @pytest.mark.asyncio
    async def test_data_integrity_contracts(self):
        """
        RED TEST: Components must preserve data integrity according to contracts
        """
        memory_manager = MemoryManager(capacity=100)
        
        # Create test email with specific data
        original_email = EphemeralEmail(
            message_id="integrity-test-001",
            from_address="original@example.com",
            to_addresses=["target@example.com"],
            subject="Data Integrity Test",
            text_body="Original content that must be preserved",
            user_email="user@example.com",
            ttl_seconds=300
        )
        
        # Store and retrieve
        await memory_manager.store_email_safe(original_email)
        retrieved_email = await memory_manager.get_email_safe("integrity-test-001")
        
        # Contract: All data must be preserved exactly
        assert retrieved_email.message_id == original_email.message_id, \
            "message_id must be preserved"
        assert retrieved_email.from_address == original_email.from_address, \
            "from_address must be preserved"
        assert retrieved_email.to_addresses == original_email.to_addresses, \
            "to_addresses must be preserved"
        assert retrieved_email.subject == original_email.subject, \
            "subject must be preserved"
        assert retrieved_email.text_body == original_email.text_body, \
            "text_body must be preserved"
        assert retrieved_email.user_email == original_email.user_email, \
            "user_email must be preserved"
        assert retrieved_email.ttl_seconds == original_email.ttl_seconds, \
            "ttl_seconds must be preserved"
        
        # Contract: TTL expiration must work correctly
        # Manually expire the email
        retrieved_email._created_at = time.time() - 400  # 400 seconds ago
        assert retrieved_email.is_expired == True, \
            "Email must be marked as expired after TTL"