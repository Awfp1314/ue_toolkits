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
    V01_V02_AVAILABLE = True
except ImportError as e:
    logger.warning(f"v0.1/v0.2 功能不可用（缺少依赖）：{e}")
    RuntimeContextManager = None
    ToolsRegistry = None
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
        self.site_recommendations_logic = None  # 存储site_recommendations逻辑层引用
        
        # v0.1 新增：运行态上下文管理器（全局单例）
        self.runtime_context = RuntimeContextManager() if V01_V02_AVAILABLE and RuntimeContextManager else None
        
        # v0.2 新增：工具注册表（延迟初始化）
        self.tools_registry: Optional[ToolsRegistry] = None
        
        # 模型加载状态标志（供UI查询）
        self._model_loading = False
        self._model_loaded = False
        self._model_load_progress = ""  # 加载进度描述
        
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
        """异步预加载 embedding 模型（后台线程）
        
        优化策略：
        1. 立即加载最关键的语义模型（IntentEngine）
        2. 记录加载耗时
        3. 更新加载状态供UI查询
        4. 失败时优雅降级
        """
        if not V01_V02_AVAILABLE:
            logger.info("v0.1/v0.2 功能不可用，跳过模型预加载")
            self._model_loaded = True  # 标记为已完成（降级模式）
            return
        
        self._model_loading = True
        self._model_load_progress = "准备加载模型..."
        
        def preload_task():
            try:
                import os
                import time
                start_time = time.time()
                
                # 清除代理设置，直接连接（避免代理问题）
                proxy_backup = {}
                for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']:
                    if key in os.environ:
                        proxy_backup[key] = os.environ[key]
                        del os.environ[key]
                        logger.info(f"已临时清除代理设置: {key}")
                
                # 设置 HuggingFace 离线模式（优先使用本地缓存，不联网）
                os.environ["HF_HUB_OFFLINE"] = "1"
                os.environ["TRANSFORMERS_OFFLINE"] = "1"
                logger.info("已启用 HuggingFace 离线模式（使用本地缓存）")
                
                # 设置 HuggingFace 镜像（如果未设置，作为备用）
                if "HF_ENDPOINT" not in os.environ:
                    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
                    logger.info("已设置 HuggingFace 镜像: https://hf-mirror.com")
                
                logger.info("🚀 开始后台预加载 AI 模型...")
                self._model_load_progress = "正在加载语义模型..."
                
                # 1. 预加载语义模型（这是最耗时的，约 2-5 秒）
                model_start = time.time()
                from modules.ai_assistant.logic.intent_parser import IntentEngine
                temp_engine = IntentEngine(model_type="bge-small")
                temp_engine.parse("预热测试")  # 触发延迟加载
                model_elapsed = time.time() - model_start
                logger.info(f"✅ 语义模型加载完成（耗时 {model_elapsed:.1f} 秒）")
                self._model_load_progress = "语义模型加载完成，正在预热向量数据库..."
                
                # 2. 预热 FAISS 记忆系统（替代 ChromaDB，更稳定）
                try:
                    memory_start = time.time()
                    from core.ai_services import EmbeddingService
                    from modules.ai_assistant.logic.enhanced_memory_manager import EnhancedMemoryManager
                    
                    self._model_load_progress = "正在初始化 FAISS 记忆系统..."
                    embedding_service = EmbeddingService()
                    temp_memory = EnhancedMemoryManager(
                        user_id="default",
                        embedding_service=embedding_service
                    )
                    memory_elapsed = time.time() - memory_start
                    
                    if temp_memory.faiss_store:
                        logger.info(f"✅ FAISS 记忆系统初始化完成（耗时 {memory_elapsed:.1f} 秒，记忆数: {temp_memory.faiss_store.count()}）")
                    else:
                        logger.warning("⚠️ FAISS 记忆系统初始化失败（将在运行时重试）")
                except Exception as e:
                    logger.warning(f"⚠️ FAISS 记忆系统预热失败（首次对话时会自动初始化）: {e}")
                
                # 所有模型加载完成后，恢复代理设置和在线模式
                for key, value in proxy_backup.items():
                    os.environ[key] = value
                    logger.info(f"已恢复代理设置: {key}")
                
                # 恢复在线模式（但保留本地缓存优先）
                if "HF_HUB_OFFLINE" in os.environ:
                    del os.environ["HF_HUB_OFFLINE"]
                if "TRANSFORMERS_OFFLINE" in os.environ:
                    del os.environ["TRANSFORMERS_OFFLINE"]
                
                total_elapsed = time.time() - start_time
                logger.info(f"🎉 所有 AI 模型预加载完成！总耗时: {total_elapsed:.1f} 秒")
                
                # 标记加载完成
                self._model_loading = False
                self._model_loaded = True
                self._model_load_progress = f"模型加载完成（耗时 {total_elapsed:.1f} 秒，已启用 FAISS 记忆系统）"
                
            except Exception as e:
                logger.warning(f"⚠️ 预加载模型失败: {e}", exc_info=True)
                self._model_loading = False
                self._model_loaded = False
                
                # 检查是否为网络/代理问题
                error_str = str(e)
                if "proxy" in error_str.lower() or "connection" in error_str.lower() or "timeout" in error_str.lower():
                    self._model_load_progress = "⚠️ 模型下载失败（网络问题），已跳过语义分析功能"
                    # 在主线程显示提示对话框
                    try:
                        from PyQt6.QtCore import QTimer
                        from PyQt6.QtWidgets import QMessageBox
                        
                        def show_warning():
                            try:
                                msg = QMessageBox()
                                msg.setIcon(QMessageBox.Icon.Warning)
                                msg.setWindowTitle("模型加载提示")
                                msg.setText("语义模型下载失败")
                                msg.setInformativeText(
                                    "由于网络问题，AI语义分析模型无法下载。\n\n"
                                    "程序将使用基础规则匹配模式运行，功能不受影响。\n\n"
                                    "如需完整功能，请检查网络连接后重启程序。"
                                )
                                msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                                msg.exec()
                            except Exception as msg_error:
                                logger.warning(f"显示消息框失败: {msg_error}")
                        
                        # 使用QTimer在主线程中执行（延迟200ms确保主窗口已加载）
                        QTimer.singleShot(200, show_warning)
                    except Exception as dialog_error:
                        logger.warning(f"创建提示对话框失败: {dialog_error}")
                else:
                    self._model_load_progress = "模型预加载失败，首次提问时会自动加载"
        
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
            from modules.ai_assistant.logic.asset_importer import AssetImporter
            from modules.ai_assistant.logic.theme_generator import ThemeGenerator
            
            asset_reader = AssetReader(self.asset_manager_logic)
            config_reader = ConfigReader(self.config_tool_logic)
            log_analyzer = LogAnalyzer()
            document_reader = DocumentReader()
            asset_importer = AssetImporter(self.asset_manager_logic)  # 测试功能
            theme_generator = ThemeGenerator()  # 测试功能
            
            # 创建工具注册表
            self.tools_registry = ToolsRegistry(
                asset_reader=asset_reader,
                config_reader=config_reader,
                log_analyzer=log_analyzer,
                document_reader=document_reader,
                asset_importer=asset_importer,
                theme_generator=theme_generator
            )
            
            logger.info("工具系统初始化完成")
            
        except Exception as e:
            logger.error(f"初始化工具系统失败: {e}", exc_info=True)
            self.tools_registry = None
    
    def get_runtime_context(self) -> RuntimeContextManager:
        """获取运行态上下文管理器（供外部访问）
        
        Returns:
            RuntimeContextManager: 运行态上下文管理器实例
        """
        return self.runtime_context
    
    def is_model_loading(self) -> bool:
        """检查模型是否正在加载
        
        Returns:
            bool: True表示正在加载中
        """
        return self._model_loading
    
    def is_model_loaded(self) -> bool:
        """检查模型是否已加载完成
        
        Returns:
            bool: True表示已加载完成
        """
        return self._model_loaded
    
    def get_model_load_progress(self) -> str:
        """获取模型加载进度描述
        
        Returns:
            str: 进度描述文本
        """
        return self._model_load_progress
    
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
            # 如果已经有site_recommendations_logic，传递给chat_window
            if self.site_recommendations_logic:
                self.chat_window.set_site_recommendations_logic(self.site_recommendations_logic)
            
            # v0.2 新增：初始化并传递工具系统
            self._init_tools_system()
            if self.tools_registry:
                if hasattr(self.chat_window, 'set_tools_system'):
                    self.chat_window.set_tools_system(self.tools_registry)
                    logger.info("工具系统已传递给 ChatWindow")
            
            # 传递模型加载状态查询接口
            if hasattr(self.chat_window, 'set_model_status_checker'):
                self.chat_window.set_model_status_checker(self)
                logger.info("模型状态查询接口已传递给 ChatWindow")
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

