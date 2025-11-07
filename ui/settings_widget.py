# -*- coding: utf-8 -*-

"""
设置界面
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFileDialog, QGroupBox, 
                             QFrame, QComboBox, QMessageBox, QScrollArea, QRadioButton,
                             QButtonGroup)
from PyQt6.QtCore import Qt, QStandardPaths
from PyQt6.QtGui import QFont
from pathlib import Path
import json
from core.logger import get_logger
from core.utils.theme_manager import get_theme_manager, Theme
from core.utils.custom_widgets import NoContextMenuLineEdit
from modules.config_tool.ui.dialogs.name_input_dialog import NameInputDialog
from ui.dialogs.close_confirmation_dialog import CloseConfirmationDialog

logger = get_logger(__name__)


class SettingsWidget(QWidget):
    """设置界面Widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.asset_manager_logic = None  # 将在显示时设置
        self.theme_manager = get_theme_manager()  # 获取主题管理器
        
        # 存储额外工程路径的输入框列表
        self.additional_preview_inputs = []
        
        self.init_ui()
        
        # 加载保存的主题设置（在UI创建之后）
        self._load_theme_from_config()
        
        # 加载保存的关闭方式设置
        self._load_close_behavior_from_config()
    
    def init_ui(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setObjectName("settingsScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # 不使用内联样式，让全局QSS生效
        
        # 创建内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)
        
        # 路径设置组
        paths_group = QGroupBox("资产管理路径设置")
        paths_layout = QVBoxLayout()
        paths_layout.setSpacing(15)
        
        # 资产库路径
        self.asset_lib_label = QLabel("资产库路径：")
        paths_layout.addWidget(self.asset_lib_label)
        
        asset_lib_layout = QHBoxLayout()
        asset_lib_layout.setSpacing(10)
        
        self.asset_lib_input = NoContextMenuLineEdit()
        self.asset_lib_input.setPlaceholderText("未设置资产库路径...")
        self.asset_lib_input.setReadOnly(True)
        self.asset_lib_input.setMaximumWidth(500)  # 设置最大宽度
        asset_lib_layout.addWidget(self.asset_lib_input)
        
        browse_asset_btn = QPushButton("浏览...")
        browse_asset_btn.setFixedWidth(80)
        browse_asset_btn.clicked.connect(self._browse_asset_library)
        asset_lib_layout.addWidget(browse_asset_btn)
        asset_lib_layout.addStretch()  # 添加弹性空间
        
        paths_layout.addLayout(asset_lib_layout)
        
        # 预览工程说明标签
        self.preview_info_label = QLabel("⚠️ 预览工程：请通过下方'添加其他工程'添加。首个添加的工程将作为默认预览工程。")
        self.preview_info_label.setStyleSheet("font-size: 12px; color: #FFA500;")
        self.preview_info_label.setWordWrap(True)
        paths_layout.addWidget(self.preview_info_label)
        
        # 额外工程路径容器（用于存放动态添加的路径）
        self.additional_preview_container = QVBoxLayout()
        self.additional_preview_container.setSpacing(15)
        paths_layout.addLayout(self.additional_preview_container)
        
        # 添加其他工程按钮
        add_preview_layout = QHBoxLayout()
        add_preview_layout.setSpacing(10)
        
        add_preview_btn = QPushButton("➕ 添加工程")
        add_preview_btn.setFixedWidth(150)
        add_preview_btn.clicked.connect(self._add_additional_preview_project)
        add_preview_layout.addWidget(add_preview_btn)
        add_preview_layout.addStretch()
        
        paths_layout.addLayout(add_preview_layout)
        
        paths_group.setLayout(paths_layout)
        content_layout.addWidget(paths_group)
        
        theme_group = QGroupBox("主题设置")
        theme_layout = QVBoxLayout()
        theme_layout.setSpacing(15)
        
        self.theme_select_label = QLabel("选择主题：")
        theme_layout.addWidget(self.theme_select_label)
        
        theme_select_layout = QHBoxLayout()
        theme_select_layout.setSpacing(10)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("深色主题", Theme.DARK)
        self.theme_combo.addItem("浅色主题", Theme.LIGHT)
        
        # 添加所有已导入的自定义主题
        self._load_custom_themes_to_combo()
        
        self.theme_combo.setMaximumWidth(200)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        theme_select_layout.addWidget(self.theme_combo)
        theme_select_layout.addStretch()
        
        theme_layout.addLayout(theme_select_layout)
        
        # 自定义主题
        self.custom_theme_label = QLabel("自定义主题：")
        theme_layout.addWidget(self.custom_theme_label)
        
        custom_theme_layout = QHBoxLayout()
        custom_theme_layout.setSpacing(10)
        
        import_theme_btn = QPushButton("导入主题文件...")
        import_theme_btn.setFixedWidth(150)
        import_theme_btn.clicked.connect(self._import_custom_theme)
        custom_theme_layout.addWidget(import_theme_btn)
        
        export_theme_btn = QPushButton("导出当前主题...")
        export_theme_btn.setFixedWidth(150)
        export_theme_btn.clicked.connect(self._export_current_theme)
        custom_theme_layout.addWidget(export_theme_btn)
        
        custom_theme_layout.addStretch()
        
        theme_layout.addLayout(custom_theme_layout)
        
        self.theme_hint_label = QLabel("提示：自定义主题文件为JSON格式，包含主题变量定义。")
        self.theme_hint_label.setStyleSheet("font-size: 12px; padding-top: 5px;")
        self.theme_hint_label.setWordWrap(True)
        theme_layout.addWidget(self.theme_hint_label)
        
        theme_group.setLayout(theme_layout)
        content_layout.addWidget(theme_group)
        
        # 关闭方式设置组
        close_behavior_group = QGroupBox("关闭方式设置")
        close_behavior_layout = QVBoxLayout()
        close_behavior_layout.setSpacing(15)
        
        close_behavior_label = QLabel("选择点击关闭按钮时的行为：")
        close_behavior_layout.addWidget(close_behavior_label)
        
        # 单选按钮组 - 放在同一行
        radio_layout = QHBoxLayout()
        radio_layout.setSpacing(20)
        
        self.close_button_group = QButtonGroup(self)
        
        self.close_directly_radio = QRadioButton("直接关闭程序")
        self.close_button_group.addButton(self.close_directly_radio, CloseConfirmationDialog.RESULT_CLOSE)
        radio_layout.addWidget(self.close_directly_radio)
        
        self.minimize_to_tray_radio = QRadioButton("最小化到系统托盘")
        self.close_button_group.addButton(self.minimize_to_tray_radio, CloseConfirmationDialog.RESULT_MINIMIZE)
        radio_layout.addWidget(self.minimize_to_tray_radio)
        
        self.ask_every_time_radio = QRadioButton("每次询问（默认）")
        self.close_button_group.addButton(self.ask_every_time_radio, 0)
        self.ask_every_time_radio.setChecked(True)  # 默认选中
        radio_layout.addWidget(self.ask_every_time_radio)
        
        radio_layout.addStretch()  # 添加弹性空间
        close_behavior_layout.addLayout(radio_layout)
        
        # 连接信号
        self.close_button_group.idClicked.connect(self._on_close_behavior_changed)
        
        close_behavior_hint = QLabel("提示：更改设置后将立即生效。")
        close_behavior_hint.setStyleSheet("font-size: 12px; padding-top: 5px;")
        close_behavior_hint.setWordWrap(True)
        close_behavior_layout.addWidget(close_behavior_hint)
        
        close_behavior_group.setLayout(close_behavior_layout)
        content_layout.addWidget(close_behavior_group)
        
        # AI 助手设置组
        ai_assistant_group = self._create_ai_assistant_settings()
        content_layout.addWidget(ai_assistant_group)
        
        content_layout.addStretch()
        
        # 设置内容容器的布局
        content_widget.setLayout(content_layout)
        
        # 将内容容器添加到滚动区域
        scroll_area.setWidget(content_widget)
        
        # 将滚动区域添加到主布局
        main_layout.addWidget(scroll_area)
        
        self.setLayout(main_layout)
        
        # 应用动态主题样式（在所有UI元素创建之后）
        self._apply_theme_style()
        
        logger.info("设置界面初始化完成")
    
    def _apply_theme_style(self):
        """应用动态主题样式"""
        tm = self.theme_manager
        
        style = f"""
            QWidget {{
                background-color: {tm.get_variable('bg_primary')};
            }}
            QLabel {{
                color: {tm.get_variable('text_primary')};
                font-size: 14px;
            }}
            QGroupBox {{
                color: {tm.get_variable('text_primary')};
                font-size: 15px;
                font-weight: bold;
                border: 1px solid {tm.get_variable('border')};
                border-radius: 6px;
                margin-top: 15px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                color: {tm.get_variable('info')};
            }}
            QLineEdit {{
                background-color: {tm.get_variable('bg_secondary')};
                border: 1px solid {tm.get_variable('border')};
                border-radius: 4px;
                padding: 8px;
                color: {tm.get_variable('text_primary')};
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {tm.get_variable('border_focus')};
            }}
            QLineEdit:disabled {{
                background-color: {tm.get_variable('bg_primary')};
                color: {tm.get_variable('text_disabled')};
            }}
            QComboBox {{
                background-color: {tm.get_variable('bg_secondary')};
                border: 1px solid {tm.get_variable('border')};
                border-radius: 4px;
                padding: 8px;
                color: {tm.get_variable('text_primary')};
                font-size: 13px;
            }}
            QComboBox:hover {{
                border: 1px solid {tm.get_variable('border_hover')};
            }}
            QComboBox:focus {{
                border: 1px solid {tm.get_variable('border_focus')};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {tm.get_variable('text_primary')};
                margin-right: 5px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {tm.get_variable('bg_secondary')};
                border: 1px solid {tm.get_variable('border')};
                selection-background-color: {tm.get_variable('accent')};
                selection-color: {tm.get_variable('text_primary')};
                color: {tm.get_variable('text_primary')};
            }}
            QPushButton {{
                background-color: {tm.get_variable('bg_tertiary')};
                color: {tm.get_variable('text_primary')};
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {tm.get_variable('bg_hover')};
            }}
            QPushButton:pressed {{
                background-color: {tm.get_variable('bg_pressed')};
            }}
            QPushButton#SaveButton {{
                background-color: {tm.get_variable('info')};
            }}
            QPushButton#SaveButton:hover {{
                background-color: {tm.get_variable('border_hover')};
            }}
            QPushButton#SaveButton:pressed {{
                background-color: {tm.get_variable('accent_pressed')};
            }}
            
            /* 滚动条样式 */
            QScrollArea#settingsScrollArea {{
                background-color: transparent;
                border: none;
            }}
            
            QScrollArea#settingsScrollArea > QWidget,
            QScrollArea#settingsScrollArea QWidget#qt_scrollarea_viewport {{
                background-color: transparent;
            }}
            
            QScrollArea#settingsScrollArea QScrollBar:vertical {{
                background: {tm.get_variable('scrollbar_track')};
                width: 12px;
                border-radius: 6px;
            }}
            
            QScrollArea#settingsScrollArea QScrollBar::handle:vertical {{
                background: {tm.get_variable('scrollbar_handle')};
                border-radius: 6px;
                min-height: 20px;
            }}
            
            QScrollArea#settingsScrollArea QScrollBar::handle:vertical:hover {{
                background: {tm.get_variable('scrollbar_handle_hover')};
            }}
            
            QScrollArea#settingsScrollArea QScrollBar::handle:vertical:pressed {{
                background: {tm.get_variable('scrollbar_handle_pressed')};
            }}
            
            QScrollArea#settingsScrollArea QScrollBar::add-line:vertical,
            QScrollArea#settingsScrollArea QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
                height: 0px;
            }}
            
            QScrollArea#settingsScrollArea QScrollBar::add-page:vertical,
            QScrollArea#settingsScrollArea QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """
        
        self.setStyleSheet(style)
        
        # 单独更新提示标签的颜色（使用浅灰色，其他标签使用默认主要文本颜色）
        if hasattr(self, 'theme_hint_label'):
            self.theme_hint_label.setStyleSheet(f"font-size: 12px; color: {tm.get_variable('text_tertiary')}; padding-top: 5px;")
        
        logger.debug("设置界面样式已更新")
    
    def set_asset_manager_logic(self, logic):
        """设置资产管理器逻辑层引用
        
        Args:
            logic: AssetManagerLogic 实例
        """
        self.asset_manager_logic = logic
        self._load_current_paths()
    
    def _load_current_paths(self):
        """加载当前路径设置"""
        if not self.asset_manager_logic:
            logger.debug("资产管理器未初始化，跳过加载路径")
            return
        
        try:
            logger.info("开始加载当前路径设置...")
            
            lib_path = self.asset_manager_logic.get_asset_library_path()
            logger.info(f"从logic获取到资产库路径: {lib_path} (类型: {type(lib_path)})")
            
            if lib_path:
                path_str = str(lib_path)
                self.asset_lib_input.setText(path_str)
                logger.info(f"✓ 已加载资产库路径到输入框: {path_str}")
            else:
                self.asset_lib_input.setText("")
                logger.warning("✗ 资产库路径为空或None")
            
            # 加载额外的预览工程路径
            self._load_additional_preview_projects()
            
            logger.info("路径加载完成")
            
        except Exception as e:
            logger.error(f"加载路径设置失败: {e}", exc_info=True)
    
    def _load_additional_preview_projects(self):
        """加载额外的预览工程路径"""
        try:
            if not self.asset_manager_logic:
                return
            
            # 从配置中加载额外的预览工程路径（带名称）
            additional_projects = self.asset_manager_logic.get_additional_preview_projects_with_names()
            
            # 清空现有的输入框
            self._clear_additional_preview_inputs()
            
            # 添加加载的路径
            for project in additional_projects:
                path_str = project.get("path", "")
                name = project.get("name", "")
                self._add_additional_preview_project_with_data(path_str, name)
            
            logger.info(f"已加载 {len(additional_projects)} 个额外预览工程")
            
        except Exception as e:
            logger.error(f"加载额外预览工程路径失败: {e}", exc_info=True)
    
    def _clear_additional_preview_inputs(self):
        """清空额外的预览工程路径输入框"""
        for input_field, container_layout in self.additional_preview_inputs:
            # 删除布局中的所有控件
            while container_layout.count():
                item = container_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # 从容器中移除这个布局
            self.additional_preview_container.removeItem(container_layout)
        
        self.additional_preview_inputs.clear()
    
    def _add_additional_preview_project(self):
        """添加新的预览工程路径（交互式）"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择预览工程文件夹",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder:
            logger.info(f"选择预览工程路径: {folder}")
            
            # 弹出命名对话框
            name_dialog = NameInputDialog(self)
            name_dialog.name_input.setPlaceholderText("请输入工程名称")
            
            # 获取已有的名称列表，防止重复
            existing_projects = self.asset_manager_logic.get_additional_preview_projects_with_names()
            existing_names = [p.get("name", "") for p in existing_projects]
            name_dialog.set_existing_names(existing_names)
            
            if name_dialog.exec() == QFileDialog.DialogCode.Accepted:
                project_name = name_dialog.get_config_name()
                if project_name:
                    self._add_additional_preview_project_with_data(folder, project_name)
                    self._save_additional_preview_projects()
                    logger.info(f"已添加工程: {project_name} -> {folder}")
            else:
                logger.info("用户取消了命名对话框")
    
    def _add_additional_preview_project_with_path(self, path_str: str):
        """使用给定的路径添加额外预览工程
        
        Args:
            path_str: 预览工程路径字符串
        """
        # 创建新的输入框容器
        container_layout = QHBoxLayout()
        container_layout.setSpacing(10)
        
        # 标签
        label = QLabel(f"额外工程 {len(self.additional_preview_inputs) + 1}：")
        container_layout.addWidget(label)
        
        # 输入框
        input_field = NoContextMenuLineEdit()
        input_field.setPlaceholderText("未设置预览工程路径...")
        input_field.setReadOnly(True)
        input_field.setMaximumWidth(500)
        input_field.setText(path_str)
        container_layout.addWidget(input_field)
        
        # 浏览按钮
        browse_btn = QPushButton("浏览...")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(lambda: self._browse_additional_preview_project(input_field))
        container_layout.addWidget(browse_btn)
        
        # 删除按钮
        remove_btn = QPushButton("✖ 移除")
        remove_btn.setFixedWidth(80)
        remove_btn.clicked.connect(lambda: self._remove_additional_preview_project(input_field, container_layout))
        container_layout.addWidget(remove_btn)
        
        container_layout.addStretch()
        
        # 添加到容器
        self.additional_preview_container.addLayout(container_layout)
        self.additional_preview_inputs.append((input_field, container_layout))
        
        logger.info(f"已添加额外预览工程路径输入框: {path_str}")
    
    def _add_additional_preview_project_with_data(self, path_str: str, name: str):
        """使用给定的路径和名称添加额外预览工程
        
        Args:
            path_str: 预览工程路径字符串
            name: 工程自定义名称
        """
        # 创建新的输入框容器
        container_layout = QHBoxLayout()
        container_layout.setSpacing(10)
        
        # 标签（显示自定义名称）
        label = QLabel(f"{name}：")
        container_layout.addWidget(label)
        
        # 输入框（显示路径，只读）
        input_field = NoContextMenuLineEdit()
        input_field.setPlaceholderText("工程路径...")
        input_field.setReadOnly(True)
        input_field.setMaximumWidth(500)
        input_field.setText(path_str)
        # 存储路径用于保存
        input_field.path = path_str
        input_field.name = name
        container_layout.addWidget(input_field)
        
        # 浏览按钮
        browse_btn = QPushButton("浏览...")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(lambda: self._browse_additional_preview_project(input_field))
        container_layout.addWidget(browse_btn)
        
        # 重命名按钮
        rename_btn = QPushButton("📝 重命名")
        rename_btn.setFixedWidth(100)
        rename_btn.clicked.connect(lambda: self._rename_additional_preview_project(input_field, label, container_layout))
        container_layout.addWidget(rename_btn)
        
        # 删除按钮
        remove_btn = QPushButton("✖ 移除")
        remove_btn.setFixedWidth(80)
        remove_btn.clicked.connect(lambda: self._remove_additional_preview_project(input_field, container_layout))
        container_layout.addWidget(remove_btn)
        
        container_layout.addStretch()
        
        # 添加到容器
        self.additional_preview_container.addLayout(container_layout)
        self.additional_preview_inputs.append((input_field, container_layout))
        
        logger.info(f"已添加额外预览工程: {name} -> {path_str}")
    
    def _browse_additional_preview_project(self, input_field: NoContextMenuLineEdit):
        """浏览额外预览工程文件夹
        
        Args:
            input_field: 输入框控件
        """
        current_path = input_field.text() or ""
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择预览工程文件夹",
            current_path,
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder:
            input_field.setText(folder)
            logger.info(f"选择额外预览工程路径: {folder}")
            self._save_additional_preview_projects()
    
    def _remove_additional_preview_project(self, input_field: NoContextMenuLineEdit, container_layout: QHBoxLayout):
        """移除额外预览工程路径
        
        Args:
            input_field: 输入框控件
            container_layout: 容器布局
        """
        # 从列表中移除
        self.additional_preview_inputs = [
            (field, layout) for field, layout in self.additional_preview_inputs
            if field is not input_field
        ]
        
        # 从UI中移除
        input_field.deleteLater()
        
        # 移除布局中的所有控件
        while container_layout.count():
            item = container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 从additional_preview_container中移除
        self.additional_preview_container.removeItem(container_layout)
        
        logger.info("已移除额外预览工程路径")
        self._save_additional_preview_projects()
    
    def _rename_additional_preview_project(self, input_field: NoContextMenuLineEdit, label: QLabel, container_layout: QHBoxLayout):
        """重命名额外预览工程
        
        Args:
            input_field: 输入框控件
            label: 标签控件
            container_layout: 容器布局
        """
        # 弹出命名对话框
        name_dialog = NameInputDialog(self)
        name_dialog.name_input.setPlaceholderText("请输入新的工程名称")
        name_dialog.name_input.setText(input_field.name)
        
        # 获取已有的名称列表（除了当前名称），防止重复
        existing_projects = self.asset_manager_logic.get_additional_preview_projects_with_names()
        existing_names = [p.get("name", "") for p in existing_projects if p.get("name", "") != input_field.name]
        name_dialog.set_existing_names(existing_names)
        
        if name_dialog.exec() == QFileDialog.DialogCode.Accepted:
            new_name = name_dialog.get_config_name()
            if new_name:
                # 更新标签显示
                label.setText(f"{new_name}：")
                # 更新输入框的名称属性
                input_field.name = new_name
                logger.info(f"已重命名工程: {input_field.name} -> {new_name}")
                self._save_additional_preview_projects()
        else:
            logger.info("用户取消了重命名")
    
    def _save_additional_preview_projects(self):
        """保存所有额外预览工程路径和名称"""
        if not self.asset_manager_logic:
            logger.warning("资产管理器未初始化，无法保存额外预览工程")
            return
        
        try:
            # 收集所有路径和名称
            projects = []
            for input_field, _ in self.additional_preview_inputs:
                path_str = getattr(input_field, 'path', input_field.text())
                name = getattr(input_field, 'name', "")
                
                if path_str and name:
                    projects.append({
                        "path": path_str,
                        "name": name
                    })
            
            # 调用logic层保存
            self.asset_manager_logic.set_additional_preview_projects_with_names(projects)
            
            logger.info(f"已保存 {len(projects)} 个额外预览工程")
            
        except Exception as e:
            logger.error(f"保存额外预览工程路径失败: {e}", exc_info=True)
            QMessageBox.warning(self, "警告", f"保存额外预览工程路径失败: {str(e)}")
    
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
            
            # 立即保存路径
            self._save_asset_library_path(folder)
    
    def _save_asset_library_path(self, path_str: str):
        """保存资产库路径
        
        Args:
            path_str: 资产库路径字符串
        """
        if not self.asset_manager_logic:
            QMessageBox.information(
                self,
                "提示",
                "资产管理器尚未加载。\n请先切换到资产管理器模块，然后再回到设置界面设置路径。"
            )
            return
        
        try:
            if path_str and path_str.strip():
                lib_path = Path(path_str.strip())
                if self.asset_manager_logic.set_asset_library_path(lib_path):
                    logger.info(f"资产库路径已保存: {lib_path}")
                    
                    # 触发资产管理器UI刷新
                    self._refresh_asset_manager_ui()
                    
                    # 不再显示成功提示框，静默完成
                    logger.info("资产库路径保存成功，已触发UI刷新")
                else:
                    QMessageBox.warning(self, "警告", "保存资产库路径失败")
        except Exception as e:
            logger.error(f"保存资产库路径失败: {e}", exc_info=True)
            QMessageBox.critical(self, "错误", f"保存资产库路径失败：{str(e)}")
    
    def _refresh_asset_manager_ui(self):
        """刷新资产管理器UI（重新扫描并加载资产）"""
        try:
            main_window = self.window()
            if not main_window:
                logger.warning("无法获取主窗口，跳过UI刷新")
                return
            
            if hasattr(main_window, 'module_provider') and main_window.module_provider:
                asset_manager_module = main_window.module_provider.get_module("asset_manager")
                
                if asset_manager_module and hasattr(asset_manager_module, 'instance'):
                    module_instance = asset_manager_module.instance
                    
                    # 刷新UI显示（set_asset_library_path已经调用了_load_config）
                    if hasattr(module_instance, 'ui') and module_instance.ui:
                        asset_manager_ui = module_instance.ui
                        
                        # 使用与分类管理相同的回调方法
                        if hasattr(asset_manager_ui, '_on_categories_updated'):
                            logger.info("刷新分类下拉框和资产显示...")
                            asset_manager_ui._on_categories_updated()
                            logger.info("✓ 资产管理器UI刷新完成")
                        else:
                            logger.warning("资产管理器UI没有_on_categories_updated方法")
                    else:
                        logger.debug("资产管理器UI尚未创建，配置已重新加载，切换到资产管理器时会自动应用")
                else:
                    logger.warning("无法获取资产管理器模块实例")
            else:
                logger.warning("module_provider 不可用")
                
        except Exception as e:
            logger.error(f"刷新资产管理器UI失败: {e}", exc_info=True)
    
    def _load_custom_themes_to_combo(self):
        """加载所有自定义主题到下拉框"""
        custom_theme_names = self.theme_manager.get_custom_theme_names()
        
        for theme_name in custom_theme_names:
            # 使用主题名称作为显示文本和数据
            display_name = f"自定义: {theme_name}"
            self.theme_combo.addItem(display_name, f"custom:{theme_name}")
        
        logger.debug(f"已加载 {len(custom_theme_names)} 个自定义主题到下拉框")
    
    def _refresh_custom_themes_combo(self):
        """刷新下拉框中的自定义主题列表"""
        # 移除所有自定义主题项（保留"深色主题"和"浅色主题"）
        items_to_remove = []
        for i in range(self.theme_combo.count()):
            item_data = self.theme_combo.itemData(i)
            if isinstance(item_data, str) and item_data.startswith("custom:"):
                items_to_remove.append(i)
        
        # 从后往前删除，避免索引问题
        for i in reversed(items_to_remove):
            self.theme_combo.removeItem(i)
        
        # 重新加载自定义主题
        self._load_custom_themes_to_combo()
    
    def _load_current_theme(self):
        """加载当前主题设置"""
        try:
            current_theme = self.theme_manager.get_theme()
            
            if current_theme == Theme.CUSTOM:
                # 如果是自定义主题，需要匹配具体的主题名称
                custom_theme_name = self.theme_manager.current_custom_theme_name
                if custom_theme_name:
                    target_data = f"custom:{custom_theme_name}"
                    for i in range(self.theme_combo.count()):
                        if self.theme_combo.itemData(i) == target_data:
                            self.theme_combo.blockSignals(True)
                            self.theme_combo.setCurrentIndex(i)
                            self.theme_combo.blockSignals(False)
                            return
            else:
                # 内置主题
                for i in range(self.theme_combo.count()):
                    theme_data = self.theme_combo.itemData(i)
                    if theme_data == current_theme:
                        self.theme_combo.blockSignals(True)
                        self.theme_combo.setCurrentIndex(i)
                        self.theme_combo.blockSignals(False)
                        break
            
            logger.debug(f"已加载当前主题设置: {current_theme.value}")
        except Exception as e:
            logger.error(f"加载主题设置失败: {e}", exc_info=True)
    
    def _on_theme_changed(self, index: int):
        """主题切换事件处理
        
        Args:
            index: 下拉框索引
        """
        try:
            theme_data = self.theme_combo.itemData(index)
            if theme_data is None:
                return
            
            if isinstance(theme_data, str) and theme_data.startswith("custom:"):
                # 提取主题名称
                theme_name = theme_data.split(":", 1)[1]
                
                # 切换到自定义主题
                self.theme_manager.set_custom_theme_by_name(theme_name)
                logger.info(f"切换到自定义主题: {theme_name}")
                
                self._apply_theme_to_app()
                
                self._save_theme_setting(f"custom:{theme_name}")
            else:
                # 内置主题
                self.theme_manager.set_theme(theme_data)
                logger.info(f"切换主题到: {theme_data.value}")
                
                self._apply_theme_to_app()
                
                self._save_theme_setting(theme_data.value)
                
        except Exception as e:
            logger.error(f"切换主题失败: {e}", exc_info=True)
            QMessageBox.critical(self, "错误", f"切换主题失败：{str(e)}")
            self._load_current_theme()
    
    def _import_custom_theme(self):
        """导入自定义主题"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "选择主题文件",
                "",
                "JSON 文件 (*.json);;所有文件 (*.*)"
            )
            
            if not file_path:
                return
            
            theme_path = Path(file_path)
            theme_name = self.theme_manager.import_theme(theme_path)
            
            logger.info(f"导入主题文件: {theme_path}, 主题名称: {theme_name}")
            
            self._refresh_custom_themes_combo()
            
            # 询问是否立即应用
            reply = QMessageBox.question(
                self,
                "导入成功",
                f"主题 '{theme_name}' 导入成功！\n\n是否立即应用此主题？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # 切换到新导入的自定义主题
                self.theme_manager.set_custom_theme_by_name(theme_name)
                self._apply_theme_to_app()
                
                # 在下拉框中选中新导入的主题
                target_data = f"custom:{theme_name}"
                for i in range(self.theme_combo.count()):
                    if self.theme_combo.itemData(i) == target_data:
                        self.theme_combo.blockSignals(True)
                        self.theme_combo.setCurrentIndex(i)
                        self.theme_combo.blockSignals(False)
                        break
                
                self._save_theme_setting(f"custom:{theme_name}")
                
                QMessageBox.information(
                    self,
                    "成功",
                    f"主题 '{theme_name}' 已应用！"
                )
            else:
                # 即使不立即应用，也要在下拉框中选中它以便用户知道它在那里
                logger.info(f"主题已导入但未应用，可在下拉框中选择")
                
        except Exception as e:
            logger.error(f"导入主题失败: {e}", exc_info=True)
            QMessageBox.critical(self, "错误", f"导入主题失败：{str(e)}")
    
    def _export_current_theme(self):
        """导出当前主题"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存主题文件",
                f"theme_{self.theme_manager.get_theme().value}.json",
                "JSON 文件 (*.json);;所有文件 (*.*)"
            )
            
            if not file_path:
                return
            
            # 导出主题
            theme_path = Path(file_path)
            self.theme_manager.export_theme(theme_path)
            
            logger.info(f"导出主题到: {theme_path}")
            
            QMessageBox.information(
                self,
                "成功",
                f"主题已成功导出到：\n{theme_path}"
            )
            
        except Exception as e:
            logger.error(f"导出主题失败: {e}", exc_info=True)
            QMessageBox.critical(self, "错误", f"导出主题失败：{str(e)}")
    
    def _apply_theme_to_app(self):
        """应用主题到整个应用"""
        try:
            # 首先应用到整个 QApplication（重新加载全局 QSS，包括滚动条样式）
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                self.theme_manager.apply_to_application(app)
                logger.info("主题已应用到整个应用")
            
            main_window = self.window()
            
            if main_window:
                # 然后应用到主窗口（对于特定样式）
                self.theme_manager.apply_to_widget(main_window)
                logger.info("主题已应用到主窗口")
                
                self._apply_theme_style()
                
                main_window.update()
                
                # 如果主窗口有module_ui_map，刷新所有模块UI
                if hasattr(main_window, 'module_ui_map'):
                    for module_name, module_widget in main_window.module_ui_map.items():
                        if module_widget:
                            # 调用模块特定的刷新方法（如果存在）
                            if hasattr(module_widget, 'refresh_theme'):
                                module_widget.refresh_theme()
                                logger.debug(f"已刷新模块主题: {module_name}")
                            else:
                                module_widget.update()
                                logger.debug(f"刷新模块UI: {module_name}")
                
                # 如果有settings_widget，也刷新它
                if hasattr(main_window, 'settings_widget') and main_window.settings_widget:
                    main_window.settings_widget._apply_theme_style()
                    logger.debug("已刷新设置界面样式")
                
                if hasattr(main_window, 'title_bar') and main_window.title_bar:
                    if hasattr(main_window.title_bar, 'refresh_theme'):
                        main_window.title_bar.refresh_theme()
                        logger.debug("已刷新标题栏主题")
                
                # 特别处理资产管理器
                if hasattr(main_window, 'module_provider'):
                    try:
                        asset_manager = main_window.module_provider.get_module("asset_manager")
                        if asset_manager and hasattr(asset_manager, 'ui') and hasattr(asset_manager.ui, 'refresh_theme'):
                            asset_manager.ui.refresh_theme()
                            logger.info("已刷新资产管理器主题")
                    except Exception as e:
                        logger.warning(f"刷新资产管理器主题失败: {e}")
                    
                    # 特别处理AI助手
                    try:
                        ai_assistant = main_window.module_provider.get_module("ai_assistant")
                        if ai_assistant and hasattr(ai_assistant, 'chat_window') and ai_assistant.chat_window:
                            if hasattr(ai_assistant.chat_window, 'refresh_theme'):
                                ai_assistant.chat_window.refresh_theme()
                                logger.info("已刷新AI助手主题")
                    except Exception as e:
                        logger.warning(f"刷新AI助手主题失败: {e}")
                
        except Exception as e:
            logger.error(f"应用主题失败: {e}", exc_info=True)
    
    def _get_config_path(self) -> Path:
        """获取主题配置文件路径
        
        Returns:
            Path: 配置文件路径
        """
        # 使用 AppData/Roaming/ue_toolkit 作为配置目录
        app_data = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        config_dir = Path(app_data) / "ue_toolkit"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "ui_settings.json"
    
    def _save_theme_setting(self, theme_name: str):
        """保存主题设置到配置文件
        
        Args:
            theme_name: 主题名称
        """
        try:
            config_path = self._get_config_path()
            
            # 读取现有配置（如果存在）
            config = {}
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                except Exception as e:
                    logger.warning(f"读取配置文件失败，将创建新配置: {e}")
            
            config['theme'] = theme_name
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"主题设置已保存到配置文件: {theme_name}")
            
        except Exception as e:
            logger.error(f"保存主题设置失败: {e}", exc_info=True)
    
    def _load_theme_from_config(self):
        """从配置文件加载主题设置"""
        try:
            config_path = self._get_config_path()
            
            if not config_path.exists():
                logger.debug("配置文件不存在，使用默认主题")
                # 即使没有配置文件，也要在下拉框中选中默认主题
                self._load_current_theme()
                return
            
            # 读取配置
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            theme_name = config.get('theme')
            if not theme_name:
                logger.debug("配置中没有主题设置")
                # 即使没有主题设置，也要在下拉框中选中默认主题
                self._load_current_theme()
                return
            
            # 根据主题名称设置主题
            if theme_name == 'dark':
                self.theme_manager.set_theme(Theme.DARK)
            elif theme_name == 'light':
                self.theme_manager.set_theme(Theme.LIGHT)
            elif theme_name.startswith('custom:'):
                # 自定义主题：格式为 "custom:theme_name"
                custom_theme_name = theme_name.split(":", 1)[1]
                try:
                    self.theme_manager.set_custom_theme_by_name(custom_theme_name)
                    logger.info(f"已从配置加载自定义主题: {custom_theme_name}")
                except ValueError as e:
                    logger.warning(f"自定义主题 '{custom_theme_name}' 不存在，使用默认主题: {e}")
                    self.theme_manager.set_theme(Theme.DARK)
            elif theme_name == 'custom':
                # 兼容旧配置格式
                self.theme_manager.set_theme(Theme.CUSTOM)
            else:
                logger.warning(f"未知的主题名称: {theme_name}，使用默认主题")
                self.theme_manager.set_theme(Theme.DARK)
            
            logger.info(f"已从配置加载主题: {theme_name}")
            
            # 在下拉框中选中当前主题
            self._load_current_theme()
            
        except Exception as e:
            logger.error(f"加载主题设置失败: {e}", exc_info=True)
            # 即使加载失败，也要在下拉框中选中默认主题
            self._load_current_theme()
    
    def _on_close_behavior_changed(self, button_id: int):
        """关闭方式选项变更时的处理
        
        Args:
            button_id: 按钮ID (0=每次询问, 1=直接关闭, 2=最小化到托盘)
        """
        try:
            logger.info(f"用户选择了关闭方式: {button_id}")
            
            # 保存到配置文件
            self._save_close_behavior_setting(button_id)
            
            # 更新主窗口的关闭行为偏好
            main_window = self.window()
            if hasattr(main_window, '_close_action_preference'):
                if button_id == CloseConfirmationDialog.RESULT_CLOSE:
                    main_window._close_action_preference = "close"
                    logger.info("关闭方式已设置为：直接关闭")
                elif button_id == CloseConfirmationDialog.RESULT_MINIMIZE:
                    main_window._close_action_preference = "minimize"
                    logger.info("关闭方式已设置为：最小化到托盘")
                else:  # 0 = 每次询问
                    main_window._close_action_preference = None
                    logger.info("关闭方式已设置为：每次询问")
            
        except Exception as e:
            logger.error(f"保存关闭方式设置失败: {e}", exc_info=True)
    
    def _save_close_behavior_setting(self, button_id: int):
        """保存关闭方式设置到配置文件
        
        Args:
            button_id: 按钮ID
        """
        try:
            # 使用 ConfigManager 来保存配置
            from core.config.config_manager import ConfigManager
            config_manager = ConfigManager("app")
            
            # 读取现有配置
            config = config_manager.load_user_config()
            
            # 如果配置是空的或者没有版本号，初始化版本号
            if not config or '_version' not in config:
                config['_version'] = "1.0.0"
            
            # 保存关闭方式
            if button_id == CloseConfirmationDialog.RESULT_CLOSE:
                config['close_action_preference'] = "close"
            elif button_id == CloseConfirmationDialog.RESULT_MINIMIZE:
                config['close_action_preference'] = "minimize"
            else:  # 0 = 每次询问
                config['close_action_preference'] = None
            
            # 保存配置
            success = config_manager.save_user_config(config)
            
            if success:
                logger.info(f"关闭方式设置已保存到 app_config: {config['close_action_preference']}")
            else:
                logger.error("保存关闭方式设置失败")
            
        except Exception as e:
            logger.error(f"保存关闭方式设置失败: {e}", exc_info=True)
    
    def _load_close_behavior_from_config(self):
        """从配置文件加载关闭方式设置"""
        try:
            # 使用 ConfigManager 来加载配置
            from core.config.config_manager import ConfigManager
            config_manager = ConfigManager("app")
            
            # 读取配置
            config = config_manager.load_user_config()
            close_preference = config.get('close_action_preference')
            
            if close_preference == "close":
                self.close_directly_radio.setChecked(True)
                logger.info("已从 app_config 加载关闭方式: 直接关闭")
            elif close_preference == "minimize":
                self.minimize_to_tray_radio.setChecked(True)
                logger.info("已从 app_config 加载关闭方式: 最小化到托盘")
            else:
                self.ask_every_time_radio.setChecked(True)
                logger.info("已从 app_config 加载关闭方式: 每次询问")
            
        except Exception as e:
            logger.error(f"加载关闭方式设置失败: {e}", exc_info=True)
    
    def _create_ai_assistant_settings(self) -> QGroupBox:
        """创建 AI 助手设置组"""
        ai_group = QGroupBox("AI 助手设置")
        ai_layout = QVBoxLayout()
        ai_layout.setSpacing(15)
        
        # LLM 供应商选择
        provider_label = QLabel("LLM 供应商：")
        ai_layout.addWidget(provider_label)
        
        provider_layout = QHBoxLayout()
        provider_layout.setSpacing(10)
        
        self.llm_provider_combo = QComboBox()
        self.llm_provider_combo.addItem("API（OpenAI 兼容）", "api")
        self.llm_provider_combo.addItem("Ollama（本地模型）", "ollama")
        self.llm_provider_combo.setMaximumWidth(250)
        self.llm_provider_combo.currentIndexChanged.connect(self._on_llm_provider_changed)
        provider_layout.addWidget(self.llm_provider_combo)
        provider_layout.addStretch()
        
        ai_layout.addLayout(provider_layout)
        
        # API 设置区域（仅 API 模式可见）
        self.api_settings_widget = QWidget()
        api_settings_layout = QVBoxLayout()
        api_settings_layout.setContentsMargins(20, 10, 0, 10)
        api_settings_layout.setSpacing(10)
        
        # API Key
        api_key_label = QLabel("API Key：")
        api_settings_layout.addWidget(api_key_label)
        
        api_key_layout = QHBoxLayout()
        api_key_layout.setSpacing(10)
        
        self.api_key_input = NoContextMenuLineEdit()
        self.api_key_input.setPlaceholderText("输入你的 API Key...")
        self.api_key_input.setEchoMode(NoContextMenuLineEdit.EchoMode.Password)
        self.api_key_input.setMaximumWidth(400)
        api_key_layout.addWidget(self.api_key_input)
        
        show_key_btn = QPushButton("👁")
        show_key_btn.setFixedWidth(40)
        show_key_btn.setCheckable(True)
        show_key_btn.clicked.connect(lambda checked: 
            self.api_key_input.setEchoMode(NoContextMenuLineEdit.EchoMode.Normal if checked 
                                           else NoContextMenuLineEdit.EchoMode.Password))
        api_key_layout.addWidget(show_key_btn)
        api_key_layout.addStretch()
        
        api_settings_layout.addLayout(api_key_layout)
        
        # API URL
        api_url_label = QLabel("API URL：")
        api_settings_layout.addWidget(api_url_label)
        
        api_url_layout = QHBoxLayout()
        api_url_layout.setSpacing(10)
        
        self.api_url_input = NoContextMenuLineEdit()
        self.api_url_input.setPlaceholderText("https://api.openai-hk.com/v1/chat/completions")
        self.api_url_input.setMaximumWidth(500)
        api_url_layout.addWidget(self.api_url_input)
        api_url_layout.addStretch()
        
        api_settings_layout.addLayout(api_url_layout)
        
        # 🔥 API 模型名称
        api_model_label = QLabel("模型名称：")
        api_settings_layout.addWidget(api_model_label)
        
        api_model_layout = QHBoxLayout()
        api_model_layout.setSpacing(10)
        
        self.api_model_input = NoContextMenuLineEdit()
        self.api_model_input.setPlaceholderText("gemini-2.5-flash")
        self.api_model_input.setMinimumWidth(300)
        self.api_model_input.setMaximumWidth(400)
        api_model_layout.addWidget(self.api_model_input)
        api_model_layout.addStretch()
        
        api_settings_layout.addLayout(api_model_layout)
        
        self.api_settings_widget.setLayout(api_settings_layout)
        ai_layout.addWidget(self.api_settings_widget)
        
        # Ollama 设置区域（仅 Ollama 模式可见）
        self.ollama_settings_widget = QWidget()
        ollama_settings_layout = QVBoxLayout()
        ollama_settings_layout.setContentsMargins(20, 10, 0, 10)
        ollama_settings_layout.setSpacing(10)
        
        # Ollama URL
        ollama_url_label = QLabel("Ollama 服务地址：")
        ollama_settings_layout.addWidget(ollama_url_label)
        
        ollama_url_layout = QHBoxLayout()
        ollama_url_layout.setSpacing(10)
        
        self.ollama_url_input = NoContextMenuLineEdit()
        self.ollama_url_input.setPlaceholderText("http://localhost:11434")
        self.ollama_url_input.setMaximumWidth(300)
        ollama_url_layout.addWidget(self.ollama_url_input)
        
        test_ollama_btn = QPushButton("测试连接")
        test_ollama_btn.setFixedWidth(100)
        test_ollama_btn.clicked.connect(self._test_ollama_connection)
        ollama_url_layout.addWidget(test_ollama_btn)
        ollama_url_layout.addStretch()
        
        ollama_settings_layout.addLayout(ollama_url_layout)
        
        # Ollama 模型选择
        ollama_model_label = QLabel("选择模型：")
        ollama_settings_layout.addWidget(ollama_model_label)
        
        ollama_model_layout = QHBoxLayout()
        ollama_model_layout.setSpacing(10)
        
        self.ollama_model_combo = QComboBox()
        self.ollama_model_combo.setEditable(False)  # 🔧 修复：不可编辑，只能选择
        self.ollama_model_combo.setPlaceholderText("扫描中...")
        self.ollama_model_combo.setMinimumWidth(350)  # 🔧 调整：增加最小宽度
        self.ollama_model_combo.setMaximumWidth(450)  # 🔧 调整：增加最大宽度
        ollama_model_layout.addWidget(self.ollama_model_combo)
        
        # 🔧 修复：去掉刷新按钮，改为自动扫描
        # refresh_models_btn = QPushButton("🔄 刷新")
        # refresh_models_btn.setFixedWidth(80)
        # refresh_models_btn.setToolTip("扫描 Ollama 中的可用模型")
        # refresh_models_btn.clicked.connect(self._refresh_ollama_models)
        # ollama_model_layout.addWidget(refresh_models_btn)
        ollama_model_layout.addStretch()
        
        ollama_settings_layout.addLayout(ollama_model_layout)
        
        # 🔥 自动扫描 Ollama 模型
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(200, self._auto_refresh_ollama_models)
        
        # Ollama 状态提示
        self.ollama_status_label = QLabel("")
        self.ollama_status_label.setStyleSheet("font-size: 12px; padding-top: 5px;")
        self.ollama_status_label.setWordWrap(True)
        ollama_settings_layout.addWidget(self.ollama_status_label)
        
        self.ollama_settings_widget.setLayout(ollama_settings_layout)
        ai_layout.addWidget(self.ollama_settings_widget)
        
        # 保存按钮（隐藏，改为自动保存）
        # save_layout = QHBoxLayout()
        # save_layout.setSpacing(10)
        # 
        # save_ai_btn = QPushButton("保存 AI 设置")
        # save_ai_btn.setFixedWidth(150)
        # save_ai_btn.clicked.connect(self._save_ai_assistant_settings)
        # save_layout.addWidget(save_ai_btn)
        # save_layout.addStretch()
        # 
        # ai_layout.addLayout(save_layout)
        
        # 🔥 热切换：连接信号，自动保存
        self.llm_provider_combo.currentIndexChanged.connect(self._auto_save_ai_settings)
        self.api_key_input.textChanged.connect(self._auto_save_ai_settings)
        self.api_url_input.textChanged.connect(self._auto_save_ai_settings)
        self.api_model_input.textChanged.connect(self._auto_save_ai_settings)  # 🔥 新增：API 模型名称
        self.ollama_url_input.textChanged.connect(self._auto_save_ai_settings)
        self.ollama_model_combo.currentTextChanged.connect(self._auto_save_ai_settings)
        
        ai_group.setLayout(ai_layout)
        
        # 延迟加载配置（避免在 UI 创建时阻塞）
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, self._load_ai_assistant_settings)
        
        return ai_group
    
    def _on_llm_provider_changed(self, index):
        """LLM 供应商切换时的处理"""
        provider = self.llm_provider_combo.currentData()
        
        # 显示/隐藏对应的设置区域
        self.api_settings_widget.setVisible(provider == "api")
        self.ollama_settings_widget.setVisible(provider == "ollama")
        
        # 🔥 如果切换到 ollama，自动扫描模型
        if provider == "ollama":
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, self._auto_refresh_ollama_models)
        
        logger.info(f"LLM 供应商切换到: {provider}")
    
    def _auto_save_ai_settings(self):
        """自动保存 AI 设置（热切换，防抖）"""
        # 如果正在加载配置，跳过自动保存
        if hasattr(self, '_loading_config') and self._loading_config:
            return
        
        # 🔥 如果正在刷新模型列表，跳过自动保存
        if hasattr(self, '_refreshing_models') and self._refreshing_models:
            return
        
        # 防抖：延迟保存，避免频繁写入
        if not hasattr(self, '_save_timer'):
            from PyQt6.QtCore import QTimer
            self._save_timer = QTimer()
            self._save_timer.timeout.connect(self._save_ai_assistant_settings_silent)
            self._save_timer.setSingleShot(True)
        
        # 重启计时器（500ms 后保存）
        self._save_timer.start(500)
    
    def _load_ai_assistant_settings(self):
        """从配置加载 AI 助手设置"""
        try:
            from core.config.config_manager import ConfigManager
            from pathlib import Path
            
            # 🔥 禁用自动保存（避免加载时触发）
            self._loading_config = True
            
            # 获取模板文件路径
            template_path = Path(__file__).parent.parent / "modules" / "ai_assistant" / "config_template.json"
            
            # 导入配置模式
            from modules.ai_assistant.config_schema import get_ai_assistant_schema
            
            # 创建 ConfigManager 并传入模板路径和配置模式
            config_manager = ConfigManager(
                "ai_assistant", 
                template_path=template_path,
                config_schema=get_ai_assistant_schema()  # 🔧 修复：添加配置模式
            )
            config = config_manager.get_module_config()
            
            # 加载 LLM 供应商
            provider = config.get("llm_provider", "api")
            index = 0 if provider == "api" else 1
            self.llm_provider_combo.setCurrentIndex(index)
            
            # 加载 API 设置（空字符串回退到默认值）
            api_settings = config.get("api_settings", {})
            api_key = api_settings.get("api_key", "")
            api_url = api_settings.get("api_url", "")
            api_model = api_settings.get("default_model", "")  # 🔥 新增：加载模型名称
            
            self.api_key_input.setText(api_key if api_key else "")
            self.api_url_input.setText(api_url if api_url else "https://api.openai-hk.com/v1/chat/completions")
            self.api_model_input.setText(api_model if api_model else "gemini-2.5-flash")  # 🔥 新增：设置模型名称
            
            # 加载 Ollama 设置（空字符串回退到默认值）
            ollama_settings = config.get("ollama_settings", {})
            ollama_url = ollama_settings.get("base_url", "")
            ollama_model = ollama_settings.get("model_name", "")
            
            self.ollama_url_input.setText(ollama_url if ollama_url else "http://localhost:11434")
            
            # 🔥 保存要选择的模型名称（等待自动扫描后再设置）
            self._saved_ollama_model = ollama_model if ollama_model else None
            
            # 触发显示/隐藏逻辑（会自动触发模型扫描）
            self._on_llm_provider_changed(index)
            
            logger.info(f"已加载 AI 助手设置（供应商: {provider}）")
            
            # 🔥 重新启用自动保存
            self._loading_config = False
        
        except Exception as e:
            logger.error(f"加载 AI 助手设置失败: {e}", exc_info=True)
            self._loading_config = False  # 确保出错时也启用
    
    def _save_ai_assistant_settings(self):
        """保存 AI 助手设置"""
        try:
            from core.config.config_manager import ConfigManager
            from pathlib import Path
            
            # 获取模板文件路径
            template_path = Path(__file__).parent.parent / "modules" / "ai_assistant" / "config_template.json"
            
            # 导入配置模式
            from modules.ai_assistant.config_schema import get_ai_assistant_schema
            
            # 创建 ConfigManager 并传入模板路径和配置模式
            config_manager = ConfigManager(
                "ai_assistant", 
                template_path=template_path,
                config_schema=get_ai_assistant_schema()  # 🔧 修复：添加配置模式
            )
            
            # 获取当前配置
            config = config_manager.get_module_config()
            
            # 更新配置
            provider = self.llm_provider_combo.currentData()
            config["llm_provider"] = provider
            
            # 更新 API 设置（如果输入框为空，保留原值或使用默认值）
            if "api_settings" not in config:
                config["api_settings"] = {}
            
            # 🔥 修复：强制保存所有 API 设置（即使为空）
            api_key = self.api_key_input.text().strip()
            config["api_settings"]["api_key"] = api_key if api_key else ""
            
            api_url = self.api_url_input.text().strip()
            config["api_settings"]["api_url"] = api_url if api_url else "https://api.openai-hk.com/v1/chat/completions"
            
            api_model = self.api_model_input.text().strip()
            config["api_settings"]["default_model"] = api_model if api_model else "gemini-2.5-flash"
            
            # 更新 Ollama 设置（如果输入框为空，保留原值或使用默认值）
            if "ollama_settings" not in config:
                config["ollama_settings"] = {}
            
            ollama_url = self.ollama_url_input.text().strip()
            if ollama_url:  # 只有非空时才更新
                config["ollama_settings"]["base_url"] = ollama_url
            elif "base_url" not in config["ollama_settings"]:
                # 如果从未设置过，使用默认值
                config["ollama_settings"]["base_url"] = "http://localhost:11434"
            
            ollama_model = self.ollama_model_combo.currentText().strip()
            if ollama_model:  # 只有非空时才更新
                config["ollama_settings"]["model_name"] = ollama_model
            elif "model_name" not in config["ollama_settings"]:
                # 如果从未设置过，使用默认值
                config["ollama_settings"]["model_name"] = "llama3"
            
            # 保存配置
            config_manager.save_user_config(config)
            
            # 提示用户
            QMessageBox.information(
                self,
                "保存成功",
                f"AI 助手设置已保存！\n\n当前供应商：{provider}\n\n新设置将在下次对话时生效。"
            )
            
            logger.info(f"AI 助手设置已保存（供应商: {provider}）")
        
        except Exception as e:
            logger.error(f"保存 AI 助手设置失败: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "保存失败",
                f"保存 AI 助手设置时出错：\n\n{str(e)}"
            )
    
    def _save_ai_assistant_settings_silent(self):
        """静默保存 AI 助手设置（热切换，不显示弹窗）"""
        try:
            from core.config.config_manager import ConfigManager
            from pathlib import Path
            
            # 获取模板文件路径
            template_path = Path(__file__).parent.parent / "modules" / "ai_assistant" / "config_template.json"
            
            # 导入配置模式
            from modules.ai_assistant.config_schema import get_ai_assistant_schema
            
            # 创建 ConfigManager 并传入模板路径和配置模式
            config_manager = ConfigManager(
                "ai_assistant", 
                template_path=template_path,
                config_schema=get_ai_assistant_schema()
            )
            
            # 获取当前配置
            config = config_manager.get_module_config()
            
            # 更新配置
            provider = self.llm_provider_combo.currentData()
            config["llm_provider"] = provider
            
            # 更新 API 设置
            if "api_settings" not in config:
                config["api_settings"] = {}
            
            # 🔥 修复：强制保存所有 API 设置（即使为空）
            api_key = self.api_key_input.text().strip()
            config["api_settings"]["api_key"] = api_key if api_key else ""
            
            api_url = self.api_url_input.text().strip()
            config["api_settings"]["api_url"] = api_url if api_url else "https://api.openai-hk.com/v1/chat/completions"
            
            api_model = self.api_model_input.text().strip()
            config["api_settings"]["default_model"] = api_model if api_model else "gemini-2.5-flash"
            
            # 更新 Ollama 设置
            if "ollama_settings" not in config:
                config["ollama_settings"] = {}
            
            ollama_url = self.ollama_url_input.text().strip()
            if ollama_url:
                config["ollama_settings"]["base_url"] = ollama_url
            elif "base_url" not in config["ollama_settings"]:
                config["ollama_settings"]["base_url"] = "http://localhost:11434"
            
            ollama_model = self.ollama_model_combo.currentText().strip()
            if ollama_model:
                config["ollama_settings"]["model_name"] = ollama_model
            elif "model_name" not in config["ollama_settings"]:
                config["ollama_settings"]["model_name"] = "llama3"
            
            # 静默保存配置（不显示弹窗）
            config_manager.save_user_config(config)
            
            logger.info(f"🔥 AI 设置已自动保存（供应商: {provider}）")
        
        except Exception as e:
            logger.error(f"自动保存 AI 助手设置失败: {e}", exc_info=True)
    
    def _test_ollama_connection(self):
        """测试 Ollama 连接"""
        try:
            from modules.ai_assistant.clients import OllamaLLMClient
            
            ollama_config = {
                "base_url": self.ollama_url_input.text() or "http://localhost:11434",
                "model_name": self.ollama_model_combo.currentText() or "llama3"
            }
            
            client = OllamaLLMClient(config=ollama_config)
            
            # 检查服务状态
            if client.check_ollama_status():
                self.ollama_status_label.setText("✅ 连接成功！Ollama 服务正常运行。")
                self.ollama_status_label.setStyleSheet("color: green; font-size: 12px;")
                
                QMessageBox.information(
                    self,
                    "连接成功",
                    f"成功连接到 Ollama 服务！\n\n地址：{ollama_config['base_url']}"
                )
            else:
                self.ollama_status_label.setText("❌ 连接失败。请确保 Ollama 已启动。")
                self.ollama_status_label.setStyleSheet("color: red; font-size: 12px;")
                
                QMessageBox.warning(
                    self,
                    "连接失败",
                    f"无法连接到 Ollama 服务。\n\n请检查：\n1. Ollama 是否已安装并启动\n2. 服务地址是否正确：{ollama_config['base_url']}"
                )
        
        except Exception as e:
            self.ollama_status_label.setText(f"❌ 测试失败：{str(e)}")
            self.ollama_status_label.setStyleSheet("color: red; font-size: 12px;")
            logger.error(f"测试 Ollama 连接失败: {e}", exc_info=True)
    
    def _refresh_ollama_models(self):
        """刷新 Ollama 可用模型列表并更新下拉框"""
        try:
            from modules.ai_assistant.clients import OllamaLLMClient
            
            ollama_config = {
                "base_url": self.ollama_url_input.text() or "http://localhost:11434",
                "model_name": "temp"
            }
            
            client = OllamaLLMClient(config=ollama_config)
            models = client.list_available_models()
            
            if models:
                # 保存当前选择
                current_model = self.ollama_model_combo.currentText()
                
                # 清空并重新填充下拉框
                self.ollama_model_combo.clear()
                for model in models:
                    self.ollama_model_combo.addItem(model)
                
                # 尝试恢复之前的选择
                if current_model:
                    index = self.ollama_model_combo.findText(current_model)
                    if index >= 0:
                        self.ollama_model_combo.setCurrentIndex(index)
                    else:
                        # 如果之前选择的模型不在列表中，设置为第一个
                        self.ollama_model_combo.setCurrentIndex(0)
                
                model_list = "\n".join(f"  - {m}" for m in models)
                self.ollama_status_label.setText(f"✅ 找到 {len(models)} 个模型")
                self.ollama_status_label.setStyleSheet("color: green; font-size: 12px;")
                
                QMessageBox.information(
                    self,
                    "刷新成功",
                    f"找到 {len(models)} 个可用模型：\n\n{model_list}\n\n已更新到下拉列表中，请选择一个。"
                )
                
                logger.info(f"成功刷新 Ollama 模型列表：{len(models)} 个模型")
            else:
                self.ollama_status_label.setText("⚠️ 未找到可用模型。请先下载：ollama pull llama3")
                self.ollama_status_label.setStyleSheet("color: orange; font-size: 12px;")
                
                QMessageBox.warning(
                    self,
                    "无可用模型",
                    "Ollama 中没有可用的模型。\n\n请先下载模型，例如：\n  ollama pull llama3\n  ollama pull mistral\n  ollama pull qwen:0.5b"
                )
        
        except Exception as e:
            self.ollama_status_label.setText(f"❌ 刷新失败：{str(e)}")
            self.ollama_status_label.setStyleSheet("color: red; font-size: 12px;")
            logger.error(f"刷新 Ollama 模型列表失败: {e}", exc_info=True)
    
    def _auto_refresh_ollama_models(self):
        """自动扫描 Ollama 模型列表（静默，不显示弹窗）"""
        try:
            from modules.ai_assistant.clients import OllamaLLMClient
            
            # 🔥 暂时禁用自动保存
            self._refreshing_models = True
            
            ollama_config = {
                "base_url": self.ollama_url_input.text() or "http://localhost:11434",
                "model_name": "temp"
            }
            
            client = OllamaLLMClient(config=ollama_config)
            models = client.list_available_models()
            
            if models:
                # 保存当前选择
                current_model = self.ollama_model_combo.currentText()
                
                # 清空并重新填充下拉框
                self.ollama_model_combo.clear()
                for model in models:
                    self.ollama_model_combo.addItem(model)
                
                # 🔥 优先使用保存的模型名称
                target_model = None
                if hasattr(self, '_saved_ollama_model') and self._saved_ollama_model:
                    target_model = self._saved_ollama_model
                    self._saved_ollama_model = None  # 清除标志
                elif current_model and current_model != "扫描中...":
                    target_model = current_model
                
                # 尝试设置目标模型
                if target_model:
                    index = self.ollama_model_combo.findText(target_model)
                    if index >= 0:
                        self.ollama_model_combo.setCurrentIndex(index)
                    else:
                        # 如果目标模型不在列表中，设置为第一个
                        self.ollama_model_combo.setCurrentIndex(0)
                else:
                    # 如果没有目标模型，设置为第一个
                    self.ollama_model_combo.setCurrentIndex(0)
                
                self.ollama_status_label.setText(f"✅ 已自动扫描到 {len(models)} 个模型")
                self.ollama_status_label.setStyleSheet("color: green; font-size: 12px;")
                
                logger.info(f"🔥 自动扫描 Ollama 模型成功：{len(models)} 个模型")
            else:
                self.ollama_status_label.setText("⚠️ 未找到可用模型。请先下载：ollama pull llama3")
                self.ollama_status_label.setStyleSheet("color: orange; font-size: 12px;")
                logger.warning("自动扫描 Ollama 模型：未找到可用模型")
        
        except Exception as e:
            self.ollama_status_label.setText(f"⚠️ 无法连接到 Ollama（{str(e)[:30]}...）")
            self.ollama_status_label.setStyleSheet("color: orange; font-size: 12px;")
            logger.warning(f"自动扫描 Ollama 模型失败: {e}")
        
        finally:
            # 🔥 重新启用自动保存
            self._refreshing_models = False

