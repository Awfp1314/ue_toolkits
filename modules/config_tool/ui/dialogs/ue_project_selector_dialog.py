# -*- coding: utf-8 -*-

"""
UE工程选择对话框
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QPushButton
from PyQt6.QtCore import Qt, QTimer

from core.utils.theme_manager import get_theme_manager


class UEProjectSelectorDialog(QDialog):
    """UE工程选择对话框"""
    
    def __init__(self, projects, parent=None):
        super().__init__(parent)
        self.projects = projects
        self.selected_project = None
        self.theme_manager = get_theme_manager()
        self.setModal(True)
        self.setFixedSize(700, 400)
        
        # 确保窗口在最前面
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        
        # 设置主题样式
        self.setStyleSheet(self._build_stylesheet())
        
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
            QListWidget {{
                background-color: {tm.get_variable('bg_tertiary')};
                color: {tm.get_variable('text_primary')};
                border: 1px solid {tm.get_variable('border')};
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
        
        label = QLabel("检测到多个UE工程，请选择一个：")
        layout.addWidget(label)
        
        self.project_list = QListWidget()
        for project in self.projects:
            # 根据PID判断是运行中的工程还是搜索到的工程
            status = "运行中" if project.pid > 0 else "已找到"
            self.project_list.addItem(f"[{status}] {project.name} - {project.project_path}")
        self.project_list.currentRowChanged.connect(self.on_selection_changed)
        layout.addWidget(self.project_list)
        
        self.ok_button = QPushButton("确定")
        self.ok_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setEnabled(False)  # 默认禁用，需要选择项目后启用
        cancel_button = QPushButton("取消")
        cancel_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        cancel_button.clicked.connect(self.reject)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
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
    
    def on_selection_changed(self, index):
        """选择改变事件"""
        self.ok_button.setEnabled(index >= 0)
    
    def get_selected_project(self):
        """获取选中的项目"""
        current_row = self.project_list.currentRow()
        if 0 <= current_row < len(self.projects):
            return self.projects[current_row]
        return None

