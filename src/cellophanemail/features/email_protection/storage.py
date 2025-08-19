"""Storage for email protection logs - self-contained."""

import logging
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from ...providers.contracts import EmailMessage
from .models import ProtectionResult

logger = logging.getLogger(__name__)


class ProtectionLogStorage:
    """
    Stores email protection decisions and logs.
    This is a simple file-based implementation for demo.
    In production, this would use a proper database.
    """
    
    def __init__(self, log_dir: str = "protection_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
    async def log_protection_decision(
        self, 
        email: EmailMessage, 
        result: ProtectionResult
    ) -> None:
        """Log a protection decision."""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "message_id": email.message_id,
                "from": email.from_address,
                "to": email.to_addresses,
                "subject": email.subject,
                "shield_address": email.shield_address,
                "decision": {
                    "forwarded": result.should_forward,
                    "threat_level": result.analysis.threat_level.value if result.analysis else None,
                    "toxicity_score": result.analysis.toxicity_score if result.analysis else 0.0,
                    "horsemen_detected": [
                        h.horseman for h in (result.analysis.horsemen_detected if result.analysis else [])
                    ],
                    "block_reason": result.block_reason,
                    "processing_time_ms": result.analysis.processing_time_ms if result.analysis else 0
                }
            }
            
            # Save to daily log file
            today = datetime.now().strftime("%Y-%m-%d")
            log_file = self.log_dir / f"protection_{today}.jsonl"
            
            with open(log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
            
            logger.info(f"Logged protection decision for {email.message_id}")
            
        except Exception as e:
            logger.error(f"Failed to log protection decision: {e}")
    
    async def get_user_stats(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get protection statistics for a user.
        Simplified for demo - in production would query database.
        """
        return {
            "total_emails": 0,
            "forwarded": 0,
            "blocked": 0,
            "threat_breakdown": {
                "harassment": 0,
                "deception": 0,
                "exploitation": 0,
                "manipulation": 0
            }
        }