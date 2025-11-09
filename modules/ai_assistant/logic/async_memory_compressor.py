# -*- coding: utf-8 -*-

"""
异步记忆压缩器

在后台线程执行记忆压缩，避免阻塞主线程
"""

from typing import List, Dict, Optional
from PyQt6.QtCore import QThread, pyqtSignal


class AsyncMemoryCompressor(QThread):
    """
    异步记忆压缩工作线程
    
    职责：
    1. 在后台线程执行记忆压缩
    2. 避免阻塞主线程
    3. 通过信号返回压缩结果
    """
    
    # 信号定义
    compression_complete = pyqtSignal(bool)  # 压缩完成：是否成功
    
    def __init__(self, memory_manager, conversation_history: List[Dict]):
        """
        初始化异步压缩器
        
        Args:
            memory_manager: EnhancedMemoryManager 实例
            conversation_history: 对话历史列表
        """
        super().__init__()
        self.memory_manager = memory_manager
        self.conversation_history = conversation_history.copy()
    
    def run(self):
        """
        在后台线程执行压缩
        
        此方法在独立线程中运行，不会阻塞主线程
        """
        try:
            print("[AsyncMemoryCompressor] 开始异步压缩...")
            
            # 执行压缩
            success = self.memory_manager.compress_old_context(self.conversation_history)
            
            if success:
                print("[AsyncMemoryCompressor] 压缩成功")
            else:
                print("[AsyncMemoryCompressor] 压缩未执行或失败")
            
            # 发送完成信号
            self.compression_complete.emit(success)
            
        except Exception as e:
            print(f"[AsyncMemoryCompressor] 压缩失败: {e}")
            import traceback
            traceback.print_exc()
            self.compression_complete.emit(False)
