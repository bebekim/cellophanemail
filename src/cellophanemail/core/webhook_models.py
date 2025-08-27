"""Shared webhook payload models to avoid circular imports."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class PostmarkWebhookPayload(BaseModel):
    """Postmark inbound webhook payload structure."""
    
    From: str
    FromName: Optional[str] = None
    To: str
    ToFull: Optional[List[Dict[str, str]]] = None
    Subject: str
    MessageID: str
    Date: str
    TextBody: Optional[str] = None
    HtmlBody: Optional[str] = None
    Tag: Optional[str] = None
    Headers: Optional[List[Dict[str, str]]] = None
    Attachments: Optional[List[Dict[str, Any]]] = None