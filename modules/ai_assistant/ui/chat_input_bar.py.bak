"""
ChatGPT 风格输入框组件
完全模仿 ChatGPT 网页端的输入区域
"""

from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QPushButton, QTextEdit, 
    QWidget, QApplication, QVBoxLayout, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor, QTextCursor, QKeyEvent


class ChatInputBar(QFrame):
    """
    ChatGPT 风格输入框
    
    信号：
        message_sent(str): 发送消息时触发，传递消息内容
    """
    
    message_sent = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ChatInputBar")
        self.init_ui()
        self.apply_styles()
        self.add_shadow()
        
    def init_ui(self):
        """初始化界面"""
        # 设置最小高度（允许动态增长）
        self.setMinimumHeight(60)
        self.setMinimumWidth(400)
        
        # 主布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # ========================================
        # 左侧 "+" 按钮
        # ========================================
        self.add_button = QPushButton("+")
        self.add_button.setObjectName("AddButton")
        self.add_button.setFixedSize(38, 38)
        self.add_button.setFont(QFont("Microsoft YaHei UI", 16))
        self.add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_button.setToolTip("附加文件")
        
        # ========================================
        # 中间输入框（自动调整高度）
        # ========================================
        self.input_field = QTextEdit()
        self.input_field.setObjectName("InputField")
        self.input_field.setPlaceholderText("发送消息...")
        self.input_field.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.input_field.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.input_field.setFont(QFont("Microsoft YaHei UI", 10))
        self.input_field.setMinimumHeight(38)
        self.input_field.setMaximumHeight(150)  # 最大高度约6行
        self.input_field.setTabChangesFocus(True)
        
        # 只接受纯文本，粘贴时自动去除格式
        self.input_field.setAcceptRichText(False)
        
        # 设置文档边距
        self.input_field.document().setDocumentMargin(2)
        
        # 连接文本变化信号，实现自动高度调整
        self.input_field.textChanged.connect(self.adjust_height)
        
        # 安装事件过滤器，处理 Enter 键
        self.input_field.installEventFilter(self)
        
        # ========================================
        # 右侧发送/语音按钮
        # ========================================
        self.send_button = QPushButton("➤")
        self.send_button.setObjectName("SendButton")
        self.send_button.setFixedSize(38, 38)
        self.send_button.setFont(QFont("Segoe UI", 14))
        self.send_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_button.setToolTip("发送消息 (Enter)")
        self.send_button.clicked.connect(self.send_message)
        
        # 添加到布局
        layout.addWidget(self.add_button)
        layout.addWidget(self.input_field, 1)  # 拉伸因子为 1
        layout.addWidget(self.send_button)
        
        # 初始化高度
        self.adjust_height()
        
    def apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            /* ========================================
               输入框容器（外层圆角矩形）
               ======================================== */
            QFrame#ChatInputBar {
                background-color: #2e2f32;
                border-radius: 24px;
                border: 1px solid #3c3d3f;
            }
            
            /* ========================================
               左侧 "+" 按钮
               ======================================== */
            QPushButton#AddButton {
                background: transparent;
                border: none;
                border-radius: 19px;
                color: #ffffff;
                font-weight: 500;
            }
            
            QPushButton#AddButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            
            QPushButton#AddButton:pressed {
                background-color: rgba(255, 255, 255, 0.15);
            }
            
            /* ========================================
               右侧发送按钮（粉红色圆形）
               ======================================== */
            QPushButton#SendButton {
                background-color: #b23565;
                border: none;
                border-radius: 19px;
                color: #ffffff;
                font-weight: bold;
            }
            
            QPushButton#SendButton:hover {
                background-color: #c94d79;
            }
            
            QPushButton#SendButton:pressed {
                background-color: #a02958;
            }
            
            QPushButton#SendButton:disabled {
                background-color: #4a4a4a;
                color: #888888;
            }
            
            /* ========================================
               中间输入框（无边框透明）
               ======================================== */
            QTextEdit#InputField {
                background: transparent;
                border: none;
                color: #ffffff;
                font-size: 15px;
                font-family: "Microsoft YaHei UI", "Segoe UI", "Inter", "Noto Sans", Arial, sans-serif;
                font-weight: 500;
                padding: 4px 6px;
                selection-background-color: #1e88e5;
                selection-color: #ffffff;
                letter-spacing: 0.2px;
            }
            
            /* Placeholder 文本样式 */
            QTextEdit#InputField::placeholder {
                color: #8e8ea0;
            }
            
            /* ========================================
               滚动条样式（深色主题）
               ======================================== */
            QTextEdit#InputField QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 0px;
            }
            
            QTextEdit#InputField QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                min-height: 20px;
            }
            
            QTextEdit#InputField QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            
            QTextEdit#InputField QScrollBar::add-line:vertical,
            QTextEdit#InputField QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QTextEdit#InputField QScrollBar::add-page:vertical,
            QTextEdit#InputField QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)
        
    def add_shadow(self):
        """添加阴影效果"""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)            # 模糊半径 12px
        shadow.setColor(QColor(0, 0, 0, 60))  # 黑色，透明度约 23%
        shadow.setOffset(0, 1)              # 向下偏移 1px
        self.setGraphicsEffect(shadow)
        
    def adjust_height(self):
        """根据内容自动调整输入框高度"""
        # 获取文档高度
        doc_height = self.input_field.document().size().height()
        
        # 计算新高度（文档高度 + 上下边距）
        content_height = int(doc_height) + 12
        
        # 限制在最小和最大高度之间
        min_height = 38
        max_height = 150
        new_height = min(max(min_height, content_height), max_height)
        
        # 只在高度变化时更新
        if self.input_field.height() != new_height:
            self.input_field.setFixedHeight(new_height)
            
            # 调整容器高度（输入框高度 + 上下内边距）
            container_height = new_height + 20  # 10px * 2
            self.setFixedHeight(container_height)
            
            # 如果超过最大高度，显示滚动条
            if content_height > max_height:
                self.input_field.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            else:
                self.input_field.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
    def eventFilter(self, obj, event):
        """事件过滤器：处理 Enter 和 Shift+Enter"""
        if obj == self.input_field and event.type() == event.Type.KeyPress:
            key_event = event
            
            # Enter 键（无修饰键）：发送消息
            if key_event.key() == Qt.Key.Key_Return and key_event.modifiers() == Qt.KeyboardModifier.NoModifier:
                self.send_message()
                return True  # 拦截事件
            
            # Shift+Enter：插入换行
            elif key_event.key() == Qt.Key.Key_Return and key_event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                self.input_field.insertPlainText("\n")
                return True
                
        return super().eventFilter(obj, event)
    
    def send_message(self):
        """发送消息"""
        message = self.input_field.toPlainText().strip()
        
        if message:
            self.message_sent.emit(message)
            self.input_field.clear()
            self.input_field.setFocus()
            # 清空后重置高度
            self.adjust_height()
            
    def get_text(self):
        """获取输入框内容"""
        return self.input_field.toPlainText()
    
    def clear(self):
        """清空输入框"""
        self.input_field.clear()
        # 清空后重置高度
        self.adjust_height()
        
    def set_focus(self):
        """设置焦点到输入框"""
        self.input_field.setFocus()
        
    def set_enabled(self, enabled: bool):
        """启用/禁用输入框"""
        self.input_field.setEnabled(enabled)
        self.send_button.setEnabled(enabled)
        self.add_button.setEnabled(enabled)


# ========================================
# 演示示例
# ========================================

class DemoWindow(QWidget):
    """演示窗口"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("ChatGPT 风格输入框演示")
        self.setGeometry(300, 200, 800, 600)
        
        # 设置深色背景（模拟 ChatGPT 界面）
        self.setStyleSheet("""
            QWidget {
                background-color: #343541;
            }
        """)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # 添加一些说明文本
        from PyQt6.QtWidgets import QLabel
        
        title = QLabel("ChatGPT 风格输入框")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #ececf1;
            font-family: "Microsoft YaHei UI", "Segoe UI";
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        description = QLabel(
            "• 按 Enter 发送消息\n"
            "• 按 Shift+Enter 换行\n"
            "• 左侧 + 按钮用于附件\n"
            "• 右侧粉色按钮发送"
        )
        description.setStyleSheet("""
            font-size: 14px;
            color: #b4b4b4;
            font-family: "Microsoft YaHei UI", "Segoe UI";
            line-height: 1.6;
        """)
        
        # 消息显示区域
        self.message_display = QLabel("等待消息...")
        self.message_display.setStyleSheet("""
            background-color: #444654;
            border-radius: 12px;
            padding: 20px;
            color: #ececf1;
            font-size: 15px;
            font-family: "Microsoft YaHei UI", "Segoe UI";
        """)
        self.message_display.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.message_display.setWordWrap(True)
        self.message_display.setMinimumHeight(200)
        
        # 创建输入框
        self.input_bar = ChatInputBar()
        self.input_bar.message_sent.connect(self.on_message_sent)
        
        # 添加到布局
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(self.message_display, 1)
        layout.addWidget(self.input_bar)
        
        # 自动聚焦到输入框
        self.input_bar.set_focus()
        
    def on_message_sent(self, message):
        """收到消息时的回调"""
        self.message_display.setText(f"📨 收到消息：\n\n{message}")


def main():
    """主函数"""
    import sys
    from PyQt6.QtGui import QFont
    
    # 设置高 DPI 支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # 设置全局字体
    default_font = QFont()
    default_font.setFamilies([
        "Microsoft YaHei UI",
        "Segoe UI", 
        "Inter",
        "Noto Sans"
    ])
    default_font.setPointSize(10)
    default_font.setWeight(QFont.Weight.Medium)
    default_font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    default_font.setStyleStrategy(
        QFont.StyleStrategy.PreferAntialias | 
        QFont.StyleStrategy.PreferQuality
    )
    app.setFont(default_font)
    
    # 创建并显示窗口
    window = DemoWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

