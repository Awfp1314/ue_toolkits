"""
主窗口模块
ChatGPT 风格的主界面
"""

import os
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QTextEdit, QPushButton, QLabel,
    QFrame, QComboBox, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QEvent, QTimer
from PyQt6.QtGui import QFont, QTextCursor

from modules.ai_assistant.ui.message_bubble import MessageBubble, StreamingBubble, ErrorBubble
from modules.ai_assistant.ui.markdown_message import MarkdownMessage, StreamingMarkdownMessage, ErrorMarkdownMessage
from modules.ai_assistant.logic.api_client import APIClient
from modules.ai_assistant.ui.chat_input import ChatInputArea
from modules.ai_assistant.logic.config import SYSTEM_PROMPT
from modules.ai_assistant.logic.context_manager import ContextManager


class ChatWindow(QWidget):
    """
    聊天窗口类
    实现 ChatGPT 风格的界面布局
    可作为独立窗口或模块嵌入使用
    """
    
    def __init__(self, as_module=False):
        super().__init__()
        self.as_module = as_module  # 是否作为模块运行
        
        # ========================================
        # 窗口属性优化（提升字体渲染质量）
        # ========================================
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        
        # 对话状态
        # 初始化对话历史，包含系统提示词
        self.conversation_history = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]
        self.current_api_client = None
        self.current_streaming_bubble = None
        self.current_theme = "dark"  # 默认深色主题
        
        # 上下文管理器（延迟初始化，需要asset_manager_logic和config_tool_logic）
        self.context_manager: Optional[ContextManager] = None
        self.asset_manager_logic = None
        self.config_tool_logic = None
        
        self.init_ui()
        self.load_theme(self.current_theme)
    
    def set_asset_manager_logic(self, asset_manager_logic):
        """设置asset_manager逻辑层引用
        
        Args:
            asset_manager_logic: asset_manager模块的逻辑层实例
        """
        from core.logger import get_logger
        logger = get_logger(__name__)
        
        print("[DEBUG] ===== set_asset_manager_logic 被调用 =====")
        print(f"[DEBUG] asset_manager_logic 类型: {type(asset_manager_logic)}")
        
        self.asset_manager_logic = asset_manager_logic
        self._init_context_manager(logger)
    
    def set_config_tool_logic(self, config_tool_logic):
        """设置config_tool逻辑层引用
        
        Args:
            config_tool_logic: config_tool模块的逻辑层实例
        """
        from core.logger import get_logger
        logger = get_logger(__name__)
        
        print("[DEBUG] ===== set_config_tool_logic 被调用 =====")
        print(f"[DEBUG] config_tool_logic 类型: {type(config_tool_logic)}")
        
        self.config_tool_logic = config_tool_logic
        self._init_context_manager(logger)
    
    def _init_context_manager(self, logger):
        """初始化上下文管理器（内部方法）"""
        try:
            self.context_manager = ContextManager(
                asset_manager_logic=self.asset_manager_logic,
                config_tool_logic=self.config_tool_logic
            )
            print("[DEBUG] [OK] ChatWindow 上下文管理器已成功初始化")
            logger.info("ChatWindow上下文管理器已初始化")
        except Exception as e:
            print(f"[DEBUG] [ERROR] 初始化上下文管理器失败: {e}")
            logger.error(f"初始化上下文管理器失败: {e}", exc_info=True)
            self.context_manager = None
            import traceback
            traceback.print_exc()
    
    def init_ui(self):
        """初始化用户界面"""
        if not self.as_module:
            self.setWindowTitle("虚幻引擎助手")
            self.setGeometry(200, 100, 1100, 750)
            self.setMinimumSize(900, 600)
        
        # 主布局（直接在 self 上创建）
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建聊天区域
        self.chat_widget = self.create_chat_area()
        
        # 添加到主布局
        main_layout.addWidget(self.chat_widget, 1)
        
        # 延迟500ms后自动发送欢迎消息
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(500, self.send_auto_greeting)
    
    def create_chat_area(self):
        """创建聊天区域"""
        chat_widget = QWidget()
        chat_widget.setObjectName("chat_area")
        
        # 使用绝对定位布局
        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)
        
        # 消息显示区域（滚动），占满整个空间
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("messages_scroll")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 外层容器（用于居中内容列）
        viewport_widget = QWidget()
        outer_layout = QVBoxLayout(viewport_widget)
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        
        # 内容列（固定最大宽度，居中显示）
        self.content_column = QWidget()
        self.content_column.setObjectName("ContentColumn")
        self.content_column.setMaximumWidth(900)  # ChatGPT 风格的最大宽度
        self.content_column.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        
        # 内容列的布局
        self.messages_layout = QVBoxLayout(self.content_column)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.messages_layout.setContentsMargins(0, 20, 0, 150)
        self.messages_layout.setSpacing(0)
        self.messages_layout.addStretch(1)
        
        outer_layout.addWidget(self.content_column)
        self.scroll_area.setWidget(viewport_widget)
        chat_layout.addWidget(self.scroll_area, 1)
        
        # 创建输入区并设为 chat_widget 的子控件（浮动在底部）
        input_area = self.create_input_area()
        input_area.setParent(chat_widget)
        
        # 监听窗口大小变化，调整输入框位置
        def on_resize(event):
            self.position_input_area(chat_widget)
            QWidget.resizeEvent(chat_widget, event)
        
        chat_widget.resizeEvent = on_resize
        
        # 延迟初始化位置
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, lambda: self.position_input_area(chat_widget))
        
        return chat_widget
    
    def position_input_area(self, chat_widget):
        """定位输入框到聊天区域底部（与内容列居中对齐）"""
        if hasattr(self, 'input_area') and hasattr(self, 'content_column'):
            width = chat_widget.width()
            height = chat_widget.height()
            input_height = self.input_area.sizeHint().height()
            
            # 计算内容列的实际宽度（最大900px）
            content_width = min(900, width)
            # 计算居中位置
            left_margin = (width - content_width) // 2
            
            # 将输入框定位到底部居中（与内容列宽度一致）
            self.input_area.setGeometry(left_margin, height - input_height, content_width, input_height)
            self.input_area.raise_()  # 确保在最上层
    
    def create_input_area(self):
        """创建底部输入区域（ChatGPT 风格）"""
        # 使用新的 ChatInputArea 组件
        self.input_area = ChatInputArea()
        self.input_area.message_sent.connect(self.on_message_sent)
        self.input_area.message_with_images_sent.connect(self.on_message_with_images_sent)
        self.input_area.stop_generation.connect(self.stop_generation)
        
        # 监听输入框高度变化，触发重新定位（保持底部固定，向上增长）
        self.input_area.height_changed.connect(
            lambda: self.position_input_area(self.chat_widget)
        )
        
        # 保持兼容性
        self.input_field = self.input_area.input_field
        self.send_button = self.input_area.send_button
        
        return self.input_area
    
    def on_message_sent(self, message):
        """处理发送的消息"""
        self.send_message()
    
    def on_message_with_images_sent(self, message, images):
        """处理带图片的消息"""
        self.send_message_with_images(message, images)
    
    def eventFilter(self, obj, event):
        """事件过滤器（处理 Enter 键）"""
        if obj == self.input_field and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                # Shift+Enter 换行，Enter 发送
                if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                    return False
                else:
                    self.send_message()
                    return True
        return super().eventFilter(obj, event)
    
    def add_message(self, message, is_user=False):
        """添加 Markdown 消息"""
        role = "user" if is_user else "assistant"
        markdown_msg = MarkdownMessage(role, message, theme=self.current_theme)
        self.messages_layout.insertWidget(
            self.messages_layout.count() - 1,
            markdown_msg
        )
        self.scroll_to_bottom()
    
    def send_auto_greeting(self):
        """自动发送欢迎问候消息（不显示用户气泡）"""
        try:
            # 将消息添加到对话历史（不显示用户气泡）
            greeting_message = "你好"
            self.conversation_history.append({
                "role": "user",
                "content": greeting_message
            })
            
            # 添加流式输出气泡
            self.add_streaming_bubble()
            
            # 发起API请求
            model = self.input_area.get_selected_model()
            print(f"[DEBUG] 自动发送问候，使用模型: {model}")
            self.current_api_client = APIClient(
                self.conversation_history.copy(),
                model=model
            )
            self.current_api_client.chunk_received.connect(self.on_chunk_received)
            self.current_api_client.request_finished.connect(self.on_request_finished)
            self.current_api_client.error_occurred.connect(self.on_error_occurred)
            print(f"[DEBUG] 启动自动问候 API 请求...")
            self.current_api_client.start()
        except Exception as e:
            print(f"[ERROR] 自动发送问候消息时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def add_streaming_bubble(self):
        """添加流式输出 Markdown 消息"""
        self.current_streaming_bubble = StreamingMarkdownMessage(theme=self.current_theme)
        # 连接重新生成信号
        self.current_streaming_bubble.regenerate_clicked.connect(self.on_regenerate_response)
        self.messages_layout.insertWidget(
            self.messages_layout.count() - 1,
            self.current_streaming_bubble
        )
        self.scroll_to_bottom()
    
    def add_error_bubble(self, error_message):
        """添加错误提示"""
        error_msg = ErrorMarkdownMessage(error_message)
        self.messages_layout.insertWidget(
            self.messages_layout.count() - 1,
            error_msg
        )
        self.scroll_to_bottom()
    
    def scroll_to_bottom(self):
        """滚动到底部"""
        # 使用 QTimer 确保在主线程中更新
        QTimer.singleShot(0, self._do_scroll)
    
    def _do_scroll(self):
        """执行滚动"""
        try:
            scrollbar = self.scroll_area.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        except:
            pass
    
    def send_message(self):
        """发送消息"""
        try:
            message = self.input_field.toPlainText().strip()
            
            if not message:
                return
            
            print(f"[DEBUG] 准备发送消息: {message[:50]}...")
            print(f"[DEBUG] 上下文管理器状态: {self.context_manager is not None}")
            
            # 保存消息并清空输入框（切换为暂停按钮）
            self.input_area.save_and_clear_message()
            
            # 锁定输入框（阻止用户编辑，但不影响按钮事件）
            self.input_field.lock()
            
            # 添加用户消息
            self.add_message(message, is_user=True)
            
            # 构建上下文（如果上下文管理器已初始化）
            full_message = message
            if self.context_manager:
                try:
                    print("[DEBUG] 正在构建上下文...")
                    context = self.context_manager.build_context(message)
                    if context:
                        # 将上下文添加到用户消息前（作为附加信息）
                        full_message = message + "\n\n" + context
                        print(f"[DEBUG] [OK] 已添加上下文信息，上下文长度: {len(context)} 字符")
                        print(f"[DEBUG] 上下文预览: {context[:200]}...")
                    else:
                        print("[DEBUG] [WARN] 上下文管理器返回空内容")
                except Exception as e:
                    print(f"[WARNING] [ERROR] 构建上下文失败: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("[DEBUG] [WARN] 上下文管理器未初始化！AI 无法访问资产/文档/日志数据")
            
            # 添加到对话历史
            self.conversation_history.append({
                "role": "user",
                "content": full_message
            })
            
            # 添加流式输出气泡
            self.add_streaming_bubble()
            
            # 启动 API 请求
            model = self.input_area.get_selected_model()
            print(f"[DEBUG] 使用模型: {model}")
            self.current_api_client = APIClient(
                self.conversation_history.copy(),
                model=model
            )
            self.current_api_client.chunk_received.connect(self.on_chunk_received)
            self.current_api_client.request_finished.connect(self.on_request_finished)
            self.current_api_client.error_occurred.connect(self.on_error_occurred)
            print(f"[DEBUG] 启动 API 请求...")
            self.current_api_client.start()
        except Exception as e:
            print(f"[ERROR] 发送消息时出错: {e}")
            import traceback
            traceback.print_exc()
            # 恢复输入框状态
            self.input_field.unlock()
            self.input_area.set_generating_state(False)
    
    def send_message_with_images(self, message, images):
        """发送带图片的消息"""
        try:
            print(f"[DEBUG] 准备发送消息: {message[:50] if message else '(仅图片)'}... 图片数量: {len(images)}")
            
            # 保存消息并清空输入框（切换为暂停按钮）
            self.input_area.save_and_clear_message()
            
            # 锁定输入框（阻止用户编辑，但不影响按钮事件）
            self.input_field.lock()
            
            # 添加用户消息（暂时只显示文本，后续可以优化显示图片）
            display_message = message if message else "[图片]"
            self.add_message(display_message, is_user=True)
            
            # 构建多模态内容
            content = []
            if message:
                content.append({"type": "text", "text": message})
            
            for image_base64 in images:
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_base64}"
                    }
                })
            
            # 添加到对话历史
            self.conversation_history.append({
                "role": "user",
                "content": content
            })
            
            # 清空输入框（已在 ChatInputArea.send_message 中处理）
            
            # 添加流式输出气泡
            self.add_streaming_bubble()
            
            # 启动 API 请求（使用支持视觉的模型）
            model = "gpt-4o"  # 使用 gpt-4o 支持图片
            print(f"[DEBUG] 使用模型: {model}")
            self.current_api_client = APIClient(
                self.conversation_history.copy(),
                model=model
            )
            self.current_api_client.chunk_received.connect(self.on_chunk_received)
            self.current_api_client.request_finished.connect(self.on_request_finished)
            self.current_api_client.error_occurred.connect(self.on_error_occurred)
            print(f"[DEBUG] 启动 API 请求...")
            self.current_api_client.start()
        except Exception as e:
            print(f"[ERROR] 发送消息时出错: {e}")
            import traceback
            traceback.print_exc()
            # 恢复输入框状态
            self.input_field.unlock()
            self.input_area.set_generating_state(False)
    
    def on_chunk_received(self, chunk):
        """接收流式数据"""
        try:
            # 使用 repr 避免 Unicode 编码错误
            try:
                print(f"[DEBUG] 收到数据块: {chunk[:20]}...")
            except UnicodeEncodeError:
                pass  # 忽略 print 的编码错误
            
            if self.current_streaming_bubble:
                self.current_streaming_bubble.append_text(chunk)
                self.scroll_to_bottom()
        except Exception as e:
            try:
                print(f"[ERROR] 处理数据块时出错: {e}")
            except UnicodeEncodeError:
                pass
            import traceback
            traceback.print_exc()
    
    def on_request_finished(self):
        """请求完成"""
        try:
            try:
                print(f"[DEBUG] 请求完成")
            except UnicodeEncodeError:
                pass
            
            # 保存助手回复并完成渲染
            if self.current_streaming_bubble:
                # 调用 finish 方法完成流式输出
                self.current_streaming_bubble.finish()
                
                assistant_message = self.current_streaming_bubble.get_text()
                try:
                    print(f"[DEBUG] 助手消息: {assistant_message[:50]}...")
                except UnicodeEncodeError:
                    pass
                if assistant_message:
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": assistant_message
                    })
                    
                    # 保存对话到记忆（如果上下文管理器可用）
                    if self.context_manager and hasattr(self.context_manager, 'memory'):
                        # 获取最后一条用户消息
                        user_message = ""
                        for msg in reversed(self.conversation_history):
                            if msg.get("role") == "user":
                                user_message = msg.get("content", "")
                                break
                        
                        if user_message:
                            # 保存到增强型记忆管理器
                            # 使用对话格式，保存到 SESSION 级别（会话结束后清除）
                            from modules.ai_assistant.logic.enhanced_memory_manager import MemoryLevel
                            
                            # 保存用户查询和 AI 回复为一轮对话
                            self.context_manager.memory.add_dialogue(user_message, assistant_message)
                            
                            # 同时提取关键信息保存到持久化记忆（如果重要）
                            # 例如：用户提到的偏好、常见问题等
                            if any(keyword in user_message for keyword in ['喜欢', '常用', '偏好', '习惯']):
                                self.context_manager.memory.add_memory(
                                    content=f"用户偏好: {user_message}",
                                    level=MemoryLevel.USER,
                                    metadata={'type': 'preference', 'source': 'conversation'},
                                    auto_evaluate=True
                                )
                            
                            print(f"[DEBUG] [OK] 已保存对话到增强型记忆管理器")
            
            # 解锁输入框
            self.input_field.unlock()
            # 恢复发送按钮状态（从暂停切换回发送）
            self.input_area.set_generating_state(False)
            self.input_field.setFocus()
            
            # 清理
            self.current_api_client = None
            self.current_streaming_bubble = None
        except Exception as e:
            print(f"[ERROR] 请求完成处理时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def on_error_occurred(self, error_message):
        """处理错误（显示思考动画，然后显示错误消息）"""
        try:
            print(f"[ERROR] API错误: {error_message}")
            
            # 如果有流式气泡，在其中显示错误（带思考动画）
            if self.current_streaming_bubble:
                # 显示错误消息（延迟2秒，让思考动画显示一会儿）
                self.current_streaming_bubble.show_error(error_message, delay_ms=2000)
                
                # 延迟2.5秒后重新启用输入（等错误消息显示后）
                QTimer.singleShot(2500, self._enable_input_after_error)
            else:
                # 如果没有流式气泡（不应该发生），使用旧的错误气泡方式
                self.add_error_bubble(error_message)
                self._enable_input_after_error()
            
            # 清理
            self.current_api_client = None
            self.current_streaming_bubble = None
        except Exception as e:
            print(f"[ERROR] 错误处理时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def _enable_input_after_error(self):
        """重新启用输入（错误显示后）"""
        self.input_field.unlock()
        # 恢复发送按钮状态（从暂停切换回发送）
        self.input_area.set_generating_state(False)
        self.input_field.setFocus()
    
    def stop_generation(self):
        """停止当前的 AI 生成"""
        try:
            print("[DEBUG] 停止生成")
            
            # 停止 API 请求
            if self.current_api_client:
                print("[DEBUG] 终止 API 请求线程")
                # 强制终止线程（不推荐但有效）
                self.current_api_client.terminate()
                self.current_api_client = None
            
            # 清理流式气泡
            if self.current_streaming_bubble:
                # 完成当前的流式输出（显示已接收的部分）
                self.current_streaming_bubble.finish()
                
                # 保存已接收的部分消息（如果有的话）
                assistant_message = self.current_streaming_bubble.get_text()
                if assistant_message and assistant_message.strip():
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": assistant_message
                    })
                
                self.current_streaming_bubble = None
            
            # 恢复输入框和消息
            self.input_field.unlock()
            self.input_area.restore_message()
            self.input_field.setFocus()
            
            print("[DEBUG] 生成已停止，消息已恢复")
        except Exception as e:
            print(f"[ERROR] 停止生成时出错: {e}")
            import traceback
            traceback.print_exc()
            # 确保恢复正常状态
            self.input_field.unlock()
            self.input_area.set_generating_state(False)
    
    def on_regenerate_response(self):
        """重新生成回答"""
        try:
            print("[DEBUG] 重新生成回答")
            
            # 检查对话历史，确保至少有系统提示和一条用户消息
            if len(self.conversation_history) < 2:
                print("[ERROR] 对话历史不足，无法重新生成")
                return
            
            # 移除最后一条 AI 回复（如果存在）
            if self.conversation_history[-1]["role"] == "assistant":
                self.conversation_history.pop()
                print("[DEBUG] 已从对话历史中移除最后一条 AI 回复")
            
            # 查找并移除最后一条 AI 消息的 widget
            last_ai_widget = None
            for i in range(self.messages_layout.count() - 1, -1, -1):
                widget = self.messages_layout.itemAt(i).widget()
                if widget:
                    # 检查是否是 StreamingMarkdownMessage 或 MarkdownMessage
                    from markdown_message import StreamingMarkdownMessage, MarkdownMessage
                    if isinstance(widget, (StreamingMarkdownMessage, MarkdownMessage)):
                        # 检查是否是 assistant 角色的消息
                        if hasattr(widget, 'role') and widget.role == "assistant":
                            last_ai_widget = widget
                            print(f"[DEBUG] 找到最后一条 AI 消息 widget: {type(widget).__name__}")
                            break
            
            # 删除找到的 AI 消息 widget
            if last_ai_widget:
                print("[DEBUG] 正在移除最后一条 AI 消息的 widget")
                self.messages_layout.removeWidget(last_ai_widget)
                last_ai_widget.setParent(None)
                last_ai_widget.deleteLater()
                
                # 如果删除的是当前流式气泡，清空引用
                if last_ai_widget == self.current_streaming_bubble:
                    self.current_streaming_bubble = None
                
                # 强制刷新界面
                from PyQt6.QtWidgets import QApplication
                QApplication.processEvents()
                print("[DEBUG] AI 消息 widget 已清除，界面已刷新")
            else:
                print("[DEBUG] 未找到需要删除的 AI 消息 widget")
            
            # 添加新的流式输出气泡
            self.add_streaming_bubble()
            print("[DEBUG] 已添加新的流式气泡")
            
            # 重新发起 API 请求
            model = self.input_area.get_selected_model()
            print(f"[DEBUG] 使用模型: {model}")
            self.current_api_client = APIClient(
                self.conversation_history.copy(),
                model=model
            )
            self.current_api_client.chunk_received.connect(self.on_chunk_received)
            self.current_api_client.request_finished.connect(self.on_request_finished)
            self.current_api_client.error_occurred.connect(self.on_error_occurred)
            print(f"[DEBUG] 重新启动 API 请求...")
            self.current_api_client.start()
        except Exception as e:
            print(f"[ERROR] 重新生成回答时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def clear_chat(self):
        """清空当前对话"""
        # 清空对话历史，并重新添加系统提示词
        self.conversation_history.clear()
        self.conversation_history.append({
            "role": "system",
            "content": SYSTEM_PROMPT
        })
        
        # 清空界面
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.current_streaming_bubble = None
    
    def new_conversation(self):
        """新建对话"""
        self.clear_chat()
    
    def toggle_theme(self):
        """切换主题"""
        if self.current_theme == "dark":
            self.current_theme = "light"
        else:
            self.current_theme = "dark"
        
        self.load_theme(self.current_theme)
    
    def load_theme(self, theme_name):
        """加载主题样式"""
        from pathlib import Path
        
        # 获取模块资源目录
        module_dir = Path(__file__).parent.parent
        theme_file = module_dir / "resources" / "themes" / f"{theme_name}.qss"
        
        if theme_file.exists():
            with open(theme_file, "r", encoding="utf-8") as f:
                stylesheet = f.read()
                self.setStyleSheet(stylesheet)
        else:
            # 如果文件不存在，使用内置样式
            if theme_name == "dark":
                self.setStyleSheet(self.get_dark_theme())
            else:
                self.setStyleSheet(self.get_light_theme())
    
    def get_dark_theme(self):
        """获取深色主题（内置）"""
        return """
            /* ========================================
               全局字体设置（ChatGPT 风格 - 清晰舒服）
               ======================================== */
            * {
                font-family: "Inter", "Noto Sans", "Microsoft YaHei UI", 
                             "PingFang SC", "Hiragino Sans GB", "Helvetica Neue",
                             "Segoe UI", Arial, sans-serif;
                font-size: 15px;
                font-weight: 400;
                letter-spacing: 0.2px;
                color: #EDEDED;
            }
            
            /* 深色主题 */
            QMainWindow {
                background-color: #444654;
            }
            
            /* 侧边栏 */
            #sidebar {
                background-color: #202123;
                border-right: 1px solid #2f2f2f;
            }
            
            #new_chat_button {
                background-color: transparent;
                color: #ececf1;
                border: 1px solid #565869;
                border-radius: 8px;
                padding: 10px;
            }
            
            #new_chat_button:hover {
                background-color: #2a2b32;
            }
            
            #sidebar_label {
                color: #8e8ea0;
            }
            
            #history_list {
                background-color: transparent;
                border: none;
                color: #ececf1;
            }
            
            #history_list::item {
                padding: 10px;
                border-radius: 6px;
                margin: 2px 0;
            }
            
            #history_list::item:hover {
                background-color: #2a2b32;
            }
            
            #history_list::item:selected {
                background-color: #343541;
            }
            
            #sidebar_button {
                background-color: transparent;
                color: #ececf1;
                border: 1px solid #565869;
                border-radius: 6px;
                text-align: left;
                padding-left: 12px;
            }
            
            #sidebar_button:hover {
                background-color: #2a2b32;
            }
            
            /* 收起/展开按钮 - ChatGPT 风格描边按钮 */
            SidebarToggleButton, QToolButton#collapse_button, QToolButton#expand_button {
                background-color: transparent;
                border: none;
                padding: 0px;
            }
            
            /* 聊天区域 */
            #chat_area {
                background-color: #343541;
            }
            
            #header {
                background-color: #343541;
                border-bottom: 1px solid #4a4a5f;
            }
            
            #title_label {
                color: #ececf1;
            }
            
            #theme_button {
                background-color: transparent;
                border: none;
                border-radius: 6px;
            }
            
            #theme_button:hover {
                background-color: #444654;
            }
            
            #messages_scroll {
                background-color: #343541;
                border: none;
            }
            
            /* 消息气泡 */
            QFrame#message_bubble[is_user="false"] {
                background-color: #444654;
                border-radius: 12px;
                border: 1px solid #565869;
            }
            
            QFrame#message_bubble[is_user="true"] {
                background-color: #2a6f3f;
                border-radius: 12px;
                border: 1px solid #3a8f5f;
            }
            
            #role_label {
                color: #ececf1;
            }
            
            #message_content {
                color: #ececf1;
            }
            
            #typing_indicator {
                color: #10a37f;
            }
            
            /* 错误气泡 */
            #error_bubble {
                background-color: #5c1a1a;
                border-radius: 10px;
                border-left: 4px solid #ef4444;
            }
            
            #error_text {
                color: #fecaca;
            }
            
            /* 输入区域 */
            #input_container {
                background-color: #343541;
                border-top: 1px solid #4a4a5f;
            }
            
            #model_label {
                color: #8e8ea0;
            }
            
            #model_combo {
                background-color: #40414f;
                color: #ececf1;
                border: 1px solid #565869;
                border-radius: 6px;
                padding: 5px 10px;
            }
            
            #model_combo::drop-down {
                border: none;
            }
            
            #model_combo QAbstractItemView {
                background-color: #40414f;
                color: #ececf1;
                selection-background-color: #1e88e5;
                selection-color: #ffffff;
                border: 1px solid #565869;
            }
            
            /* ChatGPT 风格输入容器 */
            QFrame#ChatInputBar {
                background-color: #343541;
                border: none;
                border-radius: 24px;
            }
            
            #input_wrapper {
                background-color: #40414f;
                border: 1px solid #565869;
                border-radius: 12px;
            }
            
            /* 输入框 - ChatGPT 风格 */
            #input_field, #input_field_chatgpt {
                background-color: transparent;
                color: #ffffff;
                border: none;
                font-size: 15px;
                padding: 6px 12px;
                selection-background-color: #1e88e5;
                selection-color: #ffffff;
            }
            
            #input_field:focus, #input_field_chatgpt:focus {
                background-color: rgba(255, 255, 255, 0.03);
            }
            
            /* 发送按钮 - ChatGPT 风格白色圆形 */
            QPushButton#send_button_chatgpt {
                background-color: #ffffff;
                color: #343541;
                border: none;
                border-radius: 18px;
                padding: 0px;
                text-align: center;
                font-size: 16px;
                font-weight: bold;
            }
            
            QPushButton#send_button_chatgpt:hover {
                background-color: #f0f0f0;
            }
            
            QPushButton#send_button_chatgpt:pressed {
                background-color: #e0e0e0;
            }
            
            QPushButton#send_button_chatgpt:disabled {
                background-color: #565869;
                color: #8e8ea0;
            }
            
            /* + 按钮 */
            QPushButton#add_button {
                background-color: transparent;
                color: #8e8ea0;
                border: 1px solid #565869;
                border-radius: 16px;
            }
            
            QPushButton#add_button:hover {
                background-color: rgba(255, 255, 255, 0.05);
                border-color: #6b7280;
            }
            
            /* 提示文本 */
            QLabel#hint_label {
                color: rgba(255, 255, 255, 0.4);
                font-size: 13px;
            }
            
            /* 滚动条 */
            QScrollBar:vertical {
                background-color: #343541;
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #565869;
                border-radius: 6px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #6e6e80;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """
    
    def get_light_theme(self):
        """获取浅色主题（内置）"""
        return """
            /* ========================================
               全局字体设置（ChatGPT 风格 - 清晰舒服）
               ======================================== */
            * {
                font-family: "Inter", "Noto Sans", "Microsoft YaHei UI", 
                             "PingFang SC", "Hiragino Sans GB", "Helvetica Neue",
                             "Segoe UI", Arial, sans-serif;
                font-size: 15px;
                font-weight: 400;
                letter-spacing: 0.2px;
                color: #2d333a;
            }
            
            /* 浅色主题 */
            QMainWindow {
                background-color: #ffffff;
            }
            
            /* 侧边栏 */
            #sidebar {
                background-color: #f7f7f8;
                border-right: 1px solid #e5e5e7;
            }
            
            #new_chat_button {
                background-color: transparent;
                color: #2d333a;
                border: 1px solid #d1d5da;
                border-radius: 8px;
                padding: 10px;
            }
            
            #new_chat_button:hover {
                background-color: #ececed;
            }
            
            #sidebar_label {
                color: #6e7681;
            }
            
            #history_list {
                background-color: transparent;
                border: none;
                color: #2d333a;
            }
            
            #history_list::item {
                padding: 10px;
                border-radius: 6px;
                margin: 2px 0;
            }
            
            #history_list::item:hover {
                background-color: #ececed;
            }
            
            #history_list::item:selected {
                background-color: #e0e0e0;
            }
            
            #sidebar_button {
                background-color: transparent;
                color: #2d333a;
                border: 1px solid #d1d5da;
                border-radius: 6px;
                text-align: left;
                padding-left: 12px;
            }
            
            #sidebar_button:hover {
                background-color: #ececed;
            }
            
            /* 收起/展开按钮 - ChatGPT 风格描边按钮 */
            SidebarToggleButton, QToolButton#collapse_button, QToolButton#expand_button {
                background-color: transparent;
                border: none;
                padding: 0px;
            }
            
            /* 聊天区域 */
            #chat_area {
                background-color: #ffffff;
            }
            
            #header {
                background-color: #ffffff;
                border-bottom: 1px solid #e5e5e7;
            }
            
            #title_label {
                color: #2d333a;
            }
            
            #theme_button {
                background-color: transparent;
                border: none;
                border-radius: 6px;
            }
            
            #theme_button:hover {
                background-color: #f0f0f0;
            }
            
            #messages_scroll {
                background-color: #ffffff;
                border: none;
            }
            
            /* 消息气泡 */
            QFrame#message_bubble[is_user="false"] {
                background-color: #f7f7f8;
                border-radius: 12px;
                border: 1px solid #e5e5e7;
            }
            
            QFrame#message_bubble[is_user="true"] {
                background-color: #d1f4cc;
                border-radius: 12px;
                border: 1px solid #b8e6b0;
            }
            
            #role_label {
                color: #2d333a;
            }
            
            #message_content {
                color: #2d333a;
            }
            
            #typing_indicator {
                color: #10a37f;
            }
            
            /* 错误气泡 */
            #error_bubble {
                background-color: #ffebee;
                border-radius: 10px;
                border-left: 4px solid #ef4444;
            }
            
            #error_text {
                color: #c62828;
            }
            
            /* 输入区域 */
            #input_container {
                background-color: #ffffff;
                border-top: 1px solid #e5e5e7;
            }
            
            #model_label {
                color: #6e7681;
            }
            
            #model_combo {
                background-color: #f7f7f8;
                color: #2d333a;
                border: 1px solid #d1d5da;
                border-radius: 6px;
                padding: 5px 10px;
            }
            
            #model_combo::drop-down {
                border: none;
            }
            
            #model_combo QAbstractItemView {
                background-color: #ffffff;
                color: #2d333a;
                selection-background-color: #1e88e5;
                selection-color: #ffffff;
                border: 1px solid #d1d5da;
            }
            
            #input_wrapper {
                background-color: #f7f7f8;
                border: 1px solid #d1d5da;
                border-radius: 12px;
            }
            
            /* ChatGPT 风格输入容器 - 浅色主题 */
            QFrame#ChatInputBar {
                background-color: #f7f7f8;
                border: none;
                border-radius: 24px;
            }
            
            /* 输入框 - ChatGPT 风格 */
            #input_field, #input_field_chatgpt {
                background-color: transparent;
                color: #2d333a;
                border: none;
                font-size: 15px;
                padding: 6px 12px;
                selection-background-color: #1e88e5;
                selection-color: #ffffff;
            }
            
            #input_field:focus, #input_field_chatgpt:focus {
                background-color: rgba(0, 0, 0, 0.02);
            }
            
            /* 发送按钮 - ChatGPT 风格 */
            QPushButton#send_button_chatgpt {
                background-color: #2f2f2f;
                color: #ffffff;
                border: none;
                border-radius: 18px;
                padding: 0px;
                text-align: center;
                font-size: 16px;
                font-weight: bold;
            }
            
            #send_button_chatgpt:hover {
                background-color: #3f3f3f;
            }
            
            #send_button_chatgpt:pressed {
                background-color: #1f1f1f;
            }
            
            #send_button_chatgpt:disabled {
                background-color: #d1d5da;
                color: #8e8ea0;
            }
            
            /* + 按钮 - 浅色主题 */
            QPushButton#add_button {
                background-color: transparent;
                color: #6b7280;
                border: 1px solid #d1d5da;
                border-radius: 16px;
            }
            
            QPushButton#add_button:hover {
                background-color: rgba(0, 0, 0, 0.03);
                border-color: #9ca3af;
            }
            
            /* 提示文本 - 浅色主题 */
            QLabel#hint_label {
                color: rgba(0, 0, 0, 0.4);
                font-size: 13px;
            }
            
            /* 滚动条 */
            QScrollBar:vertical {
                background-color: #ffffff;
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #d1d5da;
                border-radius: 6px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #b1b5ba;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.current_api_client and self.current_api_client.isRunning():
            self.current_api_client.stop()
            self.current_api_client.wait()
        event.accept()

