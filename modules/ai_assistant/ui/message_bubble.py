"""
消息气泡组件
负责显示用户和助手的消息
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont


class MessageBubble(QWidget):
    """
    消息气泡组件
    支持用户消息和助手消息的不同样式
    """
    
    def __init__(self, message, is_user=False, parent=None):
        super().__init__(parent)
        self.message = message
        self.is_user = is_user
        try:
            self.init_ui()
            # 暂时禁用动画，避免崩溃
            # self.animate_in()
        except Exception as e:
            import traceback
            print(f"初始化消息气泡时出错: {e}")
            print(traceback.format_exc())
    
    def init_ui(self):
        """初始化 UI"""
        # 主布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(40, 8, 40, 8)
        
        # 根据角色添加伸缩空间
        if self.is_user:
            main_layout.addStretch(1)
        
        # 气泡容器
        self.bubble_frame = QFrame()
        self.bubble_frame.setObjectName("message_bubble")
        self.bubble_frame.setProperty("is_user", self.is_user)
        
        bubble_layout = QVBoxLayout(self.bubble_frame)
        bubble_layout.setContentsMargins(16, 12, 16, 12)
        bubble_layout.setSpacing(8)
        
        # 角色标签
        role_layout = QHBoxLayout()
        role_layout.setSpacing(8)
        
        role_icon = QLabel("👤" if self.is_user else "🤖")
        role_icon.setFont(QFont("Segoe UI Emoji", 11))
        
        role_name = QLabel("You" if self.is_user else "ChatGPT")
        role_name.setFont(QFont("Microsoft YaHei UI", 10, QFont.Weight.Bold))
        role_name.setObjectName("role_label")
        
        role_layout.addWidget(role_icon)
        role_layout.addWidget(role_name)
        role_layout.addStretch()
        
        bubble_layout.addLayout(role_layout)
        
        # 消息内容
        self.message_label = QLabel()
        self.message_label.setFont(QFont("Microsoft YaHei UI", 10))
        self.message_label.setWordWrap(True)
        self.message_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.message_label.setObjectName("message_content")
        
        # 设置行距紧凑
        self.message_label.setStyleSheet("line-height: 1.4;")
        # 设置最小宽度，避免过早换行
        self.message_label.setMinimumWidth(200)
        
        # 处理 Markdown 样式（简单实现）
        try:
            formatted_message = self.format_message(self.message)
            self.message_label.setText(formatted_message)
        except Exception as e:
            import traceback
            print(f"设置消息文本时出错: {e}")
            print(traceback.format_exc())
            # 使用原始文本
            self.message_label.setText(str(self.message))
        
        bubble_layout.addWidget(self.message_label)
        
        # 设置最大宽度为窗口宽度的 70%
        # 窗口宽度 1100px - 侧边栏 240px = 860px
        # 减去边距约 80px，可用 780px，70% ≈ 550px
        # 设置为 600px 以获得更好的显示效果
        self.bubble_frame.setMaximumWidth(600)
        
        main_layout.addWidget(self.bubble_frame)
        
        # 根据角色添加伸缩空间
        if not self.is_user:
            main_layout.addStretch(1)
    
    def format_message(self, text):
        """
        格式化消息（简单的 Markdown 支持）
        支持：粗体、代码、链接等
        """
        try:
            # 替换换行符
            text = text.replace('\n', '<br>')
            
            # 粗体 **text**
            import re
            text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
            
            # 行内代码 `code`
            text = re.sub(r'`(.+?)`', r'<code style="background-color: rgba(127,127,127,0.1); padding: 2px 4px; border-radius: 3px; font-family: Consolas, monospace;">\1</code>', text)
            
            # 代码块 ```code```
            text = re.sub(
                r'```(.*?)```',
                r'<pre style="background-color: rgba(127,127,127,0.1); padding: 8px; border-radius: 6px; font-family: Consolas, monospace; overflow-x: auto;"><code>\1</code></pre>',
                text,
                flags=re.DOTALL
            )
            
            return text
        except Exception as e:
            import traceback
            print(f"格式化消息时出错: {e}")
            print(f"异常详情: {traceback.format_exc()}")
            # 返回原始文本（HTML 转义）
            try:
                return str(text).replace('\n', '<br>')
            except:
                return str(text)
    
    def animate_in(self):
        """淡入动画"""
        self.setWindowOpacity(0)
        
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(300)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()


class StreamingBubble(QWidget):
    """
    流式输出气泡
    用于实时显示 AI 回复
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_text = ""
        try:
            self.init_ui()
            # 暂时禁用动画
            # self.animate_in()
        except Exception as e:
            import traceback
            print(f"初始化流式气泡时出错: {e}")
            print(traceback.format_exc())
    
    def init_ui(self):
        """初始化 UI"""
        # 主布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(40, 8, 40, 8)
        
        # 气泡容器
        self.bubble_frame = QFrame()
        self.bubble_frame.setObjectName("message_bubble")
        self.bubble_frame.setProperty("is_user", False)
        
        bubble_layout = QVBoxLayout(self.bubble_frame)
        bubble_layout.setContentsMargins(16, 12, 16, 12)
        bubble_layout.setSpacing(8)
        
        # 角色标签
        role_layout = QHBoxLayout()
        role_layout.setSpacing(8)
        
        role_icon = QLabel("🤖")
        role_icon.setFont(QFont("Segoe UI Emoji", 11))
        
        role_name = QLabel("ChatGPT")
        role_name.setFont(QFont("Microsoft YaHei UI", 10, QFont.Weight.Bold))
        role_name.setObjectName("role_label")
        
        # 打字指示器
        self.typing_indicator = QLabel("●")
        self.typing_indicator.setObjectName("typing_indicator")
        self.typing_indicator.setFont(QFont("Microsoft YaHei UI", 8))
        
        role_layout.addWidget(role_icon)
        role_layout.addWidget(role_name)
        role_layout.addWidget(self.typing_indicator)
        role_layout.addStretch()
        
        bubble_layout.addLayout(role_layout)
        
        # 消息内容
        self.message_label = QLabel("")
        self.message_label.setFont(QFont("Microsoft YaHei UI", 10))
        self.message_label.setWordWrap(True)
        self.message_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.message_label.setObjectName("message_content")
        
        # 设置行距紧凑
        self.message_label.setStyleSheet("line-height: 1.4;")
        # 设置最小宽度，避免过早换行
        self.message_label.setMinimumWidth(200)
        
        bubble_layout.addWidget(self.message_label)
        
        # 设置最大宽度为窗口宽度的 70%
        self.bubble_frame.setMaximumWidth(600)
        
        main_layout.addWidget(self.bubble_frame)
        main_layout.addStretch(1)
    
    def append_text(self, text):
        """追加文本"""
        try:
            self.current_text += text
            # 简单格式化
            formatted_text = self.format_message(self.current_text)
            self.message_label.setText(formatted_text)
        except Exception as e:
            import traceback
            print(f"追加文本时出错: {e}")
            print(traceback.format_exc())
            # 尝试使用原始文本
            try:
                self.message_label.setText(str(self.current_text))
            except:
                pass
    
    def get_text(self):
        """获取当前文本"""
        return self.current_text
    
    def format_message(self, text):
        """格式化消息（与 MessageBubble 相同）"""
        try:
            text = text.replace('\n', '<br>')
            
            import re
            text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
            text = re.sub(r'`(.+?)`', r'<code style="background-color: rgba(127,127,127,0.1); padding: 2px 4px; border-radius: 3px; font-family: Consolas, monospace;">\1</code>', text)
            text = re.sub(
                r'```(.*?)```',
                r'<pre style="background-color: rgba(127,127,127,0.1); padding: 8px; border-radius: 6px; font-family: Consolas, monospace; overflow-x: auto;"><code>\1</code></pre>',
                text,
                flags=re.DOTALL
            )
            
            return text
        except Exception as e:
            print(f"流式格式化消息时出错: {e}")
            return text.replace('\n', '<br>') if '\n' in text else text
    
    def animate_in(self):
        """淡入动画"""
        self.setWindowOpacity(0)
        
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(300)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()


class ErrorBubble(QWidget):
    """
    错误提示气泡
    """
    
    def __init__(self, error_message, parent=None):
        super().__init__(parent)
        self.error_message = error_message
        try:
            self.init_ui()
            # 暂时禁用动画
            # self.animate_in()
        except Exception as e:
            import traceback
            print(f"初始化错误气泡时出错: {e}")
            print(traceback.format_exc())
    
    def init_ui(self):
        """初始化 UI"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(40, 8, 40, 8)
        
        # 错误容器
        error_frame = QFrame()
        error_frame.setObjectName("error_bubble")
        
        error_layout = QHBoxLayout(error_frame)
        error_layout.setContentsMargins(16, 12, 16, 12)
        error_layout.setSpacing(10)
        
        # 错误图标
        error_icon = QLabel("⚠️")
        error_icon.setFont(QFont("Segoe UI Emoji", 12))
        
        # 错误消息
        error_label = QLabel(self.error_message)
        error_label.setFont(QFont("Microsoft YaHei UI", 10))
        error_label.setWordWrap(True)
        error_label.setObjectName("error_text")
        
        error_layout.addWidget(error_icon)
        error_layout.addWidget(error_label, 1)
        
        # 设置最大宽度为窗口宽度的 70%
        error_frame.setMaximumWidth(600)
        
        main_layout.addWidget(error_frame)
        main_layout.addStretch(1)
    
    def animate_in(self):
        """淡入动画"""
        self.setWindowOpacity(0)
        
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(300)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()

