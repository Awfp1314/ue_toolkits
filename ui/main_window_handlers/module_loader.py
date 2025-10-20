# -*- coding: utf-8 -*-

"""
模块加载器 - 处理模块内容的加载和显示
"""

from typing import Dict
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from core.logger import get_logger
from core.utils.theme_manager import get_theme_manager

logger = get_logger(__name__)


class ModuleLoader:
    """模块加载处理器"""
    
    def __init__(self, main_window):
        """初始化模块加载器
        
        Args:
            main_window: 主窗口实例
        """
        self.main_window = main_window
    
    def load_module_content(self, tool_id: str):
        """加载模块内容 - 使用懒加载机制
        
        Args:
            tool_id: 工具ID（现在直接使用模块名称）
        """
        # 注意：tool_id 现在就是模块名称（如 "asset_manager"）
        module_name = tool_id
        
        logger.debug(f"尝试加载模块内容: {module_name}")
        
        if module_name not in self.main_window.module_ui_map:
            # 首次访问，使用懒加载创建UI
            logger.info(f"模块 {module_name} UI未加载，执行懒加载...")
            if not self.main_window.load_module_ui_lazy(module_name):
                logger.error(f"懒加载模块 {module_name} 失败")
                self.show_default_content_for_module(module_name)
                return
        
        widget = self.main_window.module_ui_map.get(module_name)
        if not widget:
            logger.error(f"模块 {module_name} UI加载失败")
            self.show_default_content_for_module(module_name)
            return
        
        logger.info(f"切换到模块 {module_name} 的UI")
        
        # 强制设置UI组件属性确保可见
        widget.setVisible(True)
        widget.show()
        widget.raise_()
        
        # 切换到对应的页面
        if self.main_window.content_stack:
            self.main_window.content_stack.setCurrentWidget(widget)
            logger.debug(f"成功切换到模块 {module_name}")
    
    def show_default_content_for_module(self, module_name: str):
        """为模块显示默认内容
        
        Args:
            module_name: 模块名称
        """
        default_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # 尝试从导航按钮获取显示名称
        display_name = module_name
        for btn_info in self.main_window.nav_buttons:
            if btn_info.get("id") == module_name:
                display_name = btn_info.get("display_name", module_name)
                break
        
        default_label = QLabel(f"{display_name} 功能正在开发中...")
        default_label.setObjectName("defaultContentLabel")
        default_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(default_label)
        
        # 使用 ThemeManager 应用主题
        theme_manager = get_theme_manager()
        theme_manager.apply_to_widget(default_widget)
        
        default_widget.setLayout(layout)
        
        # 添加到堆栈并切换到该页面
        if self.main_window.content_stack:
            self.main_window.content_stack.addWidget(default_widget)
            self.main_window.content_stack.setCurrentWidget(default_widget)

