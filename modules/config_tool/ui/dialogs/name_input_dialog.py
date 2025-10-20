# -*- coding: utf-8 -*-

"""
配置名称输入对话框
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton
from core.utils.custom_widgets import NoContextMenuLineEdit
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QMouseEvent

from core.utils.theme_manager import get_theme_manager


class NameInputDialog(QDialog):
    """配置名称输入对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_manager = get_theme_manager()
        
        # 去掉标题栏并确保窗口在最前面
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setModal(True)
        self.setFixedSize(300, 120)
        
        self.setStyleSheet(self._build_stylesheet())
        
        # 用于窗口拖动的变量
        self.drag_position = None
        
        self.init_ui()
    
    def _build_stylesheet(self):
        """构建动态样式表"""
        tm = self.theme_manager
        return f"""
            QDialog {{
                background-color: {tm.get_variable('bg_secondary')};
                color: {tm.get_variable('text_primary')};
                border: 1px solid {tm.get_variable('border')};
                border-radius: 4px;
            }}
            QLabel {{
                color: {tm.get_variable('text_primary')};
                font-size: 14px;
            }}
            QLineEdit {{
                background-color: {tm.get_variable('bg_tertiary')};
                color: {tm.get_variable('text_primary')};
                border: 1px solid {tm.get_variable('border')};
                padding: 8px;
                border-radius: 4px;
                font-size: 14px;
            }}
            QPushButton {{
                background-color: {tm.get_variable('bg_tertiary')};
                color: {tm.get_variable('text_primary')};
                border: 1px solid {tm.get_variable('border')};
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {tm.get_variable('bg_hover')};
            }}
            QPushButton:pressed {{
                background-color: {tm.get_variable('bg_pressed')};
            }}
        """
    
    def refresh_theme(self):
        """刷新主题样式"""
        self.setStyleSheet(self._build_stylesheet())
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.name_input = NoContextMenuLineEdit()
        self.name_input.setPlaceholderText("请输入配置名称")
        layout.addWidget(self.name_input)
        
        # 自定义按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 添加按钮（最左侧，默认禁用）
        self.add_button = QPushButton("添加")
        self.add_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.add_button.clicked.connect(self.on_add_clicked)
        self.add_button.setEnabled(False)  # 默认禁用
        button_layout.addWidget(self.add_button)
        
        # 添加弹性空间
        button_layout.addStretch()
        
        # 取消按钮（最右侧）
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 连接输入框的文本变化事件
        self.name_input.textChanged.connect(self.on_text_changed)
        
        # 连接输入框的回车事件
        self.name_input.returnPressed.connect(self.on_add_clicked)
    
    def mousePressEvent(self, a0):
        """鼠标按下事件"""
        if a0 and isinstance(a0, QMouseEvent) and a0.button() == Qt.MouseButton.LeftButton:
            self.drag_position = a0.globalPosition().toPoint() - self.frameGeometry().topLeft()
            a0.accept()
    
    def mouseMoveEvent(self, a0):
        """鼠标移动事件"""
        if a0 and isinstance(a0, QMouseEvent) and a0.buttons() == Qt.MouseButton.LeftButton and self.drag_position is not None:
            self.move(a0.globalPosition().toPoint() - self.drag_position)
            a0.accept()
    
    def mouseReleaseEvent(self, a0):
        """鼠标释放事件"""
        self.drag_position = None
        if a0:
            a0.accept()
    
    def showEvent(self, a0):
        """重写showEvent以实现相对于父窗口居中"""
        super().showEvent(a0)
        # 使用单次定时器确保在窗口显示后才进行居中计算
        QTimer.singleShot(0, self.center_on_parent)
    
    def hideEvent(self, a0):
        """重写hideEvent"""
        super().hideEvent(a0)
    
    def center_on_parent(self):
        """在父窗口上居中显示，稍微向上偏移"""
        from PyQt6.QtWidgets import QWidget
        parent = self.parent()
        if isinstance(parent, QWidget) and parent.isVisible():
            parent_geo = parent.geometry()
            
            dialog_width = self.width()
            dialog_height = self.height()
            
            # 计算对话框应该出现的位置（相对于父窗口居中，但垂直方向向上偏移30像素）
            dialog_x = parent_geo.x() + (parent_geo.width() - dialog_width) // 2
            dialog_y = parent_geo.y() + (parent_geo.height() - dialog_height) // 2 - 30
            
            # 移动对话框到计算出的位置
            self.move(dialog_x, dialog_y)
    
    def resizeEvent(self, a0):
        """重写resizeEvent以确保窗口大小改变时仍然居中"""
        super().resizeEvent(a0)
        # 确保在调整大小后仍然居中
        self.center_on_parent()
    
    def get_config_name(self) -> str:
        """获取配置名称"""
        return self.name_input.text().strip()
    
    def set_existing_names(self, names: list):
        """设置已存在的配置名称列表，用于检查重复"""
        self.existing_names = names
    
    def on_add_clicked(self):
        """添加按钮点击事件"""
        config_name = self.get_config_name()
        
        # 再次检查配置名称是否满足条件（防止按钮被意外启用）
        if not self.is_name_valid(config_name):
            return
        
        # 接受对话框
        self.accept()
    
    def on_text_changed(self, text):
        """输入框文本变化事件"""
        # 根据文本是否满足条件来启用/禁用添加按钮
        self.add_button.setEnabled(self.is_name_valid(text))
    
    def is_name_valid(self, name):
        """检查配置名称是否有效"""
        if not name or not name.strip():
            return False
        
        if hasattr(self, 'existing_names') and name in self.existing_names:
            return False
        
        return True
    
    def show_error(self, message: str):
        """显示错误信息"""
        # 不再显示错误信息，改为禁用按钮
        pass
    
    def hide_error(self):
        """隐藏错误信息"""
        # 不再显示错误信息，改为禁用按钮
        pass

