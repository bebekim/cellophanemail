"""Factory for creating email sender instances."""

from typing import Dict, Any
from .base import BaseEmailSender
from .senders.smtp_sender import SMTPEmailSender
from .senders.postmark_sender import PostmarkEmailSender


class EmailSenderFactory:
    """Factory for creating email sender plugins."""
    
    # Registry of available email senders
    _senders = {
        'smtp': SMTPEmailSender,
        'postmark': PostmarkEmailSender,
        # Future: 'gmail_api': GmailAPIEmailSender
    }
    
    @classmethod
    def create_sender(cls, sender_type: str, config: Dict[str, Any]) -> BaseEmailSender:
        """
        Create email sender instance based on type.
        
        Args:
            sender_type: Type of sender ('smtp' or 'postmark')
            config: Configuration dictionary with required settings
            
        Returns:
            BaseEmailSender: Configured email sender instance
            
        Raises:
            ValueError: If sender_type is unknown or config is invalid
        """
        if sender_type not in cls._senders:
            available_types = list(cls._senders.keys())
            raise ValueError(f"Unknown sender type '{sender_type}'. Available types: {available_types}")
        
        # Validate required configuration
        cls._validate_config(sender_type, config)
        
        # Create and return sender instance
        sender_class = cls._senders[sender_type]
        return sender_class(config)
    
    @classmethod
    def _validate_config(cls, sender_type: str, config: Dict[str, Any]) -> None:
        """
        Validate configuration for the given sender type.
        
        Args:
            sender_type: Type of sender to validate config for
            config: Configuration dictionary to validate
            
        Raises:
            ValueError: If required configuration is missing
        """
        # Common required fields for all senders
        required_common = ['SMTP_DOMAIN', 'EMAIL_USERNAME']
        
        # Sender-specific required fields
        required_specific = {
            'smtp': ['OUTBOUND_SMTP_HOST', 'OUTBOUND_SMTP_PORT', 'EMAIL_PASSWORD'],
            'postmark': ['POSTMARK_API_TOKEN']
        }
        
        # Check common required fields
        missing_common = [field for field in required_common if not config.get(field)]
        if missing_common:
            raise ValueError(f"Missing required configuration fields: {missing_common}")
        
        # Check sender-specific required fields
        if sender_type in required_specific:
            missing_specific = [field for field in required_specific[sender_type] if not config.get(field)]
            if missing_specific:
                raise ValueError(f"Missing required {sender_type} configuration fields: {missing_specific}")
    
    @classmethod
    def get_available_senders(cls) -> list[str]:
        """Get list of available sender types."""
        return list(cls._senders.keys())
    
    @classmethod
    def register_sender(cls, sender_type: str, sender_class: type) -> None:
        """
        Register a new email sender type.
        
        Args:
            sender_type: Name for the new sender type
            sender_class: Class that implements BaseEmailSender
        """
        if not issubclass(sender_class, BaseEmailSender):
            raise ValueError(f"Sender class must inherit from BaseEmailSender")
        
        cls._senders[sender_type] = sender_class