# -*- coding: utf-8 -*-

import sys
import signal
import logging
from typing import Dict, Any, Optional, Callable
from pathlib import Path
import threading

from core.utils.path_utils import PathUtils
from core.logger import Logger, get_logger
from core.config.config_manager import ConfigManager
from core.module_manager import ModuleManager, ModuleState
from core.utils.thread_utils import get_thread_manager


# 创建模块级 logger，避免在初始化过程中出现未定义错误
_module_logger = get_logger(__name__)



class AppManager:
    """应用程序生命周期管理器（线程安全单例）
    
    使用双重检查锁定模式确保线程安全：
    1. __new__ 方法在锁内创建唯一实例
    2. __init__ 方法使用实例级标记和锁保护，防止重复初始化
    3. 确保在多线程环境下的正确性
    """
    
    _instance: Optional['AppManager'] = None
    _instance_lock = threading.Lock()  # 用于保护实例创建
    
    # 声明实例属性，解决类型检查问题
    _initialized: bool
    _init_lock: threading.Lock
    _is_setup: bool
    _is_running: bool
    _logger: logging.Logger
    
    def __new__(cls) -> 'AppManager':
        """线程安全的单例模式，确保全局只有一个 AppManager 实例
        
        使用双重检查锁定（Double-Checked Locking）模式：
        1. 第一次检查：避免不必要的锁竞争
        2. 获取锁：确保同一时刻只有一个线程创建实例
        3. 第二次检查：防止多个线程同时通过第一次检查
        
        Returns:
            AppManager: 全局唯一的 AppManager 实例
        """
        if cls._instance is None:
            with cls._instance_lock:
                # 双重检查：防止多个线程同时创建实例
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    # 在实例上设置初始化标记（而非类级）
                    cls._instance._initialized = False
                    # 为实例创建专用的初始化锁
                    cls._instance._init_lock = threading.Lock()
        return cls._instance
    
    def __init__(self):
        """初始化应用程序管理器（线程安全）
        
        使用实例级锁和标记确保即使多个线程同时调用 __init__，
        初始化逻辑也只会执行一次。
        """
        # 使用实例级锁保护初始化过程
        with self._init_lock:
            # 防止重复初始化（使用实例级标记）
            if self._initialized:
                return
            
            self.logger: Optional[Logger] = None
            self.path_utils: Optional[PathUtils] = None
            self.config_manager: Optional[ConfigManager] = None
            self.module_manager: Optional[ModuleManager] = None
            self.thread_manager = None  # 延迟初始化
            
            self._is_setup = False
            self._is_running = False
            
            # 使用模块级 logger 直到 Logger 初始化完成
            self._logger = _module_logger
            
            # 注册系统信号处理器
            self._register_system_signals()
            
            # 标记已初始化（在锁内设置，确保原子性）
            self._initialized = True
    
    def _register_system_signals(self) -> None:
        """注册系统信号处理器
        
        注意：signal.signal() 只能在主线程中调用。
        如果在非主线程中初始化AppManager，信号注册会失败，但这不影响其他功能。
        """
        try:
            if threading.current_thread() is threading.main_thread():
                # 注册 SIGINT (Ctrl+C) 和 SIGTERM 信号处理器
                signal.signal(signal.SIGINT, self._signal_handler)
                signal.signal(signal.SIGTERM, self._signal_handler)
                self._logger.info("系统信号处理器注册完成")
            else:
                self._logger.warning("当前不在主线程，跳过系统信号处理器注册")
        except Exception as e:
            self._logger.error(f"注册系统信号处理器失败: {e}")
    
    def _signal_handler(self, signum: int, frame: Any) -> None:
        """系统信号处理器"""
        self._logger.info(f"接收到系统信号: {signum}")
        self.quit()
    
    def setup(self) -> bool:
        """设置应用程序，按正确顺序初始化所有核心模块
        
        Returns:
            bool: 初始化是否成功
        """
        if self._is_setup:
            self._logger.warning("应用程序已经设置完成")
            return True
        
        try:
            self._logger.info("开始设置应用程序")
            
            # 1. 初始化 PathUtils
            self._logger.info("初始化 PathUtils")
            self.path_utils = PathUtils()
            self.path_utils.create_dirs()
            
            # 2. 初始化 Logger
            self._logger.info("初始化 Logger")
            self.logger = Logger()
            
            # 更新 AppManager 自身的 logger
            self._logger = get_logger("app_manager")
            self._logger.info("Logger 初始化完成")
            
            # 3. 初始化 ConfigManager
            self._logger.info("初始化 ConfigManager")
            # AppManager 使用自己的配置模板（如果存在）
            app_template_path = Path(__file__).parent / "config_templates" / "app_config_template.json"
            self.config_manager = ConfigManager("app", app_template_path)
            
            # 4. 初始化 ModuleManager
            self._logger.info("初始化 ModuleManager")
            self.module_manager = ModuleManager()
            
            # 5. 初始化 ThreadManager
            self._logger.info("初始化 ThreadManager")
            self.thread_manager = get_thread_manager()
            
            # 标记设置完成
            self._is_setup = True
            self._logger.info("应用程序设置完成")
            
            return True
        except Exception as e:
            self._logger.error(f"应用程序设置失败: {e}")
            return False
    
    def start(self) -> bool:
        """启动应用程序（同步版本，保持向后兼容）
        
        Returns:
            bool: 启动是否成功
        """
        if not self._is_setup:
            self._logger.error("应用程序尚未设置，请先调用 setup()")
            return False
            
        if self._is_running:
            self._logger.warning("应用程序已在运行中")
            return True
        
        try:
            self._logger.info("开始启动应用程序（同步模式）")
            
            if self.module_manager:
                self._logger.info("加载模块")
                if not self.module_manager.load_modules():
                    self._logger.error("模块加载失败")
                    return False
                
                self._logger.info("初始化模块")
                if not self.module_manager.initialize_modules():
                    self._logger.error("模块初始化失败")
                    return False
            
            # 标记应用正在运行
            self._is_running = True
            
            self._logger.info("应用程序启动完成")
            return True
        except Exception as e:
            self._logger.error(f"应用程序启动失败: {e}")
            return False
    
    def start_async(
        self,
        on_complete: Optional[Callable[[bool], None]] = None,
        on_progress: Optional[Callable[[int, str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ):
        """异步启动应用程序（推荐使用）
        
        Args:
            on_complete: 完成回调 (success: bool) -> None
            on_progress: 进度回调 (percent: int, message: str) -> None
            on_error: 错误回调 (error_message: str) -> None
            
        Example:
            def on_done(success):
                if success:
                    print("应用启动成功！")
            
            def on_progress(percent, msg):
                print(f"[{percent}%] {msg}")
            
            app_manager.start_async(
                on_complete=on_done,
                on_progress=on_progress
            )
        """
        if not self._is_setup:
            error_msg = "应用程序尚未设置，请先调用 setup()"
            self._logger.error(error_msg)
            if on_error:
                on_error(error_msg)
            return
            
        if self._is_running:
            self._logger.warning("应用程序已在运行中")
            if on_complete:
                on_complete(True)
            return
        
        self._logger.info("开始异步启动应用程序")
        
        def start_task():
            try:
                if on_progress:
                    on_progress(5, "正在准备启动...")
                
                if self.module_manager:
                    if on_progress:
                        on_progress(10, "正在加载模块...")
                    
                    # 使用同步方法（在后台线程执行）
                    if not self.module_manager.load_modules():
                        raise Exception("模块加载失败")
                    
                    if on_progress:
                        on_progress(60, "模块加载完成")
                    
                    if on_progress:
                        on_progress(70, "正在初始化模块...")
                    
                    if not self.module_manager.initialize_modules():
                        raise Exception("模块初始化失败")
                    
                    if on_progress:
                        on_progress(95, "模块初始化完成")
                
                # 标记应用正在运行
                self._is_running = True
                
                if on_progress:
                    on_progress(100, "应用启动完成")
                
                self._logger.info("应用程序异步启动完成")
                return True
                
            except Exception as e:
                error_msg = f"应用程序启动失败: {e}"
                self._logger.error(error_msg)
                if on_error:
                    on_error(error_msg)
                return False
        
        if self.thread_manager:
            self.thread_manager.run_in_thread(
                start_task,
                on_result=on_complete,
                on_error=on_error,
                on_progress=on_progress
            )
        else:
            self._logger.error("ThreadManager 未初始化")
            if on_error:
                on_error("ThreadManager 未初始化")
    
    def quit(self) -> None:
        """退出应用程序"""
        if not self._is_running:
            self._logger.warning("应用程序未在运行中")
            return
        
        try:
            self._logger.info("开始退出应用程序")
            
            # 卸载模块
            if self.module_manager:
                self._logger.info("卸载模块")
                modules_to_unload = self.module_manager.get_all_modules()
                for module_name, module_info in modules_to_unload.items():
                    # 只卸载已加载或已初始化的模块
                    if module_info.state in [ModuleState.LOADED, ModuleState.INITIALIZED]:
                        self.module_manager.unload_module(module_name)
            
            # 标记应用已停止
            self._is_running = False
            
            self._logger.info("应用程序退出完成")
        except Exception as e:
            self._logger.error(f"应用程序退出时发生错误: {e}")
    
    def get_app_config(self) -> Dict[str, Any]:
        """获取应用程序配置
        
        Returns:
            Dict[str, Any]: 应用程序配置
        """
        if not self.config_manager:
            return {}
        return self.config_manager.get_module_config()
    
    def update_app_config(self, key: str, value: Any) -> bool:
        """更新应用程序配置
        
        Args:
            key: 配置键
            value: 配置值
            
        Returns:
            bool: 更新是否成功
        """
        if not self.config_manager:
            return False
        return self.config_manager.update_config_value(key, value)
    
    def is_setup(self) -> bool:
        """检查应用程序是否已设置
        
        Returns:
            bool: 是否已设置
        """
        return self._is_setup
    
    def is_running(self) -> bool:
        """检查应用程序是否正在运行
        
        Returns:
            bool: 是否正在运行
        """
        return self._is_running


# 全局访问点
_app_manager_instance: Optional[AppManager] = None
_app_manager_lock = threading.Lock()


def get_app_manager() -> AppManager:
    """获取全局 AppManager 实例
    
    Returns:
        AppManager: 全局 AppManager 实例
    """
    global _app_manager_instance, _app_manager_lock
    
    if _app_manager_instance is None:
        with _app_manager_lock:
            if _app_manager_instance is None:
                _app_manager_instance = AppManager()
    return _app_manager_instance


def setup_app() -> bool:
    """设置应用程序
    
    Returns:
        bool: 初始化是否成功
    """
    app_manager = get_app_manager()
    return app_manager.setup()


def start_app() -> bool:
    """启动应用程序
    
    Returns:
        bool: 启动是否成功
    """
    app_manager = get_app_manager()
    return app_manager.start()


def quit_app() -> None:
    """退出应用程序"""
    app_manager = get_app_manager()
    app_manager.quit()


# 全局异常处理
def global_exception_handler(exc_type: type, exc_value: BaseException, exc_traceback: Any) -> None:
    """全局异常处理器（增强版：包含UI反馈）
    
    捕获所有未处理的异常，记录日志并向用户显示友好的错误对话框
    
    Args:
        exc_type: 异常类型
        exc_value: 异常值
        exc_traceback: 异常追踪信息
    """
    if issubclass(exc_type, KeyboardInterrupt):
        # 对于键盘中断，正常退出
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # 获取 AppManager 实例记录错误
    logger: Optional[logging.Logger] = None
    try:
        app_manager = get_app_manager()
        logger = app_manager._logger if app_manager else get_logger(__name__)
        logger.error("未捕获的异常:", exc_info=(exc_type, exc_value, exc_traceback))
    except:
        # 如果无法获取 logger，使用系统默认
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    # ✅ 显示用户友好的错误对话框
    try:
        from PyQt6.QtWidgets import QApplication, QMessageBox
        import traceback
        
        # 确保QApplication存在
        if QApplication.instance():
            # 格式化详细错误信息
            error_details = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("应用程序错误")
            msg.setText(f"遇到了一个严重错误")
            msg.setInformativeText(
                f"错误类型: {exc_type.__name__}\n"
                f"错误信息: {str(exc_value)}\n\n"
                "应用程序将尝试继续运行，但可能不稳定。\n"
                "建议保存当前工作后重启应用程序。\n\n"
                "详细信息请查看下方或日志文件。"
            )
            msg.setDetailedText(error_details)
            msg.setStandardButtons(
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Close
            )
            msg.setDefaultButton(QMessageBox.StandardButton.Ok)
            
            # 设置按钮文本（添加类型检查）
            ok_button = msg.button(QMessageBox.StandardButton.Ok)
            if ok_button is not None:
                ok_button.setText("继续运行")
                
            close_button = msg.button(QMessageBox.StandardButton.Close)
            if close_button is not None:
                close_button.setText("退出应用")
            
            result = msg.exec()
            
            if result == QMessageBox.StandardButton.Close:
                # 用户选择退出
                try:
                    quit_app()
                except:
                    pass
                # 强制退出
                sys.exit(1)
            
            # 用户选择继续运行，不做任何操作
            return
            
    except Exception as ui_error:
        # GUI创建失败，至少日志已记录
        # 记录UI创建失败的错误
        if logger is not None:
            try:
                logger.error(f"显示错误对话框时失败: {ui_error}")
            except:
                pass
    
    # 如果无法显示UI或用户选择继续，不自动退出
    # 让应用程序尝试继续运行


# 设置全局异常处理器
sys.excepthook = global_exception_handler