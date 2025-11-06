"""
主窗口模块
ChatGPT 风格的主界面
"""

import os
import traceback
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
from modules.ai_assistant.ui.chat_composer import ChatGPTComposer
from modules.ai_assistant.logic.config import SYSTEM_PROMPT
from modules.ai_assistant.logic.context_manager import ContextManager


def safe_print(msg: str):
    """安全的 print 函数，避免 Windows 控制台编码错误"""
    try:
        print(msg, flush=True)
    except (OSError, UnicodeEncodeError):
        # 如果 print 失败，忽略（不要让调试输出导致程序崩溃）
        pass


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
        # 初始化对话历史，先使用默认提示词，避免初始化时加载配置阻塞
        self.conversation_history = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT  # 初始化时使用默认值
            }
        ]
        self.current_api_client = None
        self.current_streaming_bubble = None
        
        # 从全局主题管理器获取当前主题
        try:
            from core.utils.theme_manager import get_theme_manager, Theme
            theme_manager = get_theme_manager()
            current_theme = theme_manager.get_theme()
            self.current_theme = "light" if current_theme == Theme.LIGHT else "dark"
            print(f"[DEBUG] AI助手初始化，使用全局主题: {self.current_theme}")
        except Exception as e:
            print(f"[WARNING] 无法获取全局主题，使用默认深色主题: {e}")
            self.current_theme = "dark"  # 降级方案：默认深色主题
        
        # 上下文管理器（延迟初始化，需要asset_manager_logic和config_tool_logic）
        self.context_manager: Optional[ContextManager] = None
        self.asset_manager_logic = None
        self.config_tool_logic = None
        self.site_recommendations_logic = None
        self.runtime_context = None  # v0.1 新增：运行态上下文管理器
        
        # v0.2 新增：工具系统
        self.tools_registry = None
        self.action_engine = None
        
        # 模型加载状态检查器
        self.model_status_checker = None
        self._model_check_timer = None
        self._model_loading_displayed = False
        self._intent_question_sent = False  # 是否已发送询问意图的消息
        self._streaming_index = 0  # 流式输出当前索引
        self._streaming_chunks = []  # 流式输出片段列表
        
        self.init_ui()
        self.load_theme(self.current_theme)
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词（统一使用完整版）"""
        # 统一使用完整版提示词（不再区分 API 和 Ollama）
        return SYSTEM_PROMPT
    
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
    
    def set_site_recommendations_logic(self, site_recommendations_logic):
        """设置site_recommendations逻辑层引用
        
        Args:
            site_recommendations_logic: site_recommendations模块的逻辑层实例
        """
        from core.logger import get_logger
        logger = get_logger(__name__)
        
        print("[DEBUG] ===== set_site_recommendations_logic 被调用 =====")
        print(f"[DEBUG] site_recommendations_logic 类型: {type(site_recommendations_logic)}")
        
        self.site_recommendations_logic = site_recommendations_logic
        self._init_context_manager(logger)
    
    def set_runtime_context(self, runtime_context):
        """设置运行态上下文管理器（v0.1 新增）
        
        Args:
            runtime_context: RuntimeContextManager 实例
        """
        from core.logger import get_logger
        logger = get_logger(__name__)
        
        print("[DEBUG] ===== set_runtime_context 被调用 =====")
        print(f"[DEBUG] runtime_context 类型: {type(runtime_context)}")
        
        self.runtime_context = runtime_context
        self._init_context_manager(logger)
    
    def set_tools_system(self, tools_registry, action_engine):
        """设置工具系统（v0.2 新增）
        
        Args:
            tools_registry: ToolsRegistry 实例
            action_engine: ActionEngine 实例
        """
        from core.logger import get_logger
        logger = get_logger(__name__)
        
        print("[DEBUG] ===== set_tools_system 被调用 =====")
        print(f"[DEBUG] tools_registry: {tools_registry}")
        print(f"[DEBUG] action_engine: {action_engine}")
        
        self.tools_registry = tools_registry
        self.action_engine = action_engine
        logger.info("ChatWindow 工具系统已设置")
    
    def set_model_status_checker(self, ai_module):
        """设置模型加载状态检查器
        
        Args:
            ai_module: AIAssistantModule 实例，用于查询模型加载状态
        """
        from core.logger import get_logger
        from PyQt6.QtCore import QTimer
        logger = get_logger(__name__)
        
        self.model_status_checker = ai_module
        logger.info("模型状态检查器已设置")
        
        # 立即检查模型状态
        self._check_model_status()
        
        # 如果模型正在加载，启动定时器定期检查
        if ai_module.is_model_loading():
            if not self._model_check_timer:
                self._model_check_timer = QTimer(self)
                self._model_check_timer.timeout.connect(self._check_model_status)
                self._model_check_timer.start(500)  # 每500ms检查一次
                logger.info("已启动模型加载状态检查定时器")
        elif ai_module.is_model_loaded() and not self._intent_question_sent:
            # 如果模型已加载完成且未发送询问消息，延迟500ms后发送
            QTimer.singleShot(500, self._send_intent_question)
            logger.info("模型已加载，将自动发送询问意图消息")
    
    def _check_model_status(self):
        """检查模型加载状态并更新UI"""
        from core.logger import get_logger
        logger = get_logger(__name__)
        
        if not self.model_status_checker:
            return
        
        is_loading = self.model_status_checker.is_model_loading()
        is_loaded = self.model_status_checker.is_model_loaded()
        progress = self.model_status_checker.get_model_load_progress()
        
        if is_loading and not self._model_loading_displayed:
            # 首次检测到正在加载，不显示文字提示，只显示思考动画
            self._model_loading_displayed = True
            # 创建思考动画气泡（加载动画不显示重新生成按钮）
            self.add_streaming_bubble(show_regenerate=False)
            # 禁用输入框
            if hasattr(self, 'input_area') and hasattr(self.input_area, 'edit'):
                self.input_area.edit.setPlaceholderText("模型加载中，请稍候...")
                self.input_area.edit.lock()  # 锁定输入框
                self.input_area.btn_send.setEnabled(False)  # 禁用发送按钮
            logger.info(f"模型正在加载: {progress}")
        
        elif not is_loading and is_loaded and self._model_loading_displayed:
            # 加载完成，移除思考动画，直接生成AI欢迎消息
            if self.current_streaming_bubble:
                # 移除思考动画气泡
                self.current_streaming_bubble.setParent(None)
                self.current_streaming_bubble = None
            # 不在这里启用输入框！等待AI欢迎消息完成后再启用
            # 停止定时器
            if self._model_check_timer:
                self._model_check_timer.stop()
                self._model_check_timer = None
            logger.info(f"模型加载完成: {progress}")
            # 立即发送AI欢迎消息
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, self._send_intent_question)
        
        elif is_loading:
            # 更新加载进度
            self._update_loading_progress(progress)
    
    # 已移除文字提示，改为直接显示思考动画
    
    def _update_loading_progress(self, progress: str):
        """更新加载进度（可选：更新最后一条消息）"""
        # 暂时不实现动态更新，避免刷屏
        pass
    
    def _send_intent_question(self):
        """自动发送询问用户意图的消息（AI生成，每次不同）"""
        from core.logger import get_logger
        logger = get_logger(__name__)
        
        # 检查是否已发送过询问消息
        if self._intent_question_sent:
            logger.info("询问意图消息已发送过，跳过")
            return
        
        # 创建流式输出气泡（欢迎消息不显示重新生成按钮）
        self.add_streaming_bubble(show_regenerate=False)
        
        # 构建精简的欢迎消息系统提示（减少token消耗）
        base_prompt = "你是虚幻引擎资产管理工具箱的AI助手。"
        
        # 只获取最新的身份设定（使用 get_user_identity，避免重复搜索）
        identity_info = ""
        if self.context_manager and hasattr(self.context_manager, 'memory'):
            try:
                user_identity = self.context_manager.memory.get_user_identity()
                if user_identity:
                    identity_info = f"\n你的角色设定：{user_identity}"
                    logger.info(f"欢迎消息使用身份设定: {user_identity[:50]}...")
            except Exception as e:
                logger.warning(f"获取身份记忆失败: {e}")
        
        # 精简的欢迎消息生成指令
        welcome_instruction = (
            "\n\n生成一个简短的欢迎消息（100字以内）：\n"
            "1. 保持你的角色身份（如果有特殊设定）\n"
            "2. 介绍工具箱功能：管理UE资产、配置、文档\n"
            "3. 说明你可以帮助用户管理资产和解答UE问题\n"
            "4. 询问用户需要什么帮助\n"
            "5. 使用Emoji和Markdown格式\n\n"
            "直接输出欢迎消息。"
        )
        
        # 组合精简的系统提示（大幅减少token）
        full_system_prompt = base_prompt + identity_info + welcome_instruction
        
        welcome_prompt = {
            "role": "system",
            "content": full_system_prompt
        }
        
        # 构建临时的消息历史（包含完整的系统提示）
        temp_messages = [welcome_prompt, {"role": "user", "content": "请开始你的自我介绍"}]
        
        # 创建API客户端并连接信号
        from modules.ai_assistant.logic.api_client import APIClient
        
        self.current_api_client = APIClient(
            messages=temp_messages,
            model="gemini-2.5-flash",  # 使用快速模型
            temperature=0.9  # 提高温度，增加创意性和多样性
        )
        
        # 连接流式输出信号
        self.current_api_client.chunk_received.connect(self.on_chunk_received)
        
        # 连接完成信号（欢迎消息完成后的处理）
        def on_welcome_finished():
            logger.info("欢迎消息生成完成")
            if self.current_streaming_bubble:
                self.current_streaming_bubble.finish()
            self.current_streaming_bubble = None
            self.current_api_client = None
            
            # 欢迎消息完成后，解锁输入框（发送按钮状态由内容决定）
            if hasattr(self, 'input_area') and hasattr(self.input_area, 'edit'):
                self.input_area.edit.setPlaceholderText("输入消息...")
                self.input_area.edit.unlock()  # 解锁输入框
                # 根据输入框内容更新发送按钮状态（空则禁用，有内容则启用）
                self.input_area._update_send_enabled()
                self.input_field.setFocus()  # 设置焦点到输入框
                logger.info("输入框已启用，用户可以开始对话")
        
        self.current_api_client.request_finished.connect(on_welcome_finished)
        
        # 错误处理（完整版：清理UI并解锁输入框）
        def on_welcome_error(err):
            logger.error(f"欢迎消息生成失败: {err}")
            
            # 移除思考动画气泡
            if self.current_streaming_bubble:
                self.messages_layout.removeWidget(self.current_streaming_bubble)
                self.current_streaming_bubble.setParent(None)
                self.current_streaming_bubble.deleteLater()
                self.current_streaming_bubble = None
            
            # 显示错误提示
            self.add_error_bubble(f"欢迎消息生成失败：{err}\n\n请检查网络连接或 AI 配置。")
            
            # 解锁输入框，允许用户手动开始对话
            if hasattr(self, 'input_area') and hasattr(self.input_area, 'edit'):
                self.input_area.edit.setPlaceholderText("输入消息...")
                self.input_area.edit.unlock()
                self.input_area._update_send_enabled()
                self.input_field.setFocus()
                logger.info("输入框已解锁（欢迎消息失败后）")
            
            self.current_api_client = None
        
        self.current_api_client.error_occurred.connect(on_welcome_error)
        
        # 启动API调用
        self.current_api_client.start()
        
        self._intent_question_sent = True
        logger.info("已开始生成AI欢迎消息")
    
    def _init_context_manager(self, logger):
        """初始化上下文管理器（内部方法）
        
        v0.1 更新：传递 runtime_context
        Token优化：集成 MemoryCompressor
        v0.3 修复：防止重复创建导致记忆丢失
        """
        try:
            # 如果已经初始化，则跳过（防止切换模型时重复创建）
            if self.context_manager is not None:
                print("[DEBUG] [SKIP] 上下文管理器已存在，跳过重复创建（保留记忆状态）")
                return
            
            # 初始化记忆压缩器
            from modules.ai_assistant.logic.memory_compressor import MemoryCompressor
            from modules.ai_assistant.logic.api_client import APIClient
            
            def api_client_factory(messages, model="gemini-2.5-flash"):
                return APIClient(messages, model=model)
            
            memory_compressor = MemoryCompressor(
                api_client_factory=api_client_factory,
                max_history=10,  # 超过10条消息时触发压缩
                keep_recent=5,   # 压缩后保留最近5条原始消息
                compression_model="gemini-2.5-flash"
            )
            
            self.context_manager = ContextManager(
                asset_manager_logic=self.asset_manager_logic,
                config_tool_logic=self.config_tool_logic,
                site_recommendations_logic=self.site_recommendations_logic,  # 站点推荐逻辑
                runtime_context=self.runtime_context,  # v0.1 新增
                max_context_tokens=6000  # Token优化：平衡版，保留足够上下文
            )
            
            # 将压缩器注入到 EnhancedMemoryManager
            if hasattr(self.context_manager, 'memory'):
                self.context_manager.memory.memory_compressor = memory_compressor
                print("[DEBUG] [OK] 记忆压缩器已注入到 EnhancedMemoryManager")
            
            print("[DEBUG] [OK] ChatWindow 上下文管理器已成功初始化（包含运行态上下文 + Token优化）")
            logger.info("ChatWindow上下文管理器已初始化（包含运行态上下文 + Token优化）")
        except Exception as e:
            print(f"[DEBUG] [ERROR] 初始化上下文管理器失败: {e}")
            logger.error(f"初始化上下文管理器失败: {e}", exc_info=True)
            self.context_manager = None
            import traceback
            safe_print(traceback.format_exc())
    
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
        
        # 移除自动发送欢迎消息（用户反馈不需要）
        # from PyQt6.QtCore import QTimer
        # QTimer.singleShot(500, self.send_auto_greeting)
    
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
        # 使用新的 ChatGPTComposer 组件
        self.input_area = ChatGPTComposer(attachments_enabled=True)
        self.input_area.submitted.connect(self.on_message_sent)
        self.input_area.submitted_detail.connect(self.on_message_with_images_sent)
        self.input_area.stop_requested.connect(self.stop_generation)
        
        # 监听输入框高度变化，触发重新定位（保持底部固定，向上增长）
        self.input_area.height_changed.connect(
            lambda: self.position_input_area(self.chat_widget)
        )
        
        # 保持兼容性
        self.input_field = self.input_area.edit
        self.send_button = self.input_area.btn_send
        
        # 刷新主题
        self.input_area.refresh_theme(self.current_theme)
        
        # 初始状态为锁定（等待模型加载完成 + AI欢迎消息完成）
        self.input_field.lock()
        self.input_field.setPlaceholderText("模型加载中，请稍候...")
        self.send_button.setEnabled(False)
        
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
    
    def add_message(self, message, is_user=False, is_system=False):
        """添加 Markdown 消息
        
        Args:
            message: 消息内容
            is_user: 是否为用户消息
            is_system: 是否为系统消息（加载提示等）
        """
        if is_system:
            role = "system"
        else:
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
            safe_print(f"[ERROR] 自动发送问候消息时出错: {e}")
            import traceback
            safe_print(traceback.format_exc())
    
    def add_streaming_bubble(self, show_regenerate=True):
        """添加流式输出 Markdown 消息
        
        Args:
            show_regenerate: 是否显示重新生成按钮（默认True，欢迎消息设为False）
        """
        self.current_streaming_bubble = StreamingMarkdownMessage(
            theme=self.current_theme, 
            show_regenerate=show_regenerate
        )
        # 只在显示重新生成按钮时才连接信号
        if show_regenerate:
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
        # 使用 QTimer 确保在控件渲染完成后滚动
        # 立即滚动一次
        QTimer.singleShot(0, self._do_scroll)
        # 再次滚动以确保布局更新后的位置正确
        QTimer.singleShot(50, self._do_scroll)
        QTimer.singleShot(100, self._do_scroll)
    
    def _do_scroll(self):
        """执行滚动"""
        try:
            scrollbar = self.scroll_area.verticalScrollBar()
            # 强制滚动到最底部
            scrollbar.setValue(scrollbar.maximum())
        except:
            pass
    
    def send_message(self):
        """发送消息"""
        try:
            message = self.input_field.toPlainText().strip()
            
            if not message:
                return
            
            safe_print("[DEBUG] 准备发送消息...")
            safe_print(f"[DEBUG] 上下文管理器状态: {self.context_manager is not None}")
            
            # 保存消息并清空输入框（切换为暂停按钮）
            self.input_area.save_and_clear_message()
            
            # 锁定输入框（阻止用户编辑，但不影响按钮事件）
            self.input_field.lock()
            
            # 添加用户消息
            self.add_message(message, is_user=True)
            
            # Token优化：检查并压缩历史对话
            if self.context_manager and hasattr(self.context_manager, 'memory'):
                try:
                    compressed = self.context_manager.memory.compress_old_context(self.conversation_history)
                    if compressed:
                        print(f"[DEBUG] [Token优化] 对话历史已压缩，当前历史长度: {len(self.conversation_history)}")
                except Exception as e:
                    print(f"[WARNING] 压缩历史失败: {e}")
            
            # 添加用户消息到历史（不拼接上下文）
            self.conversation_history.append({
                "role": "user",
                "content": message  # 只包含用户原始消息
            })
            
            # 构建上下文（如果上下文管理器已初始化）
            context_message = None
            if self.context_manager:
                try:
                    print("[DEBUG] 正在构建上下文...")
                    # 只构建领域上下文，不包含系统提示词（系统提示词只在第一次发送）
                    context = self.context_manager.build_context(message, include_system_prompt=False)
                    if context:
                        # 将上下文作为单独的system消息发送（不累积到历史）
                        context_message = {
                            "role": "system",
                            "content": f"[当前查询的上下文信息]\n{context}"
                        }
                        print(f"[DEBUG] [OK] 已构建上下文信息，上下文长度: {len(context)} 字符")
                        try:
                            print(f"[DEBUG] 上下文预览:\n{context[:500]}...")
                        except UnicodeEncodeError:
                            # Windows终端编码问题
                            safe_preview = context[:500].encode('gbk', errors='ignore').decode('gbk')
                            print(f"[DEBUG] 上下文预览:\n{safe_preview}...")
                    else:
                        print("[DEBUG] [WARN] 上下文管理器返回空内容（可能是简单问候）")
                except Exception as e:
                    print(f"[WARNING] [ERROR] 构建上下文失败: {e}")
                    import traceback
                    safe_print(traceback.format_exc())
            else:
                print("[DEBUG] [WARN] 上下文管理器未初始化！AI 无法访问资产/文档/日志数据")
            
            # 添加流式输出气泡
            self.add_streaming_bubble()
            
            # 构建本次请求的消息列表（不影响历史记录）
            request_messages = []
            
            # 1. 添加系统提示词（包含身份信息）
            # 每次对话都重新构建系统提示词，确保包含最新的身份设定
            # 根据 LLM 供应商选择合适的提示词
            system_prompt = self._get_system_prompt()
            if self.context_manager and hasattr(self.context_manager, 'memory'):
                user_identity = self.context_manager.memory.get_user_identity()
                print(f"[DEBUG] [身份检查] get_user_identity() 返回: '{user_identity}'")
                if user_identity:
                    # 将身份融入系统提示词
                    system_prompt = f"""{SYSTEM_PROMPT}

## 🎭 特殊角色设定
{user_identity}

⚠️ 重要：请始终保持这个身份设定，在每次回答中都要展现这个角色特征。"""
                    print(f"[DEBUG] [身份设定] 已融入系统提示词: {user_identity[:50]}...")
                else:
                    print(f"[WARNING] [身份设定] get_user_identity() 返回空值，未添加身份设定")
            
            # 创建系统消息
            system_msg = {
                "role": "system",
                "content": system_prompt
            }
            
            # 添加到请求消息
            request_messages.append(system_msg)
            
            # 检查并更新历史记录中的系统提示词
            has_system_in_history = (
                len(self.conversation_history) > 0 and 
                self.conversation_history[0].get("role") == "system"
            )
            
            if has_system_in_history:
                # 更新历史中的系统提示词（确保包含最新身份设定）
                self.conversation_history[0] = system_msg
                print(f"[DEBUG] [系统提示词] 已更新历史中的系统提示词")
            else:
                # 添加到历史记录的开头
                if len(self.conversation_history) > 0:
                    self.conversation_history.insert(0, system_msg)
                else:
                    self.conversation_history.append(system_msg)
                print(f"[DEBUG] [系统提示词] 已创建并保存系统提示词到历史")
            
            # 2. 添加历史对话（已压缩，跳过系统提示词因为已经添加了）
            for msg in self.conversation_history:
                if msg.get("role") != "system":  # 跳过系统提示词，避免重复
                    request_messages.append(msg)
            
            # 3. 如果有上下文信息，插入到最后一条用户消息之前
            if context_message:
                request_messages.insert(-1, context_message)  # 插入到用户消息之前
                print(f"[DEBUG] [Token优化] 上下文作为临时system消息发送，不保存到历史")
            
            print(f"[DEBUG] [Token统计] 本次请求消息数: {len(request_messages)}")
            
            # 调试：显示完整的消息结构（用于诊断记忆问题）
            try:
                print("[DEBUG] [消息结构] 发送给API的完整消息:")
                for i, msg in enumerate(request_messages):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    content_preview = content[:150].replace('\n', ' ') if len(content) > 150 else content.replace('\n', ' ')
                    try:
                        print(f"  [{i}] {role}: {content_preview}...")
                    except UnicodeEncodeError:
                        # Windows终端GBK编码问题，移除emoji后重试
                        safe_content = content_preview.encode('gbk', errors='ignore').decode('gbk')
                        print(f"  [{i}] {role}: {safe_content}...")
            except Exception as e:
                print(f"[DEBUG] 无法显示消息结构（编码问题）: {e}")
            
            # 启动 API 请求
            model = self.input_area.get_selected_model()
            print(f"[DEBUG] 使用模型: {model}")
            self.current_api_client = APIClient(
                request_messages,  # 使用临时构建的消息列表
                model=model
            )
            self.current_api_client.chunk_received.connect(self.on_chunk_received)
            self.current_api_client.request_finished.connect(self.on_request_finished)
            self.current_api_client.error_occurred.connect(self.on_error_occurred)
            print(f"[DEBUG] 启动 API 请求...")
            self.current_api_client.start()
        except Exception as e:
            safe_print(f"[ERROR] 发送消息时出错: {e}")
            import traceback
            safe_print(traceback.format_exc())
            # 恢复输入框状态
            self.input_field.unlock()
            self.input_area.set_generating(False)
    
    def send_message_with_images(self, message, images):
        """发送带图片的消息"""
        try:
            safe_print(f"[DEBUG] 准备发送消息（图片数量: {len(images)}）")
            
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
            model = "gemini-2.5-flash"  # Gemini 2.5 Flash 支持图片
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
            safe_print(f"[ERROR] 发送消息时出错: {e}")
            import traceback
            safe_print(traceback.format_exc())
            # 恢复输入框状态
            self.input_field.unlock()
            self.input_area.set_generating(False)
    
    def on_chunk_received(self, chunk):
        """接收流式数据"""
        try:
            # 使用 repr 避免 Unicode 编码错误
            try:
                print(f"[STREAM] 收到数据块: {chunk[:20]}... (长度: {len(chunk)})")
            except UnicodeEncodeError:
                pass  # 忽略 print 的编码错误
            
            if self.current_streaming_bubble:
                print(f"[STREAM] 正在追加到流式气泡...")
                self.current_streaming_bubble.append_text(chunk)
                self.scroll_to_bottom()
            else:
                print(f"[WARNING] 流式气泡为空，无法追加文本！")
        except Exception as e:
            try:
                safe_print(f"[ERROR] 处理数据块时出错: {e}")
            except UnicodeEncodeError:
                pass
            import traceback
            safe_print(traceback.format_exc())
    
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
                    safe_print("[DEBUG] 助手消息已接收")
                except UnicodeEncodeError:
                    pass
                if assistant_message:
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": assistant_message
                    })
                    
                    # 保存对话到记忆（如果上下文管理器可用）
                    if self.context_manager and hasattr(self.context_manager, 'memory'):
                        # 获取最后一条用户消息（确保是纯净的用户消息，不包含上下文）
                        user_message = ""
                        for msg in reversed(self.conversation_history):
                            if msg.get("role") == "user":
                                content = msg.get("content", "")
                                # 处理多模态消息（list 类型）
                                if isinstance(content, list):
                                    # 提取文本部分
                                    text_parts = []
                                    for item in content:
                                        if isinstance(item, dict) and item.get("type") == "text":
                                            text_parts.append(item.get("text", ""))
                                    user_message = " ".join(text_parts)
                                else:
                                    user_message = content
                                # 确保不包含上下文信息（只保存用户原始输入）
                                if isinstance(user_message, str) and "[当前查询的上下文信息]" in user_message:
                                    # 如果包含上下文，提取用户原始消息
                                    user_message = user_message.split("[当前查询的上下文信息]")[0].strip()
                                break
                        
                        if user_message:
                            # 保存到增强型记忆管理器
                            from modules.ai_assistant.logic.enhanced_memory_manager import MemoryLevel
                            
                            try:
                                # 保存用户查询和 AI 回复为一轮对话
                                self.context_manager.memory.add_dialogue(user_message, assistant_message)
                                try:
                                    safe_print("[DEBUG] [记忆保存] 对话已保存")
                                except UnicodeEncodeError:
                                    print(f"[DEBUG] [记忆保存] 用户消息和助手回复已保存（包含特殊字符）")
                                
                                # 同时提取关键信息保存到持久化记忆（如果重要）
                                # 扩展关键词列表，包含"猫娘"等身份相关词汇
                                if any(keyword in user_message for keyword in ['喜欢', '常用', '偏好', '习惯', '猫娘', '我是', '叫我']):
                                    self.context_manager.memory.add_memory(
                                        content=f"用户相关信息: {user_message}",
                                        level=MemoryLevel.USER,
                                        metadata={'type': 'user_info', 'source': 'conversation'},
                                        auto_evaluate=True
                                    )
                                    print(f"[DEBUG] [持久化记忆] 保存重要信息到用户级记忆")
                                
                                print(f"[DEBUG] [OK] 已保存对话到记忆系统")
                            except Exception as e:
                                safe_print(f"[ERROR] 保存记忆失败: {e}")
                                import traceback
                                safe_print(traceback.format_exc())
            
            # 解锁输入框
            print("[DEBUG] 开始解锁输入框...")
            self.input_field.unlock()
            # 恢复发送按钮状态（从暂停切换回发送）
            print("[DEBUG] 调用 set_generating(False)...")
            self.input_area.set_generating(False)
            print("[DEBUG] 输入框已解锁，按钮状态已恢复")
            self.input_field.setFocus()
            
            # 清理
            self.current_api_client = None
            self.current_streaming_bubble = None
        except Exception as e:
            safe_print(f"[ERROR] 请求完成处理时出错: {e}")
            import traceback
            safe_print(traceback.format_exc())
            # 确保即使异常也要解锁输入框
            try:
                self.input_field.unlock()
                self.input_area.set_generating(False)
            except:
                pass
    
    def on_error_occurred(self, error_message):
        """处理错误（显示思考动画，然后显示错误消息）"""
        try:
            safe_print(f"[ERROR] API错误: {error_message}")
            
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
            safe_print(f"[ERROR] 错误处理时出错: {e}")
            import traceback
            safe_print(traceback.format_exc())
    
    def _enable_input_after_error(self):
        """重新启用输入（错误显示后）"""
        self.input_field.unlock()
        # 恢复发送按钮状态（从暂停切换回发送）
        self.input_area.set_generating(False)
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
            self.input_area.set_generating(False)  # 恢复发送按钮状态
            self.input_area.restore_message()
            self.input_field.setFocus()
            
            print("[DEBUG] 生成已停止，消息已恢复")
        except Exception as e:
            safe_print(f"[ERROR] 停止生成时出错: {e}")
            import traceback
            safe_print(traceback.format_exc())
            # 确保恢复正常状态
            self.input_field.unlock()
            self.input_area.set_generating(False)
    
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
                    from modules.ai_assistant.ui.markdown_message import StreamingMarkdownMessage, MarkdownMessage
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
            
            # 🔧 修复：重新构建上下文（包含记忆）
            # 获取最后一条用户消息
            last_user_message = None
            for msg in reversed(self.conversation_history):
                if msg.get("role") == "user":
                    last_user_message = msg.get("content", "")
                    break
            
            # 构建请求消息列表
            request_messages = []
            context_message = None
            
            # 如果找到用户消息且上下文管理器存在，重新构建上下文
            if last_user_message and self.context_manager:
                try:
                    print(f"[DEBUG] [重新生成] 正在为用户消息构建上下文...")
                    context = self.context_manager.build_context(last_user_message, include_system_prompt=False)
                    if context:
                        context_message = {
                            "role": "system",
                            "content": f"[当前查询的上下文信息]\n{context}"
                        }
                        print(f"[DEBUG] [重新生成] 已构建上下文（长度: {len(context)}）")
                except Exception as e:
                    print(f"[WARNING] [重新生成] 构建上下文失败: {e}")
            
            # 复制历史记录
            for msg in self.conversation_history:
                request_messages.append(msg)
            
            # 如果有上下文，插入到最后一条用户消息之前
            if context_message:
                # 找到最后一条用户消息的位置
                last_user_idx = -1
                for i in range(len(request_messages) - 1, -1, -1):
                    if request_messages[i].get("role") == "user":
                        last_user_idx = i
                        break
                
                if last_user_idx >= 0:
                    request_messages.insert(last_user_idx, context_message)
                    print(f"[DEBUG] [重新生成] 已插入上下文到消息列表（位置: {last_user_idx}）")
            
            # 重新发起 API 请求（使用包含上下文的消息列表）
            model = self.input_area.get_selected_model()
            print(f"[DEBUG] 使用模型: {model}，消息数: {len(request_messages)}")
            self.current_api_client = APIClient(
                request_messages,  # 使用包含上下文的请求消息
                model=model
            )
            self.current_api_client.chunk_received.connect(self.on_chunk_received)
            self.current_api_client.request_finished.connect(self.on_request_finished)
            self.current_api_client.error_occurred.connect(self.on_error_occurred)
            print(f"[DEBUG] 重新启动 API 请求...")
            self.current_api_client.start()
        except Exception as e:
            safe_print(f"[ERROR] 重新生成回答时出错: {e}")
            import traceback
            safe_print(traceback.format_exc())
    
    def clear_chat(self):
        """清空当前对话"""
        # 清空对话历史，并重新添加系统提示词（根据供应商选择）
        self.conversation_history.clear()
        self.conversation_history.append({
            "role": "system",
            "content": self._get_system_prompt()
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
    
    def refresh_theme(self):
        """刷新主题（响应主题切换）"""
        try:
            from core.utils.theme_manager import get_theme_manager, Theme
            theme_manager = get_theme_manager()
            current_theme = theme_manager.get_theme()
            
            # 根据主题管理器的主题切换
            if current_theme == Theme.LIGHT:
                self.current_theme = "light"
            else:
                self.current_theme = "dark"
            
            # 加载主题样式
            self.load_theme(self.current_theme)
            
            # 更新所有已存在消息的主题（重新生成图标）
            if hasattr(self, 'messages_layout') and self.messages_layout:
                from .markdown_message import MarkdownMessage, StreamingMarkdownMessage
                for i in range(self.messages_layout.count()):
                    widget = self.messages_layout.itemAt(i).widget()
                    if widget and isinstance(widget, (MarkdownMessage, StreamingMarkdownMessage)):
                        widget.set_theme(self.current_theme)
            
            # 更新输入框组件的主题
            if hasattr(self, 'input_area') and self.input_area:
                self.input_area.refresh_theme(self.current_theme)
            
            print(f"[DEBUG] AI助手主题已刷新: {self.current_theme}，已更新 {self.messages_layout.count() if hasattr(self, 'messages_layout') else 0} 条消息")
        except Exception as e:
            safe_print(f"[ERROR] 刷新AI助手主题失败: {e}")
            import traceback
            safe_print(traceback.format_exc())
    
    def load_theme(self, theme_name):
        """加载主题样式 + 组件样式"""
        from pathlib import Path
        
        # 获取模块资源目录
        module_dir = Path(__file__).parent.parent
        theme_file = module_dir / "resources" / "themes" / f"{theme_name}.qss"
        
        # 加载主主题样式
        if theme_file.exists():
            with open(theme_file, "r", encoding="utf-8") as f:
                main_stylesheet = f.read()
            # 调试：检查是否读取到了正确的背景色
            if "chat_area" in main_stylesheet:
                import re
                chat_area_match = re.search(r'(?:QWidget)?#chat_area\s*\{[^}]*background-color:\s*([^;]+)', main_stylesheet)
                if chat_area_match:
                    print(f"[DEBUG] 从 {theme_file.name} 读取到 chat_area 背景色: {chat_area_match.group(1).strip()}")
        else:
            # 如果文件不存在，使用内置样式
            if theme_name == "dark":
                main_stylesheet = self.get_dark_theme()
            else:
                main_stylesheet = self.get_light_theme()
        
        # 加载所有组件样式（从 resources/qss/components/ 目录）
        workspace_root = Path(__file__).parent.parent.parent.parent  # 回到工作空间根目录
        components_dir = workspace_root / "resources" / "qss" / "components"
        
        component_stylesheets = []
        if components_dir.exists():
            # 遍历所有 .qss 文件
            for qss_file in sorted(components_dir.glob("*.qss")):
                try:
                    with open(qss_file, "r", encoding="utf-8") as f:
                        component_stylesheets.append(f.read())
                        print(f"[DEBUG] 已加载组件样式: {qss_file.name}")
                except Exception as e:
                    safe_print(f"[ERROR] 加载组件样式失败 {qss_file.name}: {e}")
        else:
            print(f"[WARNING] 组件样式目录不存在: {components_dir}")
        
        # 合并主题样式 + 所有组件样式
        full_stylesheet = main_stylesheet + "\n" + "\n".join(component_stylesheets)
        self.setStyleSheet(full_stylesheet)
    
    def get_dark_theme(self):
        """获取深色主题（已迁移到 resources/themes/dark.qss）"""
        # 主题已迁移到独立的 QSS 文件，此方法保留用于降级
        print("[WARNING] get_dark_theme() 已废弃，主题应从 resources/themes/dark.qss 加载")
        return ""
    
    def get_light_theme(self):
        """获取浅色主题（已迁移到 resources/themes/light.qss）"""
        # 主题已迁移到独立的 QSS 文件，此方法保留用于降级
        print("[WARNING] get_light_theme() 已废弃，主题应从 resources/themes/light.qss 加载")
        return ""
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.current_api_client and self.current_api_client.isRunning():
            self.current_api_client.stop()
            self.current_api_client.wait()
        event.accept()

