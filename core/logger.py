# -*- coding: utf-8 -*-

# 全局日志系统
import logging
import logging.handlers
from pathlib import Path
from typing import Optional
import threading
import sys

# 全局锁用于线程安全的单例模式
_logger_instance_lock = threading.Lock()
# 全局Logger实例
_logger_instance: Optional['Logger'] = None


class UTF8StreamHandler(logging.StreamHandler):
    """自定义的UTF-8流处理器
    
    解决Windows控制台编码问题，而不修改全局sys.stdout/stderr。
    
    特点：
    1. 不修改全局流，只在日志处理器内部使用UTF-8编码
    2. 使用backslashreplace错误处理，保留无法编码的字符信息
    3. 保存原始流的引用，确保其他库不受影响
    4. 跨平台兼容（Windows和非Windows系统）
    """
    
    def __init__(self, stream=None):
        """初始化UTF-8流处理器
        
        Args:
            stream: 输出流，默认为sys.stdout
        """
        if stream is None:
            stream = sys.stdout
        
        self._original_stream = stream
        
        # 为Windows系统创建UTF-8包装流
        if sys.platform == 'win32' and hasattr(stream, 'buffer'):
            import io
            # 使用backslashreplace而不是replace，保留无法编码字符的信息
            # 例如：无法编码的字符会显示为 \uXXXX 而不是被替换为 ?
            self._utf8_stream = io.TextIOWrapper(
                stream.buffer,
                encoding='utf-8',
                errors='backslashreplace',  # 更安全的错误处理
                line_buffering=True  # 行缓冲，确保及时输出
            )
            super().__init__(self._utf8_stream)
        else:
            # 非Windows系统或没有buffer属性，直接使用原始流
            super().__init__(stream)
    
    def close(self):
        """关闭处理器时不关闭底层流
        
        重写此方法以防止关闭sys.stdout/stderr，
        因为这些是全局流，不应该被日志系统关闭。
        """
        self.flush()
        # 不调用 super().close()，避免关闭底层流


class Logger:
    """全局日志管理系统（线程安全单例）
    
    使用双重检查锁定模式确保线程安全：
    1. __new__ 方法在锁内创建唯一实例
    2. __init__ 方法使用实例级标记和锁保护，防止重复初始化
    3. 确保在多线程环境下的正确性
    
    编码处理改进：
    1. 使用自定义UTF8StreamHandler而不修改全局sys.stdout/stderr
    2. 使用backslashreplace错误处理策略保留字符信息
    3. 保存原始流引用，确保其他库不受影响
    """
    
    def __new__(cls) -> 'Logger':
        """线程安全的单例模式，确保全局只有一个 Logger 实例
        
        使用双重检查锁定（Double-Checked Locking）模式：
        1. 第一次检查：避免不必要的锁竞争
        2. 获取锁：确保同一时刻只有一个线程创建实例
        3. 第二次检查：防止多个线程同时通过第一次检查
        
        Returns:
            Logger: 全局唯一的 Logger 实例
        """
        global _logger_instance, _logger_instance_lock
        
        if _logger_instance is None:
            with _logger_instance_lock:
                # 双重检查：防止多个线程同时创建实例
                if _logger_instance is None:
                    _logger_instance = super().__new__(cls)
                    # 在实例上设置初始化标记（而非全局变量）
                    _logger_instance._initialized = False
                    # 为实例创建专用的初始化锁
                    _logger_instance._init_lock = threading.Lock()
        return _logger_instance
    
    def __init__(self):
        """初始化日志系统（线程安全）
        
        使用实例级锁和标记确保即使多个线程同时调用 __init__，
        初始化逻辑也只会执行一次。
        """
        # 使用实例级锁保护初始化过程
        with self._init_lock:
            # 防止重复初始化（使用实例级标记）
            if self._initialized:
                return
            
            self.logger = logging.getLogger("ue_toolkit")
            self.logger.setLevel(logging.DEBUG)
            
            # 清除现有的处理器，避免重复添加
            self.logger.handlers.clear()
            
            # 延迟导入PathUtils以避免循环导入
            from core.utils.path_utils import PathUtils
            self.path_utils = PathUtils()
            
            # 设置日志格式
            self.formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # 配置日志处理器
            self._setup_handlers()
            
            # 标记已初始化（在锁内设置，确保原子性）
            self._initialized = True
            
            self.logger.info("日志系统初始化完成")
    
    def _setup_handlers(self):
        """配置日志处理器
        
        改进的编码处理：
        1. 使用自定义UTF8StreamHandler而不修改全局sys.stdout/stderr
        2. 保存原始流的引用，确保其他库不受影响
        3. 使用backslashreplace错误处理，保留无法编码字符的信息
        """
        try:
            logs_dir = self.path_utils.get_user_logs_dir()
            log_file_path = logs_dir / "ue_toolkit.log"
            
            # 确保日志目录存在
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file_path,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(self.formatter)
            self.logger.addHandler(file_handler)
            
            # 使用自定义的UTF8StreamHandler，不修改全局sys.stdout
            console_handler = UTF8StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(self.formatter)
            self.logger.addHandler(console_handler)
            
            self._file_handler = file_handler
            self._console_handler = console_handler
            
            self.logger.info(f"日志文件路径: {log_file_path}")
            
        except PermissionError as e:
            # 权限错误
            error_msg = f"权限错误: 无法创建或写入日志文件: {e}"
            print(f"警告: {error_msg}")
            self.logger.error(error_msg)
        except FileNotFoundError as e:
            # 文件路径不存在
            error_msg = f"路径错误: 日志目录不存在且无法创建: {e}"
            print(f"警告: {error_msg}")
            self.logger.error(error_msg)
        except Exception as e:
            # 其他异常
            error_msg = f"未知错误: 无法设置文件日志处理器: {e}"
            print(f"警告: {error_msg}")
            self.logger.error(error_msg)
            # 确保至少有控制台输出
            if not self.logger.handlers:
                # 使用自定义UTF8StreamHandler作为后备
                console_handler = UTF8StreamHandler(sys.stdout)
                console_handler.setLevel(logging.INFO)
                console_handler.setFormatter(self.formatter)
                self.logger.addHandler(console_handler)
                self._console_handler = console_handler
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            logging.Logger: 日志记录器实例
        """
        return self.logger.getChild(name)
    
    def set_level(self, level: int):
        """设置日志级别
        
        Args:
            level: 日志级别 (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL)
        """
        self.logger.setLevel(level)
        for handler in self.logger.handlers:
            handler.setLevel(level)
    
    def cleanup_handlers(self):
        """清理日志处理器
        
        正确关闭所有日志处理器，释放资源。
        注意：不会关闭sys.stdout/stderr，因为使用了自定义UTF8StreamHandler。
        """
        for handler in self.logger.handlers[:]:  # 使用切片创建副本，避免迭代时修改
            try:
                handler.flush()  # 刷新缓冲区
                handler.close()  # 关闭处理器
                self.logger.removeHandler(handler)  # 从logger中移除
            except Exception as e:
                # 忽略清理过程中的错误
                print(f"警告: 清理日志处理器时出错: {e}")


def setup_logging() -> Logger:
    """全局函数，初始化日志系统
    
    Returns:
        Logger: 日志系统实例
    """
    return Logger()


def get_logger(name: str = "default") -> logging.Logger:
    """全局函数，获取日志记录器实例
    
    Args:
        name: 日志记录器名称，默认为"default"
        
    Returns:
        logging.Logger: 日志记录器实例
    """
    # 确保Logger已初始化
    logger_instance = Logger()
    return logger_instance.get_logger(name)


def init_logging_system():
    """初始化日志系统 - 统一入口函数（线程安全）
    
    这个函数应该在应用程序启动时只调用一次，通常在main.py中调用。
    其他模块只需要使用get_logger()获取logger实例即可。
    
    由于Logger类本身已经是线程安全的单例，此函数可以安全地被多次调用，
    但只有第一次调用会真正执行初始化逻辑。
    """
    global _logger_instance
    
    # 获取Logger实例（如果未初始化则自动初始化）
    logger_instance = Logger()
    
    if logger_instance._initialized:
        # 已经初始化过，只记录信息
        logger = get_logger("main")
        # 只在首次调用后才警告
        if hasattr(logger_instance, '_init_logging_system_called'):
            logger.warning("日志系统已经初始化，跳过重复初始化")
        else:
            logger.info("日志系统初始化完成")
            logger_instance._init_logging_system_called = True