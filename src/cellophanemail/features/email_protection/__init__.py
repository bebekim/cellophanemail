"""Email protection feature - Four Horsemen analysis and filtering."""

from .analyzer import FourHorsemenAnalyzer
from .processor import EmailProtectionProcessor
from .models import ProtectionResult

__all__ = ['FourHorsemenAnalyzer', 'EmailProtectionProcessor', 'ProtectionResult']