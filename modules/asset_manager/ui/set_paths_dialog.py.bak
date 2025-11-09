# -*- coding: utf-8 -*-

"""
设置路径对话框
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFileDialog, QWidget
)
from core.utils.custom_widgets import NoContextMenuLineEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QMouseEvent
from pathlib import Path
from typing import Optional

from core.logger import get_logger
from core.utils.theme_manager import get_theme_manager

logger = get_logger(__name__)


class SetPathsDialog(QDialog):
    """设置路径对话框（无标题栏）"""
    
    def __init__(self, asset_library_path: str = "", preview_project_path: str = "", parent=None):
        """
        Args:
            asset_library_path: 当前资产库路径
            preview_project_path: 当前预览工程路径
            parent: 父窗口
        """
        super().__init__(parent)
        self.theme_manager = get_theme_manager()
        self.asset_library_path = asset_library_path
        self.preview_project_path = preview_project_path
        
        # 用于实现窗口拖动
        self._drag_pos = None
        
        self.init_ui()
    
    def _build_stylesheet(self):
        """构建动态样式表"""
        tm = self.theme_manager
        return f"""
            #SetPathsDialogContainer {{
                background-color: {tm.get_variable('bg_secondary')};
                border-radius: 8px;
                border: 1px solid {tm.get_variable('border')};
            }}
            QLabel#TitleLabel {{
                color: {tm.get_variable('text_primary')};
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
            }}
            QLabel#PathLabel {{
                color: {tm.get_variable('text_secondary')};
                font-size: 13px;
                padding: 5px 0px;
            }}
            QLineEdit {{
                background-color: {tm.get_variable('bg_tertiary')};
                border: 1px solid {tm.get_variable('border')};
                border-radius: 4px;
                color: {tm.get_variable('text_primary')};
                font-size: 13px;
                padding: 8px;
            }}
            QLineEdit:focus {{
                border: 1px solid {tm.get_variable('accent')};
            }}
            QLineEdit:disabled {{
                background-color: {tm.get_variable('bg_primary')};
                color: {tm.get_variable('text_disabled')};
            }}
            QPushButton {{
                background-color: {tm.get_variable('bg_tertiary')};
                border: 1px solid {tm.get_variable('border')};
                border-radius: 4px;
                color: {tm.get_variable('text_primary')};
                font-size: 13px;
                padding: 8px 15px;
            }}
            QPushButton:hover {{
                background-color: {tm.get_variable('bg_hover')};
                border: 1px solid {tm.get_variable('border')};
            }}
            QPushButton:pressed {{
                background-color: {tm.get_variable('bg_pressed')};
            }}
            QPushButton#ConfirmButton {{
                background-color: {tm.get_variable('accent')};
                border: 1px solid {tm.get_variable('accent')};
            }}
            QPushButton#ConfirmButton:hover {{
                background-color: {tm.get_variable('accent_hover')};
            }}
            QPushButton#ConfirmButton:pressed {{
                background-color: {tm.get_variable('accent_pressed')};
            }}
        """
    
    def refresh_theme(self):
        """刷新主题样式"""
        if hasattr(self, 'main_container'):
            self.main_container.setStyleSheet(self._build_stylesheet())
    
    def init_ui(self):
        """初始化UI"""
        self.setModal(True)
        self.setFixedSize(600, 320)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.main_container = QWidget(self)
        self.main_container.setObjectName("SetPathsDialogContainer")
        self.main_container.setStyleSheet(self._build_stylesheet())
        
        layout = QVBoxLayout(self.main_container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title_label = QLabel("设置路径")
        title_label.setObjectName("TitleLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 资产库路径
        asset_lib_label = QLabel("资产库路径：")
        asset_lib_label.setObjectName("PathLabel")
        layout.addWidget(asset_lib_label)
        
        asset_lib_layout = QHBoxLayout()
        asset_lib_layout.setSpacing(10)
        
        self.asset_lib_input = NoContextMenuLineEdit()
        self.asset_lib_input.setPlaceholderText("选择资产库文件夹...")
        self.asset_lib_input.setText(self.asset_library_path)
        self.asset_lib_input.setReadOnly(True)
        asset_lib_layout.addWidget(self.asset_lib_input, 1)
        
        browse_asset_btn = QPushButton("浏览...")
        browse_asset_btn.setFixedWidth(80)
        browse_asset_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        browse_asset_btn.clicked.connect(self._browse_asset_library)
        asset_lib_layout.addWidget(browse_asset_btn)
        
        layout.addLayout(asset_lib_layout)
        
        # 预览工程路径
        preview_label = QLabel("预览工程路径：")
        preview_label.setObjectName("PathLabel")
        layout.addWidget(preview_label)
        
        preview_layout = QHBoxLayout()
        preview_layout.setSpacing(10)
        
        self.preview_input = NoContextMenuLineEdit()
        self.preview_input.setPlaceholderText("选择预览工程文件夹...")
        self.preview_input.setText(self.preview_project_path)
        self.preview_input.setReadOnly(True)
        preview_layout.addWidget(self.preview_input, 1)
        
        browse_preview_btn = QPushButton("浏览...")
        browse_preview_btn.setFixedWidth(80)
        browse_preview_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        browse_preview_btn.clicked.connect(self._browse_preview_project)
        preview_layout.addWidget(browse_preview_btn)
        
        layout.addLayout(preview_layout)
        
        layout.addStretch()
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        confirm_btn = QPushButton("确定")
        confirm_btn.setObjectName("ConfirmButton")
        confirm_btn.setFixedWidth(100)
        confirm_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        confirm_btn.clicked.connect(self.accept)
        button_layout.addWidget(confirm_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedWidth(100)
        cancel_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # 设置主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(main_container)
    
    def _browse_asset_library(self):
        """浏览资产库文件夹"""
        current_path = self.asset_lib_input.text() or ""
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择资产库文件夹",
            current_path,
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder:
            self.asset_lib_input.setText(folder)
            logger.info(f"选择资产库路径: {folder}")
    
    def _browse_preview_project(self):
        """浏览预览工程文件夹"""
        current_path = self.preview_input.text() or ""
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择预览工程文件夹",
            current_path,
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder:
            self.preview_input.setText(folder)
            logger.info(f"选择预览工程路径: {folder}")
    
    def get_paths(self) -> tuple[str, str]:
        """获取设置的路径
        
        Returns:
            元组 (资产库路径, 预览工程路径)
        """
        return self.asset_lib_input.text().strip(), self.preview_input.text().strip()
    
    def mousePressEvent(self, event: Optional[QMouseEvent]):
        """鼠标按下事件（用于拖动窗口）"""
        if event and event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event: Optional[QMouseEvent]):
        """鼠标移动事件（用于拖动窗口）"""
        if event and event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
    
    def mouseReleaseEvent(self, event: Optional[QMouseEvent]):
        """鼠标释放事件"""
        if event:
            self._drag_pos = None
            event.accept()

