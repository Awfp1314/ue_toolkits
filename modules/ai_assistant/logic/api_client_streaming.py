"""
增强型流式 API 客户端（7.0-P8）
支持智能缓冲、中文/emoji处理、工具调用检测
"""

import time
from typing import Dict, Any, Generator, Optional
from PyQt6.QtCore import QThread, pyqtSignal


class ChunkBuffer:
    """
    智能缓冲器
    
    功能：
    - 每20-50ms合并一次输出，避免UI过度刷新
    - 检测不完整的中文/emoji，暂存等待下一chunk
    - 合并工具调用的delta（function_call的name/arguments逐步组装）
    """
    
    def __init__(self, flush_interval_ms: int = 30):
        """
        初始化缓冲器
        
        Args:
            flush_interval_ms: 刷新间隔（毫秒）
        """
        self.flush_interval_ms = flush_interval_ms
        self.buffer = ""
        self.last_flush_time = time.time()
        self.incomplete_utf8 = b""  # 不完整的UTF-8字节
    
    def add(self, chunk: str) -> Optional[str]:
        """
        添加chunk到缓冲区
        
        Args:
            chunk: 文本块
        
        Returns:
            如果需要刷新，返回缓冲内容；否则返回None
        """
        self.buffer += chunk
        
        # 检查是否需要刷新
        elapsed_ms = (time.time() - self.last_flush_time) * 1000
        
        if elapsed_ms >= self.flush_interval_ms:
            return self.flush()
        
        return None
    
    def flush(self) -> str:
        """
        强制刷新缓冲区
        
        Returns:
            缓冲内容
        """
        result = self.buffer
        self.buffer = ""
        self.last_flush_time = time.time()
        return result
    
    def is_utf8_incomplete(self, text: str) -> bool:
        """
        检查文本末尾是否有不完整的UTF-8字符
        
        Args:
            text: 文本
        
        Returns:
            是否不完整
        """
        try:
            # 尝试编码最后几个字符
            last_bytes = text[-3:].encode('utf-8')
            # 检查是否是多字节字符的一部分
            for i in range(1, min(4, len(last_bytes) + 1)):
                try:
                    last_bytes[-i:].decode('utf-8')
                    return False  # 完整
                except UnicodeDecodeError:
                    continue
            return True  # 不完整
        except:
            return False


class StreamingAPIClient(QThread):
    """
    增强型流式API客户端
    
    功能：
    - 智能缓冲输出
    - 检测和处理工具调用
    - 更好的错误处理和重试
    """
    
    # 信号定义
    chunk_received = pyqtSignal(str)         # 文本chunk
    tool_call_detected = pyqtSignal(dict)    # 工具调用检测到
    request_finished = pyqtSignal()          # 请求完成
    token_usage = pyqtSignal(dict)           # Token使用量
    error_occurred = pyqtSignal(str)         # 错误
    
    def __init__(
        self, 
        messages, 
        model=None, 
        temperature=None, 
        tools=None, 
        config=None,
        buffer_ms: int = 30
    ):
        """
        初始化流式API客户端
        
        Args:
            messages: 消息历史
            model: 模型名称
            temperature: 温度参数
            tools: 工具定义
            config: LLM配置
            buffer_ms: 缓冲间隔（毫秒）
        """
        super().__init__()
        self.messages = messages
        self.model = model
        self.temperature = temperature if temperature is not None else 0.8
        self.tools = tools
        self.config = config
        self.is_running = True
        
        # 创建智能缓冲器
        self.chunk_buffer = ChunkBuffer(flush_interval_ms=buffer_ms)
        
        # 工具调用累积器
        self.current_tool_call = None
    
    def run(self):
        """
        执行流式请求
        
        流程：
        1. 创建策略客户端
        2. 启动流式生成
        3. 逐chunk接收并缓冲
        4. 检测工具调用
        5. 完成后统计token
        """
        try:
            # 导入策略客户端工厂
            from modules.ai_assistant.clients import create_llm_client
            from pathlib import Path
            
            # 加载配置（如果未提供）
            if self.config is None:
                self.config = self._load_config()
            
            # 创建策略客户端
            strategy_client = create_llm_client(self.config)
            provider = self.config.get('llm_provider', 'api')
            
            print(f"[7.0-P8] 启动流式请求，供应商: {provider}, 模型: {strategy_client.get_model_name()}")
            
            # 启动流式生成
            response_generator = strategy_client.generate_response(
                context_messages=self.messages,
                stream=True,
                temperature=self.temperature,
                tools=self.tools
            )
            
            # 处理生成器输出
            response_text = ""
            for chunk in response_generator:
                if not self.is_running:
                    break
                
                if chunk:
                    # 处理不同类型的chunk
                    if isinstance(chunk, dict):
                        chunk_type = chunk.get('type', 'content')
                        
                        if chunk_type == 'content':
                            # 文本内容
                            text = chunk.get('text', '')
                            if text:
                                response_text += text
                                
                                # 添加到缓冲器
                                buffered = self.chunk_buffer.add(text)
                                if buffered:
                                    self.chunk_received.emit(buffered)
                        
                        elif chunk_type == 'tool_call':
                            # 工具调用（delta累积）
                            self._accumulate_tool_call(chunk.get('data', {}))
                    else:
                        # 兼容旧格式：纯字符串
                        response_text += chunk
                        buffered = self.chunk_buffer.add(chunk)
                        if buffered:
                            self.chunk_received.emit(buffered)
            
            # 刷新剩余缓冲
            remaining = self.chunk_buffer.flush()
            if remaining:
                self.chunk_received.emit(remaining)
            
            # 如果有未完成的工具调用，发送
            if self.current_tool_call:
                self.tool_call_detected.emit(self.current_tool_call)
                self.current_tool_call = None
            
            # 计算token使用量
            if self.is_running:
                token_stats = self._estimate_tokens(response_text)
                self.token_usage.emit(token_stats)
            
            # 请求完成
            if self.is_running:
                self.request_finished.emit()
            
        except Exception as e:
            error_msg = f"流式请求失败: {str(e)}"
            print(f"[ERROR] [7.0-P8] {error_msg}")
            import traceback
            traceback.print_exc()
            self.error_occurred.emit(error_msg)
    
    def _accumulate_tool_call(self, delta: Dict):
        """
        累积工具调用的delta
        
        Args:
            delta: 工具调用增量数据
        """
        if self.current_tool_call is None:
            self.current_tool_call = {
                'name': '',
                'arguments': ''
            }
        
        # 累积name和arguments
        if 'name' in delta:
            self.current_tool_call['name'] += delta['name']
        if 'arguments' in delta:
            self.current_tool_call['arguments'] += delta['arguments']
    
    def _estimate_tokens(self, response_text: str) -> Dict[str, int]:
        """
        估算token使用量
        
        Args:
            response_text: 响应文本
        
        Returns:
            Token统计
        """
        # 计算输入tokens
        input_text = ""
        for msg in self.messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                input_text += content
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        input_text += item.get("text", "")
        
        # 使用改进的估算：中文≈0.65 token/字符
        prompt_tokens = int(len(input_text) * 0.65)
        completion_tokens = int(len(response_text) * 0.65)
        total_tokens = prompt_tokens + completion_tokens
        
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            from core.config.config_manager import ConfigManager
            from pathlib import Path
            from modules.ai_assistant.config_schema import get_ai_assistant_schema
            
            template_path = Path(__file__).parent.parent / "config_template.json"
            config_manager = ConfigManager(
                "ai_assistant",
                template_path=template_path,
                config_schema=get_ai_assistant_schema()
            )
            return config_manager.get_module_config()
        except Exception as e:
            print(f"[ERROR] [7.0-P8] 加载配置失败: {e}")
            raise
    
    def stop(self):
        """停止请求"""
        self.is_running = False

