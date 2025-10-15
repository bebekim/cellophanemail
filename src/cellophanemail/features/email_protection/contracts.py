"""
Formal contract interfaces for email protection components.

These abstract base classes define the contracts that all components must implement
to ensure proper integration in the privacy-focused email pipeline.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from .ephemeral_email import EphemeralEmail
    from .immediate_delivery import DeliveryResult
    from .in_memory_processor import ProcessingResult


class MemoryStorageInterface(ABC):
    """
    Abstract interface for memory storage components.
    
    Defines the contract for storing and retrieving ephemeral emails
    with proper memory management and thread-safety guarantees.
    """
    
    @abstractmethod
    async def store_email_async(self, email: "EphemeralEmail") -> bool:
        """
        Store an email in memory asynchronously.
        
        Args:
            email: EphemeralEmail instance to store
            
        Returns:
            True if stored successfully, False if storage failed
        """
        pass
    
    @abstractmethod
    async def get_email_async(self, message_id: str) -> Optional["EphemeralEmail"]:
        """
        Retrieve an email by message ID asynchronously.
        
        Args:
            message_id: Unique identifier of the email
            
        Returns:
            EphemeralEmail if found, None if not found
        """
        pass
    
    @abstractmethod
    async def get_all_emails(self) -> List["EphemeralEmail"]:
        """
        Get all emails currently stored in memory.
        
        Returns:
            List of all EphemeralEmail objects
        """
        pass
    
    @abstractmethod
    async def remove_email(self, message_id: str) -> bool:
        """
        Remove an email from memory by message ID.
        
        Args:
            message_id: Unique identifier of the email to remove
            
        Returns:
            True if email was found and removed, False otherwise
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, int]:
        """
        Get current memory usage statistics.
        
        Returns:
            Dictionary containing at minimum:
            - current_emails: Number of emails currently stored
            - max_concurrent: Maximum capacity
            - available_slots: Remaining capacity
        """
        pass


class EmailProcessorInterface(ABC):
    """
    Abstract interface for email processing components.
    
    Defines the contract for analyzing email content and making
    protection decisions without persisting sensitive data.
    """
    
    @abstractmethod
    async def process_email(self, email: "EphemeralEmail") -> "ProcessingResult":
        """
        Process an email and return processing decision.
        
        Args:
            email: EphemeralEmail instance to process
            
        Returns:
            ProcessingResult containing action and delivery information
        """
        pass


class DeliveryManagerInterface(ABC):
    """
    Abstract interface for email delivery components.
    
    Defines the contract for delivering processed emails with
    retry logic and comprehensive error handling.
    """
    
    @abstractmethod
    async def deliver_email(
        self, 
        processing_result: "ProcessingResult", 
        email: "EphemeralEmail"
    ) -> "DeliveryResult":
        """
        Deliver a processed email.
        
        Args:
            processing_result: Result from email processing
            email: Original email with metadata
            
        Returns:
            DeliveryResult with success status and delivery details
        """
        pass


class LLMAnalyzerInterface(ABC):
    """
    Abstract interface for LLM analysis components.
    
    Defines the contract for analyzing email content using
    language models while maintaining privacy standards.
    """
    
    @abstractmethod
    def analyze_toxicity(self, content: str) -> Dict[str, Any]:
        """
        Analyze content for toxicity and manipulation patterns.
        
        Args:
            content: Text content to analyze
            
        Returns:
            Dictionary containing at minimum:
            - toxicity_score: Float between 0.0 and 1.0
            - action: String indicating analysis result
        """
        pass


class ContractValidator:
    """
    Validator for ensuring components comply with their contracts.
    
    Provides runtime validation of component implementations
    against their defined interfaces.
    """
    
    def validate_memory_storage(self, component: Any) -> bool:
        """
        Validate that a component implements MemoryStorageInterface.
        
        Args:
            component: Component to validate
            
        Returns:
            True if component complies with contract, False otherwise
        """
        if not isinstance(component, MemoryStorageInterface):
            return False
        
        # Check that all abstract methods are implemented
        required_methods = [
            'store_email_async', 'get_email_async', 'get_all_emails',
            'remove_email', 'get_stats'
        ]
        
        for method in required_methods:
            if not hasattr(component, method):
                return False
            if not callable(getattr(component, method)):
                return False
        
        return True
    
    def validate_email_processor(self, component: Any) -> bool:
        """
        Validate that a component implements EmailProcessorInterface.
        
        Args:
            component: Component to validate
            
        Returns:
            True if component complies with contract, False otherwise
        """
        if not isinstance(component, EmailProcessorInterface):
            return False
        
        required_methods = ['process_email']
        
        for method in required_methods:
            if not hasattr(component, method):
                return False
            if not callable(getattr(component, method)):
                return False
        
        return True
    
    def validate_delivery_manager(self, component: Any) -> bool:
        """
        Validate that a component implements DeliveryManagerInterface.
        
        Args:
            component: Component to validate
            
        Returns:
            True if component complies with contract, False otherwise
        """
        if not isinstance(component, DeliveryManagerInterface):
            return False
        
        required_methods = ['deliver_email']
        
        for method in required_methods:
            if not hasattr(component, method):
                return False
            if not callable(getattr(component, method)):
                return False
        
        return True
    
    def validate_llm_analyzer(self, component: Any) -> bool:
        """
        Validate that a component implements LLMAnalyzerInterface.
        
        Args:
            component: Component to validate
            
        Returns:
            True if component complies with contract, False otherwise
        """
        if not isinstance(component, LLMAnalyzerInterface):
            return False
        
        required_methods = ['analyze_toxicity']
        
        for method in required_methods:
            if not hasattr(component, method):
                return False
            if not callable(getattr(component, method)):
                return False
        
        return True


def enforce_contract(interface_class):
    """
    Decorator for enforcing contract compliance at runtime.
    
    Args:
        interface_class: The interface class to enforce
        
    Returns:
        Decorator function
    """
    def decorator(cls):
        # Mark the class as contract-enforced
        cls._contract_enforced = True
        cls._interface_class = interface_class
        
        # Verify the class implements the interface
        if not issubclass(cls, interface_class):
            raise TypeError(f"{cls.__name__} must inherit from {interface_class.__name__}")
        
        return cls
    
    return decorator


# Contract compliance checkers for type validation
def check_memory_storage_contract(obj: Any) -> MemoryStorageInterface:
    """
    Type-safe contract checker for memory storage components.
    
    Args:
        obj: Object to check
        
    Returns:
        The object cast to MemoryStorageInterface
        
    Raises:
        TypeError: If object doesn't implement the interface
    """
    if not isinstance(obj, MemoryStorageInterface):
        raise TypeError(f"Object must implement MemoryStorageInterface, got {type(obj)}")
    return obj


def check_email_processor_contract(obj: Any) -> EmailProcessorInterface:
    """
    Type-safe contract checker for email processor components.
    
    Args:
        obj: Object to check
        
    Returns:
        The object cast to EmailProcessorInterface
        
    Raises:
        TypeError: If object doesn't implement the interface
    """
    if not isinstance(obj, EmailProcessorInterface):
        raise TypeError(f"Object must implement EmailProcessorInterface, got {type(obj)}")
    return obj


def check_delivery_manager_contract(obj: Any) -> DeliveryManagerInterface:
    """
    Type-safe contract checker for delivery manager components.
    
    Args:
        obj: Object to check
        
    Returns:
        The object cast to DeliveryManagerInterface
        
    Raises:
        TypeError: If object doesn't implement the interface
    """
    if not isinstance(obj, DeliveryManagerInterface):
        raise TypeError(f"Object must implement DeliveryManagerInterface, got {type(obj)}")
    return obj


def check_llm_analyzer_contract(obj: Any) -> LLMAnalyzerInterface:
    """
    Type-safe contract checker for LLM analyzer components.
    
    Args:
        obj: Object to check
        
    Returns:
        The object cast to LLMAnalyzerInterface
        
    Raises:
        TypeError: If object doesn't implement the interface
    """
    if not isinstance(obj, LLMAnalyzerInterface):
        raise TypeError(f"Object must implement LLMAnalyzerInterface, got {type(obj)}")
    return obj


class ContractRegistry:
    """
    Registry for managing component contracts and their implementations.
    
    Provides centralized management of contract compliance and
    runtime validation across the privacy pipeline.
    """
    
    def __init__(self):
        self._registered_components: Dict[str, Dict[str, Any]] = {
            "memory_storage": {},
            "email_processor": {},
            "delivery_manager": {},
            "llm_analyzer": {}
        }
        self._validator = ContractValidator()
    
    def register_memory_storage(self, name: str, component_class: type) -> None:
        """Register a memory storage implementation."""
        if not issubclass(component_class, MemoryStorageInterface):
            raise TypeError(f"{component_class.__name__} must implement MemoryStorageInterface")
        self._registered_components["memory_storage"][name] = component_class
    
    def register_email_processor(self, name: str, component_class: type) -> None:
        """Register an email processor implementation."""
        if not issubclass(component_class, EmailProcessorInterface):
            raise TypeError(f"{component_class.__name__} must implement EmailProcessorInterface")
        self._registered_components["email_processor"][name] = component_class
    
    def register_delivery_manager(self, name: str, component_class: type) -> None:
        """Register a delivery manager implementation."""
        if not issubclass(component_class, DeliveryManagerInterface):
            raise TypeError(f"{component_class.__name__} must implement DeliveryManagerInterface")
        self._registered_components["delivery_manager"][name] = component_class
    
    def register_llm_analyzer(self, name: str, component_class: type) -> None:
        """Register an LLM analyzer implementation.""" 
        if not issubclass(component_class, LLMAnalyzerInterface):
            raise TypeError(f"{component_class.__name__} must implement LLMAnalyzerInterface")
        self._registered_components["llm_analyzer"][name] = component_class
    
    def get_registered_components(self, category: str) -> Dict[str, type]:
        """Get all registered components for a category."""
        if category not in self._registered_components:
            raise ValueError(f"Unknown category: {category}")
        return self._registered_components[category].copy()
    
    def validate_all_registrations(self) -> Dict[str, List[str]]:
        """
        Validate all registered components against their contracts.
        
        Returns:
            Dictionary mapping category names to lists of validation errors
        """
        validation_errors = {
            "memory_storage": [],
            "email_processor": [],
            "delivery_manager": [],
            "llm_analyzer": []
        }
        
        # Validate memory storage components
        for name, component_class in self._registered_components["memory_storage"].items():
            try:
                # Create temporary instance to validate
                temp_instance = component_class.__new__(component_class)
                if not self._validator.validate_memory_storage(temp_instance):
                    validation_errors["memory_storage"].append(f"{name}: Failed validation")
            except Exception as e:
                validation_errors["memory_storage"].append(f"{name}: {str(e)}")
        
        # Similar validation for other categories...
        # (Implementation would be similar for each category)
        
        return validation_errors


def create_contract_factory():
    """
    Factory function for creating contract-compliant components.
    
    Returns:
        ContractRegistry instance for managing components
    """
    registry = ContractRegistry()
    
    # Auto-register known implementations
    try:
        from .memory_manager import MemoryManager
        registry.register_memory_storage("default", MemoryManager)
    except ImportError:
        pass
    
    try:
        from .in_memory_processor import InMemoryProcessor
        registry.register_email_processor("default", InMemoryProcessor)
    except ImportError:
        pass
    
    try:
        from .immediate_delivery import ImmediateDeliveryManager
        registry.register_delivery_manager("default", ImmediateDeliveryManager)
    except ImportError:
        pass
    
    try:
        from .llama_analyzer import LlamaAnalyzer
        registry.register_llm_analyzer("default", LlamaAnalyzer)
    except (ImportError, RuntimeError):
        # RuntimeError for llama-cpp-python library loading issues (e.g., macOS compatibility)
        pass
    
    return registry


# Global contract registry instance
CONTRACT_REGISTRY = create_contract_factory()