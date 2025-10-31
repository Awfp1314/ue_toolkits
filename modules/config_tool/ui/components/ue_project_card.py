# -*- coding: utf-8 -*-

"""
UE工程卡片组件
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QRect
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QPainterPath, QBrush
from pathlib import Path

from core.logger import get_logger
from core.utils.theme_manager import get_theme_manager

logger = get_logger(__name__)


class RoundedThumbnailWidget(QWidget):
    """带圆角的缩略图容器 - 直接绘制圆角图片"""
    
    def __init__(self, width: int, height: int, radius: int = 12, parent=None, theme_manager=None):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self.radius = radius
        self._pixmap = None
        self._text = ""
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
    
    def paintEvent(self, event):
        """绘制圆角缩略图"""
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
            # 图片已经在加载时裁剪到精确尺寸，直接从(0,0)绘制
            painter.drawPixmap(0, 0, self._pixmap)
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
            painter.drawText(widget_rect, Qt.AlignmentFlag.AlignCenter, self._text)
        
        painter.end()


class UEProjectCard(QFrame):
    """UE工程卡片组件"""
    
    clicked = pyqtSignal(object)  # 发送工程对象
    
    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project
        self.theme_manager = get_theme_manager()
        self.is_selected = False
        self.thumbnail_pixmap = None
        self.engine_version = None  # 缓存版本号
        
        self.setObjectName("projectCard")
        self.setFixedSize(205, 210)  # 卡片总大小（宽度与缩略图一致为200）
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._init_ui()
        self._load_thumbnail()
        self._load_engine_version()  # 初始化时加载版本号
        self._apply_style()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 使用圆角缩略图容器（宽度从220改为200）
        self.thumbnail_widget = RoundedThumbnailWidget(
            width=200, 
            height=150, 
            radius=12, 
            parent=self,
            theme_manager=self.theme_manager
        )
        self.thumbnail_widget.setObjectName("thumbnailWidget")
        layout.addWidget(self.thumbnail_widget)
        
        # 版本号标签 - 浮动在缩略图右下角
        self.version_label = QLabel(self.thumbnail_widget)
        self.version_label.setObjectName("versionLabel")
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.version_label.setVisible(False)  # 默认隐藏，加载版本号后显示
        
        # 工程名称标签
        self.name_label = QLabel(self.project.name)
        self.name_label.setObjectName("nameLabel")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setFixedHeight(60)
        layout.addWidget(self.name_label)
    
    def _load_thumbnail(self):
        """加载缩略图"""
        try:
            # 获取工程的 Saved 目录
            project_dir = self.project.project_path.parent
            saved_dir = project_dir / "Saved"
            
            if not saved_dir.exists():
                self._show_default_thumbnail()
                return
            
            # 扫描 Saved 目录下的图片文件（非递归）
            image_files = []
            for ext in ['*.png', '*.jpg', '*.jpeg']:
                image_files.extend(saved_dir.glob(ext))
            
            if not image_files:
                self._show_default_thumbnail()
                return
            
            # 选择最新的截图
            latest_image = max(image_files, key=lambda p: p.stat().st_mtime)
            
            # 加载并缩放图片（宽度从220改为200）
            pixmap = QPixmap(str(latest_image))
            if not pixmap.isNull():
                # 缩放到固定大小，保持宽高比填充
                scaled_pixmap = pixmap.scaled(
                    200, 150,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                # 裁剪到精确的 200x150 尺寸（居中裁剪）
                if scaled_pixmap.width() > 200 or scaled_pixmap.height() > 150:
                    x_offset = (scaled_pixmap.width() - 200) // 2
                    y_offset = (scaled_pixmap.height() - 150) // 2
                    scaled_pixmap = scaled_pixmap.copy(x_offset, y_offset, 200, 150)
                
                self.thumbnail_pixmap = scaled_pixmap
                self.thumbnail_widget.setPixmap(scaled_pixmap)
                logger.debug(f"成功加载工程缩略图: {self.project.name} (裁剪后尺寸: {scaled_pixmap.width()}x{scaled_pixmap.height()})")
            else:
                self._show_default_thumbnail()
                
        except Exception as e:
            logger.error(f"加载工程缩略图失败: {e}", exc_info=True)
            self._show_default_thumbnail()
    
    def _show_default_thumbnail(self):
        """显示默认缩略图"""
        # 使用 RoundedThumbnailWidget 的 setText 方法显示默认文本
        self.thumbnail_widget.setText("UE\nProject")
        self.thumbnail_pixmap = None
    
    def _apply_style(self):
        """应用样式"""
        tm = self.theme_manager
        
        if self.is_selected:
            border_color = tm.get_variable('accent')
            bg_color = tm.get_variable('bg_hover')
        else:
            border_color = tm.get_variable('border')
            bg_color = tm.get_variable('bg_secondary')
        
        self.setStyleSheet(f"""
            #projectCard {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 8px;
            }}
            #nameLabel {{
                color: {tm.get_variable('text_primary')};
                font-size: 13px;
                font-weight: bold;
                padding: 8px;
                background: transparent;
            }}
        """)
    
    def _load_engine_version(self):
        """从 .uproject 文件中加载引擎版本并缓存"""
        try:
            import json
            project_path = self.project.project_path
            logger.info(f"尝试读取工程版本: {project_path}")
            
            if not project_path.exists():
                logger.warning(f"工程文件不存在: {project_path}")
                self.engine_version = None
                return
                
            with open(project_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
                # UE项目文件中的版本信息
                engine_association = project_data.get('EngineAssociation', '')
                logger.info(f"读取到版本信息: '{engine_association}' (工程: {self.project.name})")
                
                if engine_association:
                    self.engine_version = str(engine_association)
                    logger.info(f"成功缓存版本号: {self.engine_version}")
                    # 更新版本号标签
                    self._update_version_label()
                else:
                    logger.warning(f"工程 {self.project.name} 的 EngineAssociation 字段为空")
                    self.engine_version = None
                    
        except Exception as e:
            logger.error(f"读取工程版本失败 {self.project.name}: {e}", exc_info=True)
            self.engine_version = None
    
    def _update_version_label(self):
        """更新版本号标签的显示和位置"""
        if not self.engine_version:
            self.version_label.setVisible(False)
            return
        
        # 设置文本
        self.version_label.setText(self.engine_version)
        
        # 设置样式 - 半透明黑色背景，白色文字
        self.version_label.setStyleSheet("""
            QLabel#versionLabel {
                background-color: rgba(0, 0, 0, 200);
                color: white;
                font-size: 11pt;
                font-weight: bold;
                padding: 4px 8px;
                border-radius: 4px;
            }
        """)
        
        # 计算标签大小
        self.version_label.adjustSize()
        label_width = self.version_label.width()
        label_height = self.version_label.height()
        
        # 定位到缩略图右下角（向内偏移8px，宽度从220改为200）
        margin = 8
        x = 200 - label_width - margin
        y = 150 - label_height - margin
        
        self.version_label.move(x, y)
        self.version_label.setVisible(True)
        
        logger.info(f"版本号标签已定位: '{self.engine_version}' 在位置 ({x}, {y})，尺寸 ({label_width}, {label_height})")
    
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.project)
        super().mousePressEvent(event)
    
    def set_selected(self, selected: bool):
        """设置选中状态"""
        self.is_selected = selected
        self._apply_style()
        self.update()  # 触发重绘


