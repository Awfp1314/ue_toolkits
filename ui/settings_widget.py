# -*- coding: utf-8 -*-

"""
设置界面
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFileDialog, QGroupBox, 
                             QFrame, QComboBox, QMessageBox)
from PyQt6.QtCore import Qt, QStandardPaths
from PyQt6.QtGui import QFont
from pathlib import Path
import json
from core.logger import get_logger
from core.utils.theme_manager import get_theme_manager, Theme
from core.utils.custom_widgets import NoContextMenuLineEdit

logger = get_logger(__name__)


class SettingsWidget(QWidget):
    """设置界面Widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.asset_manager_logic = None  # 将在显示时设置
        self.theme_manager = get_theme_manager()  # 获取主题管理器
        
        self.init_ui()
        
        # 加载保存的主题设置（在UI创建之后）
        self._load_theme_from_config()
    
    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
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
        
        # 预览工程路径
        self.preview_label = QLabel("预览工程路径：")
        paths_layout.addWidget(self.preview_label)
        
        preview_layout = QHBoxLayout()
        preview_layout.setSpacing(10)
        
        self.preview_input = NoContextMenuLineEdit()
        self.preview_input.setPlaceholderText("未设置预览工程路径...")
        self.preview_input.setReadOnly(True)
        self.preview_input.setMaximumWidth(500)  # 设置最大宽度
        preview_layout.addWidget(self.preview_input)
        
        browse_preview_btn = QPushButton("浏览...")
        browse_preview_btn.setFixedWidth(80)
        browse_preview_btn.clicked.connect(self._browse_preview_project)
        preview_layout.addWidget(browse_preview_btn)
        preview_layout.addStretch()  # 添加弹性空间
        
        paths_layout.addLayout(preview_layout)
        
        paths_group.setLayout(paths_layout)
        main_layout.addWidget(paths_group)
        
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
        main_layout.addWidget(theme_group)
        
        main_layout.addStretch()
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
            
            preview_path = self.asset_manager_logic.get_preview_project()
            logger.info(f"从logic获取到预览工程路径: {preview_path} (类型: {type(preview_path)})")
            
            if preview_path:
                path_str = str(preview_path)
                self.preview_input.setText(path_str)
                logger.info(f"✓ 已加载预览工程路径到输入框: {path_str}")
            else:
                self.preview_input.setText("")
                logger.warning("✗ 预览工程路径为空或None")
            
            logger.info("路径加载完成")
            
        except Exception as e:
            logger.error(f"加载路径设置失败: {e}", exc_info=True)
    
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
    
    def _browse_preview_project(self):
        """浏览预览工程文件夹"""
        current_path = self.preview_input.text() or ""
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择预览工程文件夹",
            current_path,
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder:
            self.preview_input.setText(folder)
            logger.info(f"选择预览工程路径: {folder}")
            
            # 立即保存路径
            self._save_preview_project_path(folder)
    
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
    
    def _save_preview_project_path(self, path_str: str):
        """保存预览工程路径
        
        Args:
            path_str: 预览工程路径字符串
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
                preview_path = Path(path_str.strip())
                if self.asset_manager_logic.set_preview_project(preview_path):
                    logger.info(f"预览工程路径已保存: {preview_path}")
                    
                    # 不再显示成功提示框，静默完成
                    logger.info("预览工程路径保存成功")
                else:
                    QMessageBox.warning(self, "警告", "保存预览工程路径失败")
        except Exception as e:
            logger.error(f"保存预览工程路径失败: {e}", exc_info=True)
            QMessageBox.critical(self, "错误", f"保存预览工程路径失败：{str(e)}")
    
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
                    
                    # 第一步：让逻辑层重新加载配置和扫描资产
                    if hasattr(module_instance, 'logic') and module_instance.logic:
                        asset_logic = module_instance.logic
                        logger.info("触发资产逻辑层重新加载配置...")
                        
                        # 重新加载配置，这会触发资产库的重新扫描
                        if hasattr(asset_logic, '_load_config'):
                            asset_logic._load_config()
                            logger.info("✓ 资产逻辑层配置重新加载完成")
                        else:
                            logger.warning("资产逻辑层没有_load_config方法")
                    
                    # 第二步：刷新UI显示
                    if hasattr(module_instance, 'ui') and module_instance.ui:
                        asset_manager_ui = module_instance.ui
                        
                        if hasattr(asset_manager_ui, '_refresh_category_combo'):
                            logger.info("刷新分类下拉框...")
                            asset_manager_ui._refresh_category_combo()
                        
                        if hasattr(asset_manager_ui, '_refresh_assets'):
                            logger.info("刷新资产显示...")
                            asset_manager_ui._refresh_assets()
                            logger.info("✓ 资产管理器UI刷新完成")
                        else:
                            logger.warning("资产管理器UI没有_refresh_assets方法")
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
            main_window = self.window()
            
            if main_window:
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

