# -*- coding: utf-8 -*-

"""
系统托盘管理器
"""

from pathlib import Path
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QObject, pyqtSignal
from core.logger import get_logger

logger = get_logger(__name__)


class SystemTrayManager(QObject):
    """系统托盘管理器"""
    
    # 信号
    tray_activated = pyqtSignal()  # 托盘图标被点击
    show_window_requested = pyqtSignal()  # 请求显示窗口
    quit_requested = pyqtSignal()  # 请求退出应用
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tray_icon = None
        self.tray_menu = None
        self._is_initialized = False
        
    def initialize(self, icon_path: Path):
        """初始化系统托盘
        
        Args:
            icon_path: 图标路径
        """
        if self._is_initialized:
            logger.warning("系统托盘已经初始化")
            return
            
        try:
            # 检查系统托盘是否可用
            if not QSystemTrayIcon.isSystemTrayAvailable():
                logger.warning("系统托盘不可用")
                return
                
            # 创建托盘图标
            self.tray_icon = QSystemTrayIcon(self.parent())
            
            # 设置图标
            if icon_path.exists():
                icon = QIcon(str(icon_path))
                self.tray_icon.setIcon(icon)
                logger.info(f"系统托盘图标已设置: {icon_path}")
            else:
                logger.warning(f"托盘图标文件不存在: {icon_path}")
                return
                
            # 设置工具提示
            self.tray_icon.setToolTip("UE Toolkit - 虚幻引擎工具箱")
            
            # 创建托盘菜单
            self._create_tray_menu()
            
            # 连接信号
            self.tray_icon.activated.connect(self._on_tray_activated)
            
            # 显示托盘图标
            self.tray_icon.show()
            
            self._is_initialized = True
            logger.info("系统托盘初始化成功")
            
        except Exception as e:
            logger.error(f"初始化系统托盘失败: {e}", exc_info=True)
            
    def _create_tray_menu(self):
        """创建托盘菜单"""
        self.tray_menu = QMenu()
        
        # 显示主窗口
        show_action = QAction("显示主窗口", self.tray_menu)
        show_action.triggered.connect(self._on_show_window)
        self.tray_menu.addAction(show_action)
        
        # 分隔线
        self.tray_menu.addSeparator()
        
        # 退出应用
        quit_action = QAction("退出程序", self.tray_menu)
        quit_action.triggered.connect(self._on_quit)
        self.tray_menu.addAction(quit_action)
        
        # 设置菜单
        self.tray_icon.setContextMenu(self.tray_menu)
        
    def _on_tray_activated(self, reason):
        """托盘图标激活事件
        
        Args:
            reason: 激活原因
        """
        # 单击或双击托盘图标时显示窗口
        if reason == QSystemTrayIcon.ActivationReason.Trigger or \
           reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            logger.info("托盘图标被点击，显示主窗口")
            self.show_window_requested.emit()
            
    def _on_show_window(self):
        """显示窗口菜单项"""
        logger.info("从托盘菜单显示主窗口")
        self.show_window_requested.emit()
        
    def _on_quit(self):
        """退出应用菜单项"""
        logger.info("从托盘菜单退出应用")
        self.quit_requested.emit()
        
    def show_message(self, title: str, message: str, icon=QSystemTrayIcon.MessageIcon.Information, duration: int = 3000):
        """显示托盘通知消息
        
        Args:
            title: 标题
            message: 消息内容
            icon: 图标类型
            duration: 显示时长(毫秒)
        """
        if self.tray_icon and self._is_initialized:
            self.tray_icon.showMessage(title, message, icon, duration)
            
    def hide(self):
        """隐藏托盘图标"""
        if self.tray_icon and self._is_initialized:
            self.tray_icon.hide()
            logger.info("系统托盘图标已隐藏")
            
    def show(self):
        """显示托盘图标"""
        if self.tray_icon and self._is_initialized:
            self.tray_icon.show()
            logger.info("系统托盘图标已显示")
            
    def cleanup(self):
        """清理资源"""
        if self.tray_icon:
            self.tray_icon.hide()
            self.tray_icon.deleteLater()
            self.tray_icon = None
            self._is_initialized = False
            logger.info("系统托盘资源已清理")

