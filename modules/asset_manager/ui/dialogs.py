# -*- coding: utf-8 -*-

"""
资产管理模块的统一弹窗组件
提供美观、一致的对话框样式
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QMessageBox, QWidget)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QFont, QIcon, QMouseEvent
from pathlib import Path
from core.utils.theme_manager import ThemeManager
from core.utils.custom_widgets import NoContextMenuTextEdit


class StyledMessageBox(QMessageBox):
    """美化的消息框"""
    
    @staticmethod
    def _get_stylesheet() -> str:
        """动态生成样式表（支持主题切换）"""
        tm = ThemeManager()
        return f"""
            QMessageBox {{
                background-color: {tm.get_variable('bg_secondary')};
                border: 1px solid {tm.get_variable('border')};
                border-radius: 8px;
            }}
            QMessageBox QLabel {{
                color: {tm.get_variable('text_primary')};
                font-size: 14px;
                min-width: 350px;
                padding: 10px;
            }}
            QMessageBox QPushButton {{
                background-color: {tm.get_variable('accent')};
                color: white;
                border: none;
                padding: 8px 24px;
                border-radius: 4px;
                font-size: 13px;
                min-width: 80px;
                font-weight: bold;
            }}
            QMessageBox QPushButton:hover {{
                background-color: {tm.get_variable('accent_hover')};
            }}
            QMessageBox QPushButton:pressed {{
                background-color: {tm.get_variable('accent_pressed')};
            }}
            /* 取消/否定按钮样式 */
            QPushButton[text="取消"], QPushButton[text="No"], QPushButton[text="否"] {{
                background-color: {tm.get_variable('bg_tertiary')};
            }}
            QPushButton[text="取消"]:hover, QPushButton[text="No"]:hover, QPushButton[text="否"]:hover {{
                background-color: {tm.get_variable('bg_hover')};
            }}
            QPushButton[text="取消"]:pressed, QPushButton[text="No"]:pressed, QPushButton[text="否"]:pressed {{
                background-color: {tm.get_variable('bg_pressed')};
            }}
        """
    
    @staticmethod
    def information(parent, title, text):
        """信息提示框"""
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.setStyleSheet(StyledMessageBox._get_stylesheet())
        # 去掉标题栏
        msg.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        return msg.exec()
    
    @staticmethod
    def warning(parent, title, text):
        """警告提示框"""
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.setStyleSheet(StyledMessageBox._get_stylesheet())
        # 去掉标题栏
        msg.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        return msg.exec()
    
    @staticmethod
    def error(parent, title, text):
        """错误提示框"""
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.setStyleSheet(StyledMessageBox._get_stylesheet())
        # 去掉标题栏
        msg.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        return msg.exec()
    
    @staticmethod
    def question(parent, title, text):
        """询问对话框"""
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        msg.setStyleSheet(StyledMessageBox._get_stylesheet())
        # 去掉标题栏
        msg.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        
        # 设置按钮文本为中文
        yes_button = msg.button(QMessageBox.StandardButton.Yes)
        no_button = msg.button(QMessageBox.StandardButton.No)
        if yes_button:
            yes_button.setText("是")
        if no_button:
            no_button.setText("否")
        
        return msg.exec()


class DescriptionDialog(QDialog):
    """资产描述输入对话框"""
    
    def __init__(self, asset_name: str, parent=None):
        super().__init__(parent)
        self.asset_name = asset_name
        self.description = ""
        self.drag_position = QPoint()
        self.theme_manager = ThemeManager()
        self._init_ui()
    
    def _build_stylesheet(self) -> str:
        """构建动态样式表（支持主题切换）"""
        tm = self.theme_manager
        return f"""
            QDialog {{
                background-color: {tm.get_variable('bg_secondary')};
                border: 1px solid {tm.get_variable('border')};
                border-radius: 8px;
            }}
            QLabel {{
                color: {tm.get_variable('text_primary')};
                font-size: 14px;
                padding: 5px;
            }}
            QTextEdit {{
                background-color: {tm.get_variable('bg_primary')};
                color: {tm.get_variable('text_primary')};
                border: 2px solid {tm.get_variable('border')};
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
                selection-background-color: {tm.get_variable('accent')};
            }}
            QTextEdit:focus {{
                border: 2px solid {tm.get_variable('accent')};
            }}
            QPushButton {{
                background-color: {tm.get_variable('accent')};
                color: white;
                border: none;
                padding: 10px 28px;
                border-radius: 5px;
                font-size: 13px;
                min-width: 80px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {tm.get_variable('accent_hover')};
            }}
            QPushButton:pressed {{
                background-color: {tm.get_variable('accent_pressed')};
            }}
            QPushButton#cancelButton {{
                background-color: {tm.get_variable('bg_tertiary')};
            }}
            QPushButton#cancelButton:hover {{
                background-color: {tm.get_variable('bg_hover')};
            }}
            QPushButton#cancelButton:pressed {{
                background-color: {tm.get_variable('bg_pressed')};
            }}
            QCheckBox {{
                color: {tm.get_variable('text_primary')};
                font-size: 13px;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {tm.get_variable('bg_tertiary')};
                border-radius: 4px;
                background-color: {tm.get_variable('bg_primary')};
            }}
            QCheckBox::indicator:hover {{
                border-color: {tm.get_variable('accent')};
            }}
            QCheckBox::indicator:checked {{
                background-color: {tm.get_variable('accent')};
                border-color: {tm.get_variable('accent')};
            }}
        """
    
    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("添加资产描述")
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        
        # 去掉标题栏
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        
        self.setStyleSheet(self._build_stylesheet())
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title_label = QLabel(f"为资产 \"{self.asset_name}\" 添加描述信息")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 提示文本
        hint_label = QLabel("请输入资产的描述信息（可选）：")
        hint_label.setStyleSheet(f"color: {self.theme_manager.get_variable('text_secondary')}; font-size: 12px;")
        layout.addWidget(hint_label)
        
        self.text_edit = NoContextMenuTextEdit()
        self.text_edit.setPlaceholderText("例如：高质量角色模型，包含完整的材质和动画...")
        layout.addWidget(self.text_edit)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("确认")
        ok_btn.clicked.connect(self._on_ok_clicked)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def _on_ok_clicked(self):
        """确认按钮点击事件"""
        self.description = self.text_edit.toPlainText().strip()
        self.accept()
    
    def get_description(self) -> str:
        """获取输入的描述"""
        return self.description
    
    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下事件 - 用于拖拽"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动事件 - 实现拖拽"""
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()


class ConfirmDialog(QDialog):
    """确认对话框（用于重要操作）"""
    
    def __init__(self, title: str, message: str, details: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.drag_position = QPoint()
        self.theme_manager = ThemeManager()
        self._init_ui(message, details)
    
    def _build_stylesheet(self) -> str:
        """构建动态样式表（支持主题切换）"""
        tm = self.theme_manager
        return f"""
            QDialog {{
                background-color: {tm.get_variable('bg_secondary')};
                border: 1px solid {tm.get_variable('border')};
                border-radius: 8px;
            }}
            QLabel {{
                color: {tm.get_variable('text_primary')};
                font-size: 14px;
                padding: 5px;
            }}
            QLabel#messageLabel {{
                font-size: 15px;
                font-weight: bold;
                padding: 10px 5px;
            }}
            QLabel#detailsLabel {{
                color: {tm.get_variable('text_secondary')};
                font-size: 12px;
                padding: 5px;
                background-color: {tm.get_variable('bg_primary')};
                border-radius: 4px;
                border: 1px solid {tm.get_variable('border')};
            }}
            QPushButton {{
                background-color: {tm.get_variable('accent')};
                color: white;
                border: none;
                padding: 10px 28px;
                border-radius: 5px;
                font-size: 13px;
                min-width: 80px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {tm.get_variable('accent_hover')};
            }}
            QPushButton:pressed {{
                background-color: {tm.get_variable('accent_pressed')};
            }}
            QPushButton#cancelButton {{
                background-color: {tm.get_variable('bg_tertiary')};
            }}
            QPushButton#cancelButton:hover {{
                background-color: {tm.get_variable('bg_hover')};
            }}
            QPushButton#cancelButton:pressed {{
                background-color: {tm.get_variable('bg_pressed')};
            }}
        """
    
    def _init_ui(self, message: str, details: str):
        """初始化UI"""
        self.setMinimumWidth(450)
        
        # 去掉标题栏
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        
        self.setStyleSheet(self._build_stylesheet())
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        
        message_label = QLabel(message)
        message_label.setObjectName("messageLabel")
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        
        # 详细信息
        if details:
            details_label = QLabel(details)
            details_label.setObjectName("detailsLabel")
            details_label.setWordWrap(True)
            details_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            layout.addWidget(details_label)
        
        layout.addSpacing(10)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("确认")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下事件 - 用于拖拽"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动事件 - 实现拖拽"""
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
