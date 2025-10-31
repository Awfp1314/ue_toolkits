# -*- coding: utf-8 -*-

# 路径管理、系统目录定位
import os
import platform
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class PathUtils:
    def __init__(self) -> None:
        self.system: str = platform.system()
    
    def get_user_data_dir(self) -> Path:
        """返回用户数据目录路径
        
        使用标准的跨平台目录获取方法，优先使用Path.home()
        """
        try:
            home = Path.home()
        except RuntimeError:
            # 如果无法获取主目录，使用临时目录作为备用
            import tempfile
            home = Path(tempfile.gettempdir())
            logger.warning(f"无法获取用户主目录，使用临时目录: {home}")
        
        if self.system == "Windows":
            # Windows: %APPDATA%/ue_toolkit/user_data
            base_path = home / "AppData" / "Roaming"
        elif self.system == "Darwin":  # macOS
            # Mac: ~/Library/Application Support/ue_toolkit/user_data
            base_path = home / "Library" / "Application Support"
        else:
            # Linux 和其他系统使用标准的 XDG 目录
            xdg_data_home = os.getenv('XDG_DATA_HOME')
            if xdg_data_home:
                base_path = Path(xdg_data_home)
            else:
                # 默认: ~/.local/share
                base_path = home / '.local' / 'share'
        
        user_data_path = base_path / "ue_toolkit" / "user_data"
        logger.info(f"用户数据目录路径: {user_data_path}")
        return user_data_path
    
    def get_user_config_dir(self) -> Path:
        """返回用户配置目录路径"""
        user_data_dir = self.get_user_data_dir()
        config_path = user_data_dir / "configs"
        logger.info(f"用户配置目录路径: {config_path}")
        return config_path
    
    def get_user_logs_dir(self) -> Path:
        """返回用户日志目录路径"""
        user_data_dir = self.get_user_data_dir()
        logs_path = user_data_dir / "logs"
        logger.info(f"用户日志目录路径: {logs_path}")
        return logs_path
    
    def create_dirs(self) -> None:
        """检查并创建用户目录（如 configs, logs, cache）如果这些目录不存在
        
        注意：thumbnails 和 documents 不再在全局目录创建，而是在资产库本地目录创建
        """
        user_data_dir = self.get_user_data_dir()
        
        # 需要创建的目录列表（只保留全局配置和日志目录）
        dirs_to_create = [
            "configs",
            "logs",
            "cache"
        ]
        
        logger.info(f"开始创建用户数据目录: {user_data_dir}")
        # 确保用户数据目录存在
        user_data_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"用户数据目录创建完成: {user_data_dir}")
        
        for dir_name in dirs_to_create:
            dir_path = user_data_dir / dir_name
            logger.info(f"正在创建目录: {dir_path}")
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"目录创建成功: {dir_path}")