# -*- coding: utf-8 -*-

"""
关闭确认对话框
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from core.utils.theme_manager import get_theme_manager
from core.logger import get_logger
from modules.asset_manager.ui.custom_checkbox import CustomCheckBox

logger = get_logger(__name__)


class CloseConfirmationDialog(QDialog):
    """关闭确认对话框"""
    
    RESULT_CLOSE = 1  # 直接关闭
    RESULT_MINIMIZE = 2  # 最小化到托盘
    RESULT_CANCEL = 0  # 取消
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.result_action = self.RESULT_CANCEL
        self.remember_choice = False  # 是否记住用户选择
        self.theme_manager = get_theme_manager()
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        # 无边框，透明背景
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(480, 230)  # 包含复选框的高度
        
        # 主容器
        main_container = QWidget()
        main_container.setObjectName("mainContainer")
        
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # 标题
        title_label = QLabel("关闭程序")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title_label.font()
        font.setPointSize(14)
        font.setBold(True)
        title_label.setFont(font)
        main_layout.addWidget(title_label)
        
        # 提示文本
        message_label = QLabel("选择关闭方式：")
        message_label.setObjectName("messageLabel")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setWordWrap(True)
        main_layout.addWidget(message_label)
        
        # 记住选择的复选框
        self.remember_checkbox = CustomCheckBox("记住我的选择，下次不再提示")
        checkbox_layout = QHBoxLayout()
        checkbox_layout.addStretch()
        checkbox_layout.addWidget(self.remember_checkbox)
        checkbox_layout.addStretch()
        main_layout.addLayout(checkbox_layout)
        
        main_layout.addSpacing(10)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        # 直接关闭按钮
        close_btn = QPushButton("直接关闭")
        close_btn.setObjectName("confirmButton")
        close_btn.setMinimumHeight(40)
        close_btn.setMinimumWidth(110)
        close_btn.clicked.connect(self._on_close_clicked)
        button_layout.addWidget(close_btn)
        
        # 最小化到托盘按钮
        minimize_btn = QPushButton("最小化到托盘")
        minimize_btn.setObjectName("minimizeButton")
        minimize_btn.setMinimumHeight(40)
        minimize_btn.setMinimumWidth(130)
        minimize_btn.clicked.connect(self._on_minimize_clicked)
        button_layout.addWidget(minimize_btn)
        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setMinimumWidth(90)
        cancel_btn.clicked.connect(self._on_cancel_clicked)
        button_layout.addWidget(cancel_btn)
        
        main_layout.addLayout(button_layout)
        
        # 设置主布局
        container_layout = QVBoxLayout(self)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(main_container)
        
        # 应用样式
        self._apply_style()
        
    def _apply_style(self):
        """应用主题样式"""
        tm = self.theme_manager
        
        stylesheet = f"""
            QDialog {{
                background: transparent;
            }}
            
            #mainContainer {{
                background-color: {tm.get_variable('bg_secondary')};
                border: 1px solid {tm.get_variable('border')};
                border-radius: 8px;
            }}
            
            #titleLabel {{
                color: {tm.get_variable('text_primary')};
                background: transparent;
            }}
            
            #messageLabel {{
                color: {tm.get_variable('text_secondary')};
                background: transparent;
                font-size: 13px;
            }}
            
            QPushButton {{
                background-color: {tm.get_variable('button_bg')};
                color: {tm.get_variable('button_text')};
                border: 1px solid {tm.get_variable('border')};
                border-radius: 4px;
                padding: 8px 16px;
                margin: 0px 5px;
                font-size: 13px;
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: {tm.get_variable('button_hover')};
                border-color: {tm.get_variable('accent')};
            }}
            
            QPushButton:pressed {{
                background-color: {tm.get_variable('button_pressed')};
            }}
            
            #confirmButton {{
                background-color: {tm.get_variable('danger')};
                border-color: {tm.get_variable('danger')};
            }}
            
            #confirmButton:hover {{
                background-color: {tm.get_variable('danger_hover')};
                border-color: {tm.get_variable('danger_hover')};
            }}
            
            #minimizeButton {{
                background-color: {tm.get_variable('accent')};
                border-color: {tm.get_variable('accent')};
            }}
            
            #minimizeButton:hover {{
                background-color: {tm.get_variable('accent_hover')};
                border-color: {tm.get_variable('accent_hover')};
            }}
        """
        
        self.setStyleSheet(stylesheet)
        
    def _on_close_clicked(self):
        """直接关闭"""
        self.result_action = self.RESULT_CLOSE
        self.remember_choice = self.remember_checkbox.isChecked()
        self.accept()
        
    def _on_minimize_clicked(self):
        """最小化到托盘"""
        self.result_action = self.RESULT_MINIMIZE
        self.remember_choice = self.remember_checkbox.isChecked()
        self.accept()
        
    def _on_cancel_clicked(self):
        """取消"""
        self.result_action = self.RESULT_CANCEL
        self.remember_choice = False  # 取消时不记住选择
        self.reject()
        
    def center_on_parent(self):
        """居中显示在父窗口"""
        if self.parent():
            parent_geometry = self.parent().frameGeometry()
            x = parent_geometry.x() + (parent_geometry.width() - self.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            self.move(x, y)
            logger.debug(f"关闭确认对话框已居中到: ({x}, {y})")
    
    def showEvent(self, event):
        """显示事件"""
        super().showEvent(event)
        self.center_on_parent()
        
    @staticmethod
    def ask_close_action(parent=None):
        """静态方法：显示对话框并返回用户选择
        
        Returns:
            tuple: (result_action, remember_choice)
                result_action: RESULT_CLOSE, RESULT_MINIMIZE, 或 RESULT_CANCEL
                remember_choice: bool - 是否记住用户选择
        """
        dialog = CloseConfirmationDialog(parent)
        dialog.exec()
        return dialog.result_action, dialog.remember_choice

