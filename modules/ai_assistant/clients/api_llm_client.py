# -*- coding: utf-8 -*-

"""
API LLM 客户端（策略实现）
封装 OpenAI-HK API 或其他兼容的 API 调用逻辑
"""

import json
import os
import time
import requests
from typing import Dict, Any, Generator, List, Optional
from .base_llm_client import BaseLLMClient


class ApiLLMClient(BaseLLMClient):
    """
    API LLM 客户端策略
    
    支持 OpenAI-compatible API（如 OpenAI-HK、Anthropic 等）
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化 API 客户端
        
        Args:
            config: API 配置字典，应包含：
                - api_url: API 端点 URL
                - api_key: API 密钥
                - default_model: 默认模型名称
                - temperature: 温度参数（可选）
                - timeout: 超时时间（可选）
        """
        super().__init__(config)
        
        # 从配置读取（不使用硬编码的默认值）
        self.api_url = config.get('api_url', 'https://api.openai-hk.com/v1/chat/completions')
        self.api_key = config.get('api_key', '')
        self.default_model = config.get('default_model', 'gemini-2.5-flash')
        self.default_temperature = config.get('temperature', 0.8)
        self.timeout = config.get('timeout', 60)
        
        # 验证必需的配置
        if not self.api_key:
            raise ValueError(
                "API Key 未配置！\n\n"
                "请在 [设置 → AI 助手设置] 中配置 API Key。"
            )
        
        # 构建请求头
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": self.api_key
        }
        
        # 创建持久化的Session对象（复用连接，避免每次都建立新连接）
        self._session = requests.Session()
        self._session.trust_env = False  # 禁用环境变量代理
        self._session.proxies = {'http': None, 'https': None}  # 显式禁用代理
        # 设置连接池参数
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,  # 连接池大小
            pool_maxsize=20,      # 最大连接数
            max_retries=3,        # 自动重试3次
            pool_block=False
        )
        self._session.mount('http://', adapter)
        self._session.mount('https://', adapter)
        
        # Tool calls 累积缓冲区
        self._tool_calls_buffer = []
    
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
            temperature: 温度参数（覆盖配置）
            tools: Function Calling 工具列表
            
        Yields:
            str: 响应的 token 块
        """
        # 关键调试：追踪API调用来源
        import traceback
        call_stack = ''.join(traceback.format_stack())
        print(f"\n{'='*80}")
        print(f"[API_CALL] !!! generate_response 被调用！")
        print(f"[API_CALL] 消息数量: {len(context_messages)}")
        print(f"[API_CALL] 工具数量: {len(tools) if tools else 0}")
        print(f"[API_CALL] 调用堆栈:\n{call_stack}")
        print(f"{'='*80}\n")
        
        try:
            # 清除环境变量中的代理设置（临时）
            env_backup = {}
            proxy_vars = ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'all_proxy', 'ALL_PROXY']
            for var in proxy_vars:
                if var in os.environ:
                    env_backup[var] = os.environ[var]
                    del os.environ[var]
            
            try:
                # 构建请求体
                payload = {
                    "model": self.default_model,
                    "messages": context_messages,
                    "temperature": temperature if temperature is not None else self.default_temperature,
                    "stream": stream
                }
                
                # 添加 tools 参数（如果提供）
                if tools:
                    payload["tools"] = tools
                
                # 使用持久化Session发送请求（复用连接）
                response = self._session.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    stream=stream,
                    timeout=self.timeout
                )
            finally:
                # 恢复环境变量
                for var, value in env_backup.items():
                    os.environ[var] = value
            
            # 检查响应状态
            if response.status_code != 200:
                error_text = response.text
                try:
                    error_data = json.loads(error_text)
                    error_msg = error_data.get('error', {}).get('message', error_text)
                except:
                    error_msg = error_text
                raise Exception(f"API 错误 ({response.status_code}): {error_msg}")
            
            # 处理流式响应
            if stream:
                buffer = ""
                for chunk in response.iter_content(chunk_size=None, decode_unicode=False):
                    if not chunk:
                        continue
                    
                    try:
                        # 解码并添加到缓冲区
                        buffer += chunk.decode('utf-8')
                        
                        # 处理缓冲区中的完整行
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            line = line.strip()
                            
                            if not line or not line.startswith('data: '):
                                continue
                            
                            # 提取数据
                            data_str = line[6:]
                            
                            # 检查结束标记
                            if data_str == '[DONE]':
                                return
                            
                            # 解析并提取内容
                            try:
                                data = json.loads(data_str)
                                
                                # ⚡ 提取 token 使用量（在响应中可能出现）
                                usage = data.get('usage')
                                if usage and isinstance(usage, dict):
                                    yield {
                                        'type': 'token_usage',
                                        'usage': {
                                            'prompt_tokens': usage.get('prompt_tokens', 0),
                                            'completion_tokens': usage.get('completion_tokens', 0),
                                            'total_tokens': usage.get('total_tokens', 0)
                                        }
                                    }
                                
                                if 'choices' in data and len(data['choices']) > 0:
                                    choice = data['choices'][0]
                                    delta = choice.get('delta', {})
                                    
                                    # 检测 tool_calls（优先级更高）
                                    tool_calls = delta.get('tool_calls')
                                    if tool_calls:
                                        # 累积 tool_calls（可能分多个 chunk）
                                        self._accumulate_tool_calls(tool_calls)
                                        continue
                                    
                                    # 检测 finish_reason
                                    finish_reason = choice.get('finish_reason')
                                    if finish_reason == 'tool_calls':
                                        # 返回完整的 tool_calls
                                        yield {
                                            'type': 'tool_calls',
                                            'tool_calls': self._get_accumulated_tool_calls()
                                        }
                                        return
                                    
                                    # 正常的文本内容
                                    content = delta.get('content', '')
                                    
                                    # 尝试其他格式
                                    if not content:
                                        message = choice.get('message', {})
                                        content = message.get('content', '')
                                    
                                    if not content:
                                        content = choice.get('text', '')
                                    
                                    if content:
                                        # 逐字符输出，模拟打字机效果
                                        for char in content:
                                            time.sleep(0.015)  # 每个字符延迟15ms
                                            yield {'type': 'content', 'text': char}
                            
                            except json.JSONDecodeError:
                                continue
                    
                    except UnicodeDecodeError:
                        # 多字节字符被分割，继续累积
                        continue
            else:
                # 非流式响应
                data = response.json()
                if 'choices' in data and len(data['choices']) > 0:
                    content = data['choices'][0]['message']['content']
                    yield content
        
        except requests.exceptions.Timeout:
            raise Exception("请求超时，请检查网络连接")
        except requests.exceptions.ConnectionError:
            raise Exception("连接失败，请检查网络设置")
        except Exception as e:
            raise Exception(f"API 请求失败: {str(e)}")
    
    def get_model_name(self) -> str:
        """获取模型名称"""
        return self.default_model
    
    def _accumulate_tool_calls(self, tool_calls_delta: List[Dict]):
        """
        累积流式返回的 tool_calls
        
        Args:
            tool_calls_delta: tool_calls 增量数据
        """
        for tc_delta in tool_calls_delta:
            index = tc_delta.get('index', 0)
            
            # 扩展 buffer
            while len(self._tool_calls_buffer) <= index:
                self._tool_calls_buffer.append({
                    'id': '',
                    'type': 'function',
                    'function': {'name': '', 'arguments': ''}
                })
            
            # 累积数据
            if 'id' in tc_delta:
                self._tool_calls_buffer[index]['id'] = tc_delta['id']
            
            if 'function' in tc_delta:
                func = tc_delta['function']
                if 'name' in func:
                    self._tool_calls_buffer[index]['function']['name'] += func['name']
                if 'arguments' in func:
                    self._tool_calls_buffer[index]['function']['arguments'] += func['arguments']
    
    def _get_accumulated_tool_calls(self) -> List[Dict]:
        """
        获取累积的 tool_calls 并清空缓冲区
        
        Returns:
            List[Dict]: 完整的 tool_calls 列表
        """
        result = self._tool_calls_buffer.copy()
        self._tool_calls_buffer = []
        return result
    
    def generate_response_non_streaming(
        self,
        context_messages: List[Dict[str, str]],
        temperature: float = None,
        tools: List[Dict] = None
    ) -> Dict:
        """
        生成响应（非流式，用于工具调用检测）
        
        Args:
            context_messages: 消息历史
            temperature: 温度参数（覆盖配置）
            tools: Function Calling 工具列表
            
        Returns:
            Dict: {
                'type': 'tool_calls' | 'content',
                'tool_calls': [...] | None,
                'content': str | None
            }
        """
        try:
            # 清除环境变量中的代理设置（临时）
            env_backup = {}
            proxy_vars = ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'all_proxy', 'ALL_PROXY']
            for var in proxy_vars:
                if var in os.environ:
                    env_backup[var] = os.environ[var]
                    del os.environ[var]
            
            try:
                # 构建请求体
                payload = {
                    "model": self.default_model,
                    "messages": context_messages,
                    "temperature": temperature if temperature is not None else self.default_temperature,
                    "stream": False
                }
                
                # 添加 tools 参数（如果提供）
                if tools:
                    payload["tools"] = tools
                
                # 使用持久化Session发送请求（复用连接）
                response = self._session.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=self.timeout
                )
            finally:
                # 恢复环境变量
                for var, value in env_backup.items():
                    os.environ[var] = value
            
            # 检查响应状态
            if response.status_code != 200:
                error_text = response.text
                try:
                    error_data = json.loads(error_text)
                    error_msg = error_data.get('error', {}).get('message', error_text)
                except:
                    error_msg = error_text
                raise Exception(f"API 错误 ({response.status_code}): {error_msg}")
            
            # 解析响应
            data = response.json()
            
            # ⚡ 提取token使用统计
            usage = data.get('usage', {})
            
            if 'choices' in data and len(data['choices']) > 0:
                choice = data['choices'][0]
                message = choice.get('message', {})
                
                # 检查是否有 tool_calls
                if 'tool_calls' in message and message['tool_calls']:
                    return {
                        'type': 'tool_calls',
                        'tool_calls': message['tool_calls'],
                        'content': None,
                        'usage': usage  # ⚡ 添加token统计
                    }
                else:
                    # 返回普通内容
                    content = message.get('content', '')
                    return {
                        'type': 'content',
                        'tool_calls': None,
                        'content': content,
                        'usage': usage  # ⚡ 添加token统计
                    }
            else:
                raise Exception("API 响应格式错误：缺少 choices")
        
        except requests.exceptions.Timeout:
            raise Exception("请求超时，请检查网络连接")
        except requests.exceptions.ConnectionError:
            raise Exception("连接失败，请检查网络设置")
        except Exception as e:
            raise Exception(f"API 请求失败: {str(e)}")

