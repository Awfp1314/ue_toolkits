# -*- coding: utf-8 -*-

"""
首次启动设置路径对话框
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


class FirstLaunchDialog(QDialog):
    """首次启动设置路径对话框（无标题栏，不可关闭，强制设置）"""
    
    def __init__(self, parent=None):
        """
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        
        self.theme_manager = get_theme_manager()
        
        # 禁用拖动功能（首次启动不允许拖动）
        self._drag_pos = None
        self._allow_drag = False  # 禁止拖动
        
        self.init_ui()
    
    def _build_stylesheet(self) -> str:
        """动态构建样式表
        
        Returns:
            完整的QSS样式字符串
        """
        tm = self.theme_manager
        
        return f"""
            #FirstLaunchDialogContainer {{
                background-color: {tm.get_variable('bg_secondary')};
                border-radius: 8px;
                border: 1px solid {tm.get_variable('border')};
            }}
            QLabel#TitleLabel {{
                color: {tm.get_variable('text_primary')};
                font-size: 18px;
                font-weight: bold;
                padding: 10px;
            }}
            QLabel#WelcomeLabel {{
                color: {tm.get_variable('text_secondary')};
                font-size: 14px;
                padding: 10px 0px;
            }}
            QLabel#PathLabel {{
                color: {tm.get_variable('text_secondary')};
                font-size: 13px;
                padding: 5px 0px;
            }}
            QLabel#WarningLabel {{
                color: {tm.get_variable('error')};
                font-size: 12px;
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
            QLineEdit[invalid="true"] {{
                border: 1px solid {tm.get_variable('error')};
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
                border: 1px solid {tm.get_variable('border_hover')};
            }}
            QPushButton:pressed {{
                background-color: {tm.get_variable('bg_pressed')};
            }}
            QPushButton#ConfirmButton {{
                background-color: {tm.get_variable('accent')};
                border: 1px solid {tm.get_variable('accent')};
                padding: 10px 20px;
                font-size: 14px;
            }}
            QPushButton#ConfirmButton:hover {{
                background-color: {tm.get_variable('accent_hover')};
            }}
            QPushButton#ConfirmButton:pressed {{
                background-color: {tm.get_variable('accent_pressed')};
            }}
            QPushButton#ConfirmButton:disabled {{
                background-color: {tm.get_variable('bg_tertiary')};
                border: 1px solid {tm.get_variable('border')};
                color: {tm.get_variable('text_disabled')};
            }}
        """
    
    def init_ui(self):
        """初始化UI"""
        self.setModal(True)
        self.setFixedSize(600, 300)  # 减小高度，因为移除了预览工程部分
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        main_container = QWidget(self)
        main_container.setObjectName("FirstLaunchDialogContainer")
        main_container.setStyleSheet(self._build_stylesheet())
        
        layout = QVBoxLayout(main_container)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        title_label = QLabel("🎉 欢迎使用虚幻引擎工具箱")
        title_label.setObjectName("TitleLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 欢迎说明
        welcome_label = QLabel(
            "首次使用需要设置资产库路径，用于存储和管理您的资产。\n"
            "预览工程可以稍后在设置界面中配置。"
        )
        welcome_label.setObjectName("WelcomeLabel")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_label.setWordWrap(True)
        layout.addWidget(welcome_label)
        
        layout.addSpacing(10)
        
        # 资产库路径（必填）
        asset_lib_label = QLabel("资产库路径：（必填）")
        asset_lib_label.setObjectName("PathLabel")
        layout.addWidget(asset_lib_label)
        
        asset_lib_layout = QHBoxLayout()
        asset_lib_layout.setSpacing(10)
        
        self.asset_lib_input = NoContextMenuLineEdit()
        self.asset_lib_input.setPlaceholderText("请选择资产库文件夹...")
        self.asset_lib_input.setReadOnly(True)
        self.asset_lib_input.textChanged.connect(self._validate_input)
        asset_lib_layout.addWidget(self.asset_lib_input, 1)
        
        browse_asset_btn = QPushButton("浏览...")
        browse_asset_btn.setFixedWidth(80)
        browse_asset_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        browse_asset_btn.clicked.connect(self._browse_asset_library)
        asset_lib_layout.addWidget(browse_asset_btn)
        
        layout.addLayout(asset_lib_layout)
        
        # 警告提示
        self.warning_label = QLabel("⚠️ 请选择资产库路径")
        self.warning_label.setObjectName("WarningLabel")
        self.warning_label.setVisible(False)
        layout.addWidget(self.warning_label)
        
        layout.addStretch()
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.confirm_btn = QPushButton("开始使用")
        self.confirm_btn.setObjectName("ConfirmButton")
        self.confirm_btn.setFixedWidth(150)
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.confirm_btn.clicked.connect(self._on_confirm)
        button_layout.addWidget(self.confirm_btn)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # 设置主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(main_container)
    
    def _validate_input(self):
        """验证输入"""
        asset_lib_path = self.asset_lib_input.text().strip()
        
        if asset_lib_path:
            self.confirm_btn.setEnabled(True)
            self.warning_label.setVisible(False)
            self.asset_lib_input.setProperty("invalid", False)
            self.asset_lib_input.style().unpolish(self.asset_lib_input)
            self.asset_lib_input.style().polish(self.asset_lib_input)
        else:
            self.confirm_btn.setEnabled(False)
    
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
            # 触发验证
            self._validate_input()
    
    def _on_confirm(self):
        """确认按钮点击"""
        asset_lib_path = self.asset_lib_input.text().strip()
        
        if not asset_lib_path:
            self.warning_label.setText("⚠️ 请选择资产库路径")
            self.warning_label.setVisible(True)
            self.asset_lib_input.setProperty("invalid", True)
            self.asset_lib_input.style().unpolish(self.asset_lib_input)
            self.asset_lib_input.style().polish(self.asset_lib_input)
            return
        
        if not Path(asset_lib_path).exists():
            self.warning_label.setText("⚠️ 选择的路径不存在")
            self.warning_label.setVisible(True)
            self.asset_lib_input.setProperty("invalid", True)
            self.asset_lib_input.style().unpolish(self.asset_lib_input)
            self.asset_lib_input.style().polish(self.asset_lib_input)
            return
        
        self.accept()
    
    def get_paths(self) -> tuple[str, str]:
        """获取设置的路径
        
        Returns:
            元组 (资产库路径, 预览工程路径)
        """
        return self.asset_lib_input.text().strip(), ""  # 预览工程路径现在为空，用户稍后在设置中配置
    
    def refresh_theme(self):
        """刷新主题样式"""
        # 重新应用样式表
        main_container = self.findChild(QWidget, "FirstLaunchDialogContainer")
        if main_container:
            main_container.setStyleSheet(self._build_stylesheet())
            logger.debug("首次启动对话框主题已刷新")
    
    def closeEvent(self, event):
        """重写关闭事件，阻止用户关闭对话框"""
        event.ignore()  # 忽略关闭事件
        logger.info("首次启动对话框不可关闭，必须完成设置")
    
    def keyPressEvent(self, event):
        """重写按键事件，阻止ESC键关闭对话框"""
        if event.key() == Qt.Key.Key_Escape:
            event.ignore()  # 忽略ESC键
            return
        super().keyPressEvent(event)
    
    def mousePressEvent(self, event: Optional[QMouseEvent]):
        """鼠标按下事件（禁用拖动窗口）"""
        # 首次启动对话框不允许拖动
        if event:
            event.accept()
    
    def mouseMoveEvent(self, event: Optional[QMouseEvent]):
        """鼠标移动事件（禁用拖动窗口）"""
        # 首次启动对话框不允许拖动
        if event:
            event.accept()
    
    def mouseReleaseEvent(self, event: Optional[QMouseEvent]):
        """鼠标释放事件"""
        if event:
            event.accept()

