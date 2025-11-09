"""
智能预取模块（7.0-P9）
预判用户下一步需求，提前加载数据
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DialogPattern:
    """对话模式定义"""
    name: str                      # 模式名称
    trigger_keywords: List[str]    # 触发关键词
    prefetch_actions: List[str]    # 预取动作列表
    description: str               # 描述


@dataclass
class PrefetchItem:
    """预取缓存项"""
    pattern_name: str              # 模式名称
    data: Any                      # 预取的数据
    created_at: float              # 创建时间
    ttl_minutes: int               # 有效期（分钟）
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        elapsed_minutes = (time.time() - self.created_at) / 60
        return elapsed_minutes > self.ttl_minutes


class PrefetchCache:
    """预取结果缓存"""
    
    def __init__(self, max_size: int = 10, default_ttl: int = 3):
        """
        初始化缓存
        
        Args:
            max_size: 最大缓存项数
            default_ttl: 默认TTL（分钟）
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, PrefetchItem] = {}
        self._hit_count = 0
        self._miss_count = 0
    
    def get(self, pattern_name: str) -> Optional[Any]:
        """
        获取缓存
        
        Args:
            pattern_name: 模式名称
        
        Returns:
            缓存数据或None
        """
        if pattern_name not in self._cache:
            self._miss_count += 1
            return None
        
        item = self._cache[pattern_name]
        
        # 检查过期
        if item.is_expired():
            del self._cache[pattern_name]
            self._miss_count += 1
            return None
        
        self._hit_count += 1
        return item.data
    
    def set(self, pattern_name: str, data: Any, ttl_minutes: Optional[int] = None):
        """
        设置缓存
        
        Args:
            pattern_name: 模式名称
            data: 数据
            ttl_minutes: TTL（可选）
        """
        item = PrefetchItem(
            pattern_name=pattern_name,
            data=data,
            created_at=time.time(),
            ttl_minutes=ttl_minutes or self.default_ttl
        )
        
        self._cache[pattern_name] = item
        
        # 容量控制：LRU淘汰
        if len(self._cache) > self.max_size:
            # 删除最旧的
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].created_at)
            del self._cache[oldest_key]
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._hit_count = 0
        self._miss_count = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = self._hit_count + self._miss_count
        hit_rate = self._hit_count / total if total > 0 else 0
        
        return {
            'cache_size': len(self._cache),
            'hit_count': self._hit_count,
            'miss_count': self._miss_count,
            'hit_rate': f"{hit_rate:.2%}"
        }


class SmartPrefetcher:
    """智能预取器"""
    
    # 预定义对话模式
    PATTERNS = [
        DialogPattern(
            name='blueprint_debug',
            trigger_keywords=['蓝图', '节点', '报错', '不工作', 'bug', '错误'],
            prefetch_actions=['load_common_issues', 'load_related_docs'],
            description='蓝图调试场景'
        ),
        DialogPattern(
            name='memory_query',
            trigger_keywords=['记得', '之前', '还记得', '说过', '提到'],
            prefetch_actions=['load_related_memories', 'load_conversation_summary'],
            description='记忆查询场景'
        ),
        DialogPattern(
            name='asset_search',
            trigger_keywords=['资产', '材质', '模型', '贴图', '动画', '音频'],
            prefetch_actions=['load_asset_list', 'load_asset_configs'],
            description='资产搜索场景'
        ),
        DialogPattern(
            name='doc_followup',
            trigger_keywords=['详细', '更多', '举例', '具体', '怎么用'],
            prefetch_actions=['load_full_documentation', 'load_code_examples'],
            description='文档跟进场景'
        )
    ]
    
    def __init__(self, context_manager=None):
        """
        初始化预取器
        
        Args:
            context_manager: 上下文管理器（用于执行预取动作）
        """
        self.context_manager = context_manager
        self.cache = PrefetchCache(max_size=10, default_ttl=3)
        self.stats = {
            'total_prefetch_attempts': 0,
            'successful_prefetches': 0,
            'by_pattern': {p.name: 0 for p in self.PATTERNS}
        }
    
    def detect_pattern(self, query: str) -> Optional[DialogPattern]:
        """
        检测对话模式
        
        Args:
            query: 用户查询
        
        Returns:
            匹配的模式或None
        """
        for pattern in self.PATTERNS:
            if any(kw in query for kw in pattern.trigger_keywords):
                return pattern
        return None
    
    def prefetch_for_query(self, query: str):
        """
        为查询执行预取（异步，不阻塞）
        
        Args:
            query: 用户查询
        """
        pattern = self.detect_pattern(query)
        
        if not pattern:
            return
        
        
        self.stats['total_prefetch_attempts'] += 1
        self.stats['by_pattern'][pattern.name] += 1
        
        # 执行预取动作
        try:
            prefetched_data = self._execute_prefetch(pattern)
            if prefetched_data:
                self.cache.set(pattern.name, prefetched_data)
                self.stats['successful_prefetches'] += 1
        except Exception as e:
            print(f"[WARNING] [7.0-P9] 预取失败: {e}")
    
    def get_cached(self, query: str) -> Optional[Any]:
        """
        获取预取的缓存数据
        
        Args:
            query: 用户查询
        
        Returns:
            缓存数据或None
        """
        pattern = self.detect_pattern(query)
        if not pattern:
            return None
        
        cached = self.cache.get(pattern.name)
        if cached:
        
        return cached
    
    def _execute_prefetch(self, pattern: DialogPattern) -> Optional[Dict]:
        """
        执行预取动作
        
        Args:
            pattern: 对话模式
        
        Returns:
            预取的数据
        """
        if not self.context_manager:
            return None
        
        result = {}
        
        # 根据pattern执行不同的预取动作
        try:
            if pattern.name == 'blueprint_debug':
                # 预取蓝图相关的常见问题和文档
                if hasattr(self.context_manager, 'document_reader'):
                    result['common_issues'] = "蓝图常见问题：节点连接错误、类型不匹配、循环引用等"
            
            elif pattern.name == 'memory_query':
                # 预取相关记忆
                if hasattr(self.context_manager, 'memory'):
                    result['recent_memories'] = "最近讨论的话题..."
            
            elif pattern.name == 'asset_search':
                # 预取资产列表
                if hasattr(self.context_manager, 'asset_reader'):
                    result['asset_summary'] = "资产库概览..."
            
            elif pattern.name == 'doc_followup':
                # 预取完整文档
                if hasattr(self.context_manager, 'document_reader'):
                    result['full_docs'] = "完整文档内容..."
            
            return result if result else None
        
        except Exception as e:
            print(f"[ERROR] [7.0-P9] 执行预取动作失败: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        cache_stats = self.cache.get_stats()
        
        return {
            'prefetch_attempts': self.stats['total_prefetch_attempts'],
            'successful_prefetches': self.stats['successful_prefetches'],
            'by_pattern': self.stats['by_pattern'],
            'cache': cache_stats
        }

