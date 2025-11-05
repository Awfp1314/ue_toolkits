# -*- coding: utf-8 -*-

"""
LLM 客户端抽象基类
定义策略接口，所有 LLM 客户端必须实现此接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Generator, List


class BaseLLMClient(ABC):
    """
    LLM 客户端的抽象基类（策略接口）
    
    所有具体的 LLM 客户端（API、Ollama、本地模型等）都必须继承此类
    并实现 generate_response 方法。
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化 LLM 客户端
        
        Args:
            config: 客户端配置字典
        """
        self.config = config
    
    @abstractmethod
    def generate_response(
        self,
        context_messages: List[Dict[str, str]],
        stream: bool = True,
        temperature: float = None,
        tools: List[Dict] = None
    ) -> Generator[str, None, None]:
        """
        生成响应（生成器模式，统一支持流式和非流式）
        
        Args:
            context_messages: 聊天上下文消息列表
                格式：[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
            stream: 是否流式传输（默认 True）
            temperature: 温度参数（可选，覆盖配置）
            tools: 工具列表（可选，用于 Function Calling）
            
        Yields:
            str: 响应的 token 块（流式）或完整响应（非流式，yield 一次）
            
        Raises:
            Exception: 连接失败、超时、模型错误等异常
        """
        pass
    
    def validate_config(self) -> bool:
        """
        验证配置是否有效
        
        Returns:
            bool: 配置是否有效
        """
        return self.config is not None and isinstance(self.config, dict)
    
    def get_model_name(self) -> str:
        """
        获取当前使用的模型名称
        
        Returns:
            str: 模型名称
        """
        return self.config.get('model_name', 'unknown')

