# -*- coding: utf-8 -*-

"""
配置工具UI核心类
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from core.logger import get_logger
from core.utils.style_loader import get_style_loader
from core.utils.theme_manager import get_theme_manager

from .handlers import ConfigHandler
from .layouts import LayoutBuilder

logger = get_logger(__name__)


class ConfigToolUI(QWidget):
    """配置工具UI类"""
    
    def __init__(self):
        super().__init__()
        self.config_templates = []  # 存储配置模板
        self.add_config_button = None  # 添加配置按钮引用
        self.logic = None  # 逻辑层引用
        self.theme_manager = get_theme_manager()  # 获取主题管理器
        
        self.handler = ConfigHandler(self)
        self.layout_builder = LayoutBuilder(self)
        
        logger.info("ConfigToolUI 初始化开始")
        self.init_ui()
        logger.info("ConfigToolUI 初始化完成")
    
    def init_ui(self):
        """初始化UI界面"""
        logger.info("开始初始化UI界面")
        
        self._apply_theme_style()
        
        # 设置主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        self.setLayout(main_layout)
        
        self.layout_builder.create_title_area(main_layout)
        
        # 添加分隔线
        self.layout_builder.create_separator(main_layout)
        
        self.layout_builder.create_content_area(main_layout)
        
        # 添加示例配置模板
        self.add_sample_templates()
        
        self.update_config_buttons()
        
        logger.info("UI界面初始化完成")
    
    def add_sample_templates(self):
        """添加示例配置模板"""
        logger.info("添加示例配置模板")
        logger.info(f"添加了 0 个示例模板")
    
    def update_config_buttons(self):
        """更新配置按钮显示（委托给LayoutBuilder）"""
        self.layout_builder.update_config_buttons()
    
    def on_config_button_clicked(self, template):
        """配置按钮点击事件"""
        logger.info(f"配置按钮被点击: {template.name}")
        # 这里可以实现进入配置详情页面的逻辑
        pass
    
    def on_add_config_clicked(self):
        """添加配置按钮点击事件（委托给ConfigHandler）"""
        self.handler.on_add_config_clicked()
    
    def detect_running_ue_projects(self):
        """检测运行的UE工程（委托给ConfigHandler）"""
        return self.handler.detect_running_ue_projects()
    
    def select_ue_project(self, ue_projects):
        """选择UE工程（委托给ConfigHandler）"""
        return self.handler.select_ue_project(ue_projects)
    
    def show_no_ue_project_message(self):
        """显示没有找到UE工程的消息"""
        QMessageBox.information(self, "提示", "未检测到正在运行的UE工程，请先启动UE编辑器。")
    
    def show_success_message(self, message: str = "配置添加成功！"):
        """显示成功消息"""
        QMessageBox.information(self, "成功", message)
    
    def _apply_theme_style(self):
        """应用动态主题样式"""
        tm = self.theme_manager
        
        style = f"""
            QLabel#emptyLabel {{
                color: {tm.get_variable('text_disabled')};
                font-size: 16px;
                background-color: transparent;
            }}
            
            QPushButton#addConfigButton {{
                background-color: transparent;
                color: {tm.get_variable('text_primary')};
                border: 1px solid {tm.get_variable('text_secondary')};
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }}
            
            QPushButton#addConfigButton:hover {{
                background-color: {tm.get_variable('bg_hover')};
                border: 1px solid {tm.get_variable('border_hover')};
            }}
            
            QPushButton#addConfigButton:pressed {{
                background-color: {tm.get_variable('bg_pressed')};
                border: 1px solid {tm.get_variable('border')};
            }}
            
            QPushButton[class="config-template-button"] {{
                background-color: {tm.get_variable('bg_secondary')};
                border: 1px solid {tm.get_variable('border')};
                border-radius: 4px;
                padding: 10px 15px;
                text-align: center;
                color: {tm.get_variable('text_primary')};
                font-size: 14px;
                font-weight: bold;
            }}
            
            QPushButton[class="config-template-button"]:hover {{
                background-color: {tm.get_variable('bg_tertiary')};
                border: 1px solid {tm.get_variable('border_hover')};
            }}
            
            QPushButton[class="config-template-button"]:pressed {{
                background-color: {tm.get_variable('bg_pressed')};
            }}
            
            QScrollArea#configScrollArea {{
                border: none;
                background-color: transparent;
            }}
            
            QScrollArea#configScrollArea QScrollBar:vertical {{
                background: {tm.get_variable('bg_secondary')};
                width: 15px;
                border-radius: 4px;
            }}
            
            QScrollArea#configScrollArea QScrollBar::handle:vertical {{
                background: {tm.get_variable('bg_tertiary')};
                border-radius: 4px;
            }}
            
            QScrollArea#configScrollArea QScrollBar::handle:vertical:hover {{
                background: {tm.get_variable('bg_hover')};
            }}
            
            QWidget#configContentContainer {{
                background-color: transparent;
            }}
        """
        
        self.setStyleSheet(style)
        logger.debug("配置工具样式已更新")
    
    def refresh_theme(self):
        """刷新主题样式 - 在主题切换时调用"""
        self._apply_theme_style()
        logger.info("配置工具主题已刷新")
    
    def show_error_message(self, message: str):
        """显示错误消息"""
        QMessageBox.critical(self, "错误", message)
    
    def refresh_config_list(self):
        """刷新配置列表"""
        if self.logic:
            self.config_templates = self.logic.get_templates()
            self.update_config_buttons()

