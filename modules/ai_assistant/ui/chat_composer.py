# -*- coding: utf-8 -*-
"""
ChatGPT 风格输入框组件 - 统一实现
完全模仿 ChatGPT 网页端的胶囊输入条
"""

from typing import List, Optional
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QMimeData
from PyQt6.QtGui import QFont, QKeyEvent, QPixmap, QImage
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QTextEdit, QPushButton,
    QWidget, QSizePolicy, QGraphicsDropShadowEffect
)
import base64
from PyQt6.QtCore import QBuffer


def safe_print(msg: str):
    """安全的 print 函数，避免 Windows 控制台编码错误"""
    try:
        print(msg, flush=True)
    except (OSError, UnicodeEncodeError):
        # 如果 print 失败，忽略（不要让调试输出导致程序崩溃）
        pass


class _GrowTextEdit(QTextEdit):
    """自适应高度的文本编辑框"""
    heightChanged = pyqtSignal(int)

    def __init__(self, min_h=36, max_h=200, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._min_h = min_h
        self._max_h = max_h
        self._is_locked = False
        self.setAcceptRichText(False)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.document().setDocumentMargin(0)
        self.textChanged.connect(self._recalc_height)

    def minimumSizeHint(self):
        return QSize(super().minimumSizeHint().width(), self._min_h)

    def _compute_doc_height(self) -> int:
        """计算文档高度（包含 contentsMargins，其中包括 QSS padding）"""
        doc = self.document()
        doc.setTextWidth(self.viewport().width())
        doc_height = int(doc.size().height())
        # contentsMargins 会包含 QSS 的 padding
        margins = self.contentsMargins()
        return doc_height + margins.top() + margins.bottom()

    def _recalc_height(self):
        h = max(self._min_h, min(self._compute_doc_height(), self._max_h))
        if self.height() != h:
            self.setFixedHeight(h)
            self.heightChanged.emit(h)
        if self._compute_doc_height() > self._max_h:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        else:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._recalc_height()

    def lock(self):
        """锁定输入框，阻止编辑"""
        self._is_locked = True

    def unlock(self):
        """解锁输入框"""
        self._is_locked = False

    def keyPressEvent(self, event):
        if self._is_locked:
            event.ignore()
            return
        super().keyPressEvent(event)

    def insertFromMimeData(self, source):
        """支持图片粘贴"""
        if self._is_locked:
            return
        if source.hasImage():
            image = source.imageData()
            if isinstance(image, QImage):
                # 发送信号，不插入到文本
                if hasattr(self.parent(), 'on_image_pasted'):
                    pixmap = QPixmap.fromImage(image)
                    self.parent().on_image_pasted(pixmap)
            return
        super().insertFromMimeData(source)


class ChatGPTComposer(QFrame):
    """ChatGPT 风格输入条组件"""
    submitted = pyqtSignal(str)
    submitted_detail = pyqtSignal(str, list)   # text + List[str] (base64)
    stop_requested = pyqtSignal()
    height_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None, attachments_enabled: bool = True):
        super().__init__(parent)
        self.setObjectName("ComposerRoot")
        self._attachments_enabled = attachments_enabled
        self._is_generating = False
        self._images: List[QPixmap] = []
        self._images_base64: List[str] = []
        self._last_message = ""
        self._last_images = []

        # ===== 关键修复：确保背景样式生效 =====
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        # 预览容器
        self._preview_holder = QFrame(self)
        self._preview_holder.setObjectName("ComposerPreviewHolder")
        self._preview_holder.setVisible(False)
        self._preview_holder.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        ph_layout = QHBoxLayout(self._preview_holder)
        ph_layout.setContentsMargins(2, 2, 2, 2)
        ph_layout.setSpacing(6)
        root.addWidget(self._preview_holder)

        # 胶囊外壳
        self.shell = QFrame(self)
        self.shell.setObjectName("ComposerShell")
        self.shell.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        # ===== 关键修复：设置初始属性 =====
        self.shell.setProperty("focus", "false")
        self.shell.setProperty("hasText", "false")
        self.shell.setMinimumHeight(36)  # 减小最小高度到 36px
        # 添加边框阴影效果
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(8)  # 较小的模糊半径，更贴近边框
        shadow.setColor(QColor(0x20, 0x20, 0x20, 120))  # #202020，透明度 120
        shadow.setOffset(0, 1)  # 向下偏移 1px
        self.shell.setGraphicsEffect(shadow)

        shell_h = QHBoxLayout(self.shell)
        shell_h.setContentsMargins(8, 4, 8, 4)  # 减小 padding：左右 8px，上下 4px
        shell_h.setSpacing(6)  # 减小间距到 6px

        # 左：加号
        self.btn_plus = QPushButton("+", self.shell)  # 直接设置文本
        self.btn_plus.setObjectName("PlusButton")
        self.btn_plus.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_plus.setToolTip("添加附件")
        self.btn_plus.setFixedSize(32, 32)  # 减小按钮尺寸
        shell_h.addWidget(self.btn_plus, 0, Qt.AlignmentFlag.AlignVCenter)

        # 中：文本框（自增高）
        self.edit = _GrowTextEdit(parent=self.shell)
        self.edit.setObjectName("ComposerEdit")
        self.edit.setPlaceholderText("询问任何问题")
        self.edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        font = QFont()
        font.setPointSize(14)
        self.edit.setFont(font)
        self.edit.installEventFilter(self)
        self.edit.heightChanged.connect(self._on_edit_height_changed)
        shell_h.addWidget(self.edit, 1)

        # 右：发送/停止
        self.btn_send = QPushButton("↑", self.shell)  # 直接设置文本（向上箭头）
        self.btn_send.setObjectName("SendButton")
        self.btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send.setFixedSize(32, 32)  # 减小按钮尺寸
        # ===== 关键修复：设置初始状态 =====
        self.btn_send.setProperty("state", "send")
        self.btn_send.clicked.connect(self._on_send_clicked)
        shell_h.addWidget(self.btn_send, 0, Qt.AlignmentFlag.AlignVCenter)

        root.addWidget(self.shell)

        # 下方提示
        self.hint = QLabel("Enter 发送 · Shift+Enter 换行")
        self.hint.setObjectName("ComposerHint")
        self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.hint)

        # 行为
        self.edit.textChanged.connect(self._update_send_enabled)
        self._update_send_enabled()

        # focus-within 属性模拟
        self.edit.focusInEvent = self._wrap_focus(self.edit.focusInEvent, True)
        self.edit.focusOutEvent = self._wrap_focus(self.edit.focusOutEvent, False)

        # 拖拽
        self.setAcceptDrops(self._attachments_enabled)
        self.shell.setAcceptDrops(self._attachments_enabled)
        
        # ===== 关键修复：初始化后强制刷新样式 =====
        from PyQt6.QtCore import QTimer
        # 延迟刷新，确保QSS已加载
        QTimer.singleShot(0, self._force_style_refresh)
    
    def _load_qss_from_file(self, theme: str = "dark") -> str:
        """从外部 QSS 文件加载样式
        
        Args:
            theme: 主题名称 (dark/light)
            
        Returns:
            str: QSS 内容，加载失败返回空字符串
        """
        from pathlib import Path
        
        # 组件样式文件路径
        qss_path = Path(__file__).parent.parent / "resources" / "themes" / f"chatgpt_composer_{theme}.qss"
        
        # 如果主题文件不存在，回退到默认样式
        if not qss_path.exists():
            qss_path = Path(__file__).parent.parent / "resources" / "themes" / "chatgpt_composer_dark.qss"
        
        # 如果默认样式也不存在，使用全局组件样式
        if not qss_path.exists():
            qss_path = Path(__file__).parent.parent.parent.parent / "resources" / "qss" / "components" / "chatgpt_composer.qss"
        
        try:
            if qss_path.exists():
                qss_content = qss_path.read_text(encoding="utf-8")
                safe_print(f"[ChatGPTComposer] Loaded QSS from: {qss_path.name}")
                return qss_content
            else:
                safe_print(f"[ChatGPTComposer] QSS file not found: {qss_path}")
                return ""
        except Exception as e:
            safe_print(f"[ChatGPTComposer] Failed to load QSS: {e}")
            return ""
    
    def _get_current_theme(self) -> str:
        """获取当前主题名称
        
        Returns:
            str: 主题名称 (dark/light)
        """
        try:
            from core.utils.theme_manager import get_theme_manager
            theme_manager = get_theme_manager()
            theme = theme_manager.current_theme.value  # 返回 'dark' 或 'light'
            return theme
        except Exception as e:
            safe_print(f"[ChatGPTComposer] Failed to get theme: {e}, using 'dark'")
            return "dark"
    
    def _force_style_refresh(self):
        """强制刷新所有组件样式（从外部 QSS 文件加载）"""
        # 获取当前主题
        theme = self._get_current_theme()
        
        # 从外部文件加载 QSS
        qss_content = self._load_qss_from_file(theme)
        
        if qss_content:
            # 成功加载外部 QSS，应用到组件
            self.setStyleSheet(qss_content)
            safe_print(f"[ChatGPTComposer] Applied external QSS (theme: {theme})")
        else:
            # 加载失败，使用内联兜底样式
            safe_print(f"[ChatGPTComposer] Using fallback inline styles (theme: {theme})")
            fallback_qss = self._get_fallback_qss(theme)
            self.setStyleSheet(fallback_qss)
        
        # 设置 placeholder 颜色与输入文字颜色一致
        from PyQt6.QtGui import QPalette, QColor
        palette = self.edit.palette()
        text_color = palette.color(QPalette.ColorRole.Text)
        palette.setColor(QPalette.ColorRole.PlaceholderText, text_color)
        self.edit.setPalette(palette)
        
        # 刷新所有组件样式
        for widget in [self, self.shell, self.btn_send, self.btn_plus, 
                       self._preview_holder, self.edit, self.hint]:
            if widget:
                widget.style().unpolish(widget)
                widget.style().polish(widget)
                widget.update()
    
    def _get_fallback_qss(self, theme: str = "dark") -> str:
        """获取兜底的内联样式
        
        Args:
            theme: 主题名称 (dark/light)
            
        Returns:
            str: 内联 QSS 样式
        """
        if theme == "light":
            # 浅色主题
            return """
            QFrame#ComposerShell {
                background-color: #ffffff;
                border: 1px solid #d1d5db;
                border-radius: 22px;
                min-height: 36px;
                padding: 4px 8px;
            }
            QFrame#ComposerShell[focus="true"] {
                border: 1px solid #9ca3af;
            }
            QPushButton#PlusButton {
                background-color: transparent;
                color: #6b7280;
                border: none;
                border-radius: 16px;
                font-size: 16px;
                min-width: 32px;
                max-width: 32px;
                min-height: 32px;
                max-height: 32px;
            }
            QPushButton#PlusButton:hover {
                background-color: rgba(0, 0, 0, 0.05);
            }
                    QTextEdit#ComposerEdit {
                        background-color: transparent;
                        color: #111827;
                        border: none;
                        padding: 10px 4px 8px 4px;
                    }
            QPushButton#SendButton {
                background-color: #10a37f;
                color: #ffffff;
                border: none;
                border-radius: 16px;
                font-size: 16px;
                font-weight: bold;
                min-width: 32px;
                max-width: 32px;
                min-height: 32px;
                max-height: 32px;
            }
            QPushButton#SendButton:enabled:hover {
                background-color: #0e9070;
            }
            QPushButton#SendButton:disabled {
                background-color: #d1d5db;
                color: #9ca3af;
            }
            QPushButton#SendButton[state="stop"] {
                background-color: #ef4444;
                color: #ffffff;
            }
            QPushButton#SendButton[state="stop"]:hover {
                background-color: #dc2626;
            }
            QLabel#ComposerHint {
                color: #6b7280;
                font-size: 12px;
                background-color: transparent;
            }
            """
        else:
            # 深色主题（默认）
            return """
            QFrame#ComposerShell {
                background-color: #303030;
                border: 1px solid #323232;
                border-radius: 22px;
                min-height: 36px;
                padding: 4px 8px;
            }
            QFrame#ComposerShell[focus="true"] {
                border: 1px solid #8E8EA0;
                background-color: #303030;
            }
            QFrame#ComposerShell[hasText="true"] {
                background-color: #2a2a2a;
            }
            QPushButton#PlusButton {
                background-color: transparent;
                color: #C5C5D2;
                border: none;
                border-radius: 16px;
                font-size: 16px;
                min-width: 32px;
                max-width: 32px;
                min-height: 32px;
                max-height: 32px;
            }
            QPushButton#PlusButton:hover {
                background-color: rgba(255, 255, 255, 0.08);
            }
                    QTextEdit#ComposerEdit {
                        background-color: transparent;
                        color: #ECECF1;
                        border: none;
                        padding: 10px 4px 8px 4px;
                    }
            QPushButton#SendButton {
                background-color: #b23565;
                color: #ffffff;
                border: none;
                border-radius: 16px;
                font-size: 16px;
                font-weight: bold;
                min-width: 32px;
                max-width: 32px;
                min-height: 32px;
                max-height: 32px;
            }
            QPushButton#SendButton:enabled:hover {
                background-color: #c34676;
            }
            QPushButton#SendButton:disabled {
                background-color: #565869;
                color: #ACACBE;
            }
            QPushButton#SendButton[state="stop"] {
                background-color: #ef4444;
                color: #ffffff;
            }
            QPushButton#SendButton[state="stop"]:hover {
                background-color: #dc2626;
            }
            QLabel#ComposerHint {
                color: #8E8EA0;
                font-size: 12px;
                background-color: transparent;
            }
            """
    
    def refresh_theme(self, theme: str = None):
        """响应主题切换（可被主题系统调用）
        
        Args:
            theme: 主题名称，None 时自动检测
        """
        safe_print(f"[ChatGPTComposer] Theme refresh requested (theme: {theme or 'auto'})")
        # 主题切换时重新加载样式
        self._force_style_refresh()

    # ---- focus-within ----
    def _wrap_focus(self, original, focus_in: bool):
        def _handler(ev):
            res = original(ev) if original else None
            self.shell.setProperty("focus", "true" if focus_in else "false")
            self.shell.style().unpolish(self.shell)
            self.shell.style().polish(self.shell)
            return res
        return _handler

    # ---- 发送按钮可用性 ----
    def _has_content(self) -> bool:
        return (self.edit.toPlainText().strip() != "") or (len(self._images) > 0)

    def _update_send_enabled(self):
        enable = (not self._is_generating) and self._has_content()
        self.btn_send.setEnabled(enable)
        self.shell.setProperty("hasText", "true" if self.edit.toPlainText().strip() else "false")
        self.shell.style().unpolish(self.shell)
        self.shell.style().polish(self.shell)

    def _on_edit_height_changed(self, h: int):
        self.shell.setMinimumHeight(h + 8)  # 上下 padding 各 4px
        self.height_changed.emit()

    # ---- 附件预览 ----
    def on_image_pasted(self, pixmap: QPixmap):
        """处理粘贴的图片"""
        self.add_image_preview(pixmap)

    def add_image_preview(self, pixmap: QPixmap):
        card = QFrame(self._preview_holder)
        card.setObjectName("ImageCard")
        h = QHBoxLayout(card)
        h.setContentsMargins(6, 6, 6, 6)
        h.setSpacing(6)
        img = QLabel(card)
        img.setPixmap(pixmap.scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation))
        h.addWidget(img)
        rm = QPushButton("×", card)
        rm.setObjectName("RemoveImage")
        rm.setFixedSize(22, 22)

        def _remove():
            card.setParent(None)
            self._images = [i for i in self._images if i.cacheKey() != pixmap.cacheKey()]
            self._images_base64 = [self._pixmap_to_base64(i) for i in self._images]
            self._preview_holder.setVisible(len(self._images) > 0)
            self._update_send_enabled()
        rm.clicked.connect(_remove)
        h.addWidget(rm)
        self._preview_holder.layout().addWidget(card)
        self._preview_holder.setVisible(True)
        self._images.append(pixmap)
        self._images_base64.append(self._pixmap_to_base64(pixmap))
        self._update_send_enabled()

    def _pixmap_to_base64(self, pixmap: QPixmap) -> str:
        """转换 QPixmap 为 base64"""
        buffer = QBuffer()
        buffer.open(QBuffer.OpenModeFlag.ReadWrite)
        pixmap.save(buffer, "PNG")
        return base64.b64encode(buffer.data()).decode("utf-8")

    def dragEnterEvent(self, e):
        if not self._attachments_enabled:
            e.ignore()
            return
        md: QMimeData = e.mimeData()
        if md.hasImage() or any(u for u in md.urls() if u.isLocalFile()):
            e.acceptProposedAction()
        else:
            e.ignore()

    def dropEvent(self, e):
        if not self._attachments_enabled:
            e.ignore()
            return
        md: QMimeData = e.mimeData()
        if md.hasImage():
            img = md.imageData()
            if isinstance(img, QImage):
                self.add_image_preview(QPixmap.fromImage(img))
        for u in md.urls():
            if u.isLocalFile():
                pm = QPixmap(u.toLocalFile())
                if not pm.isNull():
                    self.add_image_preview(pm)
        e.acceptProposedAction()

    # ---- 键盘行为 ----
    def eventFilter(self, obj, ev):
        if obj is self.edit and ev.type() == ev.Type.KeyPress:
            ke: QKeyEvent = ev
            if ke.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if ke.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                    self.edit.textCursor().insertText("\n")
                    return True
                elif ke.modifiers() == Qt.KeyboardModifier.NoModifier:
                    self._on_send_clicked()
                    return True
        return super().eventFilter(obj, ev)

    # ---- 发送/停止 ----
    def _on_send_clicked(self):
        if self._is_generating:
            self.stop_requested.emit()
            return
        text = self.edit.toPlainText().strip()
        if not text and not self._images:
            return

        # ⚡ 关键修复：立即设置生成状态，防止重复点击
        # 在清空输入框和发射信号之前就设置，避免在 processEvents 时重复触发
        self.set_generating(True)

        # 保存消息
        self._last_message = text
        self._last_images = self._images_base64.copy()

        # 只发射一个信号，避免重复处理
        if self._images_base64:
            # 如果有图片，只发射 submitted_detail
            self.submitted_detail.emit(text, self._images_base64.copy())
        else:
            # 如果没有图片，只发射 submitted
            self.submitted.emit(text)
        
        self.edit.clear()
        self._images.clear()
        self._images_base64.clear()
        for i in reversed(range(self._preview_holder.layout().count())):
            w = self._preview_holder.layout().itemAt(i).widget()
            if w:
                w.setParent(None)
        self._preview_holder.setVisible(False)

    # ---- 对外 API ----
    def set_generating(self, generating: bool):
        safe_print(f"[DEBUG] set_generating 被调用: {generating}")
        
        # 添加调用栈追踪（只在设置为True时）
        if generating:
            import traceback
            safe_print("[DEBUG] ===== 调用栈追踪 =====")
            for line in traceback.format_stack()[:-1]:  # 排除当前行
                safe_print(line.strip())
            safe_print("[DEBUG] ========================")
        
        self._is_generating = generating
        if generating:
            self.btn_send.setEnabled(True)
            self.btn_send.setProperty("state", "stop")
            self.btn_send.setText("■")  # 生成中显示停止图标
            safe_print("[DEBUG] 按钮设置为 stop 状态，文本: ■")
            self.edit.lock()
        else:
            self.btn_send.setProperty("state", "send")
            self.btn_send.setText("↑")  # 恢复发送图标
            safe_print("[DEBUG] 按钮设置为 send 状态，文本: ↑")
            self.edit.unlock()
            self._update_send_enabled()
        self.btn_send.style().unpolish(self.btn_send)
        self.btn_send.style().polish(self.btn_send)
        safe_print(f"[DEBUG] 按钮状态已更新，enabled: {self.btn_send.isEnabled()}")

    def restore_message(self, text: str = None):
        """恢复消息（停止生成时）"""
        if text is None:
            text = self._last_message
        self.edit.setPlainText(text or "")
        # 恢复图片（可选）
        self._update_send_enabled()

    # ---- 兼容性 API ----
    @property
    def input_field(self):
        """兼容旧代码"""
        return self.edit

    @property
    def send_button(self):
        """兼容旧代码"""
        return self.btn_send

    def get_selected_model(self):
        """获取选中的模型（从配置文件读取）"""
        try:
            from core.config.config_manager import ConfigManager
            from pathlib import Path
            from modules.ai_assistant.config_schema import get_ai_assistant_schema
            
            template_path = Path(__file__).parent.parent / "config_template.json"
            config_manager = ConfigManager(
                "ai_assistant",
                template_path=template_path,
                config_schema=get_ai_assistant_schema()
            )
            config = config_manager.get_module_config()
            
            # 根据供应商返回对应的模型
            provider = config.get("llm_provider", "api")
            if provider == "api":
                return config.get("api_settings", {}).get("default_model", "gemini-2.5-flash")
            else:  # ollama
                return config.get("ollama_settings", {}).get("model_name", "llama3")
        except Exception as e:
            print(f"[ERROR] 读取模型配置失败: {e}")
            return "gemini-2.5-flash"  # fallback

    def save_and_clear_message(self):
        """兼容旧代码"""
        self._last_message = self.edit.toPlainText().strip()
        self._last_images = self._images_base64.copy()
        self.edit.clear()
        self._images.clear()
        self._images_base64.clear()
        for i in reversed(range(self._preview_holder.layout().count())):
            w = self._preview_holder.layout().itemAt(i).widget()
            if w:
                w.setParent(None)
        self._preview_holder.setVisible(False)
        # 强制更新文档布局，然后重置高度
        self.edit.document().setTextWidth(self.edit.viewport().width())  # 更新文档宽度
        self.edit.setFixedHeight(self.edit._min_h)                       # 直接重置为最小高度 (36px)
        self.shell.setMinimumHeight(self.edit._min_h + 8)               # 同步更新外壳高度
        self.height_changed.emit()                                        # 发射高度变化信号
        self.set_generating(True)

    # ---- 诊断与自检 ----
    def run_diagnostics(self) -> dict:
        """运行组件诊断，返回各项检查结果"""
        from PyQt6.QtWidgets import QApplication
        
        results = {}
        
        # 1. QSS 加载检查
        app = QApplication.instance()
        app_qss = app.styleSheet() if app else ""
        results["qss_loaded"] = "#ComposerShell" in app_qss and "#SendButton" in app_qss
        
        # 2. 对象名检查
        expected_names = {
            "ComposerRoot": self.objectName(),
            "ComposerShell": self.shell.objectName(),
            "ComposerEdit": self.edit.objectName(),
            "SendButton": self.btn_send.objectName(),
            "PlusButton": self.btn_plus.objectName(),
            "ComposerHint": self.hint.objectName(),
            "ComposerPreviewHolder": self._preview_holder.objectName()
        }
        results["object_names_ok"] = all(
            expected == actual 
            for expected, actual in expected_names.items()
        )
        
        # 3. WA_StyledBackground 检查
        results["styled_background_ok"] = (
            self.testAttribute(Qt.WidgetAttribute.WA_StyledBackground) and
            self.shell.testAttribute(Qt.WidgetAttribute.WA_StyledBackground) and
            self._preview_holder.testAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        )
        
        # 4. 初始属性检查
        shell_focus = self.shell.property("focus")
        shell_has_text = self.shell.property("hasText")
        send_state = self.btn_send.property("state")
        results["initial_props_ok"] = (
            shell_focus in ("false", False, None) and
            shell_has_text in ("false", False, None) and
            send_state in ("send", None)
        )
        
        # 5. 最小尺寸检查
        results["min_sizes_ok"] = (
            self.shell.minimumHeight() >= 44 and
            self.btn_send.width() == 36 and self.btn_send.height() == 36 and
            self.btn_plus.width() == 36 and self.btn_plus.height() == 36
        )
        
        # 6. Enter 行为检查（模拟按键）
        try:
            self._enter_triggered = False
            self._shift_enter_triggered = False
            
            # 临时连接信号
            def on_submit(text):
                self._enter_triggered = True
            self.submitted.connect(on_submit)
            
            # 模拟 Enter（需要有内容才会触发）
            self.edit.setPlainText("test")
            from PyQt6.QtGui import QKeyEvent
            from PyQt6.QtCore import QEvent
            enter_event = QKeyEvent(
                QEvent.Type.KeyPress,
                Qt.Key.Key_Return,
                Qt.KeyboardModifier.NoModifier
            )
            self.eventFilter(self.edit, enter_event)
            
            # 模拟 Shift+Enter
            original_text = self.edit.toPlainText()
            shift_enter_event = QKeyEvent(
                QEvent.Type.KeyPress,
                Qt.Key.Key_Return,
                Qt.KeyboardModifier.ShiftModifier
            )
            self.eventFilter(self.edit, shift_enter_event)
            new_text = self.edit.toPlainText()
            self._shift_enter_triggered = "\n" in new_text
            
            results["enter_behavior_ok"] = self._enter_triggered and self._shift_enter_triggered
            
            # 清理
            self.submitted.disconnect(on_submit)
            self.edit.clear()
            delattr(self, '_enter_triggered')
            delattr(self, '_shift_enter_triggered')
        except Exception as e:
            results["enter_behavior_ok"] = False
            results["enter_behavior_error"] = str(e)
        
        # 7. 自动增高检查
        try:
            self.edit.clear()
            initial_height = self.edit.height()
            # 插入多行文本
            self.edit.setPlainText("\n".join(["line"] * 10))
            QApplication.processEvents()
            final_height = self.edit.height()
            has_scrollbar = self.edit.verticalScrollBar().isVisible() if self.edit.verticalScrollBar() else False
            results["auto_grow_ok"] = final_height > initial_height or has_scrollbar
            self.edit.clear()
        except Exception as e:
            results["auto_grow_ok"] = False
            results["auto_grow_error"] = str(e)
        
        # 8. set_generating 状态检查
        try:
            # 测试生成状态
            self.set_generating(True)
            stop_enabled = self.btn_send.isEnabled()
            stop_state = self.btn_send.property("state") == "stop"
            
            self.set_generating(False)
            send_state_restored = self.btn_send.property("state") in ("send", None)
            
            results["set_generating_ok"] = stop_enabled and stop_state and send_state_restored
        except Exception as e:
            results["set_generating_ok"] = False
            results["set_generating_error"] = str(e)
        
        # 9. 拖拽启用检查
        results["drag_drop_enabled"] = (
            self.acceptDrops() == self._attachments_enabled and
            self.shell.acceptDrops() == self._attachments_enabled
        )
        
        # 10. 极端颜色探测（可选，仅检查是否设置了基本属性）
        try:
            bg_color = self.shell.palette().window().color()
            results["extreme_color_probe"] = {
                "shell_bg_r": bg_color.red(),
                "shell_bg_g": bg_color.green(),
                "shell_bg_b": bg_color.blue()
            }
        except:
            results["extreme_color_probe"] = None
        
        return results

    def apply_sanity_defaults_if_needed(self):
        """应用兜底默认值，确保组件可用"""
        # 1. 确保 WA_StyledBackground
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.shell.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._preview_holder.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        # 2. 确保最小高度
        if self.shell.minimumHeight() < 44:
            self.shell.setMinimumHeight(56)
        
        # 3. 确保初始属性
        if self.shell.property("focus") is None:
            self.shell.setProperty("focus", "false")
        if self.shell.property("hasText") is None:
            self.shell.setProperty("hasText", "false")
        if self.btn_send.property("state") is None:
            self.btn_send.setProperty("state", "send")
        
        # 4. 确保按钮文本（如果没有图标）
        if not self.btn_send.icon().isNull() == False and not self.btn_send.text():
            self.btn_send.setText("➤")
        if not self.btn_plus.text() and self.btn_plus.icon().isNull():
            self.btn_plus.setText("+")
        
        # 5. 强制刷新样式
        for widget in [self, self.shell, self.btn_send, self.btn_plus, self._preview_holder]:
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        
        # 6. 更新发送按钮状态
        self._update_send_enabled()

