"""Caching utilities for FastAPI."""

from functools import wraps
from typing import Callable, Any, Optional
import hashlib
import json
import pickle
from datetime import datetime, timedelta

# Simple in-memory cache implementation
_cache_store = {}


class SimpleCache:
    """Simple in-memory cache for development and small-scale deployments."""
    
    def __init__(self, default_timeout: int = 3600):
        self.default_timeout = default_timeout
        self.store = _cache_store
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self.store:
            value, expiry = self.store[key]
            if expiry is None or datetime.utcnow() < expiry:
                return value
            else:
                # Expired, remove from cache
                del self.store[key]
        return None
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        """Set value in cache with optional timeout."""
        if timeout is None:
            timeout = self.default_timeout
        
        expiry = datetime.utcnow() + timedelta(seconds=timeout) if timeout else None
        self.store[key] = (value, expiry)
    
    def delete(self, key: str) -> None:
        """Delete key from cache."""
        if key in self.store:
            del self.store[key]
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.store.clear()
    
    def cached(self, timeout: int = None, make_cache_key: Optional[Callable] = None):
        """
        Decorator to cache function results.
        
        Args:
            timeout: Cache timeout in seconds.
            make_cache_key: Optional function to generate cache key.
        
        Returns:
            Decorated function.
        """
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def wrapper(*args, **kwargs):
                # Generate cache key
                if make_cache_key:
                    cache_key = make_cache_key(f, *args, **kwargs)
                else:
                    # Default key generation
                    key_data = {
                        'function': f.__name__,
                        'args': str(args),
                        'kwargs': str(sorted(kwargs.items()))
                    }
                    cache_key = hashlib.md5(
                        json.dumps(key_data, sort_keys=True).encode()
                    ).hexdigest()
                
                # Try to get from cache
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # Compute and cache result
                result = f(*args, **kwargs)
                self.set(cache_key, result, timeout=timeout or self.default_timeout)
                return result
            
            return wrapper
        return decorator


# Global cache instance
cache = SimpleCache(default_timeout=3600)