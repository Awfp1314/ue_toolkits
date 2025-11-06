"""
API 客户端模块
重构为使用策略模式，支持多种 LLM 供应商（API / Ollama）
"""

import json
import os
import time
import requests
from PyQt6.QtCore import QThread, pyqtSignal
from typing import Dict, Any, Optional
from pathlib import Path


class APIClient(QThread):
    """
    API 客户端线程（重构版）
    
    使用策略模式，通过工厂动态选择 LLM 供应商（API / Ollama）
    支持流式输出
    """
    # 信号定义
    chunk_received = pyqtSignal(str)      # 接收到数据块
    request_finished = pyqtSignal()       # 请求完成
    error_occurred = pyqtSignal(str)      # 发生错误
    
    def __init__(self, messages, model=None, temperature=None, tools=None, config=None):
        """
        初始化 API 客户端
        
        Args:
            messages: 消息历史列表
            model: 模型名称（可选，用于覆盖配置，向后兼容）
            temperature: 温度参数（可选，向后兼容）
            tools: Function Calling 工具列表（可选）
            config: LLM 配置字典（可选，如果不提供则从配置文件加载）
        """
        super().__init__()
        self.messages = messages
        self.model = model  # 保留以向后兼容
        self.temperature = temperature if temperature is not None else 0.8
        self.tools = tools
        self.is_running = True
        
        # 加载配置
        self.config = self._load_config() if config is None else config
        
        # 创建策略客户端（延迟到 run() 中，避免初始化阻塞）
        self.strategy_client = None
    
    def _load_config(self) -> Dict[str, Any]:
        """从配置文件加载 AI 助手配置"""
        try:
            from core.config.config_manager import ConfigManager
            
            # 获取模板文件路径
            template_path = Path(__file__).parent.parent / "config_template.json"
            
            # 创建 ConfigManager 并传入模板路径
            config_manager = ConfigManager("ai_assistant", template_path=template_path)
            config = config_manager.get_module_config()
            print(f"[CONFIG] AI 助手配置加载成功，供应商: {config.get('llm_provider', 'unknown')}")
            return config
        except Exception as e:
            print(f"[WARNING] 加载配置失败，使用默认 API 配置: {e}")
            import traceback
            traceback.print_exc()
            # 返回默认 API 配置
            return {
                "llm_provider": "api",
                "api_settings": {
                    "api_url": "https://api.openai-hk.com/v1/chat/completions",
                    "api_key": "hk-rf256210000027899536cbcb497417e8dfc70c2960229c22",
                    "default_model": "gemini-2.5-flash",
                    "temperature": 0.8,
                    "timeout": 60
                }
            }
    
    def run(self):
        """执行 LLM 请求（使用策略模式）"""
        try:
            # 创建策略客户端
            from modules.ai_assistant.clients import create_llm_client
            
            self.strategy_client = create_llm_client(self.config)
            provider = self.config.get('llm_provider', 'api')
            
            print(f"[LLM] 使用供应商: {provider}, 模型: {self.strategy_client.get_model_name()}")
            
            # 调用策略生成响应
            response_generator = self.strategy_client.generate_response(
                context_messages=self.messages,
                stream=True,
                temperature=self.temperature,
                tools=self.tools
            )
            
            # 处理生成器输出，发送信号到 UI
            for chunk in response_generator:
                if not self.is_running:
                    break
                
                if chunk:
                    # 支持新格式（dict）和旧格式（str）
                    if isinstance(chunk, dict):
                        # 新格式：{'type': 'content', 'text': '...'}
                        if chunk.get('type') == 'content':
                            text = chunk.get('text', '')
                            if text:
                                self.chunk_received.emit(text)
                        # 忽略 tool_calls 类型（由协调器处理）
                    else:
                        # 旧格式：纯字符串
                        self.chunk_received.emit(chunk)
            
            # 请求完成
            if self.is_running:
                self.request_finished.emit()
        
        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] LLM 请求失败: {error_msg}")
            self.error_occurred.emit(error_msg)
    
    def stop(self):
        """停止请求"""
        self.is_running = False
        self.quit()
    
    @staticmethod
    def send(
        messages: list,
        model: str = "gemini-2.5-flash",
        temperature: float = 0.8,
        tools: list = None,
        stream: bool = True
    ):
        """
        v0.2 新增：发送请求的便捷工厂方法
        
        封装 OpenAI tools 参数格式，确保兼容性
        
        Args:
            messages: 对话历史
            model: 模型名称
            temperature: 温度参数
            tools: 工具列表（ChatGPT-style格式）
                  格式：[{type:'function', function:{name, description, parameters}}]
            stream: 是否启用流式输出
            
        Returns:
            APIClient: API 客户端实例
        """
        return APIClient(
            messages=messages,
            model=model,
            temperature=temperature,
            tools=tools
        )

