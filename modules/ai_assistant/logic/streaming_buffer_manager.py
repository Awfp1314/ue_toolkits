"""
流式输出缓冲区管理器
统一管理流式输出的缓冲区和定时器（运行在 UI 线程）
"""

from PyQt6.QtCore import QTimer
from typing import Callable, Optional
from core.logger import get_logger


class StreamingBufferManager:
    """流式输出缓冲区管理器（UI 线程专用）

    设计约束：
    1. 必须在 UI 线程创建和使用
    2. 通过信号从工作线程接收数据
    3. 支持重复 start() 调用（自动重置）
    4. stop() 后忽略新的 add_chunk() 调用
    """

    def __init__(self, flush_interval_ms: int = 100):
        """初始化缓冲区管理器

        Args:
            flush_interval_ms: 刷新间隔（毫秒）
        """
        self.logger = get_logger(__name__)
        self._buffer = ""
        self._timer = QTimer()
        self._timer.setInterval(flush_interval_ms)
        self._callback: Optional[Callable[[str], None]] = None
        self._is_running = False

    def start(self, callback: Callable[[str], None]) -> None:
        """启动缓冲和定时器

        Args:
            callback: 刷新回调函数（在 UI 线程调用）

        注意：重复调用会自动重置状态
        """
        # 如果已经运行，先停止
        if self._is_running:
            self.logger.warning("StreamingBufferManager 已在运行，自动重置")
            self.stop_and_cleanup()

        self._callback = callback
        self._is_running = True
        self._timer.timeout.connect(self._flush)
        self._timer.start()
        self.logger.debug("StreamingBufferManager 已启动")

    def add_chunk(self, text: str) -> None:
        """添加文本块到缓冲区

        Args:
            text: 文本块

        注意：如果已停止，此调用会被忽略
        """
        if not self._is_running:
            self.logger.debug("StreamingBufferManager 已停止，忽略 add_chunk 调用")
            return

        self._buffer += text

    def flush(self) -> None:
        """立即刷新缓冲区"""
        if self._buffer and self._callback:
            self._callback(self._buffer)
            self._buffer = ""

    def stop_and_cleanup(self) -> None:
        """停止定时器并清理所有状态"""
        self._is_running = False

        if self._timer.isActive():
            self._timer.stop()

        # 刷新剩余缓冲区
        self.flush()

        # 断开信号
        try:
            self._timer.timeout.disconnect(self._flush)
        except TypeError:
            pass  # 信号未连接

        # 清理状态
        self._buffer = ""
        self._callback = None
        self.logger.debug("StreamingBufferManager 已清理")

    def _flush(self) -> None:
        """定时器回调：刷新缓冲区"""
        self.flush()
