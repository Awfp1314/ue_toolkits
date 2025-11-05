# -*- coding: utf-8 -*-

"""
LLM 客户端工厂
根据配置创建相应的 LLM 客户端策略
"""

from typing import Dict, Any
from .base_llm_client import BaseLLMClient
from .api_llm_client import ApiLLMClient
from .ollama_llm_client import OllamaLLMClient


def create_llm_client(config: Dict[str, Any]) -> BaseLLMClient:
    """
    工厂函数：根据配置创建 LLM 客户端
    
    Args:
        config: 完整的 AI 助手配置字典，应包含：
            - llm_provider: "api" 或 "ollama"
            - api_settings: API 配置（当 provider="api" 时）
            - ollama_settings: Ollama 配置（当 provider="ollama" 时）
    
    Returns:
        BaseLLMClient: 具体的 LLM 客户端实例
    
    Raises:
        ValueError: 如果 provider 不支持或配置缺失
    """
    provider = config.get("llm_provider", "api")
    
    if provider == "ollama":
        ollama_config = config.get("ollama_settings")
        if not ollama_config:
            raise ValueError("ollama_settings 配置缺失")
        return OllamaLLMClient(config=ollama_config)
    
    elif provider == "api":
        api_config = config.get("api_settings")
        if not api_config:
            raise ValueError("api_settings 配置缺失")
        return ApiLLMClient(config=api_config)
    
    else:
        raise ValueError(f"不支持的 LLM 供应商: {provider}，仅支持 'api' 或 'ollama'")


def create_llm_client_from_config_manager(config_manager) -> BaseLLMClient:
    """
    便捷函数：从 ConfigManager 创建 LLM 客户端
    
    Args:
        config_manager: ConfigManager 实例
    
    Returns:
        BaseLLMClient: LLM 客户端实例
    """
    config = config_manager.get_module_config("ai_assistant")
    return create_llm_client(config)

