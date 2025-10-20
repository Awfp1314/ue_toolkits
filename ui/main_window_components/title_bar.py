# -*- coding: utf-8 -*-

"""
自定义标题栏组件
"""

from typing import Optional
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QMouseEvent
from core.utils.theme_manager import get_theme_manager


class CustomTitleBar(QWidget):
    """自定义标题栏"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_window = parent
        self.drag_position = QPoint()
        self.init_ui()
        
    def init_ui(self):
        """初始化标题栏界面"""
        # 设置标题栏高度
        self.setFixedHeight(30)
        
        # 设置对象名称以便QSS选择器识别
        self.setObjectName("customTitleBar")
        
        # 使用 ThemeManager 应用样式
        theme_manager = get_theme_manager()
        theme_manager.apply_to_widget(self, component="title_bar")
        
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        
        title_layout = QHBoxLayout()
        title_layout.setSpacing(5)
        
        # 标题标签
        self.title_label = QLabel("UE Toolkit - 虚幻引擎工具箱")
        self.title_label.setObjectName("titleLabel")
        # 样式由title_bar.qss提供，无需内联设置
        title_layout.addWidget(self.title_label)
        
        layout.addLayout(title_layout)
        layout.addStretch()  # 添加弹性空间
        
        # 窗口控制按钮
        self.minimize_button = QPushButton("—")
        self.minimize_button.setObjectName("minimizeButton")
        self.minimize_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # 禁用焦点
        self.minimize_button.clicked.connect(self.minimize_window)
        
        self.maximize_button = QPushButton("□")
        self.maximize_button.setObjectName("maximizeButton")
        self.maximize_button.setEnabled(False)  # 禁用全屏按钮
        self.maximize_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # 禁用焦点
        self.maximize_button.clicked.connect(self.toggle_maximize)
        
        self.close_button = QPushButton("×")
        self.close_button.setObjectName("closeButton")
        self.close_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # 禁用焦点
        self.close_button.clicked.connect(self.close_window)
        
        # 添加按钮到布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(0)
        button_layout.addWidget(self.minimize_button)
        button_layout.addWidget(self.maximize_button)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
    
    def minimize_window(self):
        """最小化窗口"""
        self.parent_window.showMinimized()
    
    def close_window(self):
        """关闭窗口"""
        self.parent_window.close()
    
    def toggle_maximize(self):
        """切换最大化状态（已禁用全屏功能）"""
        # 禁用全屏功能，按钮点击无效果
        pass
    
    def mousePressEvent(self, a0: Optional[QMouseEvent]):
        """鼠标按下事件，用于窗口拖动"""
        if a0 and a0.button() == Qt.MouseButton.LeftButton:
            self.drag_position = a0.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
            a0.accept()
    
    def mouseMoveEvent(self, a0: Optional[QMouseEvent]):
        """鼠标移动事件，用于窗口拖动"""
        if a0 and a0.buttons() == Qt.MouseButton.LeftButton and not self.drag_position.isNull():
            self.parent_window.move(a0.globalPosition().toPoint() - self.drag_position)
            a0.accept()
    
    def mouseDoubleClickEvent(self, a0: Optional[QMouseEvent]):
        """鼠标双击事件（已禁用全屏功能）"""
        # 禁用双击全屏功能，双击无效果
        if a0:
            a0.accept()
    
    def refresh_theme(self):
        """刷新主题样式"""
        theme_manager = get_theme_manager()
        theme_manager.apply_to_widget(self, component="title_bar")

