"""
线程清理 Mixin 模块

提供标准化的 QThread 清理机制，确保线程资源正确释放。
"""

from PyQt6.QtCore import QThread
from abc import abstractmethod
from core.logger import get_logger


class ThreadCleanupMixin:
    """线程清理 Mixin（抽象基类）

    设计原则：
    1. 子类必须实现 request_stop() 方法
    2. __del__ 仅作为兜底，不应依赖
    3. terminate() 为最后手段，优先等待正常退出
    4. 提供统一的清理接口

    使用示例：
        class MyWorker(QThread, ThreadCleanupMixin):
            def __init__(self):
                QThread.__init__(self)
                self._should_stop = False

            def request_stop(self):
                self._should_stop = True

            def run(self):
                while not self._should_stop:
                    # 执行任务
                    pass

        # 使用
        worker = MyWorker()
        worker.start()
        # 清理
        worker.cleanup(timeout_ms=1000)
    """

    @abstractmethod
    def request_stop(self) -> None:
        """请求线程停止（子类必须实现）

        子类应该：
        1. 设置停止标志（如 self._should_stop = True）
        2. 中断阻塞操作（如关闭网络连接）
        3. 不要在此方法中调用 quit() 或 terminate()

        注意：
        - 此方法应该是非阻塞的
        - 仅设置停止信号，不等待线程退出
        """
        pass

    def cleanup(self, timeout_ms: int = 1000) -> bool:
        """清理线程资源

        Args:
            timeout_ms: 等待超时时间（毫秒）

        Returns:
            bool: 是否成功清理（True=正常退出，False=强制终止）

        清理流程：
        1. 调用 request_stop() 请求停止
        2. 等待 timeout_ms 让线程正常退出
        3. 超时后调用 terminate() 强制终止（最后手段）

        注意：
        - 此方法会阻塞直到线程退出或超时
        - 强制终止可能导致资源泄漏，应尽量避免
        """
        logger = get_logger(self.__class__.__name__)

        # 检查是否是 QThread 实例
        if not isinstance(self, QThread):
            logger.error(f"{self.__class__.__name__} 不是 QThread 实例，无法清理")
            return False

        # 如果线程未运行，直接返回成功
        if not self.isRunning():
            logger.debug(f"{self.__class__.__name__} 线程未运行，无需清理")
            return True

        # 1. 请求停止
        try:
            logger.debug(f"{self.__class__.__name__} 请求线程停止")
            self.request_stop()
        except Exception as e:
            logger.error(f"{self.__class__.__name__} request_stop() 失败: {e}", exc_info=True)

        # 2. 等待正常退出
        logger.debug(f"{self.__class__.__name__} 等待线程退出（超时: {timeout_ms}ms）")
        if self.wait(timeout_ms):
            logger.debug(f"{self.__class__.__name__} 线程已正常退出")
            return True

        # 3. 超时后强制终止（最后手段）
        logger.warning(f"{self.__class__.__name__} 线程未在 {timeout_ms}ms 内退出，强制终止")
        try:
            self.terminate()
            # 等待终止完成（短超时）
            if self.wait(100):
                logger.warning(f"{self.__class__.__name__} 线程已强制终止")
            else:
                logger.error(f"{self.__class__.__name__} 线程终止失败")
        except Exception as e:
            logger.error(f"{self.__class__.__name__} terminate() 失败: {e}", exc_info=True)

        return False

    def __del__(self):
        """析构函数：兜底清理（不应依赖）

        注意：
        1. __del__ 调用时机不确定
        2. 可能在程序退出时调用，此时资源可能已释放
        3. 仅作为兜底，不应作为主要清理机制
        4. 异常会被静默忽略，避免影响程序退出

        设计理念：
        - 这是最后一道防线，用于捕获忘记调用 cleanup() 的情况
        - 不应依赖此方法进行正常清理
        - 正确的做法是显式调用 cleanup()
        """
        try:
            if isinstance(self, QThread) and self.isRunning():
                logger = get_logger(self.__class__.__name__)
                logger.warning(f"{self.__class__.__name__} 线程在析构时仍在运行，执行兜底清理")
                # 使用较短的超时，避免阻塞程序退出
                self.cleanup(timeout_ms=500)
        except Exception:
            # 静默忽略所有异常，避免影响程序退出
            # 在析构时不应抛出异常
            pass
