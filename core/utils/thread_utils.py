# -*- coding: utf-8 -*-

"""
线程工具 - 用于处理耗时操作，防止UI阻塞

使用示例:
    thread_manager = ThreadManager()
    
    def long_task():
        return "result"
    
    def on_result(result):
        # 在主线程更新UI
        print(f"结果: {result}")
    
    thread_manager.run_in_thread(
        long_task,
        on_result=on_result
    )
"""

from PyQt6.QtCore import QThread, pyqtSignal, QObject
from typing import Callable, Any, Optional
import traceback
import threading
from core.logger import get_logger

logger = get_logger(__name__)


class Worker(QObject):
    """通用工作线程"""
    
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)  # 进度信号 (0-100)
    
    def __init__(self, func: Callable, *args, **kwargs):
        """初始化Worker
        
        Args:
            func: 要执行的函数
            *args: 函数的位置参数
            **kwargs: 函数的关键字参数
        """
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self._is_cancelled = False
    
    def run(self):
        """执行任务"""
        try:
            logger.debug(f"开始执行任务: {self.func.__name__}")
            result = self.func(*self.args, **self.kwargs)
            
            if not self._is_cancelled:
                self.result.emit(result)
                logger.debug(f"任务完成: {self.func.__name__}")
        except Exception as e:
            if not self._is_cancelled:
                error_msg = f"{str(e)}\n{traceback.format_exc()}"
                logger.error(f"任务执行失败: {self.func.__name__}, 错误: {error_msg}")
                self.error.emit(error_msg)
        finally:
            if not self._is_cancelled:
                self.finished.emit()
    
    def cancel(self):
        """取消任务"""
        self._is_cancelled = True
        logger.debug(f"任务被取消: {self.func.__name__}")


class ThreadManager:
    """线程管理器（增强版：支持线程数限制）
    
    管理应用程序中的所有后台线程，防止线程泄漏和资源耗尽
    
    Features:
        - 线程池管理
        - 最大线程数限制
        - 线程使用情况监控
        - 自动清理
    """
    
    def __init__(self, max_threads: int = 10):
        """初始化线程管理器
        
        Args:
            max_threads: 最大并发线程数，默认10个
        """
        self.threads = []
        self.workers = []
        self.max_threads = max_threads
        self._active_threads = 0
        self._thread_semaphore = threading.Semaphore(max_threads)
        self._thread_lock = threading.Lock()
        logger.info(f"线程管理器初始化完成，最大线程数: {max_threads}")
    
    def run_in_thread(self,
                      func: Callable,
                      on_result: Optional[Callable] = None,
                      on_error: Optional[Callable] = None,
                      on_finished: Optional[Callable] = None,
                      on_progress: Optional[Callable] = None,
                      *args, **kwargs) -> tuple[QThread, Worker]:
        """在新线程中运行函数
        
        Args:
            func: 要执行的函数
            on_result: 结果回调函数 (result: Any) -> None
            on_error: 错误回调函数 (error_msg: str) -> None
            on_finished: 完成回调函数 () -> None
            on_progress: 进度回调函数 (progress: int) -> None
            *args: 传递给func的位置参数
            **kwargs: 传递给func的关键字参数
            
        Returns:
            tuple[QThread, Worker]: 线程和工作对象的元组
            
        Example:
            def long_task(n):
                time.sleep(n)
                return f"完成: {n}秒"
            
            def show_result(result):
                print(result)
            
            thread, worker = thread_manager.run_in_thread(
                long_task, 
                on_result=show_result,
                n=5
            )
        """
        # ✅ 等待可用线程槽（如果已达最大线程数，将阻塞）
        self._thread_semaphore.acquire()
        
        with self._thread_lock:
            self._active_threads += 1
            current_usage = (self._active_threads / self.max_threads) * 100
            logger.debug(f"分配线程槽 ({self._active_threads}/{self.max_threads}, {current_usage:.1f}%)")
        
        thread = QThread()
        worker = Worker(func, *args, **kwargs)
        
        # 将worker移动到新线程
        worker.moveToThread(thread)
        
        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        
        # 连接回调
        if on_result:
            worker.result.connect(on_result)
        if on_error:
            worker.error.connect(on_error)
        if on_finished:
            worker.finished.connect(on_finished)
        if on_progress:
            worker.progress.connect(on_progress)
        
        # ✅ 线程完成时释放槽和清理
        def on_thread_finished():
            self._thread_semaphore.release()
            with self._thread_lock:
                self._active_threads -= 1
                logger.debug(f"释放线程槽 ({self._active_threads}/{self.max_threads})")
            self._remove_thread(thread, worker)
        
        thread.finished.connect(on_thread_finished)
        
        self.threads.append(thread)
        self.workers.append(worker)
        
        # 启动线程
        thread.start()
        logger.debug(f"启动新线程执行: {func.__name__}")
        
        return thread, worker
    
    def _remove_thread(self, thread: QThread, worker: Worker):
        """从列表中移除已完成的线程"""
        try:
            if thread in self.threads:
                self.threads.remove(thread)
            if worker in self.workers:
                self.workers.remove(worker)
            logger.debug("清理已完成的线程")
        except ValueError:
            pass
    
    def cancel_all(self):
        """取消所有正在运行的任务"""
        logger.info(f"取消所有任务，共 {len(self.workers)} 个")
        for worker in self.workers:
            worker.cancel()
    
    def cleanup(self):
        """清理所有线程（阻塞等待所有线程完成）"""
        logger.info(f"开始清理线程，共 {len(self.threads)} 个")
        
        # 先取消所有任务
        self.cancel_all()
        
        # 等待所有线程完成
        for thread in self.threads:
            if thread.isRunning():
                thread.quit()
                thread.wait(5000)  # 最多等待5秒
                
                if thread.isRunning():
                    logger.warning("线程未能在5秒内完成，强制终止")
                    thread.terminate()
                    thread.wait()
        
        self.threads.clear()
        self.workers.clear()
        logger.info("线程清理完成")
    
    def get_running_count(self) -> int:
        """获取正在运行的线程数量"""
        return sum(1 for thread in self.threads if thread.isRunning())
    
    def get_thread_usage(self) -> dict:
        """获取线程使用情况
        
        Returns:
            dict: 线程使用统计信息
                {
                    'active': 当前活跃线程数,
                    'max': 最大线程数,
                    'available': 可用线程槽数,
                    'usage_percent': 使用率百分比,
                    'running': 实际运行中的线程数
                }
        
        Example:
            usage = thread_manager.get_thread_usage()
            print(f"线程使用率: {usage['usage_percent']:.1f}%")
        """
        with self._thread_lock:
            active = self._active_threads
        
        running = self.get_running_count()
        available = self.max_threads - active
        usage_percent = (active / self.max_threads) * 100 if self.max_threads > 0 else 0
        
        return {
            'active': active,
            'max': self.max_threads,
            'available': available,
            'usage_percent': usage_percent,
            'running': running
        }


# 全局线程管理器实例
_global_thread_manager: Optional[ThreadManager] = None


def get_thread_manager() -> ThreadManager:
    """获取全局线程管理器实例
    
    Returns:
        ThreadManager: 全局线程管理器
    """
    global _global_thread_manager
    if _global_thread_manager is None:
        _global_thread_manager = ThreadManager()
    return _global_thread_manager


def run_async(func: Callable,
              on_result: Optional[Callable] = None,
              on_error: Optional[Callable] = None,
              *args, **kwargs) -> tuple[QThread, Worker]:
    """便捷函数：异步运行函数
    
    Args:
        func: 要执行的函数
        on_result: 结果回调
        on_error: 错误回调
        *args: 函数参数
        **kwargs: 函数关键字参数
        
    Returns:
        tuple[QThread, Worker]: 线程和工作对象
        
    Example:
        def load_data():
            return fetch_from_api()
        
        def on_loaded(data):
            self.display_data(data)
        
        run_async(load_data, on_result=on_loaded)
    """
    return get_thread_manager().run_in_thread(
        func,
        on_result=on_result,
        on_error=on_error,
        *args,
        **kwargs
    )

