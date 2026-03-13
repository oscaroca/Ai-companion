"""
Rate limiting utility using token bucket algorithm.
Prevents API abuse and manages service quotas.
"""

import time
from typing import Dict, Tuple
from threading import Lock
from utils.logging_config import get_logger


logger = get_logger(__name__)


class RateLimiter:
    """Token bucket rate limiter for per-user rate limiting."""
    
    def __init__(self, rate: int, per: float):
        """
        Initialize rate limiter.
        
        Args:
            rate: Number of requests allowed
            per: Time period in seconds
        """
        self.rate = rate
        self.per = per
        self.allowance_per_second = rate / per
        
        # Store (tokens, last_check_time) for each user
        self.buckets: Dict[str, Tuple[float, float]] = {}
        self.lock = Lock()
    
    def acquire(self, user_id: str) -> bool:
        """
        Try to acquire a token for the user.
        
        Args:
            user_id: Unique identifier for the user/client
            
        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        with self.lock:
            current_time = time.time()
            
            # Initialize bucket for new user
            if user_id not in self.buckets:
                self.buckets[user_id] = (self.rate, current_time)
            
            tokens, last_check = self.buckets[user_id]
            
            # Calculate time passed and add tokens
            time_passed = current_time - last_check
            tokens += time_passed * self.allowance_per_second
            
            # Cap tokens at rate (bucket size)
            if tokens > self.rate:
                tokens = self.rate
            
            # Try to consume a token
            if tokens >= 1.0:
                tokens -= 1.0
                self.buckets[user_id] = (tokens, current_time)
                return True
            else:
                # Rate limit exceeded
                self.buckets[user_id] = (tokens, current_time)
                logger.warning(
                    f"Rate limit exceeded for user {user_id}. "
                    f"Limit: {self.rate} requests per {self.per} seconds"
                )
                return False
    
    def reset(self, user_id: str) -> None:
        """
        Reset rate limit for a user.
        
        Args:
            user_id: Unique identifier for the user/client
        """
        with self.lock:
            if user_id in self.buckets:
                self.buckets[user_id] = (self.rate, time.time())
                logger.info(f"Rate limit reset for user {user_id}")
    
    def get_remaining(self, user_id: str) -> int:
        """
        Get remaining tokens for a user.
        
        Args:
            user_id: Unique identifier for the user/client
            
        Returns:
            Number of remaining requests
        """
        with self.lock:
            if user_id not in self.buckets:
                return self.rate
            
            tokens, last_check = self.buckets[user_id]
            current_time = time.time()
            
            # Calculate current tokens
            time_passed = current_time - last_check
            tokens += time_passed * self.allowance_per_second
            
            if tokens > self.rate:
                tokens = self.rate
            
            return int(tokens)
    
    def get_retry_after(self, user_id: str) -> float:
        """
        Get time in seconds until next request is allowed.
        
        Args:
            user_id: Unique identifier for the user/client
            
        Returns:
            Seconds until next request is allowed (0 if allowed now)
        """
        with self.lock:
            if user_id not in self.buckets:
                return 0.0
            
            tokens, last_check = self.buckets[user_id]
            current_time = time.time()
            
            # Calculate current tokens
            time_passed = current_time - last_check
            tokens += time_passed * self.allowance_per_second
            
            if tokens >= 1.0:
                return 0.0
            
            # Calculate time needed to get 1 token
            tokens_needed = 1.0 - tokens
            time_needed = tokens_needed / self.allowance_per_second
            
            return time_needed


class MultiRateLimiter:
    """Manages multiple rate limiters for different services."""
    
    def __init__(self):
        """Initialize multi-rate limiter."""
        self.limiters: Dict[str, RateLimiter] = {}
    
    def add_limiter(self, name: str, rate: int, per: float) -> None:
        """
        Add a rate limiter for a service.
        
        Args:
            name: Service name (e.g., 'openai', 'wanikani', 'user_messages')
            rate: Number of requests allowed
            per: Time period in seconds
        """
        self.limiters[name] = RateLimiter(rate, per)
        logger.info(f"Added rate limiter '{name}': {rate} requests per {per} seconds")
    
    def acquire(self, name: str, user_id: str) -> bool:
        """
        Try to acquire a token from a specific limiter.
        
        Args:
            name: Service name
            user_id: Unique identifier for the user/client
            
        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        if name not in self.limiters:
            logger.warning(f"Rate limiter '{name}' not found, allowing request")
            return True
        
        return self.limiters[name].acquire(user_id)
    
    def reset(self, name: str, user_id: str) -> None:
        """
        Reset rate limit for a user on a specific service.
        
        Args:
            name: Service name
            user_id: Unique identifier for the user/client
        """
        if name in self.limiters:
            self.limiters[name].reset(user_id)
    
    def get_remaining(self, name: str, user_id: str) -> int:
        """
        Get remaining tokens for a user on a specific service.
        
        Args:
            name: Service name
            user_id: Unique identifier for the user/client
            
        Returns:
            Number of remaining requests
        """
        if name not in self.limiters:
            return 999999  # Unlimited if limiter not found
        
        return self.limiters[name].get_remaining(user_id)
    
    def get_retry_after(self, name: str, user_id: str) -> float:
        """
        Get time until next request is allowed on a specific service.
        
        Args:
            name: Service name
            user_id: Unique identifier for the user/client
            
        Returns:
            Seconds until next request is allowed
        """
        if name not in self.limiters:
            return 0.0
        
        return self.limiters[name].get_retry_after(user_id)
