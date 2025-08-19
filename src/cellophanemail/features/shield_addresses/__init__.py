"""Shield addresses feature - manages email aliases and user lookups."""

from .manager import ShieldAddressManager
from .models import ShieldAddressInfo

__all__ = ['ShieldAddressManager', 'ShieldAddressInfo']