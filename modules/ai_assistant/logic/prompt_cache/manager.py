"""
Prompt 缓存管理器
协调缓存后端和规范化器，对外提供简洁API
"""

from typing import Dict, Any, List, Optional
from .backends import InMemoryCacheBackend, CacheEntry, CacheBackend
from .normalizer import ContentNormalizer


class PromptCacheManager:
    """Prompt 缓存管理器"""
    
    # 预定义的缓存类型
    CACHE_TYPE_SYSTEM = "system_prompt"
    CACHE_TYPE_TOOLS = "tools"
    CACHE_TYPE_IDENTITY = "identity"
    
    def __init__(self, backend: Optional[CacheBackend] = None, max_cache_size: int = 50):
        """
        初始化缓存管理器
        
        Args:
            backend: 缓存后端（默认使用内存缓存）
            max_cache_size: 最大缓存条目数
        """
        self.backend = backend or InMemoryCacheBackend(max_size=max_cache_size)
        self.normalizer = ContentNormalizer()
        
        # 已注册的静态 prompt（用于构建消息时自动使用）
        self._registered_prompts: Dict[str, str] = {}  # type -> cache_key
    
    def register_static_prompt(self, prompt_type: str, content: Any, ttl_minutes: int = 60) -> str:
        """
        注册静态 prompt（system/tools/identity）
        
        Args:
            prompt_type: prompt 类型（system/tools/identity）
            content: prompt 内容
            ttl_minutes: 缓存有效期（分钟，0表示永不过期）
        
        Returns:
            缓存 key（哈希值）
        """
        # 根据类型选择规范化方式
        if prompt_type == self.CACHE_TYPE_TOOLS:
            normalized = self.normalizer.normalize_content(content, 'tools')
        elif prompt_type in (self.CACHE_TYPE_SYSTEM, self.CACHE_TYPE_IDENTITY):
            normalized = self.normalizer.normalize_content(content, 'text')
        else:
            normalized = self.normalizer.normalize_content(content, 'text')
        
        # 生成哈希
        content_hash = self.normalizer.hash_content(normalized)
        cache_key = f"{prompt_type}:{content_hash}"
        
        # 检查是否已缓存
        existing = self.backend.get(cache_key)
        if existing and not existing.is_expired():
            # 已存在且未过期，更新注册表
            self._registered_prompts[prompt_type] = cache_key
            return cache_key
        
        # 创建缓存条目
        estimated_tokens = self.normalizer.estimate_tokens(normalized)
        entry = CacheEntry(
            content=normalized,
            content_hash=content_hash,
            created_at=__import__('time').time(),
            ttl_minutes=ttl_minutes,
            estimated_tokens=estimated_tokens
        )
        
        # 存入缓存
        self.backend.set(cache_key, entry)
        
        # 注册到映射表
        self._registered_prompts[prompt_type] = cache_key
        
        return cache_key
    
    def build_cacheable_messages(
        self, 
        user_message: str, 
        conversation_history: List[Dict],
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        构建可缓存的消息列表
        
        Args:
            user_message: 用户当前消息
            conversation_history: 对话历史
            context: 上下文信息（可选）
        
        Returns:
            {
                'messages': 最终消息列表,
                'billable_tokens_estimate': 计费 token 估算,
                'cached_sections': {type: hash} 缓存命中情况,
                'cache_stats': 缓存统计
            }
        """
        messages = []
        billable_tokens = 0
        cached_sections = {}
        
        # 1. 系统 prompt（缓存）
        system_key = self._registered_prompts.get(self.CACHE_TYPE_SYSTEM)
        if system_key:
            system_entry = self.backend.get(system_key)
            if system_entry and not system_entry.is_expired():
                messages.append({
                    'role': 'system',
                    'content': system_entry.content
                })
                cached_sections[self.CACHE_TYPE_SYSTEM] = system_entry.content_hash
                # 缓存命中，不计费（或减少计费）
                # 注意：实际 API 是否支持缓存需要根据供应商确定
                # 这里我们记录但仍计入token以保守估算
                billable_tokens += system_entry.estimated_tokens
        
        # 2. 对话历史（不缓存，但统计）
        for msg in conversation_history:
            if msg.get('role') != 'system':  # 跳过系统消息（已添加）
                messages.append(msg)
                billable_tokens += self.normalizer.estimate_tokens(
                    msg.get('content', '')
                )
        
        # 3. 上下文信息（临时system消息，不缓存）
        if context:
            messages.append({
                'role': 'system',
                'content': f"[当前查询的上下文信息]\n{context}"
            })
            billable_tokens += self.normalizer.estimate_tokens(context)
        
        # 4. 当前用户消息（不缓存）
        messages.append({
            'role': 'user',
            'content': user_message
        })
        billable_tokens += self.normalizer.estimate_tokens(user_message)
        
        # 获取缓存统计
        cache_stats = self.backend.get_stats()
        
        return {
            'messages': messages,
            'billable_tokens_estimate': billable_tokens,
            'cached_sections': cached_sections,
            'cache_stats': cache_stats
        }
    
    def invalidate_type(self, prompt_type: str):
        """使某类型的缓存失效（如身份变更）"""
        cache_key = self._registered_prompts.get(prompt_type)
        if cache_key:
            self.backend.invalidate(cache_key)
            del self._registered_prompts[prompt_type]
    
    def clear_all(self):
        """清空所有缓存"""
        self.backend.clear()
        self._registered_prompts.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.backend.get_stats()

