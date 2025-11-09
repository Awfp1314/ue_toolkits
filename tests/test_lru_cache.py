"""
Unit tests for LRU Cache implementation

Tests cover:
- LRU eviction logic (removes oldest entries when full)
- TTL expiration (using time.monotonic())
- Hit rate statistics accuracy
- Thread-safe variant concurrent access

Requirements tested: 2.1, 2.2, 2.3, 2.4
"""

import unittest
import time
import threading
import sys
import os

# Add parent directory to path to allow importing core module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.utils.lru_cache import LRUCache, ThreadSafeLRUCache, CacheEntry


class TestCacheEntry(unittest.TestCase):
    """Test CacheEntry dataclass"""
    
    def test_cache_entry_creation(self):
        """Test CacheEntry can be created with required fields"""
        entry = CacheEntry(value="test_value", timestamp=time.monotonic())
        self.assertEqual(entry.value, "test_value")
        self.assertIsInstance(entry.timestamp, float)
        self.assertEqual(entry.access_count, 0)
    
    def test_cache_entry_with_access_count(self):
        """Test CacheEntry with custom access count"""
        entry = CacheEntry(value="test", timestamp=time.monotonic(), access_count=5)
        self.assertEqual(entry.access_count, 5)


class TestLRUCache(unittest.TestCase):
    """Test LRUCache functionality"""
    
    def setUp(self):
        """Set up test cache before each test"""
        self.cache = LRUCache(max_size=3, ttl=1.0)
    
    def test_basic_set_and_get(self):
        """Test basic cache set and get operations"""
        self.cache.set("key1", "value1")
        self.assertEqual(self.cache.get("key1"), "value1")
    
    def test_get_nonexistent_key(self):
        """Test getting a key that doesn't exist returns None"""
        result = self.cache.get("nonexistent")
        self.assertIsNone(result)
    
    def test_lru_eviction_logic(self):
        """Test LRU eviction: oldest entry is removed when cache is full
        
        Requirement 2.1: Cache should evict least recently used items
        """
        # Fill cache to capacity (max_size=3)
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.set("key3", "value3")
        
        # Verify all three are present
        self.assertEqual(self.cache.get("key1"), "value1")
        self.assertEqual(self.cache.get("key2"), "value2")
        self.assertEqual(self.cache.get("key3"), "value3")
        
        # Add fourth item - should evict key1 (oldest)
        self.cache.set("key4", "value4")
        
        # key1 should be evicted
        self.assertIsNone(self.cache.get("key1"))
        # Others should still exist
        self.assertEqual(self.cache.get("key2"), "value2")
        self.assertEqual(self.cache.get("key3"), "value3")
        self.assertEqual(self.cache.get("key4"), "value4")
    
    def test_lru_access_updates_order(self):
        """Test that accessing an entry moves it to most recently used
        
        Requirement 2.1: Accessing entries should update LRU order
        """
        # Fill cache
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.set("key3", "value3")
        
        # Access key1 to make it most recently used
        self.cache.get("key1")
        
        # Add new item - should evict key2 (now oldest)
        self.cache.set("key4", "value4")
        
        # key2 should be evicted, key1 should remain
        self.assertIsNone(self.cache.get("key2"))
        self.assertEqual(self.cache.get("key1"), "value1")
    
    def test_ttl_expiration(self):
        """Test TTL-based expiration using time.monotonic()
        
        Requirement 2.2: Entries should expire after TTL
        Requirement 2.3: Should use time.monotonic() for TTL
        """
        # Create cache with 0.5 second TTL
        cache = LRUCache(max_size=10, ttl=0.5)
        
        cache.set("key1", "value1")
        
        # Should be accessible immediately
        self.assertEqual(cache.get("key1"), "value1")
        
        # Wait for expiration
        time.sleep(0.6)
        
        # Should be expired and return None
        self.assertIsNone(cache.get("key1"))
    
    def test_ttl_not_expired(self):
        """Test that entries within TTL are still accessible
        
        Requirement 2.2: Entries should be accessible before TTL expires
        """
        cache = LRUCache(max_size=10, ttl=2.0)
        
        cache.set("key1", "value1")
        
        # Wait less than TTL
        time.sleep(0.5)
        
        # Should still be accessible
        self.assertEqual(cache.get("key1"), "value1")
    
    def test_hit_rate_statistics(self):
        """Test hit rate statistics accuracy
        
        Requirement 2.4: Cache should track hits, misses, and hit rate
        """
        self.cache.set("key1", "value1")
        
        # One hit
        self.cache.get("key1")
        
        # Two misses
        self.cache.get("key2")
        self.cache.get("key3")
        
        stats = self.cache.get_stats()
        
        self.assertEqual(stats['hits'], 1)
        self.assertEqual(stats['misses'], 2)
        self.assertAlmostEqual(stats['hit_rate'], 1/3, places=2)
    
    def test_statistics_with_expired_entries(self):
        """Test that expired entries count as misses
        
        Requirement 2.4: Expired entries should count as cache misses
        """
        cache = LRUCache(max_size=10, ttl=0.3)
        
        cache.set("key1", "value1")
        
        # Wait for expiration
        time.sleep(0.4)
        
        # Access expired entry - should be a miss
        result = cache.get("key1")
        self.assertIsNone(result)
        
        stats = cache.get_stats()
        self.assertEqual(stats['hits'], 0)
        self.assertEqual(stats['misses'], 1)
        self.assertEqual(stats['hit_rate'], 0.0)
    
    def test_cache_size_tracking(self):
        """Test that cache size is tracked correctly
        
        Requirement 2.4: Cache should report current size
        """
        stats = self.cache.get_stats()
        self.assertEqual(stats['size'], 0)
        self.assertEqual(stats['max_size'], 3)
        
        self.cache.set("key1", "value1")
        stats = self.cache.get_stats()
        self.assertEqual(stats['size'], 1)
        
        self.cache.set("key2", "value2")
        self.cache.set("key3", "value3")
        stats = self.cache.get_stats()
        self.assertEqual(stats['size'], 3)
    
    def test_clear_cache(self):
        """Test clearing cache resets all state"""
        self.cache.set("key1", "value1")
        self.cache.get("key1")
        
        self.cache.clear()
        
        # Statistics should be reset after clear
        stats = self.cache.get_stats()
        self.assertEqual(stats['size'], 0)
        self.assertEqual(stats['hits'], 0)
        self.assertEqual(stats['misses'], 0)
        self.assertEqual(stats['hit_rate'], 0.0)
        
        # Cache should be empty (this get will increment misses)
        self.assertIsNone(self.cache.get("key1"))
        
        # Verify the miss was counted
        stats = self.cache.get_stats()
        self.assertEqual(stats['misses'], 1)
    
    def test_update_existing_key(self):
        """Test that setting an existing key updates the value"""
        self.cache.set("key1", "value1")
        self.cache.set("key1", "value2")
        
        self.assertEqual(self.cache.get("key1"), "value2")
        
        # Should still only have one entry
        stats = self.cache.get_stats()
        self.assertEqual(stats['size'], 1)
    
    def test_access_count_tracking(self):
        """Test that access count is incremented on each get"""
        self.cache.set("key1", "value1")
        
        # Access multiple times
        self.cache.get("key1")
        self.cache.get("key1")
        self.cache.get("key1")
        
        # Access count should be tracked (internal verification)
        # We verify this indirectly through hit statistics
        stats = self.cache.get_stats()
        self.assertEqual(stats['hits'], 3)


class TestThreadSafeLRUCache(unittest.TestCase):
    """Test ThreadSafeLRUCache concurrent access
    
    Requirement 2.4: Thread-safe variant should handle concurrent access
    """
    
    def setUp(self):
        """Set up thread-safe cache before each test"""
        self.cache = ThreadSafeLRUCache(max_size=100, ttl=10.0)
    
    def test_basic_operations(self):
        """Test that thread-safe cache supports basic operations"""
        self.cache.set("key1", "value1")
        self.assertEqual(self.cache.get("key1"), "value1")
        
        stats = self.cache.get_stats()
        self.assertEqual(stats['size'], 1)
    
    def test_concurrent_writes(self):
        """Test concurrent write operations don't cause data corruption"""
        num_threads = 10
        writes_per_thread = 50
        
        def write_worker(thread_id):
            for i in range(writes_per_thread):
                key = f"thread{thread_id}_key{i}"
                value = f"thread{thread_id}_value{i}"
                self.cache.set(key, value)
        
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=write_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify cache size (should have all entries if within max_size)
        stats = self.cache.get_stats()
        expected_size = min(num_threads * writes_per_thread, 100)
        self.assertEqual(stats['size'], expected_size)
    
    def test_concurrent_reads_and_writes(self):
        """Test concurrent reads and writes work correctly"""
        # Pre-populate cache
        for i in range(20):
            self.cache.set(f"key{i}", f"value{i}")
        
        read_results = []
        write_count = [0]
        
        def read_worker():
            for i in range(50):
                result = self.cache.get(f"key{i % 20}")
                read_results.append(result)
        
        def write_worker():
            for i in range(50):
                self.cache.set(f"new_key{i}", f"new_value{i}")
                write_count[0] += 1
        
        # Start mixed read/write threads
        threads = []
        for _ in range(5):
            threads.append(threading.Thread(target=read_worker))
            threads.append(threading.Thread(target=write_worker))
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify no crashes and operations completed
        self.assertEqual(write_count[0], 250)  # 5 threads * 50 writes
        self.assertGreater(len(read_results), 0)
    
    def test_concurrent_clear(self):
        """Test that clear operation is thread-safe"""
        # Pre-populate
        for i in range(50):
            self.cache.set(f"key{i}", f"value{i}")
        
        def clear_worker():
            self.cache.clear()
        
        def access_worker():
            for i in range(50):
                self.cache.get(f"key{i}")
        
        threads = []
        threads.append(threading.Thread(target=clear_worker))
        for _ in range(3):
            threads.append(threading.Thread(target=access_worker))
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should complete without errors
        stats = self.cache.get_stats()
        self.assertIsNotNone(stats)


class TestLRUCacheEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions"""
    
    def test_zero_ttl(self):
        """Test cache with very short TTL (near-immediate expiration)"""
        cache = LRUCache(max_size=10, ttl=0.001)
        cache.set("key1", "value1")
        
        # Wait for expiration
        time.sleep(0.002)
        
        # Should be expired
        self.assertIsNone(cache.get("key1"))
    
    def test_single_entry_cache(self):
        """Test cache with max_size=1"""
        cache = LRUCache(max_size=1, ttl=10.0)
        
        cache.set("key1", "value1")
        self.assertEqual(cache.get("key1"), "value1")
        
        # Adding second entry should evict first
        cache.set("key2", "value2")
        self.assertIsNone(cache.get("key1"))
        self.assertEqual(cache.get("key2"), "value2")
    
    def test_large_cache(self):
        """Test cache with large capacity"""
        cache = LRUCache(max_size=1000, ttl=60.0)
        
        # Add many entries
        for i in range(500):
            cache.set(f"key{i}", f"value{i}")
        
        stats = cache.get_stats()
        self.assertEqual(stats['size'], 500)
        
        # Verify random access
        self.assertEqual(cache.get("key100"), "value100")
        self.assertEqual(cache.get("key250"), "value250")


if __name__ == '__main__':
    unittest.main()
