# -*- coding: utf-8 -*-

"""
AI 助手配置模式定义
定义配置文件中合法的字段和验证规则
"""

from core.config.config_validator import ConfigSchema


def get_ai_assistant_schema() -> ConfigSchema:
    """获取 AI 助手的配置模式定义
    
    Returns:
        ConfigSchema: 配置模式
    """
    return ConfigSchema(
        required_fields={
            "_version"  # 配置版本号（必需）
        },
        optional_fields={
            "llm_provider",     # LLM 供应商（api 或 ollama）
            "api_settings",     # API 配置
            "ollama_settings"   # Ollama 配置
        },
        field_types={
            "_version": str,
            "llm_provider": str,
            "api_settings": dict,
            "ollama_settings": dict
        },
        allow_unknown_fields=True,  # 允许未知字段（向后兼容）
        strict_mode=False  # 非严格模式
    )

