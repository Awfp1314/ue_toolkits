# -*- coding: utf-8 -*-

"""
站点推荐UI界面
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDesktopServices, QFont
from PyQt6.QtCore import QUrl
from typing import Optional, List, Dict

from core.logger import get_logger
from core.utils.theme_manager import get_theme_manager

logger = get_logger(__name__)


class SiteRecommendationsUI(QWidget):
    """站点推荐UI界面"""
    
    def __init__(self, parent=None):
        """初始化UI
        
        Args:
            parent: 父组件
        """
        super().__init__(parent)
        self.logic = None
        self.site_widgets: List[QWidget] = []
        self.theme_manager = get_theme_manager()  # 保存主题管理器引用
        
        self.init_ui()
        logger.info("站点推荐UI初始化完成")
    
    def init_ui(self):
        """初始化UI界面"""
        # 使用 ThemeManager 应用主题
        theme_manager = get_theme_manager()
        theme_manager.apply_to_widget(self)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        self.setLayout(main_layout)
        
        # 描述
        desc_label = QLabel("精选虚幻引擎学习资源、资产商店和开发者社区")
        desc_label.setObjectName("descriptionLabel")
        main_layout.addWidget(desc_label)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("separator")
        separator.setFixedHeight(1)
        main_layout.addWidget(separator)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("scrollArea")
        
        # 站点容器
        self.sites_container = QWidget()
        self.sites_layout = QVBoxLayout()
        self.sites_layout.setContentsMargins(0, 0, 10, 0)
        self.sites_layout.setSpacing(20)
        self.sites_container.setLayout(self.sites_layout)
        
        scroll_area.setWidget(self.sites_container)
        main_layout.addWidget(scroll_area)
    
    def set_logic(self, logic):
        """设置业务逻辑层
        
        Args:
            logic: 业务逻辑对象
        """
        self.logic = logic
    
    def update_sites(self, sites: List[Dict[str, str]]):
        """更新站点显示
        
        Args:
            sites: 站点列表
        """
        # 清空现有站点
        for widget in self.site_widgets:
            widget.deleteLater()
        self.site_widgets.clear()
        
        # 按分类组织站点
        categories = {}
        category_order = ["资源网站", "工具", "论坛", "学习"]
        
        for site in sites:
            category = site.get("category", "其他")
            if category not in categories:
                categories[category] = []
            categories[category].append(site)
        
        # 按照指定顺序显示分类
        for category in category_order:
            if category in categories:
                self._add_category_section(category, categories[category])
        
        # 添加其他未分类的站点
        for category, category_sites in categories.items():
            if category not in category_order:
                self._add_category_section(category, category_sites)
        
        # 添加弹性空间
        self.sites_layout.addStretch()
        
        logger.info(f"更新了 {len(sites)} 个站点")
    
    def _add_category_section(self, category: str, sites: List[Dict[str, str]]):
        """添加分类区域
        
        Args:
            category: 分类名称
            sites: 该分类下的站点列表
        """
        # 分类标题
        category_label = QLabel(category)
        category_font = QFont()
        category_font.setPointSize(13)
        category_font.setBold(True)
        category_label.setFont(category_font)
        category_label.setObjectName("categoryLabel")
        self.sites_layout.addWidget(category_label)
        self.site_widgets.append(category_label)
        
        buttons_container = QWidget()
        buttons_container.setObjectName("buttonsContainer")
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(10)
        buttons_container.setLayout(container_layout)
        
        # 按行添加按钮（每行4个，左对齐）
        current_row_layout = None
        col_count = 0
        
        for site in sites:
            # 如果是新的一行，创建新的水平布局
            if col_count == 0:
                current_row_layout = QHBoxLayout()
                current_row_layout.setContentsMargins(0, 0, 0, 0)
                current_row_layout.setSpacing(10)
                container_layout.addLayout(current_row_layout)
            
            site_button = self._create_site_button(site)
            if current_row_layout is not None:
                current_row_layout.addWidget(site_button)
            self.site_widgets.append(site_button)
            
            col_count += 1
            
            # 每行4个按钮
            if col_count >= 4 and current_row_layout is not None:
                # 行满了，添加弹性空间使按钮左对齐
                current_row_layout.addStretch()
                col_count = 0
        
        # 如果最后一行不满4个按钮，添加弹性空间
        if col_count > 0 and current_row_layout is not None:
            current_row_layout.addStretch()
        
        self.sites_layout.addWidget(buttons_container)
    
    def _create_site_button(self, site: Dict[str, str]) -> QPushButton:
        """创建站点按钮（使用 ThemeManager 统一样式）
        
        Args:
            site: 站点信息
            
        Returns:
            QPushButton: 站点按钮
        """
        button = QPushButton(site.get("name", "未命名站点"))
        
        # 设置固定尺寸
        button.setFixedSize(180, 45)
        
        # 使用 ThemeManager 应用按钮样式
        theme_manager = get_theme_manager()
        theme_manager.apply_to_widget(button, component="buttons")
        
        # 设置工具提示
        description = site.get("description", "")
        url = site.get("url", "")
        tooltip = f"{description}\n\n点击访问: {url}"
        button.setToolTip(tooltip)
        
        # 连接点击事件
        button.clicked.connect(lambda: self._open_url(site.get("url", "")))
        
        return button
    
    def _open_url(self, url: str):
        """打开URL
        
        Args:
            url: 要打开的URL
        """
        if url:
            QDesktopServices.openUrl(QUrl(url))
            logger.info(f"打开URL: {url}")
    
    def refresh_theme(self):
        """刷新主题样式 - 在主题切换时调用"""
        try:
            # 重新应用主题到主界面
            self.theme_manager.apply_to_widget(self)
            
            # 重新应用主题到所有站点按钮
            for widget in self.site_widgets:
                if isinstance(widget, QPushButton):
                    self.theme_manager.apply_to_widget(widget, component="buttons")
            
            logger.info("站点推荐主题已刷新")
            
        except Exception as e:
            logger.error(f"刷新站点推荐主题失败: {e}", exc_info=True)
