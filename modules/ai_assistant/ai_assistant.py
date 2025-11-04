# -*- coding: utf-8 -*-

"""
AI 助手模块主类
"""

from PyQt6.QtWidgets import QWidget
from typing import Optional
import threading

from core.logger import get_logger
from modules.ai_assistant.ui.chat_window import ChatWindow

logger = get_logger(__name__)

# v0.1/v0.2 新增：延迟导入，避免启动时加载重量级库
try:
    from modules.ai_assistant.logic.runtime_context import RuntimeContextManager
    from modules.ai_assistant.logic.tools_registry import ToolsRegistry
    from modules.ai_assistant.logic.action_engine import ActionEngine
    V01_V02_AVAILABLE = True
except ImportError as e:
    logger.warning(f"v0.1/v0.2 功能不可用（缺少依赖）：{e}")
    RuntimeContextManager = None
    ToolsRegistry = None
    ActionEngine = None
    V01_V02_AVAILABLE = False


class AIAssistantModule:
    """AI 助手模块主类"""
    
    def __init__(self, parent=None):
        """初始化模块
        
        Args:
            parent: 父组件（可选）
        """
        self.parent = parent
        self.chat_window: Optional[ChatWindow] = None
        self.asset_manager_logic = None  # 存储asset_manager逻辑层引用
        self.config_tool_logic = None  # 存储config_tool逻辑层引用
        
        # v0.1 新增：运行态上下文管理器（全局单例）
        self.runtime_context = RuntimeContextManager() if V01_V02_AVAILABLE and RuntimeContextManager else None
        
        # v0.2 新增：工具注册表和动作引擎（延迟初始化）
        self.tools_registry: Optional[ToolsRegistry] = None
        self.action_engine: Optional[ActionEngine] = None
        
        status = "（包含运行态上下文 + 工具系统）" if V01_V02_AVAILABLE else "（v0.1/v0.2 功能不可用）"
        logger.info(f"AIAssistantModule 初始化{status}")
    
    def initialize(self, config_dir: str):
        """初始化模块
        
        Args:
            config_dir: 配置文件目录路径
        """
        logger.info(f"初始化 AI 助手模块，配置目录: {config_dir}")
        try:
            # AI 助手不需要持久化配置，可以跳过
            
            # v0.1 新增：异步预加载 embedding 模型（避免首次调用卡顿）
            self._preload_embedding_model_async()
            
            logger.info("AI 助手模块初始化完成")
        except Exception as e:
            logger.error(f"AI 助手模块初始化失败: {e}", exc_info=True)
            raise
    
    def _preload_embedding_model_async(self):
        """异步预加载 embedding 模型（后台线程）"""
        if not V01_V02_AVAILABLE:
            logger.info("v0.1/v0.2 功能不可用，跳过模型预加载")
            return
        
        def preload_task():
            try:
                logger.info("开始异步预加载 embedding 模型...")
                from modules.ai_assistant.logic.intent_parser import IntentEngine
                
                # 创建临时引擎并触发模型加载
                temp_engine = IntentEngine(model_type="bge-small")
                temp_engine.parse("测试")  # 触发延迟加载
                
                logger.info("Embedding 模型预加载完成")
            except Exception as e:
                logger.warning(f"预加载模型失败（不影响功能）: {e}")
        
        # 在后台线程运行
        thread = threading.Thread(target=preload_task, daemon=True, name="EmbeddingPreload")
        thread.start()
    
    def _init_tools_system(self):
        """
        v0.2 新增：初始化工具系统
        
        在创建 ChatWindow 时调用，确保有完整的数据读取器可用
        """
        try:
            # 只在有数据读取器时才初始化工具系统
            if not self.asset_manager_logic and not self.config_tool_logic:
                logger.warning("数据读取器未初始化，工具系统延迟创建")
                return
            
            # 需要从 ChatWindow 的 context_manager 获取 readers
            # 或者直接在这里创建（更简单）
            from modules.ai_assistant.logic.asset_reader import AssetReader
            from modules.ai_assistant.logic.config_reader import ConfigReader
            from modules.ai_assistant.logic.log_analyzer import LogAnalyzer
            from modules.ai_assistant.logic.document_reader import DocumentReader
            
            asset_reader = AssetReader(self.asset_manager_logic)
            config_reader = ConfigReader(self.config_tool_logic)
            log_analyzer = LogAnalyzer()
            document_reader = DocumentReader()
            
            # 创建工具注册表
            self.tools_registry = ToolsRegistry(
                asset_reader=asset_reader,
                config_reader=config_reader,
                log_analyzer=log_analyzer,
                document_reader=document_reader
            )
            
            # 创建动作引擎
            from modules.ai_assistant.logic.api_client import APIClient
            
            def api_client_factory(messages, model="gpt-3.5-turbo"):
                return APIClient(messages, model=model)
            
            self.action_engine = ActionEngine(
                tools_registry=self.tools_registry,
                api_client_factory=api_client_factory
            )
            
            logger.info("工具系统初始化完成")
            
        except Exception as e:
            logger.error(f"初始化工具系统失败: {e}", exc_info=True)
            self.tools_registry = None
            self.action_engine = None
    
    def get_runtime_context(self) -> RuntimeContextManager:
        """获取运行态上下文管理器（供外部访问）
        
        Returns:
            RuntimeContextManager: 运行态上下文管理器实例
        """
        return self.runtime_context
    
    def get_widget(self) -> QWidget:
        """获取模块的UI组件
        
        Returns:
            QWidget: 模块的主UI组件
        """
        logger.info("获取 AI 助手 UI 组件")
        
        if self.chat_window is None:
            logger.info("创建新的 AI 助手窗口实例")
            # 创建聊天窗口但不作为主窗口
            self.chat_window = ChatWindow(as_module=True)
            
            # v0.1 新增：传递运行态上下文管理器
            if hasattr(self.chat_window, 'set_runtime_context'):
                self.chat_window.set_runtime_context(self.runtime_context)
            
            # 如果已经有asset_manager_logic，传递给chat_window
            if self.asset_manager_logic:
                self.chat_window.set_asset_manager_logic(self.asset_manager_logic)
            # 如果已经有config_tool_logic，传递给chat_window
            if self.config_tool_logic:
                self.chat_window.set_config_tool_logic(self.config_tool_logic)
            
            # v0.2 新增：初始化并传递工具系统
            self._init_tools_system()
            if self.tools_registry and self.action_engine:
                if hasattr(self.chat_window, 'set_tools_system'):
                    self.chat_window.set_tools_system(self.tools_registry, self.action_engine)
                    logger.info("工具系统已传递给 ChatWindow")
        else:
            logger.info("返回已存在的 AI 助手窗口实例")
        
        return self.chat_window
    
    def set_asset_manager_logic(self, asset_manager_logic):
        """设置asset_manager逻辑层引用
        
        Args:
            asset_manager_logic: asset_manager模块的逻辑层实例
        """
        self.asset_manager_logic = asset_manager_logic
        logger.info("AI助手模块已接收asset_manager逻辑层引用")
        
        # 如果chat_window已经创建，更新它的上下文管理器
        if self.chat_window and hasattr(self.chat_window, 'set_asset_manager_logic'):
            self.chat_window.set_asset_manager_logic(asset_manager_logic)
    
    def set_config_tool_logic(self, config_tool_logic):
        """设置config_tool逻辑层引用
        
        Args:
            config_tool_logic: config_tool模块的逻辑层实例
        """
        self.config_tool_logic = config_tool_logic
        logger.info("AI助手模块已接收config_tool逻辑层引用")
        
        # 如果chat_window已经创建，更新它的上下文管理器
        if self.chat_window and hasattr(self.chat_window, 'set_config_tool_logic'):
            self.chat_window.set_config_tool_logic(config_tool_logic)
    
    def cleanup(self):
        """清理资源"""
        logger.info("清理 AI 助手模块资源")
        try:
            if self.chat_window:
                # 停止当前的 API 请求
                if hasattr(self.chat_window, 'current_api_client') and self.chat_window.current_api_client:
                    self.chat_window.current_api_client.stop()
                self.chat_window = None
            
            logger.info("AI 助手模块资源清理完成")
        except Exception as e:
            logger.error(f"清理模块资源时发生错误: {e}", exc_info=True)

