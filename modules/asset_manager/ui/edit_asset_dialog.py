# -*- coding: utf-8 -*-

"""
编辑资产信息对话框
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QPushButton, QWidget
)
from core.utils.custom_widgets import NoContextMenuLineEdit
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QMouseEvent
from typing import Optional, List

from core.logger import get_logger
from core.utils.theme_manager import get_theme_manager

logger = get_logger(__name__)


class EditAssetDialog(QDialog):
    """编辑资产信息对话框（无标题栏）"""
    
    def __init__(self, asset_name: str, asset_category: str, 
                 existing_names: List[str], categories: List[str], 
                 parent=None):
        """
        Args:
            asset_name: 当前资产名称
            asset_category: 当前资产分类
            existing_names: 已存在的资产名称列表（用于检查重名）
            categories: 可用的分类列表
            parent: 父窗口
        """
        super().__init__(parent)
        
        self.theme_manager = get_theme_manager()
        
        self.asset_name = asset_name
        self.asset_category = asset_category
        self.existing_names = [name for name in existing_names if name != asset_name]  # 排除当前名称
        self.categories = categories
        
        self.drag_position = QPoint()
        self.init_ui()
    
    def _build_stylesheet(self) -> str:
        """动态构建样式表
        
        Returns:
            完整的QSS样式字符串
        """
        tm = self.theme_manager
        
        return f"""
            QWidget#mainContainer {{
                background-color: {tm.get_variable('bg_secondary')};
                border: 1px solid {tm.get_variable('border')};
                border-radius: 8px;
            }}
            QLabel#titleLabel {{
                color: {tm.get_variable('text_primary')};
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton#closeBtn {{
                background-color: transparent;
                color: {tm.get_variable('text_secondary')};
                font-size: 20px;
                border: none;
                border-radius: 4px;
            }}
            QPushButton#closeBtn:hover {{
                background-color: {tm.get_variable('error')};
                color: white;
            }}
            QLabel.fieldLabel {{
                color: {tm.get_variable('text_primary')};
                font-size: 13px;
            }}
            QLineEdit {{
                background-color: {tm.get_variable('bg_tertiary')};
                border: 1px solid {tm.get_variable('border')};
                border-radius: 4px;
                padding: 8px 10px;
                color: {tm.get_variable('text_primary')};
                font-size: 13px;
            }}
            QLineEdit:hover {{
                border: 1px solid {tm.get_variable('accent')};
            }}
            QLineEdit:focus {{
                border: 1px solid {tm.get_variable('accent')};
                outline: none;
            }}
            QComboBox {{
                background-color: {tm.get_variable('bg_tertiary')};
                border: 1px solid {tm.get_variable('border')};
                border-radius: 4px;
                padding: 8px 10px;
                color: {tm.get_variable('text_primary')};
                font-size: 13px;
            }}
            QComboBox:hover {{
                border: 1px solid {tm.get_variable('accent')};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {tm.get_variable('text_secondary')};
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {tm.get_variable('bg_tertiary')};
                border: 1px solid {tm.get_variable('border')};
                selection-background-color: {tm.get_variable('accent')};
                color: {tm.get_variable('text_primary')};
            }}
            QLabel#errorLabel {{
                color: {tm.get_variable('error')};
                font-size: 12px;
                padding: 0px;
            }}
            QPushButton#okBtn {{
                background-color: {tm.get_variable('accent')};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 13px;
            }}
            QPushButton#okBtn:hover {{
                background-color: {tm.get_variable('accent_hover')};
            }}
            QPushButton#okBtn:pressed {{
                background-color: {tm.get_variable('accent_pressed')};
            }}
            QPushButton#cancelBtn {{
                background-color: {tm.get_variable('bg_tertiary')};
                color: {tm.get_variable('text_primary')};
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 13px;
            }}
            QPushButton#cancelBtn:hover {{
                background-color: {tm.get_variable('bg_hover')};
            }}
            QPushButton#cancelBtn:pressed {{
                background-color: {tm.get_variable('bg_pressed')};
            }}
        """
    
    def init_ui(self):
        """初始化UI"""
        self.setModal(True)
        self.setFixedSize(450, 320)  # 增加高度以容纳所有内容
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        main_container = QWidget()
        main_container.setObjectName("mainContainer")
        main_container.setStyleSheet(self._build_stylesheet())
        
        container_layout = QVBoxLayout(main_container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(15)
        
        # 标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel("编辑资产信息")
        title_label.setObjectName("titleLabel")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        close_btn = QPushButton("×")
        close_btn.setObjectName("closeBtn")
        close_btn.setFixedSize(30, 30)
        close_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # 禁用焦点，避免Alt键虚线框
        close_btn.clicked.connect(self.reject)
        title_layout.addWidget(close_btn)
        
        container_layout.addLayout(title_layout)
        
        # 资产名称
        name_label = QLabel("资产名称：")
        name_label.setProperty("class", "fieldLabel")
        container_layout.addWidget(name_label)
        
        self.name_input = NoContextMenuLineEdit()
        self.name_input.setText(self.asset_name)
        self.name_input.textChanged.connect(self._on_name_changed)
        container_layout.addWidget(self.name_input)
        
        # 分类选择
        category_label = QLabel("资产分类：")
        category_label.setProperty("class", "fieldLabel")
        container_layout.addWidget(category_label)
        
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.addItems(self.categories)
        self.category_combo.setCurrentText(self.asset_category)
        container_layout.addWidget(self.category_combo)
        
        self.error_label = QLabel("")
        self.error_label.setObjectName("errorLabel")
        self.error_label.setWordWrap(True)
        self.error_label.setFixedHeight(30)
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        container_layout.addWidget(self.error_label)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 确定按钮
        ok_btn = QPushButton("确定")
        ok_btn.setObjectName("okBtn")
        ok_btn.setFixedWidth(100)
        ok_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # 禁用焦点，避免Alt键虚线框
        ok_btn.clicked.connect(self._on_ok_clicked)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.setFixedWidth(100)
        cancel_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # 禁用焦点，避免Alt键虚线框
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        container_layout.addLayout(button_layout)
        
        # 设置主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(main_container)
    
    def _on_name_changed(self, text: str):
        """名称输入框内容改变时的处理"""
        # 清除错误提示
        self.error_label.setText("")
    
    def _on_ok_clicked(self):
        """确定按钮点击事件"""
        new_name = self.name_input.text().strip()
        new_category = self.category_combo.currentText().strip()
        
        if not new_name:
            self.error_label.setText("资产名称不能为空")
            return
        
        if new_name in self.existing_names:
            self.error_label.setText(f"资产名称 \"{new_name}\" 已存在")
            return
        
        if not new_category:
            self.error_label.setText("分类名称不能为空")
            return
        
        self.accept()
    
    def get_asset_info(self) -> dict:
        """获取编辑后的资产信息
        
        Returns:
            包含name和category的字典
        """
        return {
            "name": self.name_input.text().strip(),
            "category": self.category_combo.currentText().strip()
        }
    
    def refresh_theme(self):
        """刷新主题样式"""
        # 重新应用样式表
        main_container = self.findChild(QWidget, "mainContainer")
        if main_container:
            main_container.setStyleSheet(self._build_stylesheet())
            logger.debug("编辑资产对话框主题已刷新")
    
    def mousePressEvent(self, event: Optional[QMouseEvent]):
        """鼠标按下事件，用于窗口拖动"""
        if event and event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event: Optional[QMouseEvent]):
        """鼠标移动事件，用于窗口拖动"""
        if event and event.buttons() == Qt.MouseButton.LeftButton and not self.drag_position.isNull():
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

