"""
LRU Cache Implementation with TTL support

This module provides LRU (Least Recently Used) cache implementations with:
- Size-based eviction (LRU policy)
- Time-based expiration (TTL)
- Hit rate statistics
- Thread-safe variant for concurrent access

Author: AI Assistant Optimization Project
Date: 2024-11-09
"""

from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Optional, Dict
import time
import threading


@dataclass
class CacheEntry:
    """Cache entry with metadata
    
    Attributes:
        value: The cached value
        timestamp: Creation time using time.monotonic() (immune to system clock changes)
        access_count: Number of times this entry has been accessed
    """
    value: Any
    timestamp: float
    access_count: int = 0


class LRUCache:
    """LRU Cache with TTL support (single-threaded use)
    
    This cache implements:
    - LRU eviction policy (removes least recently used items when full)
    - TTL-based expiration (removes items after specified time)
    - Hit rate statistics for performance monitoring
    
    Design notes:
    - Uses time.monotonic() for TTL to avoid system clock adjustment issues
    - Uses OrderedDict for efficient LRU implementation
    - Not thread-safe by design (use ThreadSafeLRUCache for concurrent access)
    
    Example:
        cache = LRUCache(max_size=100, ttl=60.0)
        cache.set("key", "value")
        value = cache.get("key")  # Returns "value"
        stats = cache.get_stats()  # {'hit_rate': 1.0, ...}
    """
    
    def __init__(self, max_size: int = 100, ttl: float = 60.0):
        """Initialize LRU cache
        
        Args:
            max_size: Maximum number of cache entries
            ttl: Time-to-live in seconds (uses monotonic time)
        
        Note:
            This class is designed for single-threaded use.
            For multi-threaded access, use ThreadSafeLRUCache instead.
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value with automatic expiration check
        
        Args:
            key: Cache key
        
        Returns:
            Cached value if exists and not expired, None otherwise
        
        Side effects:
            - Updates access statistics
            - Removes expired entries
            - Moves accessed entry to end (most recently used)
        """
        if key not in self._cache:
            self._misses += 1
            return None
        
        entry = self._cache[key]
        
        # Check if expired (using monotonic time)
        if time.monotonic() - entry.timestamp > self._ttl:
            del self._cache[key]
            self._misses += 1
            return None
        
        # Move to end (most recently used)
        self._cache.move_to_end(key)
        entry.access_count += 1
        self._hits += 1
        return entry.value
    
    def set(self, key: str, value: Any) -> None:
        """Set cache value with automatic eviction
        
        Args:
            key: Cache key
            value: Value to cache
        
        Side effects:
            - Removes existing entry if key exists
            - Evicts oldest entry if cache is full
        """
        # Remove existing entry if present
        if key in self._cache:
            del self._cache[key]
        
        # Add new entry
        self._cache[key] = CacheEntry(
            value=value,
            timestamp=time.monotonic(),
            access_count=0
        )
        
        # Evict oldest entry if over capacity
        if len(self._cache) > self._max_size:
            # popitem(last=False) removes the first (oldest) item
            self._cache.popitem(last=False)
    
    def clear(self) -> None:
        """Clear all cache entries and reset statistics"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics
        
        Returns:
            Dictionary containing:
                - size: Current number of entries
                - max_size: Maximum capacity
                - hits: Number of cache hits
                - misses: Number of cache misses
                - hit_rate: Hit rate (0.0-1.0)
        """
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0
        
        return {
            'size': len(self._cache),
            'max_size': self._max_size,
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': hit_rate
        }


class ThreadSafeLRUCache(LRUCache):
    """Thread-safe LRU Cache using threading.Lock
    
    This class extends LRUCache with thread-safety by wrapping all
    operations with a lock. Suitable for multi-threaded environments.
    
    Example:
        cache = ThreadSafeLRUCache(max_size=100, ttl=60.0)
        # Safe to use from multiple threads
        cache.set("key", "value")
        value = cache.get("key")
    """
    
    def __init__(self, max_size: int = 100, ttl: float = 60.0):
        """Initialize thread-safe LRU cache
        
        Args:
            max_size: Maximum number of cache entries
            ttl: Time-to-live in seconds
        """
        super().__init__(max_size, ttl)
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Thread-safe get operation
        
        Args:
            key: Cache key
        
        Returns:
            Cached value if exists and not expired, None otherwise
        """
        with self._lock:
            return super().get(key)
    
    def set(self, key: str, value: Any) -> None:
        """Thread-safe set operation
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            super().set(key, value)
    
    def clear(self) -> None:
        """Thread-safe clear operation"""
        with self._lock:
            super().clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Thread-safe statistics retrieval
        
        Returns:
            Dictionary containing cache statistics
        """
        with self._lock:
            return super().get_stats()
