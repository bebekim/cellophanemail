"""
Advanced Rate Limiting System for Privacy-Focused Email Processing

Supports multiple strategies (token bucket, sliding window, fixed window),
dynamic limit adjustment, distributed deployment, and comprehensive monitoring.
"""

import time
import threading
import asyncio
from contextlib import asynccontextmanager
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
import hashlib

# Optional Redis import with graceful degradation
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)


class RateLimitStrategy(Enum):
    """Rate limiting strategies."""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window" 
    FIXED_WINDOW = "fixed_window"


@dataclass
class RateLimitResult:
    """Result of rate limit check."""
    allowed: bool
    remaining_requests: int
    retry_after_seconds: int
    current_limit: int
    window_usage: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.window_usage is None:
            self.window_usage = {}


@dataclass
class RateLimitViolation:
    """Details of a rate limit violation."""
    client_ip: str
    endpoint: str
    timestamp: float
    requests_in_window: int
    limit: int
    strategy: RateLimitStrategy


class RateLimitBackend(ABC):
    """Abstract backend for rate limiting storage."""
    
    @abstractmethod
    def get_count(self, key: str) -> int:
        pass
    
    @abstractmethod
    def increment(self, key: str, expire_seconds: int) -> int:
        pass
    
    @abstractmethod
    def get_window_data(self, key: str) -> List[float]:
        pass
    
    @abstractmethod
    def add_to_window(self, key: str, timestamp: float, window_size: int):
        pass


class InMemoryBackend(RateLimitBackend):
    """In-memory rate limiting backend."""
    
    def __init__(self):
        self._counts: Dict[str, Dict[str, Any]] = {}
        self._windows: Dict[str, List[float]] = {}
        self._lock = threading.RLock()
    
    def get_count(self, key: str) -> int:
        with self._lock:
            entry = self._counts.get(key, {})
            if entry.get('expires', 0) < time.time():
                return 0
            return entry.get('count', 0)
    
    def increment(self, key: str, expire_seconds: int) -> int:
        with self._lock:
            current_time = time.time()
            entry = self._counts.get(key, {'count': 0, 'expires': 0})
            
            if entry['expires'] < current_time:
                entry = {'count': 1, 'expires': current_time + expire_seconds}
            else:
                entry['count'] += 1
            
            self._counts[key] = entry
            return entry['count']
    
    def get_window_data(self, key: str) -> List[float]:
        with self._lock:
            return self._windows.get(key, [])
    
    def add_to_window(self, key: str, timestamp: float, window_size: int):
        with self._lock:
            window = self._windows.get(key, [])
            window.append(timestamp)
            
            # Keep only entries within window
            cutoff = timestamp - window_size
            window = [t for t in window if t > cutoff]
            
            self._windows[key] = window


class RedisBackend(RateLimitBackend):
    """Redis-backed rate limiting for distributed deployment."""
    
    def __init__(self, redis_url: str):
        if not REDIS_AVAILABLE:
            logger.warning("Redis not installed, falling back to in-memory backend")
            self.redis_client = None
            return
            
        try:
            self.redis_client = redis.from_url(
                redis_url,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            self.redis_client.ping()  # Test connection
            logger.info(f"Redis backend initialized successfully: {redis_url}")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}, falling back to in-memory")
            self.redis_client = None
    
    def get_count(self, key: str) -> int:
        if not self.redis_client:
            return 0
        try:
            count = self.redis_client.get(key)
            return int(count) if count else 0
        except Exception as e:
            logger.error(f"Redis get_count error: {e}")
            return 0
    
    def increment(self, key: str, expire_seconds: int) -> int:
        if not self.redis_client:
            return 0
        try:
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, expire_seconds)
            results = pipe.execute()
            return results[0]
        except Exception as e:
            logger.error(f"Redis increment error: {e}")
            return 0
    
    def get_window_data(self, key: str) -> List[float]:
        if not self.redis_client:
            return []
        try:
            data = self.redis_client.lrange(key, 0, -1)
            return [float(item) for item in data]
        except Exception as e:
            logger.error(f"Redis get_window_data error: {e}")
            return []
    
    def add_to_window(self, key: str, timestamp: float, window_size: int):
        if not self.redis_client:
            return
        try:
            cutoff = timestamp - window_size
            pipe = self.redis_client.pipeline()
            pipe.lpush(key, timestamp)
            pipe.ltrim(key, 0, 999)  # Keep max 1000 entries
            pipe.expire(key, window_size + 60)  # Extra TTL buffer
            pipe.execute()
            
            # Clean old entries (separate operation)
            self.redis_client.eval(
                "local items = redis.call('lrange', KEYS[1], 0, -1); "
                "redis.call('del', KEYS[1]); "
                "for i, item in ipairs(items) do "
                "  if tonumber(item) > tonumber(ARGV[1]) then "
                "    redis.call('rpush', KEYS[1], item) "
                "  end "
                "end",
                1, key, str(cutoff)
            )
        except Exception as e:
            logger.error(f"Redis add_to_window error: {e}")


class RateLimiter:
    """
    Advanced rate limiting system supporting multiple strategies and deployment models.
    
    Features:
    - Multiple strategies: token bucket, sliding window, fixed window
    - Dynamic limit adjustment based on system load
    - Distributed deployment with Redis backend
    - Comprehensive violation tracking and reporting
    """
    
    def __init__(self, strategy: RateLimitStrategy = RateLimitStrategy.FIXED_WINDOW,
                 distributed: bool = False, redis_url: str = None,
                 cache_size: int = 10000, cleanup_interval: int = 300):
        """
        Initialize rate limiter with specified strategy and backend.
        
        Args:
            strategy: Rate limiting strategy to use
            distributed: Enable distributed rate limiting with Redis
            redis_url: Redis connection URL for distributed backend
            cache_size: Maximum cache size for in-memory operations
            cleanup_interval: Cleanup interval in seconds for expired entries
        """
        self.strategy = strategy
        self.distributed = distributed
        self.cache_size = cache_size
        self.cleanup_interval = cleanup_interval
        
        # Initialize backend with fallback
        if distributed and redis_url:
            self.distributed_backend = RedisBackend(redis_url)
            # Fallback to in-memory if Redis fails
            if not self.distributed_backend.redis_client:
                self.distributed_backend = InMemoryBackend()
                self.distributed = False
        else:
            self.distributed_backend = InMemoryBackend()
        
        # Rate limiting configuration
        self._limits: Dict[str, Dict[str, Any]] = {}
        self._load_factors: Dict[str, float] = {}
        self._violations: List[RateLimitViolation] = []
        self._lock = threading.RLock()
        
        # Performance optimization: Local cache for frequent lookups
        self._local_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._last_cleanup = time.time()
        
        # Statistics tracking
        self._stats = {
            'total_checks': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'violations': 0,
            'backend_errors': 0
        }
        
        logger.info(f"RateLimiter initialized: strategy={strategy.value}, distributed={distributed}, cache_size={cache_size}")
    
    def configure_limit(self, endpoint: str, requests_per_minute: int, 
                       burst_size: Optional[int] = None, window_size_minutes: int = 1):
        """Configure rate limit for specific endpoint."""
        with self._lock:
            config = {
                'requests_per_minute': requests_per_minute,
                'burst_size': burst_size or requests_per_minute,
                'window_size_minutes': window_size_minutes,
                'window_size_seconds': window_size_minutes * 60
            }
            self._limits[endpoint] = config
            self._load_factors[endpoint] = 1.0  # Default no adjustment
            
        logger.info(f"Configured rate limit for {endpoint}: {requests_per_minute} req/min")
    
    def check_limit(self, client_ip: str, endpoint: str) -> RateLimitResult:
        """Check if request is within rate limits with optimized caching."""
        try:
            with self._lock:
                self._stats['total_checks'] += 1
                
                # Periodic cleanup
                self._maybe_cleanup()
                
                # Get endpoint configuration
                if endpoint not in self._limits:
                    self.configure_limit(endpoint, requests_per_minute=60)
                
                config = self._limits[endpoint]
                load_factor = self._load_factors.get(endpoint, 1.0)
                effective_limit = int(config['requests_per_minute'] * load_factor)
                
                # Generate rate limiting key
                key_prefix = f"rate_limit:{client_ip}:{endpoint}"
                
                # Check local cache first for recent results (if not distributed)
                if not self.distributed:
                    cache_result = self._check_local_cache(key_prefix)
                    if cache_result:
                        self._stats['cache_hits'] += 1
                        return cache_result
                    self._stats['cache_misses'] += 1
                
                # Perform rate limit check
                if self.strategy == RateLimitStrategy.TOKEN_BUCKET:
                    result = self._check_token_bucket(key_prefix, effective_limit, config, client_ip, endpoint)
                elif self.strategy == RateLimitStrategy.SLIDING_WINDOW:
                    result = self._check_sliding_window(key_prefix, effective_limit, config, client_ip, endpoint)
                else:  # FIXED_WINDOW
                    result = self._check_fixed_window(key_prefix, effective_limit, config, client_ip, endpoint)
                
                # Cache result locally if not distributed
                if not self.distributed:
                    self._cache_result(key_prefix, result)
                
                return result
                
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            self._stats['backend_errors'] += 1
            # Return permissive result on error to avoid blocking legitimate traffic
            return RateLimitResult(
                allowed=True,
                remaining_requests=100,
                retry_after_seconds=0,
                current_limit=100
            )
    
    def _check_token_bucket(self, key_prefix: str, limit: int, config: Dict[str, Any],
                           client_ip: str, endpoint: str) -> RateLimitResult:
        """Token bucket rate limiting implementation."""
        bucket_key = f"{key_prefix}:bucket"
        last_refill_key = f"{key_prefix}:refill"
        
        current_time = time.time()
        
        # Get current bucket state
        current_tokens = self.distributed_backend.get_count(bucket_key)
        last_refill = self.distributed_backend.get_count(last_refill_key)
        
        if last_refill == 0:
            last_refill = current_time
            current_tokens = config['burst_size']
        
        # Calculate tokens to add based on time passed
        time_passed = current_time - last_refill
        tokens_to_add = int(time_passed * (limit / 60.0))  # Convert per-minute to per-second
        current_tokens = min(config['burst_size'], current_tokens + tokens_to_add)
        
        if current_tokens > 0:
            # Allow request, consume token
            current_tokens -= 1
            self.distributed_backend.increment(bucket_key, 3600)  # 1 hour expiry
            self.distributed_backend.increment(last_refill_key, 3600)
            
            return RateLimitResult(
                allowed=True,
                remaining_requests=current_tokens,
                retry_after_seconds=0,
                current_limit=limit
            )
        else:
            # Rate limited
            self._record_violation(client_ip, endpoint, limit, current_tokens)
            retry_after = int(60.0 / limit)  # Time until next token
            
            return RateLimitResult(
                allowed=False,
                remaining_requests=0,
                retry_after_seconds=retry_after,
                current_limit=limit
            )
    
    def _check_sliding_window(self, key_prefix: str, limit: int, config: Dict[str, Any],
                             client_ip: str, endpoint: str) -> RateLimitResult:
        """Sliding window rate limiting implementation."""
        window_key = f"{key_prefix}:window"
        current_time = time.time()
        window_size = config['window_size_seconds']
        
        # Add current request to window
        self.distributed_backend.add_to_window(window_key, current_time, window_size)
        
        # Get requests in current window
        window_data = self.distributed_backend.get_window_data(window_key)
        requests_in_window = len([t for t in window_data if t > (current_time - window_size)])
        
        if requests_in_window <= limit:
            return RateLimitResult(
                allowed=True,
                remaining_requests=limit - requests_in_window,
                retry_after_seconds=0,
                current_limit=limit,
                window_usage={'requests_in_window': requests_in_window, 'window_size': window_size}
            )
        else:
            self._record_violation(client_ip, endpoint, limit, requests_in_window)
            
            # Calculate retry time based on oldest request
            if window_data:
                oldest_request = min(window_data)
                retry_after = max(1, int((oldest_request + window_size) - current_time))
            else:
                retry_after = window_size
            
            return RateLimitResult(
                allowed=False,
                remaining_requests=0,
                retry_after_seconds=retry_after,
                current_limit=limit,
                window_usage={'requests_in_window': requests_in_window, 'window_size': window_size}
            )
    
    def _check_fixed_window(self, key_prefix: str, limit: int, config: Dict[str, Any],
                           client_ip: str, endpoint: str) -> RateLimitResult:
        """Fixed window rate limiting implementation."""
        window_key = f"{key_prefix}:fixed"
        window_size = config['window_size_seconds']
        
        # Increment counter for current window
        current_count = self.distributed_backend.increment(window_key, window_size)
        
        if current_count <= limit:
            return RateLimitResult(
                allowed=True,
                remaining_requests=limit - current_count,
                retry_after_seconds=0,
                current_limit=limit
            )
        else:
            self._record_violation(client_ip, endpoint, limit, current_count)
            
            return RateLimitResult(
                allowed=False,
                remaining_requests=0,
                retry_after_seconds=window_size,
                current_limit=limit
            )
    
    def adjust_limit_for_load(self, endpoint: str, load_factor: float):
        """Adjust rate limits based on system load."""
        with self._lock:
            if endpoint in self._limits:
                self._load_factors[endpoint] = load_factor
                logger.info(f"Adjusted rate limit for {endpoint} by factor {load_factor}")
    
    def _check_local_cache(self, key: str) -> Optional[RateLimitResult]:
        """Check local cache for recent rate limit results."""
        if key not in self._local_cache:
            return None
        
        cache_entry = self._local_cache[key]
        cache_time = self._cache_timestamps.get(key, 0)
        
        # Cache valid for 1 second
        if time.time() - cache_time < 1.0:
            return cache_entry
        
        # Clean expired cache entry
        del self._local_cache[key]
        if key in self._cache_timestamps:
            del self._cache_timestamps[key]
        
        return None
    
    def _cache_result(self, key: str, result: RateLimitResult):
        """Cache rate limit result locally with intelligent caching strategy."""
        # Only cache successful results that aren't close to the limit
        # Don't cache if remaining requests is low (within 10% of limit) to ensure accurate limiting
        if result.allowed and result.remaining_requests > (result.current_limit * 0.1):
            self._local_cache[key] = result
            self._cache_timestamps[key] = time.time()
            
            # Maintain cache size limit
            if len(self._local_cache) > self.cache_size:
                # Remove oldest entries
                oldest_keys = sorted(
                    self._cache_timestamps.items(),
                    key=lambda x: x[1]
                )[:len(self._local_cache) - self.cache_size + 100]  # Remove extra for buffer
                
                for old_key, _ in oldest_keys:
                    self._local_cache.pop(old_key, None)
                    self._cache_timestamps.pop(old_key, None)
    
    def _maybe_cleanup(self):
        """Perform periodic cleanup of expired data."""
        current_time = time.time()
        if current_time - self._last_cleanup < self.cleanup_interval:
            return
        
        self._last_cleanup = current_time
        
        # Clean expired cache entries
        expired_keys = [
            key for key, timestamp in self._cache_timestamps.items()
            if current_time - timestamp > 60  # 1 minute expiry
        ]
        
        for key in expired_keys:
            self._local_cache.pop(key, None)
            self._cache_timestamps.pop(key, None)
        
        # Clean old violations (keep last 24 hours)
        cutoff_time = current_time - 86400
        self._violations = [
            v for v in self._violations
            if v.timestamp > cutoff_time
        ]
        
        logger.debug(f"Cleanup completed: removed {len(expired_keys)} cache entries, "
                    f"{len(self._violations)} violations remaining")
    
    def _record_violation(self, client_ip: str, endpoint: str, limit: int, current_count: int):
        """Record rate limit violation for monitoring."""
        self._stats['violations'] += 1
        
        violation = RateLimitViolation(
            client_ip=client_ip,
            endpoint=endpoint,
            timestamp=time.time(),
            requests_in_window=current_count,
            limit=limit,
            strategy=self.strategy
        )
        
        # Keep only recent violations (last 1000)
        self._violations.append(violation)
        if len(self._violations) > 1000:
            self._violations = self._violations[-1000:]
    
    def get_violations(self, since_timestamp: Optional[float] = None) -> List[RateLimitViolation]:
        """Get rate limit violations, optionally filtered by timestamp."""
        if since_timestamp is None:
            return self._violations.copy()
        return [v for v in self._violations if v.timestamp >= since_timestamp]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive rate limiter statistics."""
        with self._lock:
            current_time = time.time()
            recent_violations = [v for v in self._violations if v.timestamp > (current_time - 3600)]
            
            # Calculate cache hit rate
            total_requests = self._stats['cache_hits'] + self._stats['cache_misses']
            cache_hit_rate = (self._stats['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
            
            # Group violations by endpoint
            violations_by_endpoint = {}
            for violation in recent_violations:
                endpoint = violation.endpoint
                if endpoint not in violations_by_endpoint:
                    violations_by_endpoint[endpoint] = 0
                violations_by_endpoint[endpoint] += 1
            
            return {
                'strategy': self.strategy.value,
                'distributed': self.distributed,
                'backend_type': 'redis' if (self.distributed and 
                                          getattr(self.distributed_backend, 'redis_client', None)) else 'memory',
                'configured_endpoints': list(self._limits.keys()),
                'performance': {
                    'total_checks': self._stats['total_checks'],
                    'cache_hits': self._stats['cache_hits'],
                    'cache_misses': self._stats['cache_misses'],
                    'cache_hit_rate_percent': round(cache_hit_rate, 2),
                    'backend_errors': self._stats['backend_errors'],
                    'cache_size': len(self._local_cache),
                    'max_cache_size': self.cache_size
                },
                'violations': {
                    'total_violations': len(self._violations),
                    'recent_violations_1h': len(recent_violations),
                    'violations_by_endpoint': violations_by_endpoint
                },
                'configuration': {
                    'load_factors': self._load_factors.copy(),
                    'cleanup_interval': self.cleanup_interval,
                    'last_cleanup': self._last_cleanup
                }
            }
    
    async def get_stats_async(self) -> Dict[str, Any]:
        """Get statistics asynchronously (for async contexts)."""
        return await asyncio.get_event_loop().run_in_executor(None, self.get_stats)
    
    def reset_stats(self):
        """Reset performance statistics (useful for testing)."""
        with self._lock:
            self._stats = {
                'total_checks': 0,
                'cache_hits': 0,
                'cache_misses': 0,
                'violations': 0,
                'backend_errors': 0
            }
            logger.info("Rate limiter statistics reset")