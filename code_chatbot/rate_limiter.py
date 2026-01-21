"""
Smart Rate Limiter with Adaptive Delays and Caching
Helps maximize chat usage within free tier limits
"""

import time
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from functools import lru_cache
import hashlib

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Adaptive rate limiter that:
    1. Tracks API usage per provider
    2. Implements smart delays
    3. Caches responses for repeated queries
    4. Provides usage statistics
    """
    
    def __init__(self, provider: str = "gemini"):
        self.provider = provider
        self.request_times = []
        self.token_usage = {"input": 0, "output": 0, "total": 0}
        self.last_request_time = None
        
        # Load configuration (with fallbacks if config file missing)
        try:
            import rate_limit_config as config
        except ImportError:
            # Use defaults if config not found
            class config:
                GEMINI_RPM = 15
                GEMINI_MIN_DELAY = 2.0
                GEMINI_BURST_DELAY = 8.0
                GROQ_RPM = 30
                GROQ_MIN_DELAY = 1.0
                GROQ_BURST_DELAY = 10.0
                ENABLE_CACHE = True
                CACHE_TTL = 300
        
        # Provider-specific limits
        self.limits = {
            "gemini": {
                "rpm": config.GEMINI_RPM,
                "min_delay": config.GEMINI_MIN_DELAY,
                "burst_delay": config.GEMINI_BURST_DELAY,
            },
            "groq": {
                "rpm": config.GROQ_RPM,
                "min_delay": config.GROQ_MIN_DELAY,
                "burst_delay": config.GROQ_BURST_DELAY,
            }
        }
        
        self.response_cache = {} if config.ENABLE_CACHE else None
        self.cache_ttl = config.CACHE_TTL
        
    def get_cache_key(self, query: str, context_hash: str = "") -> str:
        """Generate cache key for a query"""
        combined = f"{query}:{context_hash}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Check if we have a cached response"""
        if self.response_cache is None:
            return None
        if cache_key in self.response_cache:
            cached_data, timestamp = self.response_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                logger.info(f"🎯 Cache hit! Saved an API call.")
                return cached_data
            else:
                # Expired, remove it
                del self.response_cache[cache_key]
        return None
    
    def cache_response(self, cache_key: str, response: Dict[str, Any]):
        """Cache a response"""
        if self.response_cache is None:
            return
        self.response_cache[cache_key] = (response, time.time())
        # Keep cache size manageable
        if len(self.response_cache) > 100:
            # Remove oldest entries
            sorted_items = sorted(self.response_cache.items(), key=lambda x: x[1][1])
            for key, _ in sorted_items[:20]:  # Remove 20 oldest
                del self.response_cache[key]
    
    def calculate_smart_delay(self) -> float:
        """
        Calculate optimal delay based on recent usage.
        Returns delay in seconds.
        """
        config = self.limits.get(self.provider, self.limits["gemini"])
        
        # Clean old request times (older than 1 minute)
        cutoff = time.time() - 60
        self.request_times = [t for t in self.request_times if t > cutoff]
        
        # Check if we're approaching the rate limit
        requests_last_minute = len(self.request_times)
        
        if requests_last_minute >= config["rpm"] * 0.9:  # 90% of limit
            logger.warning(f"⚠️ Approaching rate limit ({requests_last_minute}/{config['rpm']} RPM)")
            return config["burst_delay"]
        elif requests_last_minute >= config["rpm"] * 0.7:  # 70% of limit
            return config["min_delay"] * 1.5
        else:
            return config["min_delay"]
    
    def wait_if_needed(self):
        """
        Smart wait that adapts to usage patterns.
        Only waits when necessary to avoid rate limits.
        """
        if self.last_request_time is None:
            self.last_request_time = time.time()
            self.request_times.append(time.time())
            return
        
        delay = self.calculate_smart_delay()
        elapsed = time.time() - self.last_request_time
        
        if elapsed < delay:
            wait_time = delay - elapsed
            logger.info(f"⏱️ Smart delay: waiting {wait_time:.1f}s to avoid rate limit...")
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
        self.request_times.append(time.time())
    
    def record_usage(self, input_tokens: int = 0, output_tokens: int = 0):
        """Track token usage for statistics"""
        self.token_usage["input"] += input_tokens
        self.token_usage["output"] += output_tokens
        self.token_usage["total"] += (input_tokens + output_tokens)
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        cutoff = time.time() - 60
        recent_requests = len([t for t in self.request_times if t > cutoff])
        
        return {
            "provider": self.provider,
            "requests_last_minute": recent_requests,
            "total_tokens": self.token_usage["total"],
            "input_tokens": self.token_usage["input"],
            "output_tokens": self.token_usage["output"],
            "cache_size": len(self.response_cache) if self.response_cache else 0
        }
    
    def reset_stats(self):
        """Reset usage statistics"""
        self.token_usage = {"input": 0, "output": 0, "total": 0}
        self.request_times = []
        logger.info("📊 Usage statistics reset")


# Global rate limiters (one per provider)
_rate_limiters: Dict[str, RateLimiter] = {}

def get_rate_limiter(provider: str) -> RateLimiter:
    """Get or create rate limiter for a provider"""
    if provider not in _rate_limiters:
        _rate_limiters[provider] = RateLimiter(provider)
    return _rate_limiters[provider]
