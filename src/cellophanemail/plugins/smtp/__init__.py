"""SMTP Plugin for receiving emails via SMTP protocol."""

from .plugin import SMTPPlugin
from .server import SMTPHandler

__all__ = ["SMTPPlugin", "SMTPHandler"]