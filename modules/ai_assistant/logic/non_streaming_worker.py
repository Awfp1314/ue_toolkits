# -*- coding: utf-8 -*-

"""
NonStreamingWorker - 异步非流式 API 调用工作线程

解决 UI 阻塞问题：在后台线程执行非流式 API 调用，避免阻塞 PyQt 主线程
"""

import time
import traceback
from typing import Dict, List, Optional
from PyQt6.QtCore import QThread, pyqtSignal


class NonStreamingWorker(QThread):
    """
    后台工作线程，用于执行非流式 API 调用
    
    职责：
    1. 在独立线程中执行 LLM 的非流式 API 调用
    2. 避免阻塞 PyQt 主线程
    3. 通过信号返回结果或错误
    """
    
    # 信号定义
    result_ready = pyqtSignal(dict)  # API 调用成功，返回结果
    error_occurred = pyqtSignal(str)  # API 调用失败，返回错误信息
    
    def __init__(self, llm_client, messages: List[Dict], tools: Optional[List[Dict]] = None):
        """
        初始化工作线程
        
        Args:
            llm_client: LLM 客户端实例（ApiLLMClient 或 OllamaClient）
            messages: 消息列表
            tools: 工具定义列表（可选）
        """
        super().__init__()
        self.llm_client = llm_client
        self.messages = messages
        self.tools = tools
        self._start_time = None
    
    def run(self):
        """
        在后台线程执行 API 调用
        
        此方法在独立线程中运行，不会阻塞主线程
        """
        try:
            # 记录开始时间
            self._start_time = time.time()
            
            print(f"[NonStreamingWorker] 开始执行非流式 API 调用...")
            print(f"[NonStreamingWorker] 消息数量: {len(self.messages)}")
            print(f"[NonStreamingWorker] 工具数量: {len(self.tools) if self.tools else 0}")
            
            # 执行非流式 API 调用（这是阻塞操作，但在后台线程中执行）
            response_data = self.llm_client.generate_response_non_streaming(
                self.messages,
                tools=self.tools
            )
            
            # 计算耗时
            elapsed = time.time() - self._start_time
            print(f"[NonStreamingWorker] API 调用完成，耗时: {elapsed:.2f}秒")
            
            # 发送结果信号
            self.result_ready.emit(response_data)
            
        except AttributeError as e:
            # LLM 客户端不支持非流式方法
            error_msg = f"LLM 客户端不支持非流式调用: {str(e)}"
            print(f"[NonStreamingWorker] [ERROR] {error_msg}")
            self.error_occurred.emit(error_msg)
            
        except Exception as e:
            # 其他错误
            error_msg = f"API 调用失败: {str(e)}"
            print(f"[NonStreamingWorker] [ERROR] {error_msg}")
            print(f"[NonStreamingWorker] 错误堆栈:\n{traceback.format_exc()}")
            self.error_occurred.emit(error_msg)
    
    def get_elapsed_time(self) -> float:
        """
        获取已经过的时间（秒）
        
        Returns:
            float: 从开始到现在的时间，如果未开始则返回 0
        """
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time
