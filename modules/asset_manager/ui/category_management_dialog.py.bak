# -*- coding: utf-8 -*-

"""
分类管理对话框
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QListWidgetItem
)
from core.utils.custom_widgets import NoContextMenuLineEdit
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from core.logger import get_logger
from core.utils.theme_manager import get_theme_manager
from .confirm_delete_category_dialog import ConfirmDeleteCategoryDialog

logger = get_logger(__name__)


class CategoryManagementDialog(QDialog):
    """分类管理对话框"""
    
    # 信号：分类列表已更新
    categories_updated = pyqtSignal()
    
    def __init__(self, logic, parent=None):
        """初始化对话框
        
        Args:
            logic: AssetManagerLogic 实例
            parent: 父组件
        """
        super().__init__(parent)
        self.logic = logic
        self.theme_manager = get_theme_manager()
        
        self.init_ui()
        self.load_categories()
    
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
            QLabel#errorLabel {{
                color: {tm.get_variable('error')};
                font-size: 12px;
                padding: 5px;
            }}
            QLineEdit {{
                background-color: {tm.get_variable('bg_tertiary')};
                border: 1px solid {tm.get_variable('border')};
                border-radius: 4px;
                padding: 8px;
                color: {tm.get_variable('text_primary')};
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {tm.get_variable('accent')};
            }}
            QListWidget {{
                background-color: {tm.get_variable('bg_tertiary')};
                border: 1px solid {tm.get_variable('border')};
                border-radius: 4px;
                color: {tm.get_variable('text_primary')};
                font-size: 13px;
                padding: 5px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 8px;
                border-radius: 3px;
                border: none;
                outline: none;
            }}
            QListWidget::item:selected {{
                background-color: {tm.get_variable('accent')};
                color: white;
            }}
            QListWidget::item:hover:!selected {{
                background-color: {tm.get_variable('bg_hover')};
            }}
            QListWidget::item:selected:hover {{
                background-color: {tm.get_variable('accent_hover')};
            }}
            QListWidget:focus {{
                outline: none;
                border: 1px solid {tm.get_variable('border')};
            }}
            QPushButton {{
                background-color: {tm.get_variable('accent')};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 13px;
                min-width: 70px;
            }}
            QPushButton:hover {{
                background-color: {tm.get_variable('accent_hover')};
            }}
            QPushButton:pressed {{
                background-color: {tm.get_variable('accent_pressed')};
            }}
            QPushButton#deleteButton {{
                background-color: {tm.get_variable('error')};
                color: white;
            }}
            QPushButton#deleteButton:hover {{
                background-color: #E53935;
            }}
            QPushButton#deleteButton:pressed {{
                background-color: #C62828;
            }}
            QPushButton#closeButton {{
                background-color: {tm.get_variable('bg_tertiary')};
                color: {tm.get_variable('text_primary')};
            }}
            QPushButton#closeButton:hover {{
                background-color: {tm.get_variable('bg_hover')};
            }}
            QPushButton#closeButton:pressed {{
                background-color: {tm.get_variable('bg_pressed')};
            }}
        """
    
    def refresh_theme(self):
        """刷新主题样式"""
        self.setStyleSheet(self._build_stylesheet())
    
    def init_ui(self):
        """初始化UI"""
        self.setModal(True)
        self.setFixedSize(450, 500)
        
        # 去掉标题栏
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        
        self.drag_position = None
        
        self.setStyleSheet(self._build_stylesheet())
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(15)
        
        title_label = QLabel("分类管理")
        title_label.setObjectName("titleLabel")
        main_layout.addWidget(title_label)
        
        # 添加分类区域
        add_layout = QVBoxLayout()
        add_layout.setSpacing(8)
        
        add_label = QLabel("添加新分类：")
        add_layout.addWidget(add_label)
        
        input_layout = QHBoxLayout()
        self.name_input = NoContextMenuLineEdit()
        self.name_input.setPlaceholderText("输入分类名称...")
        self.name_input.returnPressed.connect(self.add_category)
        input_layout.addWidget(self.name_input)
        
        add_btn = QPushButton("添加")
        add_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        add_btn.clicked.connect(self.add_category)
        input_layout.addWidget(add_btn)
        
        add_layout.addLayout(input_layout)
        main_layout.addLayout(add_layout)
        
        # 错误提示标签（固定高度，避免显示/隐藏时改变窗口大小）
        self.error_label = QLabel("")
        self.error_label.setObjectName("errorLabel")
        self.error_label.setWordWrap(True)
        self.error_label.setFixedHeight(30)
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        main_layout.addWidget(self.error_label)
        
        # 分类列表
        list_label = QLabel("现有分类：")
        main_layout.addWidget(list_label)
        
        self.category_list = QListWidget()
        self.category_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        main_layout.addWidget(self.category_list)
        
        delete_btn = QPushButton("删除选中分类")
        delete_btn.setObjectName("deleteButton")
        delete_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        delete_btn.clicked.connect(self.delete_category)
        main_layout.addWidget(delete_btn)
        
        info_label = QLabel("提示：删除分类时，该分类下的资产会移至\"默认分类\"")
        info_label.setStyleSheet(f"color: {self.theme_manager.get_variable('text_secondary')}; font-size: 12px;")
        info_label.setWordWrap(True)
        main_layout.addWidget(info_label)
        
        main_layout.addStretch()
        
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.setObjectName("closeButton")
        close_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        close_btn.clicked.connect(self.accept)
        close_layout.addWidget(close_btn)
        
        main_layout.addLayout(close_layout)
    
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
    
    def load_categories(self):
        """加载分类列表"""
        self.category_list.clear()
        categories = self.logic.get_all_categories()
        
        for category in categories:
            item = QListWidgetItem(category)
            # 默认分类标记为灰色且不可删除
            if category == "默认分类":
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                item.setForeground(Qt.GlobalColor.gray)
            self.category_list.addItem(item)
    
    def add_category(self):
        """添加分类"""
        category_name = self.name_input.text().strip()
        
        if not category_name:
            self.show_error("分类名称不能为空")
            return
        
        # 调用逻辑层添加分类
        if self.logic.add_category(category_name):
            # 添加成功
            self.name_input.clear()
            self.hide_error()
            self.load_categories()
            
            # 发射信号通知UI更新
            self.categories_updated.emit()
            
            logger.info(f"添加分类成功: {category_name}")
        else:
            # 添加失败
            self.show_error(f"分类 \"{category_name}\" 已存在或无效")
    
    def delete_category(self):
        """删除选中的分类"""
        current_item = self.category_list.currentItem()
        
        if not current_item:
            self.show_error("请先选择要删除的分类")
            return
        
        category_name = current_item.text()
        
        # 不能删除默认分类
        if category_name == "默认分类":
            self.show_error("不能删除默认分类")
            return
        
        assets_in_category = [a for a in self.logic.assets if a.category == category_name]
        
        # 如果分类下有资产，显示确认对话框
        if assets_in_category:
            asset_count = len(assets_in_category)
            dialog = ConfirmDeleteCategoryDialog(category_name, asset_count, self)
            
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
        
        # 调用逻辑层删除分类
        if self.logic.remove_category(category_name):
            # 删除成功
            self.hide_error()
            self.load_categories()
            
            # 发射信号通知UI更新
            self.categories_updated.emit()
            
            logger.info(f"删除分类成功: {category_name}")
        else:
            self.show_error(f"删除分类 \"{category_name}\" 失败")
    
    def show_error(self, message):
        """显示错误信息"""
        self.error_label.setText(message)
        self.error_label.setStyleSheet(
            f"color: {self.theme_manager.get_variable('error')}; font-size: 12px; padding: 5px;"
        )
    
    def hide_error(self):
        """隐藏错误信息"""
        self.error_label.setText("")
        self.error_label.setStyleSheet("")

