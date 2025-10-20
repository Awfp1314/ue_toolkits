# -*- coding: utf-8 -*-

"""
工程运行中警告对话框
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QMouseEvent

from core.utils.theme_manager import get_theme_manager


class ProjectRunningWarningDialog(QDialog):
    """工程运行中警告对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_manager = get_theme_manager()
        self.setModal(True)
        self.setFixedSize(500, 250)
        
        # 设置无标题栏窗口
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        
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
            QPushButton {{
                background-color: {tm.get_variable('bg_tertiary')};
                color: {tm.get_variable('text_primary')};
                border: 1px solid {tm.get_variable('border')};
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
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
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 标题标签
        title_label = QLabel("⚠ 工程正在运行")
        title_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme_manager.get_variable('warning')};")
        layout.addWidget(title_label)
        
        # 提示信息标签
        message_label = QLabel("当前工程正在运行无法导入配置文件，\n请关闭保存工程后重试")
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(message_label)
        
        # 添加弹性空间
        layout.addStretch()
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton("确定")
        close_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        close_button.setFixedWidth(80)
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
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
    
    def center_on_parent(self):
        """在父窗口上居中显示"""
        from PyQt6.QtWidgets import QWidget
        parent = self.parent()
        if isinstance(parent, QWidget) and parent.isVisible():
            parent_geo = parent.geometry()
            
            dialog_width = self.width()
            dialog_height = self.height()
            
            # 计算对话框应该出现的位置（相对于父窗口居中）
            dialog_x = parent_geo.x() + (parent_geo.width() - dialog_width) // 2
            dialog_y = parent_geo.y() + (parent_geo.height() - dialog_height) // 2
            
            # 移动对话框到计算出的位置
            self.move(dialog_x, dialog_y)
