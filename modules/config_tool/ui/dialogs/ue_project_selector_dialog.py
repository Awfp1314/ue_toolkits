# -*- coding: utf-8 -*-

"""
UE工程选择对话框
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QWidget, QGridLayout, QApplication)
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QMouseEvent

from core.utils.theme_manager import get_theme_manager
from core.logger import get_logger
from ..components.ue_project_card import UEProjectCard

logger = get_logger(__name__)


class UEProjectSelectorDialog(QDialog):
    """UE工程选择对话框"""
    
    def __init__(self, projects, parent=None):
        super().__init__(parent)
        # 按.uproject文件的修改时间排序（最新的在前）
        self.projects = self._sort_projects_by_recent(projects)
        self.selected_project = None
        self.theme_manager = get_theme_manager()
        self.project_cards = []  # 存储所有卡片
        self.drag_position = QPoint()
        
        self.setModal(True)
        self.setFixedSize(920, 680)
        
        # 无边框，透明背景
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.init_ui()
    
    def _sort_projects_by_recent(self, projects):
        """按工程最近打开时间排序（根据.uproject文件修改时间）"""
        try:
            # 按.uproject文件的修改时间降序排列（最新的在前）
            sorted_projects = sorted(
                projects,
                key=lambda p: p.project_path.stat().st_mtime if p.project_path.exists() else 0,
                reverse=True
            )
            logger.info(f"已按最近打开时间排序 {len(sorted_projects)} 个工程")
            return sorted_projects
        except Exception as e:
            logger.warning(f"工程排序失败，使用原始顺序: {e}")
            return projects
    
    def _build_stylesheet(self):
        """构建动态样式表"""
        tm = self.theme_manager
        return f"""
            QDialog {{
                background: transparent;
            }}
            #mainContainer {{
                background-color: {tm.get_variable('bg_secondary')};
                border: 1px solid {tm.get_variable('border')};
                border-radius: 8px;
            }}
            #promptLabel {{
                color: {tm.get_variable('text_primary')};
                font-size: 14px;
                background: transparent;
                padding: 5px;
            }}
            QScrollArea {{
                background-color: {tm.get_variable('bg_tertiary')};
                border: 1px solid {tm.get_variable('border')};
                border-radius: 4px;
            }}
            QPushButton {{
                background-color: {tm.get_variable('bg_tertiary')};
                color: {tm.get_variable('text_primary')};
                border: 1px solid {tm.get_variable('border')};
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 14px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {tm.get_variable('bg_hover')};
                border-color: {tm.get_variable('border_hover')};
            }}
            QPushButton:pressed {{
                background-color: {tm.get_variable('bg_pressed')};
            }}
            QPushButton:disabled {{
                background-color: {tm.get_variable('bg_tertiary')};
                color: {tm.get_variable('text_disabled')};
                border-color: {tm.get_variable('border')};
            }}
        """
    
    def refresh_theme(self):
        """刷新主题样式"""
        self.setStyleSheet(self._build_stylesheet())
    
    def init_ui(self):
        """初始化UI"""
        # 设置样式
        self.setStyleSheet(self._build_stylesheet())
        
        # 主容器
        main_container = QWidget()
        main_container.setObjectName("mainContainer")
        
        container_layout = QVBoxLayout(main_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # 创建自定义标题栏并隐藏窗口控制按钮
        from ui.main_window_components.title_bar import CustomTitleBar
        title_bar = CustomTitleBar(self)
        # 修改标题文本
        for child in title_bar.findChildren(QLabel):
            if child.objectName() == "titleLabel":
                child.setText("选择UE工程")
                break
        # 隐藏窗口控制按钮
        for child in title_bar.findChildren(QPushButton):
            child.hide()
        container_layout.addWidget(title_bar)
        
        # 内容区域
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(25, 15, 25, 25)
        content_layout.setSpacing(15)
        
        # 提示标签
        prompt_label = QLabel("搜索到以下UE工程，请选择一个：")
        prompt_label.setObjectName("promptLabel")
        content_layout.addWidget(prompt_label)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 卡片容器
        cards_container = QWidget()
        cards_layout = QGridLayout(cards_container)
        cards_layout.setSpacing(15)
        cards_layout.setContentsMargins(10, 10, 10, 10)
        
        # 添加工程卡片（3列网格）
        columns = 3
        for i, project in enumerate(self.projects):
            card = UEProjectCard(project)
            card.clicked.connect(self._on_card_clicked)
            
            row = i // columns
            col = i % columns
            cards_layout.addWidget(card, row, col)
            
            self.project_cards.append(card)
        
        # 添加伸缩项，使卡片靠上对齐
        cards_layout.setRowStretch(cards_layout.rowCount(), 1)
        
        scroll_area.setWidget(cards_container)
        content_layout.addWidget(scroll_area)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.ok_button = QPushButton("确定")
        self.ok_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setEnabled(False)  # 默认禁用
        button_layout.addWidget(self.ok_button)
        
        cancel_button = QPushButton("取消")
        cancel_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        content_layout.addLayout(button_layout)
        
        container_layout.addWidget(content_widget)
        
        # 设置主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(main_container)
        
        # 延迟居中，确保窗口完全初始化
        QTimer.singleShot(0, self.center_on_parent)
    
    def showEvent(self, a0):
        """重写showEvent以实现相对于父窗口居中"""
        super().showEvent(a0)
        # 再次尝试居中
        self.center_on_parent()
    
    def center_on_parent(self):
        """在父窗口上居中显示"""
        from PyQt6.QtWidgets import QWidget
        from PyQt6.QtGui import QScreen
        
        # 向上查找真正的主窗口
        main_window = None
        parent = self.parent()
        
        while parent:
            # 查找 UEMainWindow 或者有窗口标志的顶层窗口
            if parent.isWindow() and parent.isVisible():
                main_window = parent
                break
            parent = parent.parent()
        
        logger.info(f"找到主窗口: {main_window}")
        
        if main_window:
            # 使用主窗口的屏幕坐标进行居中
            main_geo = main_window.frameGeometry()
            
            dialog_width = self.width()
            dialog_height = self.height()
            
            logger.info(f"主窗口几何: x={main_geo.x()}, y={main_geo.y()}, w={main_geo.width()}, h={main_geo.height()}")
            logger.info(f"对话框尺寸: w={dialog_width}, h={dialog_height}")
            
            # 计算对话框应该出现的位置（相对于主窗口居中）
            dialog_x = main_geo.x() + (main_geo.width() - dialog_width) // 2
            dialog_y = main_geo.y() + (main_geo.height() - dialog_height) // 2
            
            # 移动对话框到计算出的位置
            self.move(dialog_x, dialog_y)
            logger.info(f"对话框已居中到: ({dialog_x}, {dialog_y})")
        else:
            # 如果没有找到主窗口，相对于屏幕居中
            logger.info("未找到主窗口，使用屏幕居中")
            screen = QApplication.primaryScreen()
            if screen:
                screen_geo = screen.availableGeometry()
                dialog_x = (screen_geo.width() - self.width()) // 2
                dialog_y = (screen_geo.height() - self.height()) // 2
                self.move(dialog_x, dialog_y)
                logger.info(f"对话框相对屏幕居中: ({dialog_x}, {dialog_y})")
    
    def _on_card_clicked(self, project):
        """卡片点击事件"""
        # 取消其他卡片的选中状态
        for card in self.project_cards:
            if card.project == project:
                card.set_selected(True)
                self.selected_project = project
            else:
                card.set_selected(False)
        
        # 启用确定按钮
        self.ok_button.setEnabled(True)
        logger.debug(f"选中工程: {project.name}")
    
    def get_selected_project(self):
        """获取选中的项目"""
        return self.selected_project
    
    def mousePressEvent(self, event):
        """鼠标按下事件 - 用于拖动标题栏"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 检查是否点击在标题栏区域（前30像素高度）
            if event.position().y() < 30:
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 用于拖动窗口"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

