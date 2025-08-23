"""Email protection feature - Streamlined LLM-based analysis and filtering."""

from .processor import EmailProtectionProcessor
from .streamlined_processor import StreamlinedEmailProtectionProcessor
from .graduated_decision_maker import ProtectionAction, GraduatedDecisionMaker
from .models import ProtectionResult

__all__ = [
    'EmailProtectionProcessor',
    'StreamlinedEmailProtectionProcessor', 
    'ProtectionAction',
    'GraduatedDecisionMaker',
    'ProtectionResult'
]