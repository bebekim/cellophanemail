"""
LLM Analyzer Integration Bridge

Provides a unified interface that can switch between privacy-focused local Llama
analysis and full-featured Anthropic/OpenAI analysis while maintaining contract
compliance and performance optimization.
"""

import os
import time
import logging
from enum import Enum
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass

from .contracts import LLMAnalyzerInterface
from .llama_analyzer import LlamaAnalyzer
from .consolidated_analyzer import ConsolidatedLLMAnalyzer
from .llm_analyzer import SimpleLLMAnalyzer

logger = logging.getLogger(__name__)


class AnalyzerMode(Enum):
    """Supported analyzer modes for the bridge."""
    PRIVACY = "privacy"      # Local Llama analyzer for privacy-focused processing
    ANTHROPIC = "anthropic"  # Anthropic Claude API for full-featured analysis
    OPENAI = "openai"        # OpenAI GPT API for full-featured analysis


@dataclass
class AnalyzerCacheEntry:
    """Cache entry for analyzer results."""
    content_hash: str
    result: Dict[str, Any]
    timestamp: float
    analyzer_mode: AnalyzerMode


class LLMAnalyzerBridge(LLMAnalyzerInterface):
    """
    Bridge between privacy-focused local analysis and full-featured cloud analysis.
    
    Provides a unified interface that can dynamically switch between local Llama
    analysis (for privacy) and cloud-based analysis (for full features) while
    maintaining contract compliance and performance optimization through caching.
    """
    
    def __init__(
        self,
        mode: AnalyzerMode = AnalyzerMode.PRIVACY,
        enable_fallback: bool = True,
        cache_enabled: bool = True,
        cache_ttl_seconds: int = 300
    ):
        """
        Initialize the LLM analyzer bridge.
        
        Args:
            mode: Primary analyzer mode to use
            enable_fallback: Whether to fallback to privacy mode on errors
            cache_enabled: Whether to enable result caching
            cache_ttl_seconds: Time-to-live for cache entries
        """
        self.mode = mode
        self.enable_fallback = enable_fallback
        self.cache_enabled = cache_enabled
        self.cache_ttl_seconds = cache_ttl_seconds
        
        # Performance tracking
        self._metrics = {
            "total_analyses": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_response_time_ms": 0.0,
            "fallback_count": 0,
            "error_count": 0
        }
        self._response_times = []
        
        # Result cache
        self._cache: Dict[str, AnalyzerCacheEntry] = {}
        
        # Initialize analyzers based on mode
        self._primary_analyzer = self._create_analyzer(mode)
        self._fallback_analyzer = None
        
        if enable_fallback and mode != AnalyzerMode.PRIVACY:
            self._fallback_analyzer = self._create_analyzer(AnalyzerMode.PRIVACY)
        
        # Privacy configuration
        self.privacy_config = {
            "local_processing": mode == AnalyzerMode.PRIVACY,
            "data_retention": "none" if mode == AnalyzerMode.PRIVACY else "temporary",
            "api_calls": mode != AnalyzerMode.PRIVACY
        }
    
    def _create_analyzer(self, mode: AnalyzerMode) -> Union[LlamaAnalyzer, ConsolidatedLLMAnalyzer, None]:
        """Create analyzer instance based on mode."""
        try:
            if mode == AnalyzerMode.PRIVACY:
                return LlamaAnalyzer(temperature=0.1)
            elif mode == AnalyzerMode.ANTHROPIC:
                llm_analyzer = SimpleLLMAnalyzer(provider="anthropic")
                return ConsolidatedLLMAnalyzer(llm_analyzer=llm_analyzer, temperature=0.0)
            elif mode == AnalyzerMode.OPENAI:
                llm_analyzer = SimpleLLMAnalyzer(provider="openai")
                return ConsolidatedLLMAnalyzer(llm_analyzer=llm_analyzer, temperature=0.0)
            else:
                raise ValueError(f"Unsupported analyzer mode: {mode}")
        except Exception as e:
            logger.warning(f"Failed to create {mode.value} analyzer: {e}")
            
            # If we can't create any analyzer, we'll use a fallback approach
            # This is important for test environments where models aren't available
            if mode == AnalyzerMode.PRIVACY:
                # For privacy mode failures, we can't fallback further
                logger.error(f"Privacy analyzer creation failed: {e}")
                return None
            else:
                # For cloud analyzers, try to fallback to privacy mode
                try:
                    return LlamaAnalyzer(temperature=0.1)
                except Exception as fallback_error:
                    logger.error(f"Fallback to privacy analyzer also failed: {fallback_error}")
                    return None
    
    @classmethod
    def from_environment(cls) -> 'LLMAnalyzerBridge':
        """Create bridge configured from environment variables."""
        mode_str = os.getenv('LLM_ANALYZER_MODE', 'privacy').lower()
        
        try:
            mode = AnalyzerMode(mode_str)
        except ValueError:
            logger.warning(f"Invalid LLM_ANALYZER_MODE: {mode_str}, using privacy mode")
            mode = AnalyzerMode.PRIVACY
        
        enable_fallback = os.getenv('LLM_ANALYZER_FALLBACK', 'true').lower() == 'true'
        cache_enabled = os.getenv('LLM_ANALYZER_CACHE', 'true').lower() == 'true'
        cache_ttl = int(os.getenv('LLM_ANALYZER_CACHE_TTL', '300'))
        
        return cls(
            mode=mode,
            enable_fallback=enable_fallback,
            cache_enabled=cache_enabled,
            cache_ttl_seconds=cache_ttl
        )
    
    def analyze_toxicity(self, content: str) -> Dict[str, Any]:
        """
        Analyze content for toxicity using configured analyzer mode.
        
        Args:
            content: Text content to analyze
            
        Returns:
            Dictionary with toxicity analysis results
        """
        start_time = time.time()
        self._metrics["total_analyses"] += 1
        
        try:
            # Check cache first
            if self.cache_enabled:
                cached_result = self._get_cached_result(content)
                if cached_result:
                    self._metrics["cache_hits"] += 1
                    return cached_result
                else:
                    self._metrics["cache_misses"] += 1
            
            # Perform analysis with primary analyzer
            result = self._analyze_with_mode(content, self.mode, self._primary_analyzer)
            
            # Cache result
            if self.cache_enabled:
                self._cache_result(content, result, self.mode)
            
            # Update performance metrics
            response_time = int((time.time() - start_time) * 1000)
            self._response_times.append(response_time)
            if len(self._response_times) > 100:  # Keep last 100 measurements
                self._response_times = self._response_times[-100:]
            self._metrics["avg_response_time_ms"] = sum(self._response_times) / len(self._response_times)
            
            return result
            
        except Exception as e:
            self._metrics["error_count"] += 1
            logger.error(f"Primary analyzer failed: {e}")
            
            # Try fallback if enabled
            if self.enable_fallback and self._fallback_analyzer:
                try:
                    self._metrics["fallback_count"] += 1
                    logger.info("Attempting fallback to privacy analyzer")
                    
                    result = self._analyze_with_mode(content, AnalyzerMode.PRIVACY, self._fallback_analyzer)
                    
                    # Cache fallback result
                    if self.cache_enabled:
                        self._cache_result(content, result, AnalyzerMode.PRIVACY)
                    
                    return result
                    
                except Exception as fallback_error:
                    logger.error(f"Fallback analyzer also failed: {fallback_error}")
            
            # Return safe default if all analyzers fail
            return self._create_safe_fallback_result(str(e))
    
    def _analyze_with_mode(
        self, 
        content: str, 
        mode: AnalyzerMode, 
        analyzer: Union[LlamaAnalyzer, ConsolidatedLLMAnalyzer, None]
    ) -> Dict[str, Any]:
        """Analyze content with specific mode and analyzer."""
        if analyzer is None:
            # No analyzer available, return safe fallback
            return self._create_safe_fallback_result("Analyzer not available")
        
        if mode == AnalyzerMode.PRIVACY:
            # Use local Llama analyzer
            return analyzer.analyze_toxicity(content)
        else:
            # Use consolidated analyzer (async) - simplified approach
            import asyncio
            import concurrent.futures
            
            try:
                # Create coroutine for the analysis
                coro = analyzer.analyze_email(content, "unknown@sender.com")
                
                try:
                    # Try to get the current event loop
                    current_loop = asyncio.get_running_loop()
                    # We're in an async context - run in thread pool
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, coro)
                        consolidated_result = future.result(timeout=30)
                        
                except RuntimeError:
                    # No running event loop, safe to use asyncio.run
                    consolidated_result = asyncio.run(coro)
                    
            except Exception as async_error:
                logger.error(f"Async analysis failed: {async_error}")
                raise
            
            # Convert consolidated result to contract-compliant format
            return self._convert_consolidated_result(consolidated_result)
    
    def _convert_consolidated_result(self, consolidated_result) -> Dict[str, Any]:
        """Convert ConsolidatedAnalysis to contract-compliant format."""
        return {
            "toxicity_score": consolidated_result.toxicity_score,
            "manipulation": len(consolidated_result.manipulation_tactics) > 0,
            "gaslighting": any("gaslighting" in tactic.lower() 
                             for tactic in consolidated_result.manipulation_tactics),
            "stonewalling": any(h.horseman == "stonewalling" 
                              for h in consolidated_result.horsemen_detected),
            "defensive": any(h.horseman == "defensiveness" 
                           for h in consolidated_result.horsemen_detected),
            "action": "SAFE" if consolidated_result.safe else "TOXIC"
        }
    
    def _create_safe_fallback_result(self, error_message: str) -> Dict[str, Any]:
        """Create safe fallback result when all analyzers fail."""
        return {
            "toxicity_score": 0.5,  # Conservative middle score
            "manipulation": False,
            "gaslighting": False,
            "stonewalling": False,
            "defensive": False,
            "action": "SAFE",
            "error": f"Analysis failed: {error_message}",
            "fallback": True
        }
    
    def _get_cached_result(self, content: str) -> Optional[Dict[str, Any]]:
        """Get cached result if available and not expired."""
        content_hash = str(hash(content))
        
        if content_hash in self._cache:
            entry = self._cache[content_hash]
            if time.time() - entry.timestamp < self.cache_ttl_seconds:
                return entry.result
            else:
                # Remove expired entry
                del self._cache[content_hash]
        
        return None
    
    def _cache_result(self, content: str, result: Dict[str, Any], mode: AnalyzerMode) -> None:
        """Cache analysis result with improved memory management."""
        content_hash = str(hash(content))
        
        self._cache[content_hash] = AnalyzerCacheEntry(
            content_hash=content_hash,
            result=result.copy(),  # Store copy to prevent mutations
            timestamp=time.time(),
            analyzer_mode=mode
        )
        
        # Proactive cache cleanup to prevent memory issues
        self._cleanup_expired_entries()
        
        # Limit cache size with more efficient cleanup
        if len(self._cache) > 1000:
            self._evict_oldest_entries(keep_count=900)  # Keep some buffer
    
    def _cleanup_expired_entries(self) -> int:
        """Remove expired cache entries and return count removed."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time - entry.timestamp >= self.cache_ttl_seconds
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        return len(expired_keys)
    
    def _evict_oldest_entries(self, keep_count: int = 900) -> int:
        """Evict oldest entries, keeping only the most recent ones."""
        if len(self._cache) <= keep_count:
            return 0
        
        # Sort by timestamp and keep only the newest entries
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].timestamp,
            reverse=True  # Newest first
        )
        
        entries_to_keep = dict(sorted_entries[:keep_count])
        evicted_count = len(self._cache) - len(entries_to_keep)
        
        self._cache.clear()
        self._cache.update(entries_to_keep)
        
        return evicted_count
    
    def clear_cache(self) -> None:
        """Clear the analysis result cache."""
        self._cache.clear()
        logger.info("Analysis cache cleared")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        # Calculate cache efficiency
        total_requests = self._metrics["cache_hits"] + self._metrics["cache_misses"]
        cache_hit_rate = (
            self._metrics["cache_hits"] / total_requests 
            if total_requests > 0 else 0.0
        )
        
        return {
            **self._metrics,
            "cache_size": len(self._cache),
            "cache_hit_rate": round(cache_hit_rate, 3),
            "analyzer_mode": self.mode.value,
            "fallback_enabled": self.enable_fallback,
            "cache_enabled": self.cache_enabled,
            "cache_efficiency": {
                "hit_rate": cache_hit_rate,
                "total_requests": total_requests,
                "size_utilization": len(self._cache) / 1000.0  # Assuming max 1000
            }
        }
    
    def is_privacy_compliant(self) -> bool:
        """Check if current configuration is privacy compliant."""
        return self.mode == AnalyzerMode.PRIVACY
    
    @property
    def _consolidated_analyzer(self) -> Optional[ConsolidatedLLMAnalyzer]:
        """Access to internal consolidated analyzer (for testing)."""
        if self._primary_analyzer and isinstance(self._primary_analyzer, ConsolidatedLLMAnalyzer):
            return self._primary_analyzer
        return None