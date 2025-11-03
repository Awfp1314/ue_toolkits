# -*- coding: utf-8 -*-

"""
增强型记忆管理器（基于 Mem0 概念）
提供多级记忆、向量检索和智能上下文管理
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from collections import deque
from core.logger import get_logger

logger = get_logger(__name__)


class MemoryLevel:
    """记忆级别枚举"""
    USER = "user"           # 用户级（跨会话持久化）
    SESSION = "session"     # 会话级（当前会话）
    CONTEXT = "context"     # 上下文级（最近几轮）


class Memory:
    """记忆项"""
    
    def __init__(self, content: str, level: str = MemoryLevel.SESSION, 
                 metadata: Optional[Dict] = None, timestamp: Optional[str] = None):
        self.content = content
        self.level = level
        self.metadata = metadata or {}
        self.timestamp = timestamp or datetime.now().isoformat()
        self.importance = self.metadata.get('importance', 0.5)  # 0-1，重要性评分


class EnhancedMemoryManager:
    """增强型记忆管理器
    
    参考 Mem0 设计理念：
    - 多级记忆（用户/会话/上下文）
    - 智能检索和过滤
    - 记忆重要性评分
    - 持久化存储
    """
    
    def __init__(self, user_id: str = "default", storage_dir: Optional[Path] = None):
        """初始化记忆管理器
        
        Args:
            user_id: 用户ID（用于用户级记忆）
            storage_dir: 存储目录（用于持久化）
        """
        self.user_id = user_id
        self.logger = logger
        
        # 存储目录
        if storage_dir:
            self.storage_dir = Path(storage_dir)
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        else:
            from core.utils.path_utils import PathUtils
            path_utils = PathUtils()
            self.storage_dir = path_utils.get_user_data_dir() / "ai_memory"
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.memory_file = self.storage_dir / f"{user_id}_memory.json"
        
        # 记忆存储
        self.user_memories: List[Memory] = []      # 用户级（持久化）
        self.session_memories: List[Memory] = []   # 会话级（临时）
        self.context_buffer = deque(maxlen=10)     # 上下文缓冲（最近10轮）
        
        # 加载持久化记忆
        self._load_user_memories()
        
        self.logger.info(f"增强型记忆管理器初始化完成（用户: {user_id}）")
    
    def add_memory(self, content: str, level: str = MemoryLevel.SESSION, 
                   metadata: Optional[Dict] = None, auto_evaluate: bool = True):
        """添加记忆
        
        Args:
            content: 记忆内容
            level: 记忆级别
            metadata: 元数据（如类型、标签等）
            auto_evaluate: 是否自动评估重要性
        """
        memory = Memory(content, level, metadata)
        
        # 自动评估重要性（简单规则，可扩展为 AI 评估）
        if auto_evaluate:
            memory.importance = self._evaluate_importance(content, metadata)
        
        # 根据级别添加到对应存储
        if level == MemoryLevel.USER:
            self.user_memories.append(memory)
            self._save_user_memories()  # 持久化
        elif level == MemoryLevel.SESSION:
            self.session_memories.append(memory)
        elif level == MemoryLevel.CONTEXT:
            self.context_buffer.append(memory)
        
        self.logger.debug(f"添加记忆 [{level}]: {content[:50]}... (重要性: {memory.importance:.2f})")
    
    def add_dialogue(self, user_query: str, assistant_response: str, 
                    auto_classify: bool = True):
        """添加对话到记忆
        
        Args:
            user_query: 用户查询
            assistant_response: AI 回复
            auto_classify: 是否自动分类重要性并选择存储级别
        """
        # 添加用户查询
        metadata_user = {'type': 'user_query'}
        level = MemoryLevel.CONTEXT  # 默认上下文级
        
        if auto_classify:
            # 智能判断是否值得长期保存
            if self._is_important_query(user_query):
                level = MemoryLevel.USER
                metadata_user['tags'] = ['重要查询']
        
        self.add_memory(f"用户: {user_query}", level, metadata_user)
        
        # 添加 AI 回复（精简版）
        response_summary = assistant_response[:200] + "..." if len(assistant_response) > 200 else assistant_response
        metadata_assistant = {'type': 'assistant_response'}
        self.add_memory(f"助手: {response_summary}", MemoryLevel.CONTEXT, metadata_assistant)
    
    def get_relevant_memories(self, query: str, limit: int = 5, 
                             min_importance: float = 0.3) -> List[str]:
        """获取相关记忆（基于关键词匹配，可扩展为向量检索）
        
        Args:
            query: 查询内容
            limit: 返回数量限制
            min_importance: 最小重要性阈值
            
        Returns:
            List[str]: 相关记忆列表
        """
        all_memories = []
        
        # 合并所有级别的记忆
        all_memories.extend([(m, 3.0) for m in self.user_memories])      # 用户级权重最高
        all_memories.extend([(m, 2.0) for m in self.session_memories])   # 会话级次之
        all_memories.extend([(m, 1.0) for m in self.context_buffer])     # 上下文级权重较低
        
        # 简单的关键词匹配评分（可替换为向量相似度）
        query_lower = query.lower()
        scored_memories = []
        
        for memory, level_weight in all_memories:
            if memory.importance < min_importance:
                continue
            
            # 简单评分：关键词匹配 + 重要性 + 级别权重
            relevance_score = 0
            
            # 关键词匹配
            query_words = query_lower.split()
            content_lower = memory.content.lower()
            matches = sum(1 for word in query_words if word in content_lower)
            relevance_score += matches * 0.3
            
            # 重要性
            relevance_score += memory.importance * 0.4
            
            # 级别权重
            relevance_score += level_weight * 0.3
            
            if relevance_score > 0:
                scored_memories.append((memory, relevance_score))
        
        # 排序并返回
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        return [m.content for m, _ in scored_memories[:limit]]
    
    def get_recent_context(self, limit: int = 5) -> str:
        """获取最近的上下文（格式化为字符串）
        
        Args:
            limit: 获取数量
            
        Returns:
            str: 格式化的上下文
        """
        recent = list(self.context_buffer)[-limit:]
        if not recent:
            return ""
        
        formatted = ["[最近对话上下文]"]
        for memory in recent:
            formatted.append(memory.content)
        
        return "\n".join(formatted)
    
    def get_user_profile(self) -> str:
        """获取用户画像（从用户级记忆中提取）
        
        Returns:
            str: 用户画像信息
        """
        if not self.user_memories:
            return ""
        
        # 提取高重要性记忆
        important_memories = [m for m in self.user_memories if m.importance > 0.7]
        
        if not important_memories:
            return ""
        
        profile = ["[用户习惯和偏好]"]
        for memory in important_memories[-5:]:  # 最近5条重要记忆
            profile.append(f"- {memory.content}")
        
        return "\n".join(profile)
    
    def clear_session(self):
        """清空会话级记忆"""
        self.session_memories.clear()
        self.context_buffer.clear()
        self.logger.info("会话记忆已清空")
    
    def _evaluate_importance(self, content: str, metadata: Optional[Dict] = None) -> float:
        """评估记忆重要性（简单规则，可扩展为 AI 评分）
        
        Args:
            content: 内容
            metadata: 元数据
            
        Returns:
            float: 重要性评分 (0-1)
        """
        score = 0.5  # 默认中等重要性
        
        # 规则1：包含特定关键词提升重要性
        important_keywords = ['错误', '配置', '路径', '文件', '资产', '设置', '问题']
        content_lower = content.lower()
        matches = sum(1 for keyword in important_keywords if keyword in content_lower)
        score += matches * 0.1
        
        # 规则2：内容长度（过长或过短降低重要性）
        if 20 < len(content) < 200:
            score += 0.1
        
        # 规则3：元数据标签
        if metadata and 'tags' in metadata:
            if '重要' in str(metadata['tags']):
                score += 0.2
        
        return min(1.0, max(0.0, score))
    
    def _is_important_query(self, query: str) -> bool:
        """判断查询是否重要（值得长期保存）
        
        Args:
            query: 查询内容
            
        Returns:
            bool: 是否重要
        """
        # 包含特定关键词的查询视为重要
        important_indicators = ['怎么', '如何', '为什么', '配置', '设置', '问题', '错误']
        query_lower = query.lower()
        
        return any(indicator in query_lower for indicator in important_indicators)
    
    def _load_user_memories(self):
        """从文件加载用户级记忆"""
        try:
            if self.memory_file.exists():
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for item in data.get('memories', []):
                    memory = Memory(
                        content=item['content'],
                        level=MemoryLevel.USER,
                        metadata=item.get('metadata', {}),
                        timestamp=item.get('timestamp')
                    )
                    memory.importance = item.get('importance', 0.5)
                    self.user_memories.append(memory)
                
                self.logger.info(f"加载了 {len(self.user_memories)} 条用户记忆")
        
        except Exception as e:
            self.logger.error(f"加载用户记忆失败: {e}")
    
    def _save_user_memories(self):
        """保存用户级记忆到文件"""
        try:
            data = {
                'user_id': self.user_id,
                'updated_at': datetime.now().isoformat(),
                'memories': [
                    {
                        'content': m.content,
                        'importance': m.importance,
                        'metadata': m.metadata,
                        'timestamp': m.timestamp
                    }
                    for m in self.user_memories
                ]
            }
            
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"保存了 {len(self.user_memories)} 条用户记忆")
        
        except Exception as e:
            self.logger.error(f"保存用户记忆失败: {e}")

