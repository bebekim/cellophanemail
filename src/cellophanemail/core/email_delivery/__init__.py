"""Email delivery plugin architecture."""

from .factory import EmailSenderFactory
from .base import BaseEmailSender
from .senders.smtp_sender import SMTPEmailSender
from .senders.postmark_sender import PostmarkEmailSender

__all__ = [
    'EmailSenderFactory',
    'BaseEmailSender', 
    'SMTPEmailSender',
    'PostmarkEmailSender'
]