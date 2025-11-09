# -*- coding: utf-8 -*-

"""
添加资产对话框
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QCheckBox,
    QFileDialog, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from pathlib import Path
from typing import Optional, List, Tuple

from core.logger import get_logger
from core.utils.theme_manager import get_theme_manager
from core.utils.custom_widgets import NoContextMenuLineEdit
from ..logic.asset_model import AssetType
from .custom_checkbox import CustomCheckBox

logger = get_logger(__name__)


class AddAssetDialog(QDialog):
    """添加资产对话框"""
    
    def __init__(self, existing_asset_names: List[str], categories: List[str], 
                 prefill_path: Optional[str] = None, prefill_type: Optional[AssetType] = None,
                 parent=None):
        """初始化对话框
        
        Args:
            existing_asset_names: 已存在的资产名称列表
            categories: 已有的分类列表
            prefill_path: 预填充的资产路径（可选）
            prefill_type: 预填充的资产类型（可选）
            parent: 父组件
        """
        super().__init__(parent)
        
        self.theme_manager = get_theme_manager()
        
        self.existing_asset_names = existing_asset_names
        self.categories = categories
        self.asset_path = None
        self.asset_type = None
        self.prefill_path = prefill_path
        self.prefill_type = prefill_type
        
        self.init_ui()
    
    def _build_stylesheet(self) -> str:
        """动态构建主对话框样式表
        
        Returns:
            完整的QSS样式字符串
        """
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
            QLabel#errorLabel {{
                color: {tm.get_variable('error')};
                font-size: 13px;
                font-weight: bold;
                padding: 10px;
                background-color: {tm.get_variable('bg_tertiary')};
                border: 1px solid {tm.get_variable('error')};
                border-radius: 4px;
            }}
            QLineEdit, QComboBox {{
                background-color: {tm.get_variable('bg_tertiary')};
                border: 1px solid {tm.get_variable('border')};
                border-radius: 4px;
                padding: 8px;
                color: {tm.get_variable('text_primary')};
                font-size: 13px;
            }}
            QLineEdit:focus, QComboBox:focus {{
                border: 1px solid {tm.get_variable('accent')};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {tm.get_variable('text_secondary')};
                margin-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {tm.get_variable('bg_tertiary')};
                border: 1px solid {tm.get_variable('border')};
                selection-background-color: {tm.get_variable('accent')};
                color: {tm.get_variable('text_primary')};
                padding: 5px;
            }}
            QCheckBox {{
                color: {tm.get_variable('text_primary')};
                font-size: 13px;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {tm.get_variable('border')};
                border-radius: 3px;
                background-color: {tm.get_variable('bg_tertiary')};
            }}
            QCheckBox::indicator:checked {{
                background-color: {tm.get_variable('accent')};
                border-color: {tm.get_variable('accent')};
            }}
            QCheckBox::indicator:checked::after {{
                content: "✓";
                color: white;
            }}
            QPushButton {{
                background-color: {tm.get_variable('accent')};
                color: white;
                border: none;
                padding: 10px 24px;
                border-radius: 4px;
                font-size: 13px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {tm.get_variable('accent_hover')};
            }}
            QPushButton:pressed {{
                background-color: {tm.get_variable('accent_pressed')};
            }}
            QPushButton#cancelButton {{
                background-color: {tm.get_variable('bg_tertiary')};
                color: {tm.get_variable('text_primary')};
            }}
            QPushButton#cancelButton:hover {{
                background-color: {tm.get_variable('bg_hover')};
            }}
            QPushButton#cancelButton:pressed {{
                background-color: {tm.get_variable('bg_pressed')};
            }}
            QPushButton#selectPathButton {{
                background-color: {tm.get_variable('bg_tertiary')};
                color: {tm.get_variable('text_primary')};
                padding: 8px 16px;
                min-width: 80px;
            }}
            QPushButton#selectPathButton:hover {{
                background-color: {tm.get_variable('bg_hover')};
            }}
        """
    
    def _build_menu_stylesheet(self) -> str:
        """动态构建菜单样式表
        
        Returns:
            QMenu的QSS样式字符串
        """
        tm = self.theme_manager
        
        return f"""
            QMenu {{
                background-color: {tm.get_variable('bg_secondary')};
                border: 1px solid {tm.get_variable('border')};
                padding: 5px;
            }}
            QMenu::item {{
                color: {tm.get_variable('text_primary')};
                padding: 8px 20px;
                border-radius: 3px;
            }}
            QMenu::item:selected {{
                background-color: {tm.get_variable('accent')};
            }}
        """
    
    def init_ui(self):
        """初始化UI"""
        self.setModal(True)
        self.setMinimumSize(550, 400)
        
        # 去掉标题栏
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        
        self.drag_position = None
        
        self.setStyleSheet(self._build_stylesheet())
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(15)
        
        title_label = QLabel("添加资产")
        title_label.setObjectName("titleLabel")
        main_layout.addWidget(title_label)
        
        path_layout = QHBoxLayout()
        path_label = QLabel("资产路径：")
        path_label.setFixedWidth(80)
        path_layout.addWidget(path_label)
        
        self.path_display = NoContextMenuLineEdit()
        self.path_display.setPlaceholderText("请选择资产路径...")
        self.path_display.setReadOnly(True)
        path_layout.addWidget(self.path_display)
        
        select_path_btn = QPushButton("浏览...")
        select_path_btn.setObjectName("selectPathButton")
        select_path_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # 禁用焦点，避免Alt键虚线框
        select_path_btn.clicked.connect(self.select_asset_path)
        path_layout.addWidget(select_path_btn)
        
        main_layout.addLayout(path_layout)
        
        name_layout = QHBoxLayout()
        name_label = QLabel("资产名称：")
        name_label.setFixedWidth(80)
        name_layout.addWidget(name_label)
        
        self.name_input = NoContextMenuLineEdit()
        self.name_input.setPlaceholderText("输入资产名称...")
        self.name_input.textChanged.connect(self.on_name_changed)
        name_layout.addWidget(self.name_input)
        
        main_layout.addLayout(name_layout)
        
        category_layout = QHBoxLayout()
        category_label = QLabel("资产分类：")
        category_label.setFixedWidth(80)
        category_layout.addWidget(category_label)
        
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.addItems(self.categories)
        self.category_combo.setCurrentText("默认分类")
        category_layout.addWidget(self.category_combo)
        
        main_layout.addLayout(category_layout)
        
        self.create_doc_checkbox = CustomCheckBox("创建说明文档")
        self.create_doc_checkbox.setChecked(True)
        main_layout.addWidget(self.create_doc_checkbox)
        
        self.error_label = QLabel("")
        self.error_label.setObjectName("errorLabel")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        main_layout.addWidget(self.error_label)
        
        main_layout.addStretch()
        
        button_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("添加")
        self.add_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # 禁用焦点，避免Alt键虚线框
        self.add_btn.clicked.connect(self.on_add_clicked)
        self.add_btn.setEnabled(True)  # 确保按钮可用
        button_layout.addWidget(self.add_btn)
        
        logger.debug("添加按钮已创建并连接信号")
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # 禁用焦点，避免Alt键虚线框
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        main_layout.addLayout(button_layout)
        
        # 如果有预填数据，则填充
        if self.prefill_path:
            self.path_display.setText(self.prefill_path)
            self.asset_path = Path(self.prefill_path)
            self.asset_type = self.prefill_type
            
            # 自动填充资产名称
            path = Path(self.prefill_path)
            if self.prefill_type == AssetType.FILE:
                auto_name = path.stem
            else:
                auto_name = path.name
            self.name_input.setText(auto_name)
    
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
    
    def select_asset_path(self):
        """选择资产路径"""
        # 弹出菜单让用户选择类型
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QCursor
        
        menu = QMenu(self)
        menu.setStyleSheet(self._build_menu_stylesheet())
        
        package_action = menu.addAction("📦 选择资源包（文件夹）")
        file_action = menu.addAction("📄 选择资源文件")
        
        action = menu.exec(QCursor.pos())
        
        if action == package_action:
            self._select_package()
        elif action == file_action:
            self._select_file()
    
    def _select_package(self):
        """选择资源包"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择资源包文件夹",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if dir_path:
            self.asset_path = Path(dir_path)
            self.asset_type = AssetType.PACKAGE
            self.path_display.setText(str(self.asset_path))
            
            # 自动填充名称
            if not self.name_input.text():
                self.name_input.setText(self.asset_path.name)
    
    def _select_file(self):
        """选择资源文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择资产文件",
            "",
            "所有文件 (*);;模型文件 (*.fbx *.obj *.gltf);;贴图文件 (*.png *.jpg *.tga *.bmp)"
        )
        
        if file_path:
            self.asset_path = Path(file_path)
            self.asset_type = AssetType.FILE
            self.path_display.setText(str(self.asset_path))
            
            # 自动填充名称
            if not self.name_input.text():
                self.name_input.setText(self.asset_path.stem)
    
    def on_name_changed(self, text):
        """名称改变时隐藏错误提示"""
        if text:
            self.error_label.hide()
    
    def validate_input(self) -> Tuple[bool, str]:
        """验证输入
        
        Returns:
            (是否有效, 错误信息)
        """
        if not self.asset_path:
            return False, "请先选择资产路径"
        
        name = self.name_input.text().strip()
        if not name:
            return False, "资产名称不能为空"
        
        if name in self.existing_asset_names:
            return False, f"资产名称 \"{name}\" 已存在，请使用其他名称"
        
        return True, ""
    
    def on_add_clicked(self):
        """点击添加按钮"""
        logger.info("点击添加按钮")
        
        valid, error_msg = self.validate_input()
        
        if not valid:
            logger.warning(f"输入验证失败: {error_msg}")
            self.error_label.setText(error_msg)
            self.error_label.show()
            
            # 如果是路径问题，给路径输入框加个高亮
            if "路径" in error_msg:
                self.path_display.setFocus()
            # 如果是名称问题，给名称输入框加个高亮
            elif "名称" in error_msg:
                self.name_input.setFocus()
            
            return
        
        logger.info(f"验证通过，准备添加资产: {self.name_input.text().strip()}")
        self.accept()
    
    def get_asset_info(self) -> dict:
        """获取资产信息
        
        Returns:
            资产信息字典
        """
        return {
            "path": self.asset_path,
            "type": self.asset_type,
            "name": self.name_input.text().strip(),
            "category": self.category_combo.currentText().strip() or "默认分类",
            "create_doc": self.create_doc_checkbox.isChecked()
        }
    
    def refresh_theme(self):
        """刷新主题样式"""
        self.setStyleSheet(self._build_stylesheet())
        logger.debug("添加资产对话框主题已刷新")

