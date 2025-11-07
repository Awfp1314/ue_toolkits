"""
ChatGPT 风格的 Markdown 消息组件
无气泡设计，纯 Markdown 渲染（HTML 转换）
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTextBrowser, QGraphicsOpacityEffect, QPushButton
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRectF, pyqtProperty, pyqtSignal, QSize, QUrl
from PyQt6.QtGui import QFont, QPainter, QColor, QIcon, QPixmap, QPen, QDesktopServices, QPainterPath, QLinearGradient, QBrush

def safe_print(msg: str):
    """安全的 print 函数，避免 Windows 控制台编码错误"""
    try:
        print(msg, flush=True)
    except (OSError, UnicodeEncodeError):
        # 如果 print 失败，忽略（不要让调试输出导致程序崩溃）
        pass

import traceback

try:
    import markdown
    from markdown.extensions.fenced_code import FencedCodeExtension
    from markdown.extensions.tables import TableExtension
    from markdown.extensions.codehilite import CodeHiliteExtension
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    safe_print("警告: markdown 库未安装，将使用基础渲染。请运行: pip install markdown")

# Pygments 用于语法高亮
try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, guess_lexer
    from pygments.formatters import HtmlFormatter
    from pygments.util import ClassNotFound
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False
    safe_print("提示: pygments 库未安装，代码块将不会有语法高亮。运行: pip install pygments")


class RoundedBubble(QWidget):
    """自定义圆角气泡（使用 QPainter 手动绘制）"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.radius = 18  # 圆角半径
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    
    def paintEvent(self, event):
        """绘制圆角渐变背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # 抗锯齿
        
        # 创建圆角路径
        path = QPainterPath()
        rect = QRectF(0, 0, self.width(), self.height())
        path.addRoundedRect(rect, self.radius, self.radius)
        
        # 创建线性渐变（从紫色到粉色）
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor("#8B5CF6"))  # 紫色
        gradient.setColorAt(1, QColor("#EC4899"))  # 粉色
        
        # 绘制
        painter.fillPath(path, QBrush(gradient))


class CircleWidget(QWidget):
    """圆形绘制 widget"""
    def __init__(self, parent=None, theme="dark"):
        super().__init__(parent)
        self.setFixedSize(20, 30)
        self._scale = 1.0
        self.parent_indicator = parent
        self.theme = theme
    
    def paintEvent(self, event):
        """绘制圆形"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 根据主题选择颜色：深色主题用浅色，浅色主题用深色
        color = "#E0E0E0" if self.theme == "dark" else "#565869"
        painter.setBrush(QColor(color))
        painter.setPen(Qt.PenStyle.NoPen)
        
        # 从父对象获取缩放值
        scale = self.parent_indicator._scale if self.parent_indicator else 1.0
        
        # 计算圆形位置和大小
        radius = 5 * scale
        center_x = self.width() / 2
        center_y = self.height() / 2
        rect = QRectF(center_x - radius, center_y - radius, radius * 2, radius * 2)
        painter.drawEllipse(rect)


class ThinkingIndicator(QWidget):
    """思考中动画指示器（呼吸式圆形 + "正在思考"文字）"""
    
    def __init__(self, parent=None, theme="dark"):
        super().__init__(parent)
        self._scale = 1.0
        self.theme = theme
        
        # 创建水平布局（圆形 + 文字）
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        # 圆形容器（传递主题）
        self.circle_widget = CircleWidget(self, theme=theme)
        layout.addWidget(self.circle_widget, 0, Qt.AlignmentFlag.AlignVCenter)
        
        # 设置圆形的透明度效果
        self.opacity_effect = QGraphicsOpacityEffect(self.circle_widget)
        self.circle_widget.setGraphicsEffect(self.opacity_effect)
        
        # 文字标签（初始隐藏，每个字符独立动画）
        self.text_container = QWidget()
        self.text_container.setVisible(False)
        text_layout = QHBoxLayout(self.text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)  # 字符间距
        
        # 根据主题选择颜色：深色主题用浅色，浅色主题用深色
        text_color = "#E0E0E0" if theme == "dark" else "#565869"
        
        # 创建单独的字符标签（"正在思考"）
        self.char_labels = []
        self.char_opacity_effects = []
        self.char_animations = []
        
        characters = ["正", "在", "思", "考"]
        for char in characters:
            label = QLabel(char)
            # 使用和AI回答相同的字体样式
            label.setStyleSheet(f"""
                font-family: "Microsoft YaHei UI", "PingFang SC", "Noto Sans CJK SC", 
                             "Source Han Sans CN", "思源黑体", "Hiragino Sans GB",
                             "Segoe UI", "Inter", "Roboto", Arial, sans-serif;
                font-size: 18px;
                font-weight: 500;
                color: {text_color};
            """)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # 为每个字符创建透明度效果
            opacity_effect = QGraphicsOpacityEffect(label)
            opacity_effect.setOpacity(0.3)  # 初始半透明
            label.setGraphicsEffect(opacity_effect)
            
            self.char_labels.append(label)
            self.char_opacity_effects.append(opacity_effect)
            text_layout.addWidget(label)
        
        layout.addWidget(self.text_container, 0, Qt.AlignmentFlag.AlignVCenter)
        
        # 4秒后显示文字的定时器
        self.show_text_timer = QTimer(self)
        self.show_text_timer.setSingleShot(True)
        self.show_text_timer.timeout.connect(self._show_thinking_text)
        self.show_text_timer.start(4000)  # 4秒后触发
        
        # 缩放动画（使用定时器实现循环）
        self.scale_anim_forward = QPropertyAnimation(self, b"scale")
        self.scale_anim_forward.setStartValue(1.0)
        self.scale_anim_forward.setEndValue(1.5)
        self.scale_anim_forward.setDuration(800)
        self.scale_anim_forward.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        self.scale_anim_backward = QPropertyAnimation(self, b"scale")
        self.scale_anim_backward.setStartValue(1.5)
        self.scale_anim_backward.setEndValue(1.0)
        self.scale_anim_backward.setDuration(800)
        self.scale_anim_backward.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # 连接动画完成信号，实现循环
        self.scale_anim_forward.finished.connect(self.scale_anim_backward.start)
        self.scale_anim_backward.finished.connect(self.scale_anim_forward.start)
        
        # 透明度动画
        self.opacity_anim_forward = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_anim_forward.setStartValue(1.0)
        self.opacity_anim_forward.setEndValue(0.6)
        self.opacity_anim_forward.setDuration(800)
        self.opacity_anim_forward.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        self.opacity_anim_backward = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_anim_backward.setStartValue(0.6)
        self.opacity_anim_backward.setEndValue(1.0)
        self.opacity_anim_backward.setDuration(800)
        self.opacity_anim_backward.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # 连接透明度动画
        self.opacity_anim_forward.finished.connect(self.opacity_anim_backward.start)
        self.opacity_anim_backward.finished.connect(self.opacity_anim_forward.start)
        
        # 启动动画
        self.scale_anim_forward.start()
        self.opacity_anim_forward.start()
    
    def _show_thinking_text(self):
        """显示"正在思考..."文字并启动动画（ChatGPT风格）"""
        self.text_container.setVisible(True)
        self._start_text_animation()
    
    def _start_text_animation(self):
        """启动文字动画：每个字符依次淡入淡出（从左到右波浪式）"""
        # 为每个字符创建动画
        stagger_delay = 250  # 每个字符之间的延迟（毫秒）
        fade_duration = 500  # 单个字符淡入淡出的持续时间（毫秒）
        
        for i, opacity_effect in enumerate(self.char_opacity_effects):
            # 创建淡入动画（0.3 -> 1.0）
            fade_in = QPropertyAnimation(opacity_effect, b"opacity")
            fade_in.setStartValue(0.3)
            fade_in.setEndValue(1.0)
            fade_in.setDuration(fade_duration)
            fade_in.setEasingCurve(QEasingCurve.Type.InOutSine)
            
            # 创建淡出动画（1.0 -> 0.3）
            fade_out = QPropertyAnimation(opacity_effect, b"opacity")
            fade_out.setStartValue(1.0)
            fade_out.setEndValue(0.3)
            fade_out.setDuration(fade_duration)
            fade_out.setEasingCurve(QEasingCurve.Type.InOutSine)
            
            # 使用定时器实现延迟和循环
            def create_animation_loop(fade_in_anim, fade_out_anim, delay):
                """为每个字符创建循环动画"""
                # 连接淡入和淡出
                fade_in_anim.finished.connect(fade_out_anim.start)
                fade_out_anim.finished.connect(fade_in_anim.start)
                
                # 延迟启动
                QTimer.singleShot(delay, fade_in_anim.start)
            
            # 计算每个字符的延迟时间
            delay = i * stagger_delay
            create_animation_loop(fade_in, fade_out, delay)
            
            # 保存动画引用，防止被垃圾回收
            self.char_animations.append((fade_in, fade_out))
    
    def get_scale(self):
        """获取缩放值"""
        return self._scale
    
    def set_scale(self, value):
        """设置缩放值"""
        self._scale = value
        self.circle_widget.update()  # 触发圆形重绘
    
    scale = pyqtProperty(float, get_scale, set_scale)
    
    def stop(self):
        """停止所有动画"""
        # 停止圆形动画
        self.scale_anim_forward.stop()
        self.scale_anim_backward.stop()
        self.opacity_anim_forward.stop()
        self.opacity_anim_backward.stop()
        
        # 停止4秒定时器（如果还没触发）
        if self.show_text_timer and self.show_text_timer.isActive():
            self.show_text_timer.stop()
        
        # 停止所有字符动画
        for fade_in, fade_out in self.char_animations:
            fade_in.stop()
            fade_out.stop()


def markdown_to_html(text, theme="dark", compact=False):
    """
    将 Markdown 文本转换为 HTML，带自定义样式
    """
    if not MARKDOWN_AVAILABLE:
        return f'<div style="white-space: pre-wrap;">{text or ""}</div>'
    
    if not text:
        return f'<div style="white-space: pre-wrap;"></div>'
    
    try:
        # 配置 CodeHilite 扩展以使用 Pygments
        extensions = [
            'fenced_code',
            'tables',
            'nl2br',  # 换行支持
            'sane_lists'  # 更好的列表支持
        ]
        
        # 如果 Pygments 可用，启用代码高亮
        if PYGMENTS_AVAILABLE:
            extensions.append(CodeHiliteExtension(
                linenums=False,  # 不显示行号（可以改为True显示行号）
                guess_lang=True,  # 自动猜测语言
                css_class='highlight'  # CSS 类名
            ))
        
        # 使用 markdown 库转换
        html = markdown.markdown(text, extensions=extensions)
    except Exception as e:
        # 如果转换失败，返回纯文本
        print(f"[ERROR] Markdown 转换错误: {e}")
        return f'<div style="white-space: pre-wrap;">{text}</div>'
    
    # 添加自定义 CSS 样式
    if theme == "dark":
        # 紧凑模式用于用户消息
        if compact:
            css = """
            <style>
                body {
                    font-family: "Microsoft YaHei UI", "PingFang SC", "Noto Sans CJK SC", 
                                 "Source Han Sans CN", "思源黑体", "Hiragino Sans GB",
                                 "Segoe UI", "Inter", "Roboto", Arial, sans-serif;
                    font-size: 18px;
                    font-weight: 500;
                    line-height: 2.2;
                    color: #ffffff;
                    margin: 0;
                    padding: 0;
                    max-width: 100%;
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                    letter-spacing: 1px;
                    -webkit-font-smoothing: antialiased;
                    -moz-osx-font-smoothing: grayscale;
                }
                p {
                    margin: 0;
                    padding: 0;
                    line-height: 2.0;
                }
            </style>
            """
        else:
            css = """
            <style>
                body {
                    font-family: "Microsoft YaHei UI", "PingFang SC", "Noto Sans CJK SC", 
                                 "Source Han Sans CN", "思源黑体", "Hiragino Sans GB",
                                 "Segoe UI", "Inter", "Roboto", Arial, sans-serif;
                    font-size: 18px;
                    font-weight: 500;
                    line-height: 2.2em;
                    color: #EDEDED;
                    margin: 0;
                    padding: 16px 20px;
                    max-width: 100%;
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                    letter-spacing: 1px;
                    -webkit-font-smoothing: antialiased;
                    -moz-osx-font-smoothing: grayscale;
                    text-rendering: optimizeLegibility;
                    overflow-x: hidden;
                }
            
            h1, h2, h3, h4, h5, h6 {
                font-weight: 600;
                margin-top: 1.5em;
                margin-bottom: 1.2em;
                color: #ececf1;
                line-height: 1.5;
            }
            
            h1 { font-size: 1.8em; }
            h2 { font-size: 1.5em; }
            h3 { font-size: 1.3em; }
            
            p {
                margin: 1.2em 0;
                line-height: 2.2em;
            }
            
            ul, ol {
                margin: 1.2em 0;
                padding-left: 30px;
            }
            
            li {
                margin: 0.6em 0;
                line-height: 2.2em;
            }
            
            code {
                background-color: #2d2d2d;
                color: #e6db74;
                padding: 2px 6px;
                border-radius: 4px;
                font-family: "JetBrains Mono", "Fira Code", "Consolas", "Courier New", "Monaco", monospace;
                font-size: 14px;
                font-weight: 400;
                letter-spacing: 0;
            }
            
            pre {
                background-color: #1E1E1E;
                border: none;
                border-radius: 8px;
                padding: 16px 20px;
                overflow-x: auto;
                overflow-y: hidden;
                margin: 0.8em 0;
                max-width: 100%;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
                white-space: pre;
                word-wrap: normal;
                word-break: normal;
            }
            
            pre code {
                background-color: transparent;
                padding: 0;
                color: #d4d4d4;
                font-size: 13.5px;
                font-weight: 400;
                line-height: 1.6;
                letter-spacing: 0;
                font-family: "JetBrains Mono", "Fira Code", "Consolas", "Courier New", "Monaco", monospace;
                white-space: pre;
                word-wrap: normal;
                display: inline-block;
                min-width: 100%;
            }
            
            /* Pygments 语法高亮样式 (VS Code Dark+ 主题) */
            .highlight { background: #1E1E1E; border-radius: 8px; }
            .highlight .hll { background-color: #49483e }
            .highlight .c { color: #6A9955; font-style: italic } /* Comment */
            .highlight .err { color: #f92672 } /* Error */
            .highlight .k { color: #C586C0 } /* Keyword */
            .highlight .l { color: #ae81ff } /* Literal */
            .highlight .n { color: #d4d4d4 } /* Name */
            .highlight .o { color: #d4d4d4 } /* Operator */
            .highlight .p { color: #d4d4d4 } /* Punctuation */
            .highlight .ch { color: #6A9955; font-style: italic } /* Comment.Hashbang */
            .highlight .cm { color: #6A9955; font-style: italic } /* Comment.Multiline */
            .highlight .cp { color: #6A9955; font-weight: bold } /* Comment.Preproc */
            .highlight .cpf { color: #6A9955; font-style: italic } /* Comment.PreprocFile */
            .highlight .c1 { color: #6A9955; font-style: italic } /* Comment.Single */
            .highlight .cs { color: #6A9955; font-weight: bold; font-style: italic } /* Comment.Special */
            .highlight .gd { color: #f92672 } /* Generic.Deleted */
            .highlight .ge { font-style: italic } /* Generic.Emph */
            .highlight .gi { color: #a6e22e } /* Generic.Inserted */
            .highlight .gs { font-weight: bold } /* Generic.Strong */
            .highlight .gu { color: #75715e } /* Generic.Subheading */
            .highlight .kc { color: #C586C0 } /* Keyword.Constant */
            .highlight .kd { color: #569CD6 } /* Keyword.Declaration */
            .highlight .kn { color: #C586C0 } /* Keyword.Namespace */
            .highlight .kp { color: #C586C0 } /* Keyword.Pseudo */
            .highlight .kr { color: #C586C0 } /* Keyword.Reserved */
            .highlight .kt { color: #4EC9B0 } /* Keyword.Type */
            .highlight .ld { color: #CE9178 } /* Literal.Date */
            .highlight .m { color: #B5CEA8 } /* Literal.Number */
            .highlight .s { color: #CE9178 } /* Literal.String */
            .highlight .na { color: #9CDCFE } /* Name.Attribute */
            .highlight .nb { color: #4EC9B0 } /* Name.Builtin */
            .highlight .nc { color: #4EC9B0; font-weight: bold } /* Name.Class */
            .highlight .no { color: #DCDCAA } /* Name.Constant */
            .highlight .nd { color: #DCDCAA } /* Name.Decorator */
            .highlight .ni { color: #d4d4d4 } /* Name.Entity */
            .highlight .ne { color: #DCDCAA; font-weight: bold } /* Name.Exception */
            .highlight .nf { color: #DCDCAA } /* Name.Function */
            .highlight .nl { color: #d4d4d4 } /* Name.Label */
            .highlight .nn { color: #4EC9B0 } /* Name.Namespace */
            .highlight .nx { color: #9CDCFE } /* Name.Other */
            .highlight .py { color: #d4d4d4 } /* Name.Property */
            .highlight .nt { color: #569CD6 } /* Name.Tag */
            .highlight .nv { color: #9CDCFE } /* Name.Variable */
            .highlight .ow { color: #C586C0; font-weight: bold } /* Operator.Word */
            .highlight .w { color: #d4d4d4 } /* Text.Whitespace */
            .highlight .mb { color: #B5CEA8 } /* Literal.Number.Bin */
            .highlight .mf { color: #B5CEA8 } /* Literal.Number.Float */
            .highlight .mh { color: #B5CEA8 } /* Literal.Number.Hex */
            .highlight .mi { color: #B5CEA8 } /* Literal.Number.Integer */
            .highlight .mo { color: #B5CEA8 } /* Literal.Number.Oct */
            .highlight .sa { color: #CE9178 } /* Literal.String.Affix */
            .highlight .sb { color: #CE9178 } /* Literal.String.Backtick */
            .highlight .sc { color: #CE9178 } /* Literal.String.Char */
            .highlight .dl { color: #CE9178 } /* Literal.String.Delimiter */
            .highlight .sd { color: #CE9178; font-style: italic } /* Literal.String.Doc */
            .highlight .s2 { color: #CE9178 } /* Literal.String.Double */
            .highlight .se { color: #D7BA7D } /* Literal.String.Escape */
            .highlight .sh { color: #CE9178 } /* Literal.String.Heredoc */
            .highlight .si { color: #CE9178 } /* Literal.String.Interpol */
            .highlight .sx { color: #CE9178 } /* Literal.String.Other */
            .highlight .sr { color: #D16969 } /* Literal.String.Regex */
            .highlight .s1 { color: #CE9178 } /* Literal.String.Single */
            .highlight .ss { color: #CE9178 } /* Literal.String.Symbol */
            .highlight .bp { color: #4EC9B0 } /* Name.Builtin.Pseudo */
            .highlight .fm { color: #DCDCAA } /* Name.Function.Magic */
            .highlight .vc { color: #9CDCFE } /* Name.Variable.Class */
            .highlight .vg { color: #9CDCFE } /* Name.Variable.Global */
            .highlight .vi { color: #9CDCFE } /* Name.Variable.Instance */
            .highlight .vm { color: #9CDCFE } /* Name.Variable.Magic */
            .highlight .il { color: #B5CEA8 } /* Literal.Number.Integer.Long */
            
            a {
                color: #19c37d;
                text-decoration: none;
                transition: all 0.2s ease;
            }
            
            a:hover {
                text-decoration: underline;
                color: #20d68b;
            }
            
            blockquote {
                border-left: 4px solid #444654;
                padding-left: 16px;
                margin: 0.8em 0;
                color: #b4b4b4;
                font-style: italic;
                background-color: rgba(68, 70, 84, 0.15);
                padding: 12px 16px;
                border-radius: 4px;
            }
            
            table {
                border-collapse: collapse;
                margin: 0.8em 0;
                width: 100%;
                max-width: 100%;
                overflow-x: auto;
                display: block;
            }
            
            th, td {
                border: 1px solid #444654;
                padding: 10px 14px;
                text-align: left;
            }
            
            th {
                background-color: #2d2d2d;
                font-weight: 600;
            }
            
            tr:hover {
                background-color: rgba(68, 70, 84, 0.2);
            }
            
            strong {
                font-weight: 600;
                color: #ececf1;
            }
            
            em {
                font-style: italic;
                color: #d4d4d4;
            }
            
            hr {
                border: none;
                border-top: 1px solid #444654;
                margin: 1.6em 0;
            }
        </style>
        """
    else:  # light theme
        # 紧凑模式用于用户消息
        if compact:
            css = """
            <style>
                body {
                    font-family: "Microsoft YaHei UI", "PingFang SC", "Noto Sans CJK SC", 
                                 "Source Han Sans CN", "思源黑体", "Hiragino Sans GB",
                                 "Segoe UI", "Inter", "Roboto", Arial, sans-serif;
                    font-size: 18px;
                    font-weight: 500;
                    line-height: 2.2;
                    color: #2d333a;
                    margin: 0;
                    padding: 0;
                    max-width: 100%;
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                    letter-spacing: 1px;
                    -webkit-font-smoothing: antialiased;
                    -moz-osx-font-smoothing: grayscale;
                }
                p {
                    margin: 0;
                    padding: 0;
                    line-height: 2.0;
                }
            </style>
            """
        else:
            css = """
            <style>
                body {
                    font-family: "Microsoft YaHei UI", "PingFang SC", "Noto Sans CJK SC", 
                                 "Source Han Sans CN", "思源黑体", "Hiragino Sans GB",
                                 "Segoe UI", "Inter", "Roboto", Arial, sans-serif;
                    font-size: 18px;
                    font-weight: 500;
                    line-height: 2.2em;
                    color: #374151;
                    margin: 0;
                    padding: 16px 20px;
                    max-width: 100%;
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                    letter-spacing: 1px;
                    -webkit-font-smoothing: antialiased;
                    -moz-osx-font-smoothing: grayscale;
                    text-rendering: optimizeLegibility;
                    overflow-x: hidden;
                }
            
            h1, h2, h3, h4, h5, h6 {
                font-weight: 600;
                margin-top: 1.5em;
                margin-bottom: 1.2em;
                color: #1f2937;
                line-height: 1.5;
            }
            
            h1 { font-size: 1.8em; }
            h2 { font-size: 1.5em; }
            h3 { font-size: 1.3em; }
            
            p {
                margin: 1.2em 0;
                line-height: 2.2em;
            }
            
            ul, ol {
                margin: 1.2em 0;
                padding-left: 30px;
            }
            
            li {
                margin: 0.6em 0;
                line-height: 2.2em;
            }
            
            code {
                background-color: #f3f4f6;
                color: #c7254e;
                padding: 2px 6px;
                border-radius: 4px;
                font-family: "JetBrains Mono", "Fira Code", "Consolas", "Courier New", "Monaco", monospace;
                font-size: 14px;
                font-weight: 400;
                letter-spacing: 0;
            }
            
            pre {
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 16px 20px;
                overflow-x: auto;
                overflow-y: hidden;
                margin: 0.8em 0;
                max-width: 100%;
                box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
                white-space: pre;
                word-wrap: normal;
                word-break: normal;
            }
            
            pre code {
                background-color: transparent;
                padding: 0;
                color: #1f2937;
                font-size: 13.5px;
                font-weight: 400;
                line-height: 1.6;
                letter-spacing: 0;
                font-family: "JetBrains Mono", "Fira Code", "Consolas", "Courier New", "Monaco", monospace;
                white-space: pre;
                word-wrap: normal;
                display: inline-block;
                min-width: 100%;
            }
            
            /* Pygments 语法高亮样式 (Light 主题) */
            .highlight { background: #f9fafb; border-radius: 8px; }
            .highlight .hll { background-color: #ffc }
            .highlight .c { color: #008000; font-style: italic } /* Comment */
            .highlight .err { border: 1px solid #FF0000 } /* Error */
            .highlight .k { color: #0000ff } /* Keyword */
            .highlight .ch { color: #008000; font-style: italic } /* Comment.Hashbang */
            .highlight .cm { color: #008000; font-style: italic } /* Comment.Multiline */
            .highlight .cp { color: #0000ff } /* Comment.Preproc */
            .highlight .cpf { color: #008000; font-style: italic } /* Comment.PreprocFile */
            .highlight .c1 { color: #008000; font-style: italic } /* Comment.Single */
            .highlight .cs { color: #008000; font-style: italic } /* Comment.Special */
            .highlight .gd { color: #A00000 } /* Generic.Deleted */
            .highlight .ge { font-style: italic } /* Generic.Emph */
            .highlight .gr { color: #FF0000 } /* Generic.Error */
            .highlight .gh { color: #000080; font-weight: bold } /* Generic.Heading */
            .highlight .gi { color: #00A000 } /* Generic.Inserted */
            .highlight .go { color: #888888 } /* Generic.Output */
            .highlight .gp { color: #000080; font-weight: bold } /* Generic.Prompt */
            .highlight .gs { font-weight: bold } /* Generic.Strong */
            .highlight .gu { color: #800080; font-weight: bold } /* Generic.Subheading */
            .highlight .gt { color: #0044DD } /* Generic.Traceback */
            .highlight .kc { color: #0000ff } /* Keyword.Constant */
            .highlight .kd { color: #0000ff } /* Keyword.Declaration */
            .highlight .kn { color: #0000ff } /* Keyword.Namespace */
            .highlight .kp { color: #0000ff } /* Keyword.Pseudo */
            .highlight .kr { color: #0000ff } /* Keyword.Reserved */
            .highlight .kt { color: #2b91af } /* Keyword.Type */
            .highlight .m { color: #009999 } /* Literal.Number */
            .highlight .s { color: #a31515 } /* Literal.String */
            .highlight .na { color: #FF0000 } /* Name.Attribute */
            .highlight .nb { color: #2b91af } /* Name.Builtin */
            .highlight .nc { color: #2b91af } /* Name.Class */
            .highlight .no { color: #2b91af } /* Name.Constant */
            .highlight .nd { color: #2b91af } /* Name.Decorator */
            .highlight .ni { color: #999999 } /* Name.Entity */
            .highlight .ne { color: #2b91af } /* Name.Exception */
            .highlight .nf { color: #795e26 } /* Name.Function */
            .highlight .nl { color: #2b91af } /* Name.Label */
            .highlight .nn { color: #2b91af } /* Name.Namespace */
            .highlight .nt { color: #800000 } /* Name.Tag */
            .highlight .nv { color: #001080 } /* Name.Variable */
            .highlight .ow { color: #0000ff } /* Operator.Word */
            .highlight .w { color: #bbbbbb } /* Text.Whitespace */
            .highlight .mb { color: #009999 } /* Literal.Number.Bin */
            .highlight .mf { color: #009999 } /* Literal.Number.Float */
            .highlight .mh { color: #009999 } /* Literal.Number.Hex */
            .highlight .mi { color: #009999 } /* Literal.Number.Integer */
            .highlight .mo { color: #009999 } /* Literal.Number.Oct */
            .highlight .sa { color: #a31515 } /* Literal.String.Affix */
            .highlight .sb { color: #a31515 } /* Literal.String.Backtick */
            .highlight .sc { color: #a31515 } /* Literal.String.Char */
            .highlight .dl { color: #a31515 } /* Literal.String.Delimiter */
            .highlight .sd { color: #a31515; font-style: italic } /* Literal.String.Doc */
            .highlight .s2 { color: #a31515 } /* Literal.String.Double */
            .highlight .se { color: #ee0077; font-weight: bold } /* Literal.String.Escape */
            .highlight .sh { color: #a31515 } /* Literal.String.Heredoc */
            .highlight .si { color: #a31515 } /* Literal.String.Interpol */
            .highlight .sx { color: #a31515 } /* Literal.String.Other */
            .highlight .sr { color: #811f3f } /* Literal.String.Regex */
            .highlight .s1 { color: #a31515 } /* Literal.String.Single */
            .highlight .ss { color: #a31515 } /* Literal.String.Symbol */
            .highlight .bp { color: #2b91af } /* Name.Builtin.Pseudo */
            .highlight .fm { color: #795e26 } /* Name.Function.Magic */
            .highlight .vc { color: #001080 } /* Name.Variable.Class */
            .highlight .vg { color: #001080 } /* Name.Variable.Global */
            .highlight .vi { color: #001080 } /* Name.Variable.Instance */
            .highlight .vm { color: #001080 } /* Name.Variable.Magic */
            .highlight .il { color: #009999 } /* Literal.Number.Integer.Long */
            
            a {
                color: #10a37f;
                text-decoration: none;
                transition: all 0.2s ease;
            }
            
            a:hover {
                text-decoration: underline;
                color: #0d8f6f;
            }
            
            blockquote {
                border-left: 4px solid #d1d5db;
                padding-left: 16px;
                margin: 0.8em 0;
                color: #6b7280;
                font-style: italic;
                background-color: rgba(209, 213, 219, 0.2);
                padding: 12px 16px;
                border-radius: 4px;
            }
            
            table {
                border-collapse: collapse;
                margin: 0.8em 0;
                width: 100%;
                max-width: 100%;
                overflow-x: auto;
                display: block;
            }
            
            th, td {
                border: 1px solid #e5e7eb;
                padding: 10px 14px;
                text-align: left;
            }
            
            th {
                background-color: #f3f4f6;
                font-weight: 600;
            }
            
            tr:hover {
                background-color: rgba(229, 231, 235, 0.3);
            }
            
            strong {
                font-weight: 600;
                color: #1f2937;
            }
            
            em {
                font-style: italic;
                color: #4b5563;
            }
            
            hr {
                border: none;
                border-top: 1px solid #e5e7eb;
                margin: 1.6em 0;
            }
        </style>
        """
    
    return css + html


class MarkdownMessage(QFrame):
    """
    单条 Markdown 消息
    ChatGPT 风格，无气泡
    """
    
    def __init__(self, role, message, theme="dark", parent=None):
        super().__init__(parent)
        self.role = role  # "user" 或 "assistant"
        self.message = message
        self.theme = theme
        self.init_ui()
    
    def init_ui(self):
        """初始化 UI"""
        self.setObjectName("markdown_message")
        
        if self.role == "user":
            # 用户消息：右对齐气泡样式
            self._init_user_message()
        elif self.role == "system":
            # 系统消息：居中显示，特殊样式
            self._init_system_message()
        else:
            # 助手消息：全宽左对齐，无气泡
            self._init_assistant_message()
    
    def _init_user_message(self):
        """初始化用户消息（ChatGPT 风格：粉紫渐变气泡，右对齐）"""
        # 主布局：垂直布局，包含气泡和按钮
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 12, 80, 12)  # 右边距80px与输入框对齐，上下12px
        main_layout.setSpacing(0)
        
        # 气泡容器：水平布局
        bubble_container = QWidget()
        bubble_container_layout = QHBoxLayout(bubble_container)
        bubble_container_layout.setContentsMargins(0, 0, 0, 0)
        bubble_container_layout.setSpacing(0)
        
        # 左侧留白（弹性空间）
        bubble_container_layout.addStretch(1)
        
        # 用户消息气泡（ChatGPT 粉紫渐变风格 - 使用自定义绘制）
        self.bubble = RoundedBubble()
        self.bubble.setObjectName("user_bubble")
        
        bubble_layout = QVBoxLayout(self.bubble)
        bubble_layout.setContentsMargins(16, 7, 16, 7)  # 左右16px，上下7px（更紧凑）
        bubble_layout.setSpacing(0)
        
        # 消息内容（使用 QLabel）
        self.text_label = QLabel(self.message)
        self.text_label.setObjectName("user_text_label")
        self.text_label.setWordWrap(True)  # 自动换行
        self.text_label.setTextFormat(Qt.TextFormat.PlainText)  # 纯文本格式
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        # 设置白色文字
        self.text_label.setStyleSheet("QLabel#user_text_label { color: #FFFFFF; background-color: transparent; }")
        
        # 设置字体以确保清晰度（ChatGPT 风格）
        font = QFont()
        font.setFamilies([
            "Microsoft YaHei UI", "PingFang SC", "Noto Sans CJK SC",
            "Source Han Sans CN", "Hiragino Sans GB",
            "Segoe UI", "Inter", "Roboto", "Arial", "sans-serif"
        ])
        font.setPointSize(14)  # 18px ≈ 14pt（更大）
        font.setWeight(QFont.Weight.DemiBold)  # 稍微加粗
        font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
        font.setStyleStrategy(
            QFont.StyleStrategy.PreferAntialias | 
            QFont.StyleStrategy.PreferQuality
        )
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.0)  # 字间距1px
        self.text_label.setFont(font)
        
        # 设置最大宽度（约85%，最大800px，避免过早换行）
        self.text_label.setMaximumWidth(800)
        
        bubble_layout.addWidget(self.text_label)
        bubble_container_layout.addWidget(self.bubble)
        
        # 添加气泡容器到主布局
        main_layout.addWidget(bubble_container)
        
        # 添加操作按钮容器
        button_container = QWidget()
        button_container_layout = QHBoxLayout(button_container)
        button_container_layout.setContentsMargins(0, 4, 0, 0)  # 顶部间距4px
        button_container_layout.setSpacing(8)
        
        # 左侧留白
        button_container_layout.addStretch(1)
        
        # 复制按钮（使用自定义图标）
        self.user_copy_button = QPushButton()
        self.user_copy_button.setObjectName("action_button")
        self.user_copy_button.setProperty("theme", self.theme)  # 设置主题属性
        self.user_copy_button.setFixedSize(28, 28)  # 稍微减小按钮尺寸，减少锯齿
        self.user_copy_button.setToolTip("复制内容")
        self.user_copy_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.user_copy_button.setFlat(False)  # 确保QSS背景颜色生效
        self.user_copy_button.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # 启用样式背景
        self.user_copy_button.setIcon(self._create_copy_icon())
        self.user_copy_button.setIconSize(QSize(18, 18))  # 相应减小图标尺寸
        # 样式由 QSS 文件控制
        self.user_copy_button.clicked.connect(self.on_user_copy_clicked)
        
        button_container_layout.addWidget(self.user_copy_button)
        
        # 添加按钮容器到主布局
        main_layout.addWidget(button_container)
        
        # 调整气泡大小以适应内容
        self.bubble.adjustSize()
        
        # 添加淡入动画（可选）
        self.setWindowOpacity(0.0)
        self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_animation.setDuration(200)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        QTimer.singleShot(50, self.fade_in_animation.start)
    
    def _init_assistant_message(self):
        """初始化助手消息（居中，无气泡，宽度 780px）"""
        # 外层布局（水平布局，用于居中）
        outer_layout = QHBoxLayout(self)
        outer_layout.setContentsMargins(0, 12, 0, 12)  # 上下间距
        outer_layout.setSpacing(0)
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 添加左侧弹性空间
        outer_layout.addStretch(1)
        
        # 助手消息容器（固定宽度 780px，无背景）
        assistant_container = QWidget()
        assistant_container.setObjectName("assistant_message_container")
        assistant_container.setFixedWidth(780)  # 固定宽度 780px
        
        # 设置容器大小策略：垂直方向最小
        from PyQt6.QtWidgets import QSizePolicy
        assistant_container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        
        # 容器的垂直布局
        container_layout = QVBoxLayout(assistant_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Markdown 内容渲染器（无头像和名称）
        self.markdown_browser = QTextBrowser()
        self.markdown_browser.setObjectName("assistant_message_content")
        self.markdown_browser.setOpenExternalLinks(True)  # 自动打开外部链接
        self.markdown_browser.setOpenLinks(True)  # 允许打开链接
        self.markdown_browser.setReadOnly(True)
        self.markdown_browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.markdown_browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 设置鼠标指针为文本编辑样式（I-beam）
        self.markdown_browser.viewport().setCursor(Qt.CursorShape.IBeamCursor)
        
        # 设置选中文本的样式（深色主题/浅色主题都保持高对比度）
        selection_bg = "#3390FF" if self.theme == "dark" else "#0078D7"
        selection_fg = "#FFFFFF"
        self.markdown_browser.setStyleSheet(f"""
            QTextBrowser {{
                selection-background-color: {selection_bg};
                selection-color: {selection_fg};
            }}
        """)
        
        # 连接链接点击信号，手动处理链接打开
        self.markdown_browser.anchorClicked.connect(lambda url: QDesktopServices.openUrl(url))
        
        # 设置QTextBrowser占满整个容器宽度
        self.markdown_browser.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        # 渲染 Markdown 为 HTML
        html_content = markdown_to_html(self.message, self.theme)
        self.markdown_browser.setHtml(html_content)
        
        # 不使用 setStyleSheet，而是在 HTML CSS 中设置样式
        self.markdown_browser.document().setDocumentMargin(0)
        
        # 自动调整高度
        self.markdown_browser.document().contentsChanged.connect(
            self.adjust_height
        )
        
        container_layout.addWidget(self.markdown_browser)
        
        # 添加容器到外层布局（居中）
        outer_layout.addWidget(assistant_container)
        
        # 添加右侧弹性空间
        outer_layout.addStretch(1)
    
    def _init_system_message(self):
        """初始化系统消息（居中显示，半透明背景，特殊样式）"""
        # 外层布局（水平布局，用于居中）
        outer_layout = QHBoxLayout(self)
        outer_layout.setContentsMargins(0, 12, 0, 12)  # 上下间距
        outer_layout.setSpacing(0)
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 添加左侧弹性空间
        outer_layout.addStretch(1)
        
        # 系统消息容器（固定宽度 650px，浅色背景）
        system_container = QWidget()
        system_container.setObjectName("system_message_container")
        system_container.setProperty("theme", self.theme)  # 设置主题属性
        system_container.setFixedWidth(650)
        
        # 设置容器大小策略
        from PyQt6.QtWidgets import QSizePolicy
        system_container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        # 样式由 QSS 文件控制
        
        # 容器的垂直布局
        container_layout = QVBoxLayout(system_container)
        container_layout.setContentsMargins(16, 12, 16, 12)
        container_layout.setSpacing(0)
        
        # 系统消息文本标签
        from PyQt6.QtWidgets import QLabel
        message_label = QLabel(self.message)
        message_label.setObjectName("system_message_content")
        message_label.setProperty("theme", self.theme)  # 设置主题属性
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # 样式由 QSS 文件控制
        
        container_layout.addWidget(message_label)
        
        # 添加容器到外层布局（居中）
        outer_layout.addWidget(system_container)
        
        # 添加右侧弹性空间
        outer_layout.addStretch(1)
    
    def adjust_height(self):
        """自动调整高度以适应内容"""
        if self.role == "user":
            # 用户消息：QLabel 自动适配，只需调整气泡
            if hasattr(self, 'bubble'):
                self.bubble.adjustSize()
        else:
            # 助手消息：调整 QTextBrowser 高度
            if hasattr(self, 'markdown_browser'):
                doc_height = self.markdown_browser.document().size().height()
                final_height = int(doc_height) + 10
                self.markdown_browser.setFixedHeight(max(final_height, 20))
    
    def append_text(self, text):
        """追加文本（用于流式输出）"""
        self.message += text
        html_content = markdown_to_html(self.message, self.theme)
        self.markdown_browser.setHtml(html_content)
    
    def get_text(self):
        """获取当前文本"""
        return self.message
    
    def _create_copy_icon(self):
        """创建复制图标（两个重叠的圆角正方形）"""
        from PyQt6.QtCore import QPointF
        from PyQt6.QtGui import QPainterPath
        
        # 使用更大的画布以获得更清晰的渲染
        size = 48
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # 设置颜色和画笔
        color = QColor("#ececf1") if self.theme == "dark" else QColor("#565869")
        pen = QPen(color, 2.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # 方块大小和位置
        box_size = 20
        corner_radius = 3
        offset = 7  # 两个矩形的偏移量
        
        # 绘制后面的方块（右下）- 只绘制右边和下边的L形
        back_x = 9 + offset
        back_y = 9 + offset
        
        path = QPainterPath()
        # 从右边中间开始，向上到右上角
        path.moveTo(back_x + box_size, back_y + box_size / 2)
        path.lineTo(back_x + box_size, back_y + corner_radius)
        # 右上角圆角
        path.arcTo(back_x + box_size - corner_radius * 2, back_y, 
                   corner_radius * 2, corner_radius * 2, 0, 90)
        # 移动到右下角（不绘制上边）
        path.moveTo(back_x + box_size, back_y + box_size / 2)
        path.lineTo(back_x + box_size, back_y + box_size - corner_radius)
        # 右下角圆角
        path.arcTo(back_x + box_size - corner_radius * 2, back_y + box_size - corner_radius * 2,
                   corner_radius * 2, corner_radius * 2, 0, -90)
        # 下边
        path.lineTo(back_x + corner_radius, back_y + box_size)
        # 左下角圆角
        path.arcTo(back_x, back_y + box_size - corner_radius * 2,
                   corner_radius * 2, corner_radius * 2, -90, -90)
        painter.drawPath(path)
        
        # 绘制前面的方块（左上）- 完整绘制
        painter.drawRoundedRect(10, 10, box_size, box_size, corner_radius, corner_radius)
        
        painter.end()
        return QIcon(pixmap)
    
    def set_theme(self, theme):
        """更新主题并重新生成图标和内容"""
        self.theme = theme
        
        # 如果是用户消息，重新创建复制按钮图标
        if self.role == "user" and hasattr(self, 'user_copy_button'):
            self.user_copy_button.setIcon(self._create_copy_icon())
            self.user_copy_button.setProperty("theme", theme)
            # 刷新样式
            self.user_copy_button.style().unpolish(self.user_copy_button)
            self.user_copy_button.style().polish(self.user_copy_button)
        
        # 如果是助手消息，重新渲染 Markdown HTML（使用新主题的CSS）
        if self.role == "assistant" and hasattr(self, 'markdown_browser'):
            html_content = markdown_to_html(self.message, self.theme)
            self.markdown_browser.setHtml(html_content)
        
        # 如果是系统消息，更新容器和标签的主题属性
        if self.role == "system":
            # 查找系统消息容器和标签，更新它们的主题属性
            system_container = self.findChild(QWidget, "system_message_container")
            if system_container:
                system_container.setProperty("theme", theme)
                system_container.style().unpolish(system_container)
                system_container.style().polish(system_container)
            
            message_label = self.findChild(QLabel, "system_message_content")
            if message_label:
                message_label.setProperty("theme", theme)
                message_label.style().unpolish(message_label)
                message_label.style().polish(message_label)
    
    def on_user_copy_clicked(self):
        """用户消息复制按钮点击"""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.message)
        # 暂时修改按钮图标以提示已复制
        original_icon = self.user_copy_button.icon()
        self.user_copy_button.setText("✓")
        self.user_copy_button.setIcon(QIcon())
        QTimer.singleShot(1000, lambda: (self.user_copy_button.setText(""), self.user_copy_button.setIcon(original_icon)))


class StreamingMarkdownMessage(QFrame):
    """
    流式输出的 Markdown 消息
    """
    
    # 添加信号
    copy_clicked = pyqtSignal()  # 复制按钮点击信号
    regenerate_clicked = pyqtSignal()  # 重新生成按钮点击信号
    
    def __init__(self, theme="dark", show_regenerate=True, parent=None):
        super().__init__(parent)
        self.role = "assistant"  # 流式消息总是 AI 的回答
        self.current_text = ""
        self.theme = theme
        self.show_regenerate = show_regenerate  # 是否显示重新生成按钮
        self.first_text_received = False  # 标记是否收到第一个文本块
        self.thinking_animation_started = False  # 标记思考动画是否已启动
        self.init_ui()
    
    def init_ui(self):
        """初始化 UI（流式助手消息：居中，无气泡，宽度 780px）"""
        self.setObjectName("markdown_message")
        
        # 工具状态标签（初始化为 None，需要时创建）
        self.tool_status_label = None
        
        # 外层布局（水平布局，用于居中）
        outer_layout = QHBoxLayout(self)
        outer_layout.setContentsMargins(0, 12, 0, 12)  # 上下间距
        outer_layout.setSpacing(0)
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 添加左侧弹性空间
        outer_layout.addStretch(1)
        
        # 助手消息容器（固定宽度 780px，无背景）
        assistant_container = QWidget()
        assistant_container.setObjectName("assistant_message_container_streaming")
        assistant_container.setFixedWidth(780)  # 固定宽度 780px
        
        # 设置容器大小策略：垂直方向最小
        from PyQt6.QtWidgets import QSizePolicy
        assistant_container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        
        # 容器的垂直布局
        container_layout = QVBoxLayout(assistant_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # 思考动画指示器（初始显示，传递主题）
        self.thinking_indicator = ThinkingIndicator(theme=self.theme)
        container_layout.addWidget(self.thinking_indicator)
        
        # Markdown 内容渲染器（初始隐藏）
        self.markdown_browser = QTextBrowser()
        self.markdown_browser.setObjectName("assistant_message_content")
        self.markdown_browser.setOpenExternalLinks(True)  # 自动打开外部链接
        self.markdown_browser.setOpenLinks(True)  # 允许打开链接
        self.markdown_browser.setReadOnly(True)
        self.markdown_browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.markdown_browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 设置鼠标指针为文本编辑样式（I-beam）
        self.markdown_browser.viewport().setCursor(Qt.CursorShape.IBeamCursor)
        
        # 设置选中文本的样式（深色主题/浅色主题都保持高对比度）
        selection_bg = "#3390FF" if self.theme == "dark" else "#0078D7"
        selection_fg = "#FFFFFF"
        self.markdown_browser.setStyleSheet(f"""
            QTextBrowser {{
                selection-background-color: {selection_bg};
                selection-color: {selection_fg};
            }}
        """)
        
        # 连接链接点击信号，手动处理链接打开
        self.markdown_browser.anchorClicked.connect(lambda url: QDesktopServices.openUrl(url))
        
        # 设置QTextBrowser占满整个容器宽度
        self.markdown_browser.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.markdown_browser.setMinimumHeight(40)
        self.markdown_browser.hide()  # 初始隐藏
        
        # 不使用 setStyleSheet，而是在 HTML CSS 中设置样式
        self.markdown_browser.document().setDocumentMargin(0)
        
        # 自动调整高度
        self.markdown_browser.document().contentsChanged.connect(
            self.adjust_height
        )
        
        container_layout.addWidget(self.markdown_browser)
        
        # 添加操作按钮容器（初始隐藏）
        self.action_buttons_container = QWidget()
        self.action_buttons_container.setObjectName("action_buttons_container")
        buttons_layout = QHBoxLayout(self.action_buttons_container)
        buttons_layout.setContentsMargins(0, 8, 0, 0)  # 顶部间距
        buttons_layout.setSpacing(8)
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # 复制按钮（使用自定义图标）
        self.copy_button = QPushButton()
        self.copy_button.setObjectName("action_button")
        self.copy_button.setProperty("theme", self.theme)  # 设置主题属性
        self.copy_button.setFixedSize(28, 28)  # 稍微减小按钮尺寸，减少锯齿
        self.copy_button.setToolTip("复制内容")
        self.copy_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_button.setFlat(False)  # 确保QSS背景颜色生效
        self.copy_button.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # 启用样式背景
        self.copy_button.setIcon(self._create_copy_icon())
        self.copy_button.setIconSize(QSize(18, 18))  # 相应减小图标尺寸
        # 样式由 QSS 文件控制
        self.copy_button.clicked.connect(self.on_copy_clicked)
        buttons_layout.addWidget(self.copy_button)
        
        # 重新生成按钮（根据参数决定是否创建）
        if self.show_regenerate:
            self.regenerate_button = QPushButton()
            self.regenerate_button.setObjectName("action_button")
            self.regenerate_button.setProperty("theme", self.theme)  # 设置主题属性
            self.regenerate_button.setFixedSize(28, 28)  # 稍微减小按钮尺寸，减少锯齿
            self.regenerate_button.setToolTip("重新生成回答")
            self.regenerate_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.regenerate_button.setFlat(False)  # 确保QSS背景颜色生效
            self.regenerate_button.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # 启用样式背景
            self.regenerate_button.setIcon(self._create_regenerate_icon())
            self.regenerate_button.setIconSize(QSize(18, 18))  # 相应减小图标尺寸
            # 样式由 QSS 文件控制
            self.regenerate_button.clicked.connect(self.on_regenerate_clicked)
            buttons_layout.addWidget(self.regenerate_button)
        
        buttons_layout.addStretch(1)
        
        container_layout.addWidget(self.action_buttons_container)
        self.action_buttons_container.hide()  # 初始隐藏
        
        # 添加容器到外层布局（居中）
        outer_layout.addWidget(assistant_container)
        
        # 添加右侧弹性空间
        outer_layout.addStretch(1)
        
        # 延迟启动思考动画，确保最小显示时间（300ms）
        QTimer.singleShot(50, self._start_thinking_animation)
    
    def _start_thinking_animation(self):
        """启动思考动画（确保最小显示时间）"""
        if not self.first_text_received:
            self.thinking_animation_started = True
            self.thinking_indicator.show()  # 确保显示
    
    def _stop_thinking_animation(self):
        """停止思考动画（内部方法）"""
        if hasattr(self, 'thinking_indicator') and self.thinking_indicator:
            self.thinking_indicator.stop()
            self.thinking_indicator.hide()
        if hasattr(self, 'markdown_browser') and self.markdown_browser:
            self.markdown_browser.show()
    
    def _create_copy_icon(self):
        """创建复制图标（两个重叠的圆角正方形）"""
        from PyQt6.QtCore import QPointF
        from PyQt6.QtGui import QPainterPath
        
        # 使用更大的画布以获得更清晰的渲染
        size = 48
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # 设置颜色和画笔
        color = QColor("#ececf1") if self.theme == "dark" else QColor("#565869")
        pen = QPen(color, 2.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # 方块大小和位置
        box_size = 20
        corner_radius = 3
        offset = 7  # 两个矩形的偏移量
        
        # 绘制后面的方块（右下）- 只绘制右边和下边的L形
        back_x = 9 + offset
        back_y = 9 + offset
        
        path = QPainterPath()
        # 从右边中间开始，向上到右上角
        path.moveTo(back_x + box_size, back_y + box_size / 2)
        path.lineTo(back_x + box_size, back_y + corner_radius)
        # 右上角圆角
        path.arcTo(back_x + box_size - corner_radius * 2, back_y, 
                   corner_radius * 2, corner_radius * 2, 0, 90)
        # 移动到右下角（不绘制上边）
        path.moveTo(back_x + box_size, back_y + box_size / 2)
        path.lineTo(back_x + box_size, back_y + box_size - corner_radius)
        # 右下角圆角
        path.arcTo(back_x + box_size - corner_radius * 2, back_y + box_size - corner_radius * 2,
                   corner_radius * 2, corner_radius * 2, 0, -90)
        # 下边
        path.lineTo(back_x + corner_radius, back_y + box_size)
        # 左下角圆角
        path.arcTo(back_x, back_y + box_size - corner_radius * 2,
                   corner_radius * 2, corner_radius * 2, -90, -90)
        painter.drawPath(path)
        
        # 绘制前面的方块（左上）- 完整绘制
        painter.drawRoundedRect(10, 10, box_size, box_size, corner_radius, corner_radius)
        
        painter.end()
        return QIcon(pixmap)
    
    def _create_regenerate_icon(self):
        """创建重新生成图标（两个半圆形箭头）"""
        from PyQt6.QtCore import QPointF, QRectF
        from PyQt6.QtGui import QPainterPath
        import math
        
        # 使用更大的画布以获得更清晰的渲染
        size = 48
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # 设置颜色和画笔
        color = QColor("#ececf1") if self.theme == "dark" else QColor("#565869")
        pen = QPen(color, 2.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # 圆心和半径
        center_x = size / 2
        center_y = size / 2
        radius = 10  # 与复制图标的 box_size 一致（直径20）
        gap = 50  # 两个箭头之间的间隙（度数）
        
        # 绘制第一个半圆形箭头（右上到左下，顺时针）
        rect = QRectF(center_x - radius, center_y - radius, radius * 2, radius * 2)
        start_angle1 = (90 - gap / 2) * 16
        span_angle1 = (180 - gap) * 16  # 正值表示顺时针
        painter.drawArc(rect, start_angle1, span_angle1)
        
        # 第一个箭头的箭头头部（在左下方，指向顺时针方向）
        arrow1_angle = math.radians(270 + gap / 2)
        arrow1_tip_x = center_x + radius * math.cos(arrow1_angle)
        arrow1_tip_y = center_y + radius * math.sin(arrow1_angle)
        arrow_length = 4
        
        # 箭头1的两条边（指向顺时针方向）
        arrow1_inner_x = arrow1_tip_x + arrow_length * math.cos(arrow1_angle + math.radians(30))
        arrow1_inner_y = arrow1_tip_y + arrow_length * math.sin(arrow1_angle + math.radians(30))
        arrow1_outer_x = arrow1_tip_x - arrow_length * math.cos(arrow1_angle - math.radians(60))
        arrow1_outer_y = arrow1_tip_y - arrow_length * math.sin(arrow1_angle - math.radians(60))
        
        painter.drawLine(QPointF(arrow1_tip_x, arrow1_tip_y), QPointF(arrow1_inner_x, arrow1_inner_y))
        painter.drawLine(QPointF(arrow1_tip_x, arrow1_tip_y), QPointF(arrow1_outer_x, arrow1_outer_y))
        
        # 绘制第二个半圆形箭头（左下到右上，顺时针）
        start_angle2 = (270 - gap / 2) * 16
        span_angle2 = (180 - gap) * 16  # 正值表示顺时针
        painter.drawArc(rect, start_angle2, span_angle2)
        
        # 第二个箭头的箭头头部（在右上方，指向顺时针方向）
        arrow2_angle = math.radians(90 + gap / 2)
        arrow2_tip_x = center_x + radius * math.cos(arrow2_angle)
        arrow2_tip_y = center_y + radius * math.sin(arrow2_angle)
        
        # 箭头2的两条边（指向顺时针方向）
        arrow2_inner_x = arrow2_tip_x + arrow_length * math.cos(arrow2_angle + math.radians(30))
        arrow2_inner_y = arrow2_tip_y + arrow_length * math.sin(arrow2_angle + math.radians(30))
        arrow2_outer_x = arrow2_tip_x - arrow_length * math.cos(arrow2_angle - math.radians(60))
        arrow2_outer_y = arrow2_tip_y - arrow_length * math.sin(arrow2_angle - math.radians(60))
        
        painter.drawLine(QPointF(arrow2_tip_x, arrow2_tip_y), QPointF(arrow2_inner_x, arrow2_inner_y))
        painter.drawLine(QPointF(arrow2_tip_x, arrow2_tip_y), QPointF(arrow2_outer_x, arrow2_outer_y))
        
        painter.end()
        return QIcon(pixmap)
    
    def on_copy_clicked(self):
        """复制按钮点击"""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.current_text)
        # 暂时修改按钮图标以提示已复制
        original_icon = self.copy_button.icon()
        self.copy_button.setText("✓")
        self.copy_button.setIcon(QIcon())
        QTimer.singleShot(1000, lambda: (self.copy_button.setText(""), self.copy_button.setIcon(original_icon)))
    
    def on_regenerate_clicked(self):
        """重新生成按钮点击"""
        self.regenerate_clicked.emit()
    
    def set_theme(self, theme):
        """更新主题并重新生成图标和内容"""
        self.theme = theme
        
        # 重新创建复制和重新生成按钮图标
        if hasattr(self, 'copy_button'):
            self.copy_button.setIcon(self._create_copy_icon())
            self.copy_button.setProperty("theme", theme)
            # 刷新样式
            self.copy_button.style().unpolish(self.copy_button)
            self.copy_button.style().polish(self.copy_button)
        
        if hasattr(self, 'regenerate_button'):
            self.regenerate_button.setIcon(self._create_regenerate_icon())
            self.regenerate_button.setProperty("theme", theme)
            # 刷新样式
            self.regenerate_button.style().unpolish(self.regenerate_button)
            self.regenerate_button.style().polish(self.regenerate_button)
        
        # 重新渲染 Markdown HTML（使用新主题的CSS）
        if hasattr(self, 'markdown_browser') and self.current_text:
            html_content = markdown_to_html(self.current_text, self.theme)
            self.markdown_browser.setHtml(html_content)
    
    def showEvent(self, event):
        """组件显示事件 - 切换回来时重新调整高度"""
        super().showEvent(event)
        # 强制重新调整高度，避免切换界面后内容被裁剪
        if hasattr(self, 'markdown_browser') and self.markdown_browser.isVisible():
            QTimer.singleShot(50, self.adjust_height)  # 延迟50ms确保布局完成
    
    def adjust_height(self):
        """自动调整高度"""
        doc_height = self.markdown_browser.document().size().height()
        self.markdown_browser.setFixedHeight(int(doc_height) + 10)
    
    def append_text(self, text):
        """追加文本"""
        try:
            # 收到第一个文本块时（不管是否为空），移除思考动画
            # 这表示API已经开始响应，即使第一个块是空白
            if not self.first_text_received:
                self.first_text_received = True
                # 确保思考动画至少显示300ms后才停止（避免闪烁）
                if self.thinking_animation_started:
                    # 动画已经启动，延迟停止以保证最小显示时间
                    QTimer.singleShot(300, self._stop_thinking_animation)
                else:
                    # 动画还没启动（文本太快到达），直接停止
                    self._stop_thinking_animation()
            
            self.current_text += text
            html_content = markdown_to_html(self.current_text, self.theme)
            self.markdown_browser.setHtml(html_content)
        except Exception as e:
            print(f"[ERROR] append_text 出错: {e}")
    
    def finish(self):
        """完成流式输出"""
        try:
            # 如果还没有收到任何文本（思考动画还在显示），先移除它
            if not self.first_text_received:
                self.first_text_received = True
                self._stop_thinking_animation()
            
            # 确保最终内容被正确渲染为 HTML
            # 断开 contentsChanged 信号，避免在设置内容时触发高度调整
            try:
                self.markdown_browser.document().contentsChanged.disconnect(self.adjust_height)
            except:
                pass
            
            # 最后一次渲染
            final_html = markdown_to_html(self.current_text, self.theme)
            self.markdown_browser.setHtml(final_html)
            
            # 重新连接信号
            self.markdown_browser.document().contentsChanged.connect(self.adjust_height)
            
            # 手动调整一次高度
            self.adjust_height()
            
            # 显示操作按钮
            self.action_buttons_container.show()
            
            print(f"[OK] Markdown 渲染完成 (文本长度: {len(self.current_text)}, HTML长度: {len(final_html)})")
        except Exception as e:
            print(f"[ERROR] finish() 出错: {e}")
            import traceback
            safe_print(traceback.format_exc())
    
    def get_text(self):
        """获取当前文本"""
        return self.current_text
    
    def show_error(self, error_message, delay_ms=2000):
        """
        显示错误消息（流式输出，像正常回答一样）
        delay_ms: 延迟时间（毫秒），默认2秒
        """
        # 在错误消息前加警示符号
        full_error_text = f"⚠️ {error_message}"
        
        # 延迟后开始流式输出错误消息
        def start_streaming():
            # 停止思考动画
            if not self.first_text_received:
                self.first_text_received = True
                self._stop_thinking_animation()
            
            # 流式输出每个字符
            self._stream_error_text(full_error_text, 0)
        
        QTimer.singleShot(delay_ms, start_streaming)
    
    def _stream_error_text(self, text, index):
        """递归地流式输出错误文本"""
        if index < len(text):
            # 追加一个字符
            self.current_text += text[index]
            html_content = markdown_to_html(self.current_text, self.theme)
            self.markdown_browser.setHtml(html_content)
            
            # 延迟后输出下一个字符（30ms间隔）
            QTimer.singleShot(30, lambda: self._stream_error_text(text, index + 1))
    
    def show_tool_status(self, status_text):
        """
        显示工具调用状态
        
        Args:
            status_text: 状态文本
        """
        from PyQt6.QtWidgets import QLabel
        
        if not self.tool_status_label:
            # 创建状态标签
            self.tool_status_label = QLabel()
            self.tool_status_label.setObjectName("tool_status")
            self.tool_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # 插入到布局顶部（在 assistant_container 的第一个位置）
            # 找到 assistant_container
            outer_layout = self.layout()
            if outer_layout and outer_layout.count() >= 2:
                assistant_container = outer_layout.itemAt(1).widget()  # 索引 1 是 assistant_container
                if assistant_container:
                    container_layout = assistant_container.layout()
                    if container_layout:
                        container_layout.insertWidget(0, self.tool_status_label)
        
        # 更新状态文本
        self.tool_status_label.setText(f"🔧 {status_text}")
        self.tool_status_label.show()
        
        # 3秒后自动隐藏
        QTimer.singleShot(3000, self.tool_status_label.hide)


class ErrorMarkdownMessage(QFrame):
    """
    错误提示消息
    """
    
    def __init__(self, error_message, parent=None):
        super().__init__(parent)
        self.error_message = error_message
        self.init_ui()
    
    def init_ui(self):
        """初始化 UI"""
        self.setObjectName("error_message")
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(60, 20, 60, 20)
        main_layout.setSpacing(10)
        
        # 错误标题
        error_layout = QHBoxLayout()
        error_layout.setSpacing(10)
        
        icon = QLabel("⚠️")
        icon.setFont(QFont("Segoe UI Emoji", 12))
        
        title = QLabel("错误")
        title.setFont(QFont("Microsoft YaHei UI", 11, QFont.Weight.Bold))
        title.setObjectName("error_title")
        
        error_layout.addWidget(icon)
        error_layout.addWidget(title)
        error_layout.addStretch()
        
        main_layout.addLayout(error_layout)
        
        # 错误内容
        error_text = QLabel(self.error_message)
        error_text.setFont(QFont("Microsoft YaHei UI", 10))
        error_text.setWordWrap(True)
        error_text.setObjectName("error_text")
        
        main_layout.addWidget(error_text)

