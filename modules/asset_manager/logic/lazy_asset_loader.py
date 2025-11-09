# -*- coding: utf-8 -*-

"""
延迟资产加载器
优化程序启动性能，将资产加载延迟到首次访问时
"""

from PyQt6.QtCore import QThread, pyqtSignal
from typing import Optional, Callable, List
from core.logger import get_logger

logger = get_logger(__name__)


class AssetLoadThread(QThread):
    """资产加载工作线程
    
    在后台线程中执行资产加载操作，避免阻塞 UI 线程
    """
    load_complete = pyqtSignal(bool, str)  # (success, error_message)
    
    def __init__(self, asset_manager_logic):
        """初始化资产加载线程
        
        Args:
            asset_manager_logic: AssetManagerLogic 实例
        """
        super().__init__()
        self.asset_manager_logic = asset_manager_logic
        logger.debug("AssetLoadThread 已创建")
    
    def run(self):
        """执行资产加载（在工作线程中运行）"""
        try:
            logger.info("开始在后台线程加载资产...")
            self.asset_manager_logic.get_all_assets()
            logger.info("资产加载成功")
            self.load_complete.emit(True, "")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"资产加载失败: {error_msg}", exc_info=True)
            self.load_complete.emit(False, error_msg)


class LazyAssetLoader:
    """延迟资产加载器
    
    设计原则：
    1. 多次 ensure_loaded() 不重复开线程
    2. 失败后允许重试（通过 reset() 方法）
    3. 上报错误给调用方
    4. 支持多个回调（处理并发调用）
    
    使用场景：
    - 程序启动时不立即加载资产
    - 用户首次打开资产管理器时才加载
    - 加载失败后允许用户重试
    """
    
    def __init__(self, asset_manager_logic):
        """初始化延迟加载器
        
        Args:
            asset_manager_logic: AssetManagerLogic 实例
        """
        self.logger = get_logger(__name__)
        self.asset_manager_logic = asset_manager_logic
        
        # 状态标志
        self._loaded = False
        self._loading = False
        self._load_thread: Optional[AssetLoadThread] = None
        self._error_message = ""
        
        # 回调列表（支持多个并发调用）
        self._pending_callbacks: List[Callable[[bool, str], None]] = []
        
        self.logger.info("LazyAssetLoader 已初始化")
    
    def ensure_loaded(self, on_complete: Optional[Callable[[bool, str], None]] = None) -> None:
        """确保资产已加载（异步）
        
        Args:
            on_complete: 完成回调 (success: bool, error_message: str)
        
        行为：
        1. 如果已加载，立即调用回调
        2. 如果正在加载，将回调加入队列等待
        3. 如果未加载，启动新的加载线程
        4. 如果之前失败，允许重试
        """
        # 已加载，立即返回
        if self._loaded:
            self.logger.debug("资产已加载，立即返回")
            if on_complete:
                on_complete(True, "")
            return
        
        # 添加回调到队列
        if on_complete:
            self._pending_callbacks.append(on_complete)
            self.logger.debug(f"添加回调到队列，当前队列长度: {len(self._pending_callbacks)}")
        
        # 正在加载，等待完成
        if self._loading:
            self.logger.debug("资产正在加载中，等待完成")
            return
        
        # 开始加载
        self.logger.info("开始异步加载资产")
        self._loading = True
        self._load_thread = AssetLoadThread(self.asset_manager_logic)
        self._load_thread.load_complete.connect(self._on_load_complete)
        self._load_thread.start()
    
    def _on_load_complete(self, success: bool, error_message: str):
        """加载完成回调（内部方法）
        
        Args:
            success: 是否成功
            error_message: 错误消息（如果失败）
        """
        self._loading = False
        
        if success:
            self._loaded = True
            self._error_message = ""
            self.logger.info("资产加载成功")
        else:
            self._loaded = False
            self._error_message = error_message
            self.logger.error(f"资产加载失败: {error_message}")
        
        # 调用所有待处理的回调
        callbacks = self._pending_callbacks.copy()
        self._pending_callbacks.clear()
        
        self.logger.debug(f"调用 {len(callbacks)} 个待处理的回调")
        for callback in callbacks:
            try:
                callback(success, error_message)
            except Exception as e:
                self.logger.error(f"回调执行失败: {e}", exc_info=True)

    def is_loaded(self) -> bool:
        """检查是否已加载

        Returns:
            bool: 如果资产已加载返回 True
        """
        return self._loaded

    def is_loading(self) -> bool:
        """检查是否正在加载

        Returns:
            bool: 如果正在加载返回 True
        """
        return self._loading

    def get_error(self) -> str:
        """获取最后的错误消息

        Returns:
            str: 错误消息，如果没有错误返回空字符串
        """
        return self._error_message

    def reset(self) -> None:
        """重置状态（用于重试）

        清除加载状态和错误消息，允许重新加载资产
        通常在加载失败后，用户点击"重试"按钮时调用
        """
        self._loaded = False
        self._loading = False
        self._error_message = ""
        self._pending_callbacks.clear()

        # 清理线程
        if self._load_thread and self._load_thread.isRunning():
            self.logger.warning("重置时线程仍在运行，等待线程结束")
            self._load_thread.wait(1000)  # 等待最多 1 秒

        self._load_thread = None
        self.logger.info("LazyAssetLoader 已重置，可以重新加载")

