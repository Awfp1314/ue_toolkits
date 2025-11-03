# -*- coding: utf-8 -*-

"""
对话记忆管理器
缓存最近的对话历史，供上下文管理器使用
"""

from typing import List, Dict
from collections import deque
from core.logger import get_logger

logger = get_logger(__name__)


class ConversationMemory:
    """对话记忆管理器"""
    
    def __init__(self, max_history: int = 10):
        """初始化对话记忆
        
        Args:
            max_history: 最多保存的对话轮数
        """
        self.max_history = max_history
        self.history = deque(maxlen=max_history)
        self.logger = logger
    
    def add_dialogue(self, user_query: str, assistant_response: str):
        """添加一轮对话到记忆
        
        Args:
            user_query: 用户查询
            assistant_response: AI 回复
        """
        self.history.append({
            "user": user_query,
            "assistant": assistant_response
        })
        self.logger.debug(f"添加对话到记忆，当前记忆数: {len(self.history)}")
    
    def get_recent_dialogues(self, limit: int = 5) -> List[str]:
        """获取最近的对话历史（格式化为字符串列表）
        
        Args:
            limit: 获取的对话轮数
            
        Returns:
            List[str]: 格式化的对话历史
        """
        recent = list(self.history)[-limit:]
        formatted = []
        
        for i, dialogue in enumerate(recent, 1):
            formatted.append(f"[对话 {i}]")
            formatted.append(f"用户: {dialogue['user']}")
            # 只保留回复的前200个字符，避免过长
            response = dialogue['assistant']
            if len(response) > 200:
                response = response[:200] + "..."
            formatted.append(f"助手: {response}")
        
        return formatted
    
    def get_recent_context(self, limit: int = 3) -> str:
        """获取最近的对话上下文（格式化为单个字符串）
        
        Args:
            limit: 获取的对话轮数
            
        Returns:
            str: 格式化的对话上下文
        """
        dialogues = self.get_recent_dialogues(limit)
        if not dialogues:
            return ""
        
        return "[最近对话记忆]\n" + "\n".join(dialogues)
    
    def clear(self):
        """清空对话记忆"""
        self.history.clear()
        self.logger.info("对话记忆已清空")
    
    def get_last_user_query(self) -> str:
        """获取最后一次用户查询
        
        Returns:
            str: 最后一次查询，如果没有则返回空字符串
        """
        if self.history:
            return self.history[-1]['user']
        return ""
    
    def has_history(self) -> bool:
        """检查是否有对话历史
        
        Returns:
            bool: 是否有历史记录
        """
        return len(self.history) > 0

