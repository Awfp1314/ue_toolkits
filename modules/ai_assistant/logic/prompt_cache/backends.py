"""
缓存后端实现
支持多种缓存策略（内存、文件等）
"""

import time
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from collections import OrderedDict
from dataclasses import dataclass


@dataclass
class CacheEntry:
    """缓存条目"""
    content: str
    content_hash: str
    created_at: float
    ttl_minutes: int
    estimated_tokens: int
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl_minutes <= 0:
            return False  # TTL为0表示永不过期
        elapsed_minutes = (time.time() - self.created_at) / 60
        return elapsed_minutes > self.ttl_minutes


class CacheBackend(ABC):
    """缓存后端抽象接口"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[CacheEntry]:
        """获取缓存项"""
        pass
    
    @abstractmethod
    def set(self, key: str, entry: CacheEntry):
        """设置缓存项"""
        pass
    
    @abstractmethod
    def invalidate(self, key: str) -> bool:
        """使缓存失效"""
        pass
    
    @abstractmethod
    def clear(self):
        """清空所有缓存"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        pass


class InMemoryCacheBackend(CacheBackend):
    """内存缓存后端（带LRU淘汰策略）"""
    
    def __init__(self, max_size: int = 50):
        """
        初始化内存缓存
        
        Args:
            max_size: 最大缓存条目数
        """
        self.max_size = max_size
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._hit_count = 0
        self._miss_count = 0
        self._total_tokens_saved = 0
    
    def get(self, key: str) -> Optional[CacheEntry]:
        """获取缓存项（LRU更新）"""
        if key not in self._cache:
            self._miss_count += 1
            return None
        
        entry = self._cache[key]
        
        # 检查是否过期
        if entry.is_expired():
            del self._cache[key]
            self._miss_count += 1
            return None
        
        # LRU：移到末尾
        self._cache.move_to_end(key)
        self._hit_count += 1
        self._total_tokens_saved += entry.estimated_tokens
        return entry
    
    def set(self, key: str, entry: CacheEntry):
        """设置缓存项（LRU淘汰）"""
        # 如果已存在，更新并移到末尾
        if key in self._cache:
            self._cache.move_to_end(key)
        
        self._cache[key] = entry
        
        # LRU淘汰：超出容量时删除最旧的
        while len(self._cache) > self.max_size:
            self._cache.popitem(last=False)
    
    def invalidate(self, key: str) -> bool:
        """使缓存失效"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self):
        """清空所有缓存"""
        self._cache.clear()
        self._hit_count = 0
        self._miss_count = 0
        self._total_tokens_saved = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_requests = self._hit_count + self._miss_count
        hit_rate = self._hit_count / total_requests if total_requests > 0 else 0
        
        return {
            'cache_size': len(self._cache),
            'max_size': self.max_size,
            'hit_count': self._hit_count,
            'miss_count': self._miss_count,
            'hit_rate': f"{hit_rate:.2%}",
            'total_tokens_saved': self._total_tokens_saved
        }

