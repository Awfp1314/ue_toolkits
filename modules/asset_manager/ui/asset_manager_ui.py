# -*- coding: utf-8 -*-

"""
资产管理主界面
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFileDialog, QMessageBox, QScrollArea,
                             QFrame, QGridLayout, QDialog, QComboBox)
from core.utils.custom_widgets import NoContextMenuLineEdit
from PyQt6.QtCore import Qt, pyqtSlot, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from pathlib import Path
import threading

from core.logger import get_logger
from .progress_dialog import ProgressDialog
from core.utils.theme_manager import get_theme_manager
from ..logic.asset_manager_logic import AssetManagerLogic
from ..logic.asset_model import Asset, AssetType
from ..logic.thumbnail_generator import ThumbnailGenerator
from .asset_card import AssetCard
from .dialogs import StyledMessageBox, DescriptionDialog, ConfirmDialog
from .add_asset_dialog import AddAssetDialog
from .category_management_dialog import CategoryManagementDialog
from .first_launch_dialog import FirstLaunchDialog

logger = get_logger(__name__)


class AssetManagerUI(QWidget):
    """资产管理主界面"""
    
    def __init__(self, logic: AssetManagerLogic, parent=None):
        super().__init__(parent)
        self.logic = logic
        self.theme_manager = get_theme_manager()  # 获取主题管理器
        self.asset_cards = {}  # {asset_id: AssetCard}
        self._showing_error = False  # 防止递归显示错误对话框
        self._current_progress_dialog = None  # 当前进度对话框引用
        self.current_category = None  # 当前选中的分类，None表示全部
        self.search_text = ""  # 当前搜索文本
        self.sort_method = "添加时间（最新）"  # 当前排序方式
        
        # 启用拖放
        self.setAcceptDrops(True)
        
        # 连接逻辑层信号
        self._connect_signals()
        
        self._init_ui()
        
        # 检查是否首次启动，如果是则显示首次启动对话框
        self._check_first_launch()
        
        self.logic.get_all_assets()
        self._refresh_assets()
    
    def _connect_signals(self):
        """连接逻辑层信号"""
        self.logic.asset_added.connect(self._on_asset_added)
        self.logic.asset_removed.connect(self._on_asset_removed)
        self.logic.assets_loaded.connect(self._on_assets_loaded)
        # 移除预览启动提示对话框，直接显示进度条即可
        # self.logic.preview_started.connect(self._on_preview_started)
        self.logic.thumbnail_updated.connect(self._on_thumbnail_updated)
        self.logic.error_occurred.connect(self._on_error)
    
    def _build_stylesheet(self):
        """构建统一的样式表
        
        Returns:
            str: 完整的样式表字符串
        """
        tm = self.theme_manager
        return f"""
            /* 主widget和全局对话框样式 */
            QWidget {{
                background-color: transparent;
            }}
            QMessageBox {{
                background-color: {tm.get_variable('bg_secondary')};
            }}
            QMessageBox QLabel {{
                color: {tm.get_variable('text_primary')};
                font-size: 13px;
                min-width: 300px;
            }}
            QMessageBox QPushButton {{
                background-color: {tm.get_variable('info')};
                color: white;
                border: none;
                padding: 6px 20px;
                border-radius: 4px;
                font-size: 13px;
                min-width: 70px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: {tm.get_variable('border_hover')};
            }}
            QMessageBox QPushButton:pressed {{
                background-color: {tm.get_variable('accent_pressed')};
            }}
            
            /* 分类标签 */
            #assetManagerCategoryLabel {{
                color: {tm.get_variable('text_primary')};
                font-size: 13px;
            }}
            
            /* 分类下拉框 */
            #assetManagerCategoryCombo {{
                background-color: {tm.get_variable('bg_tertiary')};
                border: 1px solid {tm.get_variable('border')};
                border-radius: 4px;
                padding: 6px 10px;
                color: {tm.get_variable('text_primary')};
                font-size: 13px;
            }}
            #assetManagerCategoryCombo:hover {{
                border: 1px solid {tm.get_variable('border_hover')};
            }}
            #assetManagerCategoryCombo::drop-down {{
                border: none;
                width: 30px;
            }}
            #assetManagerCategoryCombo::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {tm.get_variable('text_tertiary')};
                margin-right: 8px;
            }}
            #assetManagerCategoryCombo QAbstractItemView {{
                background-color: {tm.get_variable('bg_tertiary')};
                border: 1px solid {tm.get_variable('border')};
                selection-background-color: {tm.get_variable('accent')};
                color: {tm.get_variable('text_primary')};
            }}
            
            /* 管理分类按钮 */
            #assetManagerManageCategoryBtn {{
                background-color: {tm.get_variable('bg_tertiary')};
                border: 1px solid {tm.get_variable('border')};
                border-radius: 4px;
                color: {tm.get_variable('text_secondary')};
                font-size: 18px;
            }}
            #assetManagerManageCategoryBtn:hover {{
                background-color: {tm.get_variable('bg_hover')};
                border-color: {tm.get_variable('border_hover')};
                color: {tm.get_variable('text_primary')};
            }}
            #assetManagerManageCategoryBtn:pressed {{
                background-color: {tm.get_variable('bg_pressed')};
            }}
            
            /* 搜索标签 */
            #assetManagerSearchLabel {{
                color: {tm.get_variable('text_primary')};
                font-size: 13px;
                margin-left: 20px;
            }}
            
            /* 搜索输入框 */
            #assetManagerSearchInput {{
                background-color: {tm.get_variable('bg_tertiary')};
                border: 1px solid {tm.get_variable('border')};
                border-radius: 4px;
                padding: 6px 10px;
                color: {tm.get_variable('text_primary')};
                font-size: 13px;
            }}
            #assetManagerSearchInput:focus {{
                border: 1px solid {tm.get_variable('accent')};
            }}
            
            /* 排序标签 */
            #assetManagerSortLabel {{
                color: {tm.get_variable('text_primary')};
                font-size: 13px;
                margin-left: 15px;
            }}
            
            /* 排序下拉框 */
            #assetManagerSortCombo {{
                background-color: {tm.get_variable('bg_tertiary')};
                border: 1px solid {tm.get_variable('border')};
                border-radius: 4px;
                padding: 6px 10px;
                color: {tm.get_variable('text_primary')};
                font-size: 13px;
            }}
            #assetManagerSortCombo:hover {{
                border: 1px solid {tm.get_variable('border_hover')};
            }}
            #assetManagerSortCombo::drop-down {{
                border: none;
                width: 30px;
            }}
            #assetManagerSortCombo::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {tm.get_variable('text_tertiary')};
                margin-right: 8px;
            }}
            #assetManagerSortCombo QAbstractItemView {{
                background-color: {tm.get_variable('bg_tertiary')};
                border: 1px solid {tm.get_variable('border')};
                selection-background-color: {tm.get_variable('accent')};
                color: {tm.get_variable('text_primary')};
            }}
            
            /* 添加资产按钮 */
            #assetManagerAddAssetBtn {{
                background: {tm.get_variable('accent')};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }}
            #assetManagerAddAssetBtn:hover {{
                background: {tm.get_variable('border_hover')};
            }}
            #assetManagerAddAssetBtn:pressed {{
                background: {tm.get_variable('accent_pressed')};
            }}
            
            /* 分隔线 */
            #assetManagerSeparator {{
                background-color: {tm.get_variable('border')};
            }}
            
            /* 滚动区域 */
            #assetManagerScrollArea {{
                border: none;
                background-color: transparent;
            }}
            #assetManagerScrollArea > QWidget {{
                background-color: transparent;
            }}
            #assetManagerScrollArea QScrollBar:vertical {{
                background-color: {tm.get_variable('bg_secondary')};
                width: 12px;
                border-radius: 6px;
            }}
            #assetManagerScrollArea QScrollBar::handle:vertical {{
                background-color: {tm.get_variable('bg_tertiary')};
                border-radius: 6px;
                min-height: 20px;
            }}
            #assetManagerScrollArea QScrollBar::handle:vertical:hover {{
                background-color: {tm.get_variable('bg_hover')};
            }}
            
            /* 资产容器 */
            #assetManagerAssetsContainer {{
                background-color: transparent;
            }}
            
            /* 空状态容器 */
            #assetManagerEmptyContainer {{
                background-color: transparent;
            }}
            
            /* 空状态标签 */
            #assetManagerEmptyLabel {{
                color: {tm.get_variable('text_tertiary')};
                font-size: 16px;
                line-height: 1.8;
            }}
        """
    
    def _init_ui(self):
        """初始化UI"""
        self.setStyleSheet(self._build_stylesheet())
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        top_layout = QHBoxLayout()
        
        # 分类选择框
        self.category_label = QLabel("分类：")
        self.category_label.setObjectName("assetManagerCategoryLabel")
        top_layout.addWidget(self.category_label)
        
        self.category_combo = QComboBox()
        self.category_combo.setObjectName("assetManagerCategoryCombo")
        self.category_combo.setFixedWidth(150)
        self.category_combo.currentTextChanged.connect(self._on_category_changed)
        top_layout.addWidget(self.category_combo)
        
        # 分类管理按钮（齿轮图标）
        self.manage_category_btn = QPushButton("⚙")
        self.manage_category_btn.setObjectName("assetManagerManageCategoryBtn")
        self.manage_category_btn.setFixedSize(32, 32)
        self.manage_category_btn.setToolTip("管理分类")
        self.manage_category_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # 禁用焦点
        self.manage_category_btn.clicked.connect(self._show_category_management)
        top_layout.addWidget(self.manage_category_btn)
        
        # 搜索框
        self.search_label = QLabel("搜索：")
        self.search_label.setObjectName("assetManagerSearchLabel")
        top_layout.addWidget(self.search_label)
        
        self.search_input = NoContextMenuLineEdit()
        self.search_input.setObjectName("assetManagerSearchInput")
        self.search_input.setFixedWidth(200)
        self.search_input.setPlaceholderText("输入资产名称或拼音...")
        self.search_input.textChanged.connect(self._on_search_changed)
        top_layout.addWidget(self.search_input)
        
        # 排序选择框
        self.sort_label = QLabel("排序：")
        self.sort_label.setObjectName("assetManagerSortLabel")
        top_layout.addWidget(self.sort_label)
        
        self.sort_combo = QComboBox()
        self.sort_combo.setObjectName("assetManagerSortCombo")
        self.sort_combo.setFixedWidth(150)
        self.sort_combo.addItems([
            "添加时间（最新）",
            "添加时间（最旧）",
            "名称（A-Z）",
            "名称（Z-A）",
            "分类（A-Z）",
            "分类（Z-A）"
        ])
        # 使用 activated 信号而不是 currentTextChanged，这样用户每次主动选择都会触发
        # 即使选择的是相同的选项，也会触发排序（解决第一次点击无响应的问题）
        self.sort_combo.activated.connect(lambda: self._on_sort_changed(self.sort_combo.currentText()))
        top_layout.addWidget(self.sort_combo)
        
        top_layout.addStretch()
        
        # 添加资产按钮
        self.add_asset_btn = QPushButton("添加资产")
        self.add_asset_btn.setObjectName("assetManagerAddAssetBtn")
        self.add_asset_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # 禁用焦点
        self.add_asset_btn.clicked.connect(self._show_add_asset_dialog)
        top_layout.addWidget(self.add_asset_btn)
        
        main_layout.addLayout(top_layout)
        
        self.separator = QFrame()
        self.separator.setObjectName("assetManagerSeparator")
        self.separator.setFrameShape(QFrame.Shape.HLine)
        self.separator.setFixedHeight(1)
        main_layout.addWidget(self.separator)
        
        # 资产展示区域（滚动区域）
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("assetManagerScrollArea")
        self.scroll_area.setWidgetResizable(True)
        
        # 资产容器
        self.assets_container = QWidget()
        self.assets_container.setObjectName("assetManagerAssetsContainer")
        self.assets_layout = QGridLayout()
        self.assets_layout.setSpacing(20)
        self.assets_layout.setContentsMargins(20, 0, 40, 0)  # 右边距更宽，为滚动条留空间
        self.assets_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.assets_container.setLayout(self.assets_layout)
        
        # 空状态容器（用于垂直居中）
        self.empty_container = QWidget()
        self.empty_container.setObjectName("assetManagerEmptyContainer")
        empty_container_layout = QVBoxLayout()
        empty_container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 空状态提示
        self.empty_label = QLabel("暂无资产\n点击上方按钮添加资源包或文件")
        self.empty_label.setObjectName("assetManagerEmptyLabel")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        empty_container_layout.addWidget(self.empty_label)
        self.empty_container.setLayout(empty_container_layout)
        
        self.scroll_area.setWidget(self.empty_container)  # 默认显示空状态
        main_layout.addWidget(self.scroll_area)
        
        self.setLayout(main_layout)
    
        self._update_category_combo()
    
    def _update_category_combo(self):
        """更新分类选择框"""

        self.category_combo.blockSignals(True)
        
        try:
            current_category = self.category_combo.currentText()
            categories = self.logic.get_all_categories()
            
            logger.info(f"[DEBUG] 更新分类下拉框 - 当前选中: {current_category}, 获取到的分类: {categories}")
            
            # 清空并重新添加
            self.category_combo.clear()
            self.category_combo.addItem("全部分类")
            
            # 添加所有分类
            self.category_combo.addItems(categories)
            logger.info(f"[DEBUG] 分类已添加到下拉框，共 {self.category_combo.count()} 项")
            
            # 恢复之前选中的分类
            if current_category:
                index = self.category_combo.findText(current_category)
                if index >= 0:
                    self.category_combo.setCurrentIndex(index)
        finally:
            # 恢复信号
            self.category_combo.blockSignals(False)
            logger.info(f"[DEBUG] 分类下拉框更新完成，当前选中: {self.category_combo.currentText()}")
    
    def _on_category_changed(self, category_name: str):
        """分类改变事件"""
        if category_name == "全部分类":
            self.current_category = None
        else:
            self.current_category = category_name
        
        self._refresh_assets()
    
    def _on_search_changed(self, search_text: str):
        """搜索文本改变事件"""
        self.search_text = search_text.strip()
        
        self._refresh_assets()
    
    def _on_sort_changed(self, sort_method: str):
        """排序方式改变事件"""
        self.sort_method = sort_method
        
        self._refresh_assets()
    
    def _show_category_management(self):
        """显示分类管理对话框"""
        dialog = CategoryManagementDialog(self.logic, self)
        
        # 连接信号，当分类更新时刷新UI
        dialog.categories_updated.connect(self._on_categories_updated)
        
        dialog.exec()
    
    def _on_categories_updated(self):
        """分类更新后的回调"""
        # 更新分类选择框（内部已处理选中状态）
        self._update_category_combo()
        
        # 刷新资产列表（因为分类可能被删除，需要重新加载）
        logger.debug("分类已更新，刷新资产列表")
        self._refresh_assets()
    
    def _show_add_asset_dialog(self):
        """显示添加资产对话框"""
        logger.info("准备显示添加资产对话框")
        
        existing_names = self.logic.get_all_asset_names()
        categories = self.logic.get_all_categories()
        logger.debug(f"当前有 {len(existing_names)} 个资产，{len(categories)} 个分类")
        
        dialog = AddAssetDialog(existing_names, categories, parent=self)
        
        logger.info("等待用户操作对话框...")
        result = dialog.exec()
        logger.info(f"对话框返回结果: {result} (Accepted={QDialog.DialogCode.Accepted})")
        
        if result == QDialog.DialogCode.Accepted:
            asset_info = dialog.get_asset_info()
            logger.info(f"开始添加资产: {asset_info.get('name')}, 路径: {asset_info.get('path')}")
            
            progress_dialog = ProgressDialog(
                title="添加资产",
                parent=self
            )
            progress_dialog.status_label.setText(f"正在添加资产 \"{asset_info.get('name')}\"...")
            
            # 保存进度对话框引用，防止被垃圾回收
            self._current_progress_dialog = progress_dialog
            
            # 连接进度更新信号
            self.logic.progress_updated.connect(progress_dialog.update_progress)
            
            progress_dialog.show()
            
            # 在后台线程中添加资产
            def add_with_progress():
                try:
                    self._do_add_asset_with_info(asset_info)
                    # 添加成功，关闭进度对话框
                    QTimer.singleShot(500, progress_dialog.finish_success)
                except Exception as e:
                    logger.error(f"添加资产异常: {e}", exc_info=True)
                    error_msg = str(e)
                    QTimer.singleShot(0, lambda: progress_dialog.finish_error(error_msg))
                finally:
                    # 断开信号
                    try:
                        self.logic.progress_updated.disconnect(progress_dialog.update_progress)
                    except:
                        pass
                    
                    # 延迟清理对话框，确保 finish_success 已执行
                    QTimer.singleShot(1500, lambda: self._cleanup_progress_dialog(progress_dialog))
            
            thread = threading.Thread(target=add_with_progress, daemon=True)
            thread.start()
            logger.info(f"后台线程已启动: {thread.name}")
        else:
            logger.info("用户取消了添加资产操作")
    
    def _do_add_asset_with_info(self, asset_info: dict):
        """使用资产信息添加资产（后台线程）
        
        Args:
            asset_info: 资产信息字典
        """
        logger.info(f">>> 进入 _do_add_asset_with_info 方法，准备添加资产: {asset_info.get('name')}")
        try:
            asset_path = asset_info["path"]
            asset_type = asset_info["type"]
            asset_name = asset_info["name"]
            category = asset_info["category"]
            create_doc = asset_info["create_doc"]
            
            logger.info(f"调用 logic.add_asset(): name={asset_name}, type={asset_type}, category={category}, create_doc={create_doc}")
            
            # 添加资产（传递create_markdown参数用于文档创建）
            asset = self.logic.add_asset(
                asset_path=asset_path,
                asset_type=asset_type,
                name=asset_name,
                category=category,
                description="",  # 初始描述为空
                create_markdown=create_doc  # ✅ 添加此参数
            )
            
            logger.info(f"logic.add_asset() 返回结果: {asset}")
            
            if asset:
                # 确保资产的分类存在于分类列表中
                if category not in self.logic.categories:
                    self.logic.add_category(category)
                
                # 生成缩略图（如果需要）
                should_generate_thumbnail = False
                
                # 注意：此时 asset_path 已经被移动了，所以使用 asset.path 代替
                if asset.asset_type == AssetType.FILE:
                    if asset.path.suffix.lower() in ThumbnailGenerator.IMAGE_EXTENSIONS:
                        should_generate_thumbnail = True
                elif asset.asset_type == AssetType.PACKAGE:
                    for ext in ThumbnailGenerator.IMAGE_EXTENSIONS:
                        if list(asset.path.glob(f"*{ext}")):
                            should_generate_thumbnail = True
                            break
                
                if should_generate_thumbnail:
                    thumbnail_path = self.logic.thumbnails_dir / f"{asset.id}.png"
                    success = ThumbnailGenerator.generate_thumbnail(
                        asset.path,
                        thumbnail_path,
                        asset_type.value
                    )
                    if success:
                        asset.thumbnail_path = thumbnail_path
                        logger.info(f"缩略图生成成功: {asset.name}")
                    else:
                        logger.warning(f"缩略图生成失败: {asset.name}")
                else:
                    asset.thumbnail_path = None
                    logger.info(f"跳过缩略图生成，将显示文本: {asset.name}")
                
                self.logic._save_config()
                logger.info(f"资产添加完成: {asset.name}")
                
                QTimer.singleShot(0, self._update_category_combo)
                QTimer.singleShot(0, self._refresh_assets)
                
        except Exception as e:
            logger.error(f"添加资产失败: {e}", exc_info=True)
            self.logic.error_occurred.emit(f"添加资产失败: {e}")
            raise  # 重新抛出异常，让进度对话框显示错误
    
    def _set_paths(self):
        """设置资产库路径和预览工程路径"""
        from .set_paths_dialog import SetPathsDialog
        
        current_lib_path = self.logic.get_asset_library_path()
        current_preview_path = self.logic.get_preview_project()
        
        dialog = SetPathsDialog(
            asset_library_path=str(current_lib_path) if current_lib_path else "",
            preview_project_path=str(current_preview_path) if current_preview_path else "",
            parent=self
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            lib_path_str, preview_path_str = dialog.get_paths()
            
            # 设置资产库路径
            if lib_path_str:
                lib_path = Path(lib_path_str)
                if self.logic.set_asset_library_path(lib_path):
                    logger.info(f"资产库路径已设置: {lib_path}")
                    # set_asset_library_path 内部已调用 _load_config()
                    # 使用小延迟确保数据完全加载后再更新UI
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(0, self._on_categories_updated)
            
            # 设置预览工程路径
            if preview_path_str:
                preview_path = Path(preview_path_str)
                if self.logic.set_preview_project(preview_path):
                    logger.info(f"预览工程路径已设置: {preview_path}")
            
            StyledMessageBox.information(
                self,
                "成功",
                "路径设置已保存"
            )
    
    def _recreate_empty_container(self, message: str = None):
        """重新创建空状态容器
        
        Args:
            message: 自定义提示消息，如果为None则使用默认消息
        """
        self.empty_container = QWidget()
        self.empty_container.setObjectName("assetManagerEmptyContainer")
        empty_container_layout = QVBoxLayout()
        empty_container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if message is None:
            message = "暂无资产\n点击上方按钮添加资源包或文件"
        
        self.empty_label = QLabel(message)
        self.empty_label.setObjectName("assetManagerEmptyLabel")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        empty_container_layout.addWidget(self.empty_label)
        self.empty_container.setLayout(empty_container_layout)
    
    def _refresh_assets(self):
        """刷新资产显示"""
        scroll_bar = self.scroll_area.verticalScrollBar()
        saved_scroll_value = scroll_bar.value() if scroll_bar else 0
        
        # 清空现有卡片
        for card in self.asset_cards.values():
            card.deleteLater()
        self.asset_cards.clear()
        
        # 清空布局（检查布局是否有效）
        try:
            while self.assets_layout.count():
                item = self.assets_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        except RuntimeError:
            # 布局已被删除，需要重新创建容器和布局
            logger.warning("资产布局已被删除，重新创建容器和布局")
            self.assets_container = QWidget()
            self.assets_container.setObjectName("assetManagerAssetsContainer")
            self.assets_layout = QGridLayout()
            self.assets_layout.setSpacing(15)
            self.assets_layout.setContentsMargins(20, 0, 40, 0)  # 右边距更宽，为滚动条留空间
            self.assets_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            self.assets_container.setLayout(self.assets_layout)
        
        # 获取资产（根据当前分类和搜索文本过滤）
        if self.search_text:
            assets = self.logic.search_assets(self.search_text, category=self.current_category)
        else:
            assets = self.logic.get_all_assets(category=self.current_category)
        
        # 对资产进行排序
        if assets and self.sort_method:
            assets = self.logic.sort_assets(assets, self.sort_method)
        
        if not assets:
            # 根据是否有搜索文本显示不同的提示
            if self.search_text:
                message = f"未找到匹配 \"{self.search_text}\" 的资产\n请尝试其他搜索词"
            else:
                message = "暂无资产\n点击上方按钮添加资源包或文件"
            
            try:
                # 先检查对象是否被删除
                if self.empty_container:
                    try:
                        # 尝试访问对象，如果已删除会抛出 RuntimeError
                        _ = self.empty_container.isHidden()
                        self.empty_label.setText(message)
                        self.scroll_area.setWidget(self.empty_container)
                    except RuntimeError:
                        # 对象已被删除，重新创建
                        self._recreate_empty_container(message)
                        self.scroll_area.setWidget(self.empty_container)
                else:
                    # 对象不存在，创建新的
                    self._recreate_empty_container(message)
                    self.scroll_area.setWidget(self.empty_container)
            except RuntimeError:
                # 容器已被删除，重新创建
                self._recreate_empty_container(message)
                self.scroll_area.setWidget(self.empty_container)
            return
        
        # 检查assets_container是否有效
        try:
            self.scroll_area.setWidget(self.assets_container)
        except RuntimeError:
            # 容器已被删除，重新创建
            logger.warning("资产容器已被删除，重新创建")
            self.assets_container = QWidget()
            self.assets_container.setObjectName("assetManagerAssetsContainer")
            self.assets_layout = QGridLayout()
            self.assets_layout.setSpacing(15)
            self.assets_layout.setContentsMargins(20, 0, 40, 0)  # 右边距更宽，为滚动条留空间
            self.assets_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            self.assets_container.setLayout(self.assets_layout)
            self.scroll_area.setWidget(self.assets_container)
        
        # 添加资产卡片（网格布局，每行4个）
        columns = 4
        for i, asset in enumerate(assets):
            card = AssetCard(asset)
            card.preview_clicked.connect(self._preview_asset)
            card.delete_clicked.connect(self._delete_asset)
            card.migrate_clicked.connect(self._migrate_asset)
            card.edit_info_clicked.connect(self._edit_asset_info)
            card.description_updated.connect(self._update_asset_description)
            
            row = i // columns
            col = i % columns
            self.assets_layout.addWidget(card, row, col)
            
            self.asset_cards[asset.id] = card
        
        # 恢复滚动位置（使用QTimer延迟执行，确保布局完成）
        QTimer.singleShot(0, lambda: self._restore_scroll_position(saved_scroll_value))
    
    def _restore_scroll_position(self, value: int):
        """恢复滚动位置
        
        Args:
            value: 滚动条的值
        """
        try:
            scroll_bar = self.scroll_area.verticalScrollBar()
            if scroll_bar and value > 0:
                scroll_bar.setValue(value)
                logger.debug(f"已恢复滚动位置: {value}")
        except Exception as e:
            logger.debug(f"恢复滚动位置失败: {e}")
    
    @pyqtSlot(str)
    def _preview_asset(self, asset_id: str):
        """预览资产"""
        # 获取所有预览工程
        additional_projects = self.logic.get_additional_preview_projects_with_names()
        
        if not additional_projects:
            StyledMessageBox.warning(
                self,
                "警告",
                "请先设置预览工程！\n\n请在左侧工具栏的「设置」中配置预览工程路径。"
            )
            return
        
        # 如果只有一个工程，直接使用
        if len(additional_projects) == 1:
            preview_project = Path(additional_projects[0]["path"])
        else:
            # 多个工程时，弹出选择对话框
            project_names = [p.get("name", "未命名") for p in additional_projects]
            
            # 创建一个简单的项目选择对话框
            from PyQt6.QtWidgets import QInputDialog
            selected_name, ok = QInputDialog.getItem(
                self,
                "选择预览工程",
                "请选择要预览的工程：",
                project_names,
                0,
                False
            )
            
            if not ok:
                logger.info("用户取消了工程选择")
                return
            
            # 找到选中的工程路径
            selected_index = project_names.index(selected_name)
            preview_project = Path(additional_projects[selected_index]["path"])
        
        if not preview_project or not preview_project.exists():
            StyledMessageBox.warning(
                self,
                "警告",
                "选中的预览工程不存在！\n\n请检查工程路径是否有效。"
            )
            return
        
        # 直接开始预览，不显示确认对话框
        # 显示进度对话框（非阻塞模式）
        progress_dialog = ProgressDialog("预览资产", self)
        
        # 保持对对话框的引用，防止被垃圾回收
        self._preview_progress_dialog = progress_dialog
        
        # 开始预览（在后台线程），使用progress_dialog的update_progress方法作为回调
        self.logic.preview_asset(asset_id, progress_callback=progress_dialog.update_progress, preview_project_path=preview_project)
        
        # 使用show()而不是exec()，这样对话框不会阻塞
        progress_dialog.show()
    
    @pyqtSlot(str)
    def _delete_asset(self, asset_id: str):
        """删除资产"""
        asset = self.logic.get_asset(asset_id)
        if not asset:
            return
        
        dialog = ConfirmDialog(
            "确认删除",
            f"确定要删除资产 \"{asset.name}\" 吗？",
            "注意：这将永久删除资产库中的文件/文件夹，此操作不可恢复！",
            self
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.logic.remove_asset(asset_id, delete_physical=True)
    
    @pyqtSlot(str)
    def _migrate_asset(self, asset_id: str):
        """迁移资产到目标工程（使用工程选择器）"""
        try:
            # 1. 检测运行的UE工程和搜索所有UE工程
            from core.utils.ue_process_utils import UEProcessUtils
            ue_utils = UEProcessUtils()
            
            # 首先检测运行中的工程
            running_projects = ue_utils.detect_running_ue_projects()
            logger.info(f"检测到 {len(running_projects)} 个运行中的UE工程")
            
            # 如果没有运行的工程，则搜索所有UE工程
            all_projects = []
            if not running_projects:
                logger.info("未检测到运行的UE工程，开始搜索所有UE工程")
                all_projects = ue_utils.search_all_ue_projects()
                logger.info(f"搜索到 {len(all_projects)} 个UE工程")
            
            # 合并运行的工程和搜索到的工程
            ue_projects = running_projects + all_projects
            
            # 2. 如果没有找到任何工程，显示提示
            if not ue_projects:
                StyledMessageBox.warning(
                    self,
                    "未找到UE工程",
                    "未检测到任何虚幻引擎工程。\n\n请确保至少有一个UE工程在运行，或者您的磁盘上存在UE工程。"
                )
                return
            
            # 3. 选择目标工程
            selected_project = self._select_ue_project(ue_projects)
            if not selected_project:
                return
            
            target_project = selected_project.project_path.parent
            logger.info(f"选择的目标工程: {target_project}")
            
            # 4. 确认迁移
            asset = self.logic.get_asset(asset_id)
            dialog = ConfirmDialog(
                "确认迁移",
                f"确定要将资产 \"{asset.name}\" 迁移到目标工程吗？",
                f"目标工程：{selected_project.name}\n路径：{target_project}\n\n资产将被复制到目标工程的Content文件夹中。",
                self
            )
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                progress_dialog = ProgressDialog("迁移资产", self)
                
                # 在后台线程执行迁移
                def do_migrate():
                    try:
                        if self.logic.migrate_asset(asset_id, target_project, progress_callback=progress_dialog.update_progress):
                            logger.info(f"资产迁移成功")
                        else:
                            # 迁移失败，使用QTimer在主线程显示错误
                            QTimer.singleShot(0, lambda: progress_dialog.finish_error("迁移失败"))
                    except Exception as e:
                        logger.error(f"迁移时出错: {e}", exc_info=True)
                        # 使用QTimer在主线程显示错误
                        QTimer.singleShot(0, lambda: progress_dialog.finish_error(str(e)))
                
                thread = threading.Thread(target=do_migrate, daemon=True)
                thread.start()
                
                progress_dialog.exec()
        except Exception as e:
            logger.error(f"迁移资产时出错: {e}", exc_info=True)
            StyledMessageBox.error(
                self,
                "错误",
                f"迁移资产时发生错误：\n{str(e)}"
            )
    
    def _select_ue_project(self, ue_projects):
        """选择UE工程
        
        Args:
            ue_projects: UE工程列表
            
        Returns:
            选择的工程对象，如果取消则返回None
        """
        if not ue_projects:
            return None
        elif len(ue_projects) == 1:
            # 只有一个工程，直接返回
            return ue_projects[0]
        else:
            # 多个工程，显示选择对话框
            # 导入配置工具的工程选择器对话框
            from modules.config_tool.ui.dialogs import UEProjectSelectorDialog
            dialog = UEProjectSelectorDialog(ue_projects, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                return dialog.get_selected_project()
            return None
    
    @pyqtSlot(str)
    def _edit_asset_info(self, asset_id: str):
        """编辑资产信息（名称和分类）"""
        asset = self.logic.get_asset(asset_id)
        if not asset:
            return
        
        from .edit_asset_dialog import EditAssetDialog
        
        existing_names = self.logic.get_all_asset_names()
        
        categories = self.logic.get_all_categories()
        
        dialog = EditAssetDialog(asset.name, asset.category, existing_names, categories, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            asset_info = dialog.get_asset_info()
            new_name = asset_info["name"]
            new_category = asset_info["category"]
            
            old_name = asset.name
            old_category = asset.category
            
            name_changed = new_name != old_name
            category_changed = new_category != old_category
            
            if not name_changed and not category_changed:
                logger.info("资产信息未改变")
                return
            
            if self.logic.update_asset_info(asset_id, new_name, new_category):
                logger.info(f"资产信息已更新: {old_name} -> {new_name}, {old_category} -> {new_category}")
                
                if category_changed:
                    self._update_category_combo()
                
                # 智能刷新
                if self.current_category is None:
                    # 全部分类视图：只需更新卡片
                    if asset_id in self.asset_cards:
                        card = self.asset_cards[asset_id]
                        if name_changed:
                            # 如果名称改变，需要刷新整个卡片（因为名称显示在卡片上）
                            self._refresh_assets()
                        elif category_changed:
                            # 只更新分类显示
                            card.update_category_display(new_category)
                            logger.info(f"✓ 已更新卡片 {asset.name} 的分类显示为 [{new_category}]")
                    else:
                        self._refresh_assets()
                else:
                    # 特定分类视图：需要刷新列表（资产可能被移出当前分类）
                    self._refresh_assets()
    
    # 信号槽处理方法
    
    @pyqtSlot(object)
    def _on_asset_added(self, asset: Asset):
        """资产添加完成"""
        logger.info(f"UI: 资产已添加 - {asset.name}")
        self._refresh_assets()
    
    @pyqtSlot(str)
    def _on_asset_removed(self, asset_id: str):
        """资产删除完成"""
        logger.info(f"UI: 资产已删除 - {asset_id}")
        self._refresh_assets()
    
    @pyqtSlot(list)
    def _on_assets_loaded(self, assets: list):
        """资产列表加载完成"""
        logger.info(f"UI: 已加载 {len(assets)} 个资产")
        self._refresh_assets()
    
    @pyqtSlot(str)
    def _on_preview_started(self, asset_id: str):
        """预览启动"""
        asset = self.logic.get_asset(asset_id)
        StyledMessageBox.information(
            self,
            "预览已启动",
            f"资产 \"{asset.name}\" 正在准备预览...\n\n"
            "虚幻引擎将自动启动，请稍候..."
        )
    
    @pyqtSlot(str, str)
    def _on_thumbnail_updated(self, asset_id: str, thumbnail_path: str):
        """缩略图更新"""
        try:
            logger.info(f"UI: 收到缩略图更新通知 - asset_id={asset_id}, path={thumbnail_path}")
            
            # 查找对应的资产卡片
            if asset_id in self.asset_cards:
                card = self.asset_cards[asset_id]
                # 重新加载缩略图
                card._load_thumbnail()
                logger.info(f"UI: 资产卡片缩略图已更新 - {asset_id}")
            else:
                logger.warning(f"UI: 未找到资产卡片 - {asset_id}")
                
        except Exception as e:
            logger.error(f"UI: 更新缩略图时出错: {e}", exc_info=True)
    
    @pyqtSlot(str)
    def _on_error(self, error_message: str):
        """错误发生"""
        # 使用QTimer延迟显示错误，避免递归调用
        QTimer.singleShot(0, lambda: self._show_error_dialog(error_message))
    
    def _show_error_dialog(self, error_message: str):
        """实际显示错误对话框"""
        try:
            # 防止递归调用
            if hasattr(self, '_showing_error') and self._showing_error:
                logger.warning(f"跳过重复的错误提示: {error_message}")
                return
            
            self._showing_error = True
            StyledMessageBox.error(
                self,
                "错误",
                error_message
            )
        except Exception as e:
            logger.error(f"显示错误对话框时出错: {e}", exc_info=True)
        finally:
            self._showing_error = False
    
    @pyqtSlot(str, str)
    def _update_asset_description(self, asset_id: str, new_description: str):
        """更新资产描述"""
        try:
            logger.info(f"更新资产描述: {asset_id}")
            # 调用逻辑层保存描述
            self.logic.update_asset_description(asset_id, new_description)
            logger.info(f"资产描述保存成功: {asset_id}")
        except Exception as e:
            logger.error(f"保存资产描述失败: {e}", exc_info=True)
    
    
    def dragEnterEvent(self, event):
        """拖入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            logger.debug("接受拖放操作")
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        """拖动移动事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """放下事件"""
        if not event.mimeData().hasUrls():
            event.ignore()
            return
        
        urls = event.mimeData().urls()
        if not urls:
            event.ignore()
            return
        
        # 只处理第一个拖入的项
        file_path = urls[0].toLocalFile()
        path = Path(file_path)
        
        if not path.exists():
            logger.warning(f"拖入的路径不存在: {path}")
            event.ignore()
            return
        
        logger.info(f"拖入路径: {path}")
        
        # 自动识别是文件夹还是文件
        if path.is_dir():
            asset_type = AssetType.PACKAGE
            logger.info("识别为资产包（文件夹）")
        else:
            asset_type = AssetType.FILE
            logger.info("识别为文件")
        
        # 弹出添加资产对话框
        self._show_add_asset_dialog_with_path(path, asset_type)
        
        event.acceptProposedAction()
    
    def _show_add_asset_dialog_with_path(self, asset_path: Path, asset_type: AssetType):
        """显示添加资产对话框并预填路径
        
        Args:
            asset_path: 资产路径
            asset_type: 资产类型
        """
        try:
            library_path = self.logic.get_asset_library_path()
            if not library_path or not library_path.exists():
                StyledMessageBox.warning(
                    self,
                    "警告",
                    "请先设置资产库路径！\n\n请在左侧工具栏的「设置」中配置资产库路径。"
                )
                return
            
            categories = self.logic.get_all_categories()
            existing_names = self.logic.get_all_asset_names()
            
            dialog = AddAssetDialog(
                existing_asset_names=existing_names,
                categories=categories,
                prefill_path=str(asset_path),
                prefill_type=asset_type,
                parent=self
            )
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                result = dialog.get_asset_info()
                
                asset_name = result["name"]
                if asset_name in self.logic.get_all_asset_names():
                    StyledMessageBox.warning(
                        self,
                        "警告",
                        f"资产名称 \"{asset_name}\" 已存在，请使用其他名称。"
                    )
                    return
                
                # 显示进度对话框
                progress_dialog = ProgressDialog(
                    title="添加资产",
                    parent=self
                )
                progress_dialog.status_label.setText(f"正在添加资产 \"{result.get('name')}\"...")
                
                # 保存进度对话框引用，防止被垃圾回收
                self._current_progress_dialog = progress_dialog
                
                # 连接进度更新信号
                self.logic.progress_updated.connect(progress_dialog.update_progress)
                
                progress_dialog.show()
                
                # 在后台线程中添加资产
                def add_asset_thread():
                    try:
                        asset = self.logic.add_asset(
                            asset_path=result["path"],
                            asset_type=result["type"],
                            name=result["name"],
                            category=result["category"],
                            description="",
                            create_markdown=result.get("create_doc", False)
                        )
                        
                        if asset:
                            logger.info(f"拖放添加资产成功: {asset.name}")
                            QTimer.singleShot(500, progress_dialog.finish_success)
                        else:
                            logger.error("拖放添加资产失败")
                            QTimer.singleShot(0, lambda: progress_dialog.finish_error("添加资产失败"))
                    
                    except Exception as e:
                        logger.error(f"拖放添加资产失败: {e}", exc_info=True)
                        error_msg = str(e)
                        QTimer.singleShot(0, lambda: progress_dialog.finish_error(error_msg))
                    finally:
                        # 断开信号
                        try:
                            self.logic.progress_updated.disconnect(progress_dialog.update_progress)
                        except:
                            pass
                        
                        # 延迟清理对话框，确保 finish_success 已执行
                        QTimer.singleShot(1500, lambda: self._cleanup_progress_dialog(progress_dialog))
                
                thread = threading.Thread(target=add_asset_thread, daemon=True)
                thread.start()
        
        except Exception as e:
            logger.error(f"显示添加资产对话框失败: {e}", exc_info=True)
            StyledMessageBox.critical(
                self,
                "错误",
                f"显示添加资产对话框失败: {str(e)}"
            )
    
    def _check_first_launch(self):
        """检查是否首次启动，如果是则显示首次启动对话框"""
        try:
            library_path = self.logic.get_asset_library_path()
            
            if not library_path or not library_path.exists():
                logger.info("检测到首次启动，显示设置路径对话框")
                
                dialog = FirstLaunchDialog(parent=self.window())
                
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    lib_path_str, preview_path_str = dialog.get_paths()
                    
                    # 设置资产库路径
                    if lib_path_str:
                        lib_path = Path(lib_path_str)
                        if self.logic.set_asset_library_path(lib_path):
                            logger.info(f"首次启动：资产库路径已设置: {lib_path}")
                            
                            # 注意：预览工程不再在首次启动时设置，用户需要在设置界面中配置
                            
                            QTimer.singleShot(100, self._refresh_assets)
                            
                            QTimer.singleShot(500, lambda: StyledMessageBox.information(
                                self,
                                "欢迎",
                                f"资产库路径设置成功！\n\n{lib_path}"
                            ))
                        else:
                            logger.error("首次启动：设置资产库路径失败")
                            StyledMessageBox.critical(
                                self,
                                "错误",
                                "设置资产库路径失败，请稍后在设置中重新配置。"
                            )
                else:
                    logger.warning("用户取消了首次启动设置（理论上不应该发生）")

        except Exception as e:
            logger.error(f"检查首次启动失败: {e}", exc_info=True)
    
    def refresh_theme(self):
        """刷新主题样式 - 在主题切换时调用"""
        try:
            tm = self.theme_manager
            
            # 应用统一样式表（所有组件的样式都在这里统一更新）
            self.setStyleSheet(self._build_stylesheet())
            
            for card in self.asset_cards.values():
                if hasattr(card, 'theme_manager'):
                    card.theme_manager = tm
                if hasattr(card, 'refresh_theme'):
                    card.refresh_theme()
            
            logger.info("资产管理器主题已刷新")
            
        except Exception as e:
            logger.error(f"刷新资产管理器主题失败: {e}", exc_info=True)

