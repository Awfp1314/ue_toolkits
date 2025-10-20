# -*- coding: utf-8 -*-

"""
布局构建器 - 负责构建UI布局
"""

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QScrollArea, QWidget, QFrame
)
from PyQt6.QtCore import Qt

from core.logger import get_logger
from core.utils.style_loader import get_style_loader
from core.utils.theme_manager import get_theme_manager

logger = get_logger(__name__)


class LayoutBuilder:
    """布局构建器"""
    
    def __init__(self, ui):
        """初始化布局构建器
        
        Args:
            ui: ConfigToolUI实例
        """
        self.ui = ui
    
    def create_title_area(self, parent_layout):
        """创建标题区域（包含添加配置按钮）"""
        logger.info("创建标题区域")
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加弹性空间将按钮推到右侧
        title_layout.addStretch()
        
        # 右侧创建"＋添加配置"按钮
        self.ui.add_config_button = QPushButton("＋添加配置")
        self.ui.add_config_button.setObjectName("addConfigButton")
        # 样式由config_tool.qss提供，无需内联设置
        self.ui.add_config_button.setFixedHeight(35)
        self.ui.add_config_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # 禁用焦点
        # 注意：按钮点击事件连接在ConfigToolModule的setup_connections方法中完成
        # 不要在这里重复连接，避免事件被触发两次
        title_layout.addWidget(self.ui.add_config_button)
        
        parent_layout.addLayout(title_layout)
        logger.info("标题区域创建完成")
    
    def create_separator(self, parent_layout):
        """创建分隔线"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        theme_manager = get_theme_manager()
        separator.setStyleSheet(f"background-color: {theme_manager.get_variable('border')};")
        separator.setFixedHeight(1)
        parent_layout.addWidget(separator)
    
    def create_content_area(self, parent_layout):
        """创建内容显示区域"""
        logger.info("创建内容显示区域")
        self.ui.scroll_area = QScrollArea()
        self.ui.scroll_area.setObjectName("configScrollArea")
        # 样式由config_tool.qss提供，无需内联设置
        self.ui.scroll_area.setWidgetResizable(True)
        
        self.ui.content_container = QWidget()
        self.ui.content_container.setObjectName("configContentContainer")
        # 样式由config_tool.qss提供，无需内联设置
        self.ui.scroll_area.setWidget(self.ui.content_container)
        
        self.ui.config_grid_layout = QGridLayout()
        self.ui.config_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.ui.config_grid_layout.setSpacing(15)
        
        self.ui.empty_layout = QVBoxLayout()
        self.ui.empty_layout.setContentsMargins(0, 0, 0, 0)
        self.ui.empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.ui.empty_label = QLabel("暂无配置模板\n点击右上角按钮添加配置")
        self.ui.empty_label.setObjectName("emptyLabel")
        # 样式由config_tool.qss提供，无需内联设置
        self.ui.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ui.empty_label.hide()  # 默认隐藏
        
        # 将空状态标签添加到空状态布局
        self.ui.empty_layout.addWidget(self.ui.empty_label)
        
        self.ui.main_content_layout = QVBoxLayout(self.ui.content_container)
        self.ui.main_content_layout.setContentsMargins(0, 0, 0, 0)
        self.ui.main_content_layout.addLayout(self.ui.config_grid_layout)
        self.ui.main_content_layout.addLayout(self.ui.empty_layout)
        
        parent_layout.addWidget(self.ui.scroll_area)
        logger.info("内容显示区域创建完成")
    
    def update_config_buttons(self):
        """更新配置按钮显示"""
        logger.info("更新配置按钮显示")
            
        # 清除现有的配置按钮
        for i in reversed(range(self.ui.config_grid_layout.count())):
            item = self.ui.config_grid_layout.itemAt(i)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
        
        if hasattr(self.ui, 'empty_label'):
            self.ui.empty_label.hide()
        
        # 固定每行4个按钮
        buttons_per_row = 4
        
        # 如果没有配置模板，显示空状态
        if not self.ui.config_templates:
            self.show_empty_state()
            logger.info("没有配置模板，显示空状态")
            return
        
        # 添加配置按钮，始终从左到右排列
        for i, template in enumerate(self.ui.config_templates):
            row = i // buttons_per_row
            col = i % buttons_per_row
            
            config_button = self.create_config_button(template)
            self.ui.config_grid_layout.addWidget(config_button, row, col)
        
        # 设置布局对齐方式为左对齐
        self.ui.config_grid_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        logger.info(f"更新了 {len(self.ui.config_templates)} 个配置按钮")
    
    def create_config_button(self, template):
        """创建配置按钮"""
        logger.info(f"创建配置按钮: {template.name}")
        # 使用自定义按钮类支持双击事件
        from ..components import ConfigTemplateButton
        button = ConfigTemplateButton(template, self.ui)
        
        # 连接按钮点击事件
        button.clicked.connect(lambda: self.ui.on_config_button_clicked(template))
        
        # 连接右键菜单事件
        button.customContextMenuRequested.connect(lambda pos: self.ui.handler.show_config_context_menu(pos, button, template))
        
        return button
    
    def show_empty_state(self):
        """显示空状态"""
        logger.info("显示空状态")
            
        # 清除现有的配置按钮
        for i in reversed(range(self.ui.config_grid_layout.count())):
            item = self.ui.config_grid_layout.itemAt(i)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
        
        self.ui.empty_label.show()
        
        logger.info("空状态显示完成")

