"""Analysis caching service for cost optimization."""

import hashlib
import json
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AnalysisCacheService:
    """Cache service to reduce AI analysis costs through intelligent caching."""
    
    def __init__(self):
        # In production, use Redis. For now, simple in-memory cache
        self._cache = {}
        self._cache_stats = {
            'hits': 0,
            'misses': 0,
            'cost_saved_usd': 0.0
        }
        # Cache TTL based on content type
        self._cache_ttl = {
            'safe_business': timedelta(days=7),      # Business emails cache longer
            'safe_personal': timedelta(days=1),     # Personal emails cache shorter
            'suspicious': timedelta(hours=1),       # Suspicious content cache briefly
            'harmful': timedelta(minutes=30)        # Harmful content minimal cache
        }
    
    def _generate_cache_key(self, content: str, sender: str) -> str:
        """Generate cache key from content and sender."""
        # Normalize content for better cache hits
        normalized_content = content.lower().strip()
        # Hash to create consistent key while protecting privacy
        content_hash = hashlib.sha256(
            f"{normalized_content}:{sender}".encode()
        ).hexdigest()[:16]
        return f"analysis:{content_hash}"
    
    def _get_cache_category(self, classification: str, content: str) -> str:
        """Determine cache category for TTL selection."""
        business_indicators = [
            'unsubscribe', 'newsletter', 'receipt', 'invoice', 
            'order confirmation', 'delivery', 'account statement'
        ]
        
        if classification == 'SAFE':
            for indicator in business_indicators:
                if indicator in content.lower():
                    return 'safe_business'
            return 'safe_personal'
        elif classification in ['WARNING']:
            return 'suspicious'
        else:  # HARMFUL, ABUSIVE
            return 'harmful'
    
    def get_cached_analysis(self, content: str, sender: str) -> Optional[Dict]:
        """Get cached analysis result if available."""
        cache_key = self._generate_cache_key(content, sender)
        
        if cache_key in self._cache:
            cached_data = self._cache[cache_key]
            
            # Check if cache entry is still valid
            if datetime.now() < cached_data['expires_at']:
                self._cache_stats['hits'] += 1
                # Estimate cost savings (approximate Anthropic API cost)
                self._cache_stats['cost_saved_usd'] += 0.003  # ~$3 per 1000 tokens
                
                result = cached_data['result'].copy()
                result['cache_hit'] = True
                result['cached_at'] = cached_data['cached_at'].isoformat()
                
                logger.info(f"Cache HIT for analysis - saved $0.003")
                return result
            else:
                # Cache expired, remove entry
                del self._cache[cache_key]
        
        self._cache_stats['misses'] += 1
        return None
    
    def cache_analysis(self, content: str, sender: str, analysis_result: Dict) -> None:
        """Cache analysis result with appropriate TTL."""
        cache_key = self._generate_cache_key(content, sender)
        
        # Determine cache duration based on result
        classification = analysis_result.get('classification', 'SAFE')
        cache_category = self._get_cache_category(classification, content)
        ttl = self._cache_ttl[cache_category]
        
        cached_data = {
            'result': analysis_result.copy(),
            'cached_at': datetime.now(),
            'expires_at': datetime.now() + ttl,
            'cache_category': cache_category
        }
        
        self._cache[cache_key] = cached_data
        
        logger.info(f"Cached analysis result - category: {cache_category}, TTL: {ttl}")
    
    def get_cache_stats(self) -> Dict:
        """Get cache performance statistics."""
        total_requests = self._cache_stats['hits'] + self._cache_stats['misses']
        hit_rate = (self._cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_hits': self._cache_stats['hits'],
            'cache_misses': self._cache_stats['misses'],
            'hit_rate_percent': round(hit_rate, 2),
            'total_cost_saved_usd': round(self._cache_stats['cost_saved_usd'], 4),
            'cache_entries': len(self._cache)
        }
    
    def cleanup_expired_entries(self) -> int:
        """Remove expired cache entries to manage memory."""
        now = datetime.now()
        expired_keys = [
            key for key, data in self._cache.items()
            if now >= data['expires_at']
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        return len(expired_keys)
    
    def clear_cache(self) -> None:
        """Clear all cache entries (for testing/maintenance)."""
        entries_cleared = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared {entries_cleared} cache entries")


# Global cache instance
_analysis_cache = AnalysisCacheService()


def get_analysis_cache() -> AnalysisCacheService:
    """Get the global analysis cache instance."""
    return _analysis_cache