# -*- coding: utf-8 -*-

"""
资产卡片UI组件
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QMenu, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRectF, QObject, QTimer, QEvent
from PyQt6.QtGui import QPixmap, QAction, QCursor, QPainter, QPainterPath, QBrush, QPen
from pathlib import Path

from core.logger import get_logger
from core.utils.theme_manager import get_theme_manager
from ..logic.asset_model import Asset, AssetType

logger = get_logger(__name__)


class MenuEventFilter(QObject):
    """菜单事件过滤器 - 监听全局事件实现自动关闭"""
    
    def __init__(self, menu: QMenu, card_widget=None):
        super().__init__()
        self.menu = menu
        self.card_widget = card_widget  # 保存对卡片的引用
        self.mouse_was_inside = True  # 标记鼠标是否曾在菜单内
        
        # 安装到应用程序级别，捕获所有事件
        QApplication.instance().installEventFilter(self)
        
        # 启动定时器，持续检测鼠标位置
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self._check_mouse_position)
        self.check_timer.start(50)  # 每50ms检查一次鼠标位置
        
    def eventFilter(self, obj, event):
        """全局事件过滤器 - 监控鼠标按下和窗口失活"""
        try:
            if not self.menu or not self.menu.isVisible():
                return False
        except RuntimeError:
            # 菜单已被删除
            return False
        
        # 监控鼠标按下事件
        if event.type() == QEvent.Type.MouseButtonPress:
            click_pos = QCursor.pos()
            menu_rect = self.menu.rect()
            menu_global_pos = self.menu.mapToGlobal(menu_rect.topLeft())
            menu_global_rect = menu_rect.translated(menu_global_pos)
            
            # 如果点击在菜单外，关闭菜单
            if not menu_global_rect.contains(click_pos):
                self._close_menu()
                return False
        
        # 监控窗口失去激活状态
        elif event.type() == QEvent.Type.WindowDeactivate:
            if obj == self.menu:
                self._close_menu()
        
        return False
    
    def _check_mouse_position(self):
        """定时检测鼠标位置，鼠标离开菜单时自动关闭"""
        try:
            if not self.menu or not self.menu.isVisible():
                self.check_timer.stop()
                return
        except RuntimeError:
            # 菜单已被删除
            self.check_timer.stop()
            return
        
        cursor_pos = QCursor.pos()
        menu_rect = self.menu.rect()
        menu_global_pos = self.menu.mapToGlobal(menu_rect.topLeft())
        menu_global_rect = menu_rect.translated(menu_global_pos)
        
        mouse_inside = menu_global_rect.contains(cursor_pos)
        
        # 如果鼠标曾经在菜单内，现在离开了，则关闭菜单
        if self.mouse_was_inside and not mouse_inside:
            self._close_menu()
        
        if mouse_inside:
            self.mouse_was_inside = True
    
    def _close_menu(self):
        """关闭菜单"""
        try:
            if self.menu and self.menu.isVisible():
                # 停止定时器
                if hasattr(self, 'check_timer'):
                    self.check_timer.stop()
                
                # 先从应用程序移除事件过滤器
                QApplication.instance().removeEventFilter(self)
                
                self.menu.hide()
                self.menu.deleteLater()
                self.menu = None
                
                # 清除卡片的悬停状态
                if self.card_widget:
                    # 模拟鼠标离开事件，清除 hover 状态
                    self.card_widget.setAttribute(Qt.WidgetAttribute.WA_UnderMouse, False)
                    self.card_widget.update()
        except RuntimeError:
            # 菜单已被删除，只需清理定时器和引用
            if hasattr(self, 'check_timer'):
                self.check_timer.stop()
            self.menu = None


class RoundedThumbnailWidget(QWidget):
    """带圆角的缩略图容器 - 直接绘制圆角图片"""
    
    def __init__(self, width: int, height: int, radius: int = 12, parent=None, theme_manager=None):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self.radius = radius
        self._pixmap = None
        self._text = ""
        self._word_wrap = False
        self.theme_manager = theme_manager
        
        # 设置背景色
        self.setAutoFillBackground(False)
    
    def setPixmap(self, pixmap: QPixmap):
        """设置图片"""
        if pixmap and not pixmap.isNull():
            self._pixmap = pixmap
        else:
            self._pixmap = None
        self._text = ""
        self.update()  # 触发重绘
    
    def setText(self, text: str):
        """设置文本（无图片时）"""
        self._text = text
        self._pixmap = None
        self.update()  # 触发重绘
    
    def clear(self):
        """清空内容"""
        self._pixmap = None
        self._text = ""
        self.update()
    
    def setAlignment(self, alignment):
        """设置对齐方式（保持接口兼容）"""
        pass  # 我们在paintEvent中手动居中
    
    def setWordWrap(self, wrap: bool):
        """设置文字换行"""
        self._word_wrap = wrap
    
    def paintEvent(self, event):
        """绘制圆角缩略图"""
        from PyQt6.QtGui import QColor
        from PyQt6.QtCore import QRect
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        
        widget_rect = self.rect()
        w = widget_rect.width()
        h = widget_rect.height()
        
        path = QPainterPath()
        # 使用明确的坐标来绘制圆角矩形
        path.addRoundedRect(QRectF(0.0, 0.0, float(w), float(h)), 
                           float(self.radius), float(self.radius))
        
        # 裁剪到圆角区域
        painter.setClipPath(path)
        
        # 填充背景色 - 使用主题变量
        if self.theme_manager:
            bg_color = self.theme_manager.get_variable('bg_tertiary')
            if not bg_color:  # 如果获取失败
                bg_color = "#1a1a1a"
        else:
            bg_color = "#1a1a1a"  # 默认深色背景
        painter.fillRect(0, 0, w, h, QColor(bg_color))
        
        # 绘制内容
        if self._pixmap and not self._pixmap.isNull():
            # 填充模式：图片居中绘制，超出部分被圆角路径裁剪
            pixmap_to_draw = self._pixmap
            
            # 计算居中位置（可能是负数，表示图片超出容器）
            px_w = pixmap_to_draw.width()
            px_h = pixmap_to_draw.height()
            x = (w - px_w) // 2
            y = (h - px_h) // 2
            
            # 绘制图片 - 超出部分会被圆角裁剪路径自动裁剪
            painter.drawPixmap(x, y, pixmap_to_draw)
        elif self._text:
            # 绘制文本 - 居中对齐，使用主题变量
            if self.theme_manager:
                text_color = self.theme_manager.get_variable('text_secondary')
                if not text_color:  # 如果获取失败
                    text_color = "#707070"
            else:
                text_color = "#707070"  # 默认灰色
            painter.setPen(QColor(text_color))
            font = painter.font()
            font.setPixelSize(18)
            font.setWeight(600)
            painter.setFont(font)
            
            # 使用QRect和AlignCenter绘制文本
            text_rect = QRect(20, 20, w - 40, h - 40)  # 添加padding
            painter.drawText(text_rect, 
                           int(Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap), 
                           self._text)
        
        painter.end()


class AssetCard(QFrame):
    """资产卡片组件
    
    Signals:
        preview_clicked: 点击预览按钮信号 (str: asset_id)
        delete_clicked: 点击删除按钮信号 (str: asset_id)
        migrate_clicked: 点击迁移按钮信号 (str: asset_id)
        description_updated: 描述更新信号 (str: asset_id, str: new_description)
    """
    
    preview_clicked = pyqtSignal(str)  # asset_id
    delete_clicked = pyqtSignal(str)  # asset_id
    migrate_clicked = pyqtSignal(str)  # asset_id
    edit_info_clicked = pyqtSignal(str)  # asset_id (原change_category_clicked)
    description_updated = pyqtSignal(str, str)  # asset_id, new_description (已废弃)
    open_markdown_editor = pyqtSignal(str, str)  # asset_id, markdown_path
    
    def __init__(self, asset: Asset, asset_manager_ui=None, parent=None):
        super().__init__(parent)
        self.asset = asset
        self.asset_manager_ui = asset_manager_ui
        self.theme_manager = get_theme_manager()
        self._init_ui()
    
    def mousePressEvent(self, event):
        """鼠标点击事件 - 单击卡片显示描述编辑对话框"""
        logger.info(f"[AssetCard] 鼠标点击事件触发 - 资产: {self.asset.name}, 按钮: {event.button()}")
        if event.button() == Qt.MouseButton.LeftButton:
            is_button_area = self._is_clicking_button(event.pos())
            logger.info(f"[AssetCard] 点击位置: {event.pos()}, 卡片高度: {self.height()}, 是否按钮区域: {is_button_area}")
            # 如果点击的是按钮，则不弹出对话框
            if not is_button_area:
                logger.info(f"[AssetCard] 准备打开文档: {self.asset.id}.txt")
                self._show_description_dialog()
            else:
                logger.info(f"[AssetCard] 点击在按钮区域，跳过打开文档")
        super().mousePressEvent(event)
    
    def _is_clicking_button(self, pos):
        """检查是否点击了按钮区域"""
        # 简单判断：按钮区域在底部32px高度
        return pos.y() > self.height() - 50
    
    def _show_description_dialog(self):
        """点击卡片打开关联的文本文档"""
        try:
            import subprocess
            import sys
            from pathlib import Path
            
            logger.info(f"[AssetCard] _show_description_dialog 被调用 - 资产: {self.asset.name}")
            
            # 构建文档文件名（与资产ID关联）
            doc_filename = f"{self.asset.id}.txt"
            logger.info(f"[AssetCard] 文档文件名: {doc_filename}")
            
            # 优先使用本地文档目录，如果不存在则查找全局文档目录（向后兼容）
            if hasattr(self.asset_manager_ui, 'logic') and hasattr(self.asset_manager_ui.logic, 'documents_dir'):
                # 使用本地文档目录
                documents_dir = self.asset_manager_ui.logic.documents_dir
                doc_path = documents_dir / doc_filename
                logger.info(f"[AssetCard] 使用本地文档目录: {documents_dir}")
            else:
                # 向后兼容：查找全局文档目录
                user_data_dir = Path.home() / "AppData" / "Roaming" / "ue_toolkit" / "user_data"
                documents_dir = user_data_dir / "documents"
                doc_path = documents_dir / doc_filename
                logger.info(f"[AssetCard] 使用全局文档目录: {documents_dir}")
            
            logger.info(f"[AssetCard] 完整文档路径: {doc_path}")
            logger.info(f"[AssetCard] 文档是否存在: {doc_path.exists()}")
            
            # 如果文档存在，打开它
            if doc_path.exists():
                logger.info(f"[AssetCard] 打开文本文档: {doc_path}")
                if sys.platform == "win32":
                    subprocess.Popen(['notepad', str(doc_path)])
                    logger.info(f"[AssetCard] 已启动 notepad 打开文档")
                elif sys.platform == "darwin":
                    subprocess.Popen(['open', '-a', 'TextEdit', str(doc_path)])
                    logger.info(f"[AssetCard] 已启动 TextEdit 打开文档")
                else:
                    subprocess.Popen(['gedit', str(doc_path)])
                    logger.info(f"[AssetCard] 已启动 gedit 打开文档")
            else:
                logger.warning(f"[AssetCard] 文本文档不存在: {doc_path}")
                logger.info(f"[AssetCard] 资产 {self.asset.name} 的关联文本文档位置应该是: {doc_path}")
                logger.info(f"[AssetCard] 请通过添加资产时勾选'创建文档'选项来生成文档")
        
        except Exception as e:
            logger.error(f"[AssetCard] 打开文本文档失败: {e}", exc_info=True)
    
    def _init_ui(self):
        """初始化UI - 极简现代化卡片设计"""
        self.setObjectName("assetCard")
        self.setFrameShape(QFrame.Shape.NoFrame)
        
        # 极简现代化样式 - 纯色背景 + 微妙阴影 + 悬停效果（动态主题）
        tm = self.theme_manager
        self.setStyleSheet(f"""
            #assetCard {{
                background-color: {tm.get_variable('bg_secondary')};
                border: none;
                border-radius: 16px;
            }}
            #assetCard:hover {{
                background-color: {tm.get_variable('bg_tertiary')};
                border: 2px solid {tm.get_variable('border_hover')};
            }}
            #assetCardContent {{
                background-color: transparent;
            }}
            #assetCardSeparator {{
                background-color: {tm.get_variable('text_primary')};
                border: none;
                margin: 0px 12px;
            }}
            #assetCardName {{
                color: {tm.get_variable('text_primary')};
                font-size: 14px;
                font-weight: 600;
            }}
            #assetCardCategory {{
                color: {tm.get_variable('text_secondary')};
                font-size: 10px;
                background-color: {tm.get_variable('bg_tertiary')};
                border-radius: 4px;
                padding: 2px 8px;
            }}
            #assetCardPreviewBtn {{
                background: {tm.get_variable('info')};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }}
            #assetCardPreviewBtn:hover {{
                background: {tm.get_variable('border_hover')};
            }}
            #assetCardPreviewBtn:pressed {{
                background: {tm.get_variable('accent_pressed')};
            }}
            #assetCardMoreBtn {{
                background-color: {tm.get_variable('bg_tertiary')};
                color: {tm.get_variable('text_secondary')};
                border: 1px solid {tm.get_variable('border')};
                border-radius: 8px;
                font-size: 20px;
                font-weight: bold;
            }}
            #assetCardMoreBtn:hover {{
                background-color: {tm.get_variable('bg_hover')};
                border-color: {tm.get_variable('border_hover')};
                color: {tm.get_variable('text_primary')};
            }}
            #assetCardMoreBtn:pressed {{
                background-color: {tm.get_variable('bg_pressed')};
            }}
            QLabel[class="assetCardInfo"] {{
                color: {tm.get_variable('text_secondary')};
                font-size: 11px;
                padding: 0px 8px;
                margin: 1px 0px;
            }}
        """)
        self.setFixedSize(240, 310)  # 紧凑的卡片高度
        
        # 主布局 - 无边距,让子widget完全填充
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # 无边距
        layout.setSpacing(0)
        
        # 使用自定义的圆角缩略图容器
        self.thumbnail_label = RoundedThumbnailWidget(width=216, height=140, radius=12, 
                                                       parent=self, theme_manager=self.theme_manager)
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._load_thumbnail()
        
        thumbnail_layout = QHBoxLayout()
        thumbnail_layout.setContentsMargins(0, 3, 0, 0)  # 上边距6px（上移）
        thumbnail_layout.setSpacing(0)
        thumbnail_layout.addStretch(1)  # 左边弹性空间
        thumbnail_layout.addWidget(self.thumbnail_label)  # 缩略图
        thumbnail_layout.addStretch(1)  # 右边弹性空间
        
        # 将布局添加到主布局
        layout.addLayout(thumbnail_layout)
        
        # 分隔线 - 缩略图和内容之间
        self.separator_top = QFrame()
        self.separator_top.setObjectName("assetCardSeparator")
        self.separator_top.setFrameShape(QFrame.Shape.HLine)
        self.separator_top.setFrameShadow(QFrame.Shadow.Plain)
        self.separator_top.setFixedHeight(1)  # 固定高度1px
        # 样式由上方 setStyleSheet 中的 #assetCardSeparator 提供
        # 添加分隔线到布局，并设置上下边距
        layout.addSpacing(4)  # 上边距4px
        layout.addWidget(self.separator_top)
        layout.addSpacing(0)  # 下边距0px
        
        self.content_widget = QWidget()
        self.content_widget.setObjectName("assetCardContent")
        # 样式由上方 setStyleSheet 中的 #assetCardContent 提供
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(16, 8, 16, 16)  # 调整边距
        content_layout.setSpacing(0)  # 无间距，让文本紧凑
        
        # 资产名称和分类 - 水平布局
        name_category_layout = QHBoxLayout()
        name_category_layout.setSpacing(8)
        name_category_layout.setContentsMargins(0, 0, 0, 4)
        
        # 资产名称 - 左对齐大标题
        self.name_label = QLabel(self.asset.name)
        self.name_label.setObjectName("assetCardName")
        # 样式由上方 setStyleSheet 中的 #assetCardName 提供
        self.name_label.setWordWrap(False)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        name_category_layout.addWidget(self.name_label, 1)  # stretch=1 让名称占据剩余空间
        
        # 分类标签 - 右对齐小标签
        self.category_label = QLabel(self.asset.category)
        self.category_label.setObjectName("assetCardCategory")
        # 样式由上方 setStyleSheet 中的 #assetCardCategory 提供
        self.category_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        name_category_layout.addWidget(self.category_label, 0)  # stretch=0 保持最小宽度
        
        content_layout.addLayout(name_category_layout)
        
        # 资产信息 - 纯文本垂直排列（小字体）
        # 样式由上方 setStyleSheet 中的 .assetCardInfo 提供
        
        try:
            # 中文类型映射
            type_name_map = {
                AssetType.PACKAGE: "资源包",
                AssetType.FILE: "文件"
            }
            type_display_name = type_name_map.get(self.asset.asset_type, "未知")
            
            # 资产大小
            size_text = self.asset._format_size() if hasattr(self.asset, '_format_size') else f"{getattr(self.asset, 'size', 0)} B"
            self.size_info_label = QLabel(f"资产大小：{size_text}")
            self.size_info_label.setProperty("class", "assetCardInfo")
            self.size_info_label.setAlignment(Qt.AlignmentFlag.AlignLeft)  # 左对齐
            content_layout.addWidget(self.size_info_label)
            
            # 资产类型
            self.type_info_label = QLabel(f"资产类型：{type_display_name}")
            self.type_info_label.setProperty("class", "assetCardInfo")
            self.type_info_label.setAlignment(Qt.AlignmentFlag.AlignLeft)  # 左对齐
            content_layout.addWidget(self.type_info_label)
            
            logger.debug(f"资产信息显示: 大小={size_text}, 类型={type_display_name}")
        except Exception as e:
            logger.error(f"创建资产信息标签失败: {e}", exc_info=True)
            self.error_label = QLabel("信息加载失败")
            self.error_label.setProperty("class", "assetCardInfo")
            self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            content_layout.addWidget(self.error_label)
        
        # 按钮区域 - 极简扁平设计（无弹性空间，紧凑布局）
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 预览按钮 - 主要操作,全宽设计
        self.preview_btn = QPushButton("▶  预览资产")
        self.preview_btn.setObjectName("assetCardPreviewBtn")
        # 样式由上方 setStyleSheet 中的 #assetCardPreviewBtn 提供
        self.preview_btn.setFixedHeight(32)
        self.preview_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.preview_btn.clicked.connect(lambda: self.preview_clicked.emit(self.asset.id))
        button_layout.addWidget(self.preview_btn, stretch=1)
        
        # 更多按钮 - 次要操作,图标化
        self.more_btn = QPushButton("⋮")
        self.more_btn.setObjectName("assetCardMoreBtn")
        # 样式由上方 setStyleSheet 中的 #assetCardMoreBtn 提供
        self.more_btn.setFixedSize(32, 32)
        self.more_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.more_btn.clicked.connect(self._show_context_menu)
        button_layout.addWidget(self.more_btn)
        
        content_layout.addLayout(button_layout)
        
        layout.addWidget(self.content_widget)
        
        self.setLayout(layout)
    
    def _load_thumbnail(self):
        """加载缩略图 - 高质量缩放"""
        try:
            if self.asset.thumbnail_path and Path(self.asset.thumbnail_path).exists():
                pixmap = QPixmap(str(self.asset.thumbnail_path))
                if not pixmap.isNull():
                    # 成功加载图片 - 保持比例填充容器
                    # 使用 KeepAspectRatioByExpanding 模式，图片会放大填充整个容器
                    # 超出部分会被 RoundedThumbnailWidget 的圆角路径裁剪
                    scaled_pixmap = pixmap.scaled(
                        QSize(216, 140),  # 容器完整尺寸
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,  # 保持比例填充
                        Qt.TransformationMode.SmoothTransformation  # 高质量缩放
                    )
                    # 清除文本,设置图片（圆角和居中由RoundedThumbnailWidget自动处理）
                    self.thumbnail_label.clear()
                    self.thumbnail_label.setPixmap(scaled_pixmap)
                    self.thumbnail_label.setWordWrap(False)
                    logger.debug(f"成功加载缩略图: {self.asset.name}")
                    return
                else:
                    logger.warning(f"缩略图文件损坏或无效: {self.asset.thumbnail_path}")
            
            # 没有缩略图或加载失败,显示默认图标
            self._show_default_icon()
            
        except Exception as e:
            logger.error(f"加载缩略图失败: {e}", exc_info=True)
            self._show_default_icon()
    
    def update_category_display(self, new_category: str):
        """更新分类显示
        
        Args:
            new_category: 新的分类名称
        """
        if hasattr(self, 'category_label'):
            self.category_label.setText(new_category)
            logger.debug(f"已更新资产 {self.asset.name} 的分类显示为: {new_category}")

    def _show_default_icon(self):
        """显示默认图标(文本) - 极简现代化设计"""
        # 根据资产类型显示不同的Emoji和文本
        if self.asset.asset_type == AssetType.PACKAGE:
            icon_emoji = "📦"
            icon_label = "资源包"
        else:
            # 文件类型：显示文件扩展名
            ext = self.asset.file_extension.upper() if self.asset.file_extension else "文件"
            icon_emoji = "📄"
            icon_label = ext
        
        icon_text = f"{icon_emoji}\n{icon_label}"
        
        # 设置默认图标文本（圆角由RoundedThumbnailWidget自动处理）
        self.thumbnail_label.setText(icon_text)
        self.thumbnail_label.setWordWrap(True)
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logger.debug(f"显示默认图标文本: {self.asset.name} - {icon_text}")
    
    def _open_asset_location(self):
        """打开资产所在文件夹"""
        try:
            import subprocess
            import sys
            from pathlib import Path
            
            asset_path = Path(self.asset.path)
            
            # 如果是文件，获取其父目录；如果是文件夹，直接使用该路径
            if asset_path.is_file():
                folder_path = asset_path.parent
                # 打开文件夹并选中该文件
                if sys.platform == "win32":
                    # Windows: 使用 explorer /select 命令选中文件
                    subprocess.run(['explorer', '/select,', str(asset_path)])
                    logger.info(f"[AssetCard] 在资源管理器中打开并选中: {asset_path}")
                elif sys.platform == "darwin":
                    # macOS: 使用 open -R 命令选中文件
                    subprocess.run(['open', '-R', str(asset_path)])
                    logger.info(f"[AssetCard] 在 Finder 中打开并选中: {asset_path}")
                else:
                    # Linux: 打开父文件夹（大多数文件管理器不支持选中文件）
                    subprocess.run(['xdg-open', str(folder_path)])
                    logger.info(f"[AssetCard] 打开文件夹: {folder_path}")
            elif asset_path.is_dir():
                # 如果是文件夹，直接打开该文件夹
                if sys.platform == "win32":
                    subprocess.run(['explorer', str(asset_path)])
                    logger.info(f"[AssetCard] 在资源管理器中打开文件夹: {asset_path}")
                elif sys.platform == "darwin":
                    subprocess.run(['open', str(asset_path)])
                    logger.info(f"[AssetCard] 在 Finder 中打开文件夹: {asset_path}")
                else:
                    subprocess.run(['xdg-open', str(asset_path)])
                    logger.info(f"[AssetCard] 打开文件夹: {asset_path}")
            else:
                logger.warning(f"[AssetCard] 资产路径不存在: {asset_path}")
                
        except Exception as e:
            logger.error(f"[AssetCard] 打开资产所在位置失败: {e}", exc_info=True)
    
    def _show_context_menu(self):
        """显示右键菜单 - 现代化设计，鼠标移开自动关闭"""
        tm = self.theme_manager
        menu = QMenu(self)
        menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        menu.setWindowFlags(
            Qt.WindowType.Popup |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.NoDropShadowWindowHint
        )
        # 现代化菜单样式 - 圆角 + 渐变高亮
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {tm.get_variable('bg_secondary')};
                color: {tm.get_variable('text_primary')};
                border: 1px solid {tm.get_variable('border')};
                border-radius: 8px;
                padding: 6px;
            }}
            QMenu::item {{
                padding: 10px 35px;
                background-color: transparent;
                border-radius: 6px;
                font-size: 11px;
            }}
            QMenu::item:selected {{
                background: {tm.get_variable('accent')};
                color: white;
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {tm.get_variable('border')};
                margin: 4px 8px;
            }}
        """)
        
        # 迁移资产
        migrate_action = QAction("迁移到工程", menu)
        migrate_action.triggered.connect(lambda: self.migrate_clicked.emit(self.asset.id))
        menu.addAction(migrate_action)
        
        # 编辑信息
        edit_info_action = QAction("编辑信息", menu)
        edit_info_action.triggered.connect(lambda: self.edit_info_clicked.emit(self.asset.id))
        menu.addAction(edit_info_action)
        
        # 打开资产所在路径
        open_location_action = QAction("打开所在位置", menu)
        open_location_action.triggered.connect(self._open_asset_location)
        menu.addAction(open_location_action)
        
        menu.addSeparator()
        
        # 删除资产
        delete_action = QAction("删除资产", menu)
        delete_action.triggered.connect(lambda: self.delete_clicked.emit(self.asset.id))
        menu.addAction(delete_action)
        
        # 安装事件过滤器，实现鼠标移开自动关闭，并传递卡片引用用于清除悬停状态
        self.menu_event_filter = MenuEventFilter(menu, card_widget=self)
        
        menu.popup(QCursor.pos())
    
    def refresh_theme(self):
        """刷新主题样式 - 在主题切换时调用"""
        try:
            tm = self.theme_manager
            
            self.setStyleSheet(f"""
                #assetCard {{
                    background-color: {tm.get_variable('bg_secondary')};
                    border: none;
                    border-radius: 16px;
                }}
                #assetCard:hover {{
                    background-color: {tm.get_variable('bg_tertiary')};
                    border: 2px solid {tm.get_variable('border_hover')};
                }}
                #assetCardContent {{
                    background-color: transparent;
                }}
                #assetCardSeparator {{
                    background-color: {tm.get_variable('text_primary')};
                    border: none;
                    margin: 0px 12px;
                }}
                #assetCardName {{
                    color: {tm.get_variable('text_primary')};
                    font-size: 14px;
                    font-weight: 600;
                }}
                #assetCardCategory {{
                    color: {tm.get_variable('text_secondary')};
                    font-size: 10px;
                    background-color: {tm.get_variable('bg_tertiary')};
                    border-radius: 4px;
                    padding: 2px 8px;
                }}
                #assetCardPreviewBtn {{
                    background: {tm.get_variable('info')};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 12px;
                    font-weight: 600;
                    letter-spacing: 0.5px;
                }}
                #assetCardPreviewBtn:hover {{
                    background: {tm.get_variable('border_hover')};
                }}
                #assetCardPreviewBtn:pressed {{
                    background: {tm.get_variable('accent_pressed')};
                }}
                #assetCardMoreBtn {{
                    background-color: {tm.get_variable('bg_tertiary')};
                    color: {tm.get_variable('text_secondary')};
                    border: 1px solid {tm.get_variable('border')};
                    border-radius: 8px;
                    font-size: 20px;
                    font-weight: bold;
                }}
                #assetCardMoreBtn:hover {{
                    background-color: {tm.get_variable('bg_hover')};
                    border-color: {tm.get_variable('border_hover')};
                    color: {tm.get_variable('text_primary')};
                }}
                #assetCardMoreBtn:pressed {{
                    background-color: {tm.get_variable('bg_pressed')};
                }}
                QLabel[class="assetCardInfo"] {{
                    color: {tm.get_variable('text_secondary')};
                    font-size: 11px;
                    padding: 0px 8px;
                    margin: 1px 0px;
                }}
            """)
            
            if hasattr(self, 'thumbnail_label'):
                self.thumbnail_label.theme_manager = tm
                bg_color = tm.get_variable('bg_tertiary')
                logger = get_logger(__name__)
                logger.debug(f"刷新缩略图主题，背景色将使用: {bg_color}")
                self.thumbnail_label.update()  # 触发重绘以应用新主题
            
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"刷新资产卡片主题失败: {e}", exc_info=True)

