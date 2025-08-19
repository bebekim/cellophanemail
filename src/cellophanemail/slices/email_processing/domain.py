"""Domain objects for Email Processing Vertical Slice.

TDD GREEN PHASE: Minimal implementation to pass failing tests.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from uuid import UUID

from cellophanemail.core.email_message import EmailMessage


@dataclass
class ProcessEmailCommand:
    """Command to process an email through the vertical slice.
    
    TDD: Created to satisfy test_email_processing_command_and_result_domain_objects
    """
    email_message: EmailMessage
    organization_id: str
    user_id: str


@dataclass
class EmailProcessingResult:
    """Result of email processing through the vertical slice.
    
    TDD: Created to satisfy test_email_processing_command_and_result_domain_objects
    """
    email_id: UUID
    should_forward: bool
    block_reason: Optional[str] = None
    toxicity_score: float = 0.0
    horsemen_detected: List[str] = field(default_factory=list)
    ai_analysis: Dict[str, Any] = field(default_factory=dict)
    processing_time_ms: float = 0.0