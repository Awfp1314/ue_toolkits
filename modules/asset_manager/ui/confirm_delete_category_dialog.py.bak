# -*- coding: utf-8 -*-

"""
确认删除分类对话框
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from core.utils.theme_manager import get_theme_manager


class ConfirmDeleteCategoryDialog(QDialog):
    """确认删除分类对话框"""
    
    def __init__(self, category_name: str, asset_count: int, parent=None):
        """初始化对话框
        
        Args:
            category_name: 分类名称
            asset_count: 分类下的资产数量
            parent: 父组件
        """
        super().__init__(parent)
        self.theme_manager = get_theme_manager()
        self.category_name = category_name
        self.asset_count = asset_count
        
        self.init_ui()
    
    def _build_stylesheet(self):
        """构建动态样式表"""
        tm = self.theme_manager
        return f"""
            QDialog {{
                background-color: {tm.get_variable('bg_secondary')};
                border: 1px solid {tm.get_variable('border')};
                border-radius: 8px;
            }}
            QLabel {{
                color: {tm.get_variable('text_primary')};
                font-size: 13px;
            }}
            QLabel#titleLabel {{
                font-size: 15px;
                font-weight: bold;
                padding: 5px 0;
            }}
            QLabel#messageLabel {{
                color: {tm.get_variable('text_secondary')};
                line-height: 1.5;
            }}
            QLabel#warningLabel {{
                color: {tm.get_variable('warning')};
                padding: 10px;
                background-color: {tm.get_variable('bg_tertiary')};
                border-radius: 4px;
                border-left: 3px solid {tm.get_variable('warning')};
            }}
            QPushButton {{
                background-color: {tm.get_variable('bg_tertiary')};
                color: {tm.get_variable('text_primary')};
                border: 1px solid {tm.get_variable('border')};
                padding: 10px 24px;
                border-radius: 4px;
                font-size: 13px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {tm.get_variable('bg_hover')};
            }}
            QPushButton:pressed {{
                background-color: {tm.get_variable('bg_pressed')};
            }}
            QPushButton#deleteButton {{
                background-color: {tm.get_variable('error')};
                color: white;
                border: 1px solid {tm.get_variable('error')};
            }}
            QPushButton#deleteButton:hover {{
                background-color: #E53935;
            }}
            QPushButton#deleteButton:pressed {{
                background-color: #C62828;
            }}
        """
    
    def refresh_theme(self):
        """刷新主题样式"""
        self.setStyleSheet(self._build_stylesheet())
    
    def init_ui(self):
        """初始化UI"""
        self.setModal(True)
        self.setFixedSize(400, 220)
        
        # 去掉标题栏
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        
        self.drag_position = None
        
        self.setStyleSheet(self._build_stylesheet())
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(15)
        
        title_label = QLabel("确认删除")
        title_label.setObjectName("titleLabel")
        main_layout.addWidget(title_label)
        
        # 警告消息
        warning_label = QLabel(f"⚠ 分类 \"{self.category_name}\" 下有 {self.asset_count} 个资产")
        warning_label.setObjectName("warningLabel")
        warning_label.setWordWrap(True)
        main_layout.addWidget(warning_label)
        
        # 说明消息
        message_label = QLabel("删除后，这些资产将移至\"默认分类\"。\n\n确定要删除吗？")
        message_label.setObjectName("messageLabel")
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        main_layout.addWidget(message_label)
        
        main_layout.addStretch()
        
        button_layout = QHBoxLayout()
        
        delete_btn = QPushButton("删除")
        delete_btn.setObjectName("deleteButton")
        delete_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        delete_btn.clicked.connect(self.accept)
        button_layout.addWidget(delete_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        main_layout.addLayout(button_layout)
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

