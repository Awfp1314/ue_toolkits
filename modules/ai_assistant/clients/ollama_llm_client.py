# -*- coding: utf-8 -*-

"""
Ollama LLM 客户端（策略实现）
支持本地 Ollama 模型服务
"""

import json
import time
from typing import Dict, Any, Generator, List, Optional
from .base_llm_client import BaseLLMClient


class OllamaLLMClient(BaseLLMClient):
    """
    Ollama LLM 客户端策略
    
    通过 Ollama 的 HTTP API 调用本地运行的大语言模型
    文档：https://github.com/ollama/ollama/blob/main/docs/api.md
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化 Ollama 客户端
        
        Args:
            config: Ollama 配置字典，应包含：
                - base_url: Ollama 服务地址（默认 http://localhost:11434）
                - model_name: 模型名称（如 llama3、mistral 等）
                - stream: 是否流式传输（默认 True）
                - timeout: 超时时间（默认 60）
        """
        super().__init__(config)
        
        self.base_url = config.get('base_url', 'http://localhost:11434')
        self.model_name = config.get('model_name', 'llama3')
        self.stream = config.get('stream', True)
        self.timeout = config.get('timeout', 60)
        
        # 构建 API 端点
        self.chat_endpoint = f"{self.base_url}/api/chat"
    
    def generate_response(
        self,
        context_messages: List[Dict[str, str]],
        stream: bool = True,
        temperature: float = None,
        tools: List[Dict] = None
    ) -> Generator[str, None, None]:
        """
        生成响应（流式）
        
        Args:
            context_messages: 消息历史
            stream: 是否流式传输
            temperature: 温度参数（Ollama 支持，可选）
            tools: Function Calling（Ollama 部分模型支持，可选）
            
        Yields:
            str: 响应的 token 块
        """
        try:
            import httpx
        except ImportError:
            raise Exception("httpx 库未安装，请运行: pip install httpx")
        
        try:
            # 构建请求体
            payload = {
                "model": self.model_name,
                "messages": context_messages,
                "stream": stream
            }
            
            # 添加可选参数
            if temperature is not None:
                payload["temperature"] = temperature
            
            # Ollama 的 tools 格式（如果支持）
            if tools:
                payload["tools"] = tools
            
            # 发送请求
            with httpx.stream(
                "POST",
                self.chat_endpoint,
                json=payload,
                timeout=self.timeout
            ) as response:
                
                # 检查响应状态
                if response.status_code != 200:
                    error_text = response.text
                    try:
                        error_data = json.loads(error_text)
                        error_msg = error_data.get('error', error_text)
                    except:
                        error_msg = error_text
                    raise Exception(f"Ollama API 错误 ({response.status_code}): {error_msg}")
                
                # 处理流式响应
                if stream:
                    for line in response.iter_lines():
                        if not line.strip():
                            continue
                        
                        try:
                            # Ollama 返回的每一行都是一个 JSON 对象
                            data = json.loads(line)
                            
                            # 提取内容
                            if 'message' in data:
                                content = data['message'].get('content', '')
                                
                                if content:
                                    # 切分成小块模拟打字效果
                                    chunk_size = 3
                                    for i in range(0, len(content), chunk_size):
                                        small_chunk = content[i:i+chunk_size]
                                        yield small_chunk
                                        time.sleep(0.015)  # 15ms 延迟
                            
                            # 检查是否完成
                            if data.get('done', False):
                                return
                        
                        except json.JSONDecodeError:
                            continue
                else:
                    # 非流式响应
                    response_text = response.text
                    data = json.loads(response_text)
                    
                    if 'message' in data:
                        content = data['message'].get('content', '')
                        yield content
        
        except httpx.ConnectError:
            raise Exception(f"无法连接到 Ollama 服务 ({self.base_url})，请确保 Ollama 已启动")
        except httpx.TimeoutException:
            raise Exception(f"Ollama 请求超时（{self.timeout}秒），模型可能在加载中")
        except Exception as e:
            raise Exception(f"Ollama 请求失败: {str(e)}")
    
    def get_model_name(self) -> str:
        """获取模型名称"""
        return self.model_name
    
    def list_available_models(self) -> List[str]:
        """
        列出 Ollama 中可用的模型
        
        Returns:
            List[str]: 模型名称列表
        """
        try:
            import httpx
            
            list_endpoint = f"{self.base_url}/api/tags"
            response = httpx.get(list_endpoint, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                return [model['name'] for model in models]
            else:
                return []
        
        except Exception as e:
            print(f"[WARNING] 获取 Ollama 模型列表失败: {e}")
            return []
    
    def check_ollama_status(self) -> bool:
        """
        检查 Ollama 服务是否可用
        
        Returns:
            bool: 服务是否可用
        """
        try:
            import httpx
            
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        
        except:
            return False

