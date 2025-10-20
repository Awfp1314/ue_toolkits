# -*- coding: utf-8 -*-

"""
导航处理器 - 处理侧边栏导航和工具切换
"""

from typing import Dict, Any, List
from core.logger import get_logger

logger = get_logger(__name__)


class NavigationHandler:
    """导航事件处理器"""
    
    def __init__(self, main_window):
        """初始化导航处理器
        
        Args:
            main_window: 主窗口实例
        """
        self.main_window = main_window
        self.nav_buttons: List[Dict[str, Any]] = []
    
    def on_tool_button_clicked(self, tool_id: str):
        """工具按钮点击事件
        
        Args:
            tool_id: 工具ID
        """
        # 找到当前点击的按钮
        clicked_button = None
        for btn_info in self.nav_buttons:
            if btn_info["id"] == tool_id:
                clicked_button = btn_info["button"]
                break
        
        # 取消其他按钮的选中状态
        for btn_info in self.nav_buttons:
            if btn_info["id"] != tool_id:
                btn_info["button"].setChecked(False)
        
        # 取消设置按钮的选中状态
        if hasattr(self.main_window, 'settings_button'):
            self.main_window.settings_button.setChecked(False)
        
        # 确保当前按钮被选中
        if clicked_button:
            clicked_button.setChecked(True)
        
        # 更新工具标题（从按钮信息中获取显示名称）
        tool_name = tool_id  # 默认使用ID
        for btn_info in self.nav_buttons:
            if btn_info["id"] == tool_id:
                tool_name = btn_info.get("display_name", tool_id)
                break
        
        if hasattr(self.main_window, 'tool_title_label'):
            self.main_window.tool_title_label.setText(tool_name)
        
        from .module_loader import ModuleLoader
        loader = ModuleLoader(self.main_window)
        loader.load_module_content(tool_id)

