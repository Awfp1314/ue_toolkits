"""
API 客户端模块
负责与 OpenAI-HK API 通信
"""

import json
import os
import requests
from PyQt6.QtCore import QThread, pyqtSignal


class APIClient(QThread):
    """
    API 客户端线程
    支持流式输出
    """
    # 信号定义
    chunk_received = pyqtSignal(str)      # 接收到数据块
    request_finished = pyqtSignal()       # 请求完成
    error_occurred = pyqtSignal(str)      # 发生错误
    
    def __init__(self, messages, model="gpt-3.5-turbo", temperature=0.8, tools=None):
        super().__init__()
        self.messages = messages
        self.model = model
        self.temperature = temperature
        self.tools = tools  # v0.2 新增：OpenAI tools 参数
        self.is_running = True
        
        # API 配置
        self.api_url = "https://api.openai-hk.com/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "hk-rf256210000027899536cbcb497417e8dfc70c2960229c22"
        }
    
    def run(self):
        """执行 API 请求"""
        try:
            print(f"[API] 开始请求，模型: {self.model}")
            
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
                    "model": self.model,
                    "messages": self.messages,
                    "temperature": self.temperature,
                    "stream": True  # 启用流式输出
                }
                
                # v0.2 新增：添加 tools 参数（如果提供）
                # 兼容 ChatGPT-style: tools=[{type:'function', function:{name,parameters}}]
                if self.tools:
                    payload["tools"] = self.tools
                    print(f"[API] 启用工具调用模式，工具数量: {len(self.tools)}")
                
                print(f"[API] 发送请求到: {self.api_url}")
                print(f"[API] 已禁用代理设置")
                
                # 创建一个 Session 对象，完全禁用代理
                session = requests.Session()
                session.trust_env = False  # 不信任环境变量
                
                # 发送请求（绕过系统代理）
                response = session.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    stream=True,
                    timeout=60,
                    proxies={'http': None, 'https': None}  # 明确禁用所有代理
                )
            finally:
                # 恢复环境变量
                for var, value in env_backup.items():
                    os.environ[var] = value
            print(f"[API] 收到响应，状态码: {response.status_code}")
            
            # 检查响应状态
            if response.status_code != 200:
                error_text = response.text
                try:
                    error_data = json.loads(error_text)
                    error_msg = error_data.get('error', {}).get('message', error_text)
                except:
                    error_msg = error_text
                self.error_occurred.emit(f"API 错误 ({response.status_code}): {error_msg}")
                return
            
            # 处理流式响应
            for line in response.iter_lines():
                if not self.is_running:
                    break
                
                if not line:
                    continue
                
                line = line.decode('utf-8')
                
                # 跳过非数据行
                if not line.startswith('data: '):
                    continue
                
                # 提取数据
                data_str = line[6:]
                
                # 检查结束标记
                if data_str == '[DONE]':
                    break
                
                try:
                    # 解析 JSON
                    data = json.loads(data_str)
                    
                    # 提取内容
                    if 'choices' in data and len(data['choices']) > 0:
                        delta = data['choices'][0].get('delta', {})
                        content = delta.get('content', '')
                        
                        if content:
                            # 发送内容块
                            self.chunk_received.emit(content)
                
                except json.JSONDecodeError as e:
                    # 忽略 JSON 解析错误
                    continue
                except Exception as e:
                    # 其他错误
                    print(f"处理数据块时出错: {str(e)}")
                    continue
            
            # 请求完成
            self.request_finished.emit()
        
        except requests.exceptions.Timeout:
            self.error_occurred.emit("请求超时，请检查网络连接")
        except requests.exceptions.ConnectionError:
            self.error_occurred.emit("连接失败，请检查网络设置")
        except Exception as e:
            self.error_occurred.emit(f"发生错误: {str(e)}")
    
    def stop(self):
        """停止请求"""
        self.is_running = False
        self.quit()
    
    @staticmethod
    def send(
        messages: list,
        model: str = "gpt-3.5-turbo",
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

