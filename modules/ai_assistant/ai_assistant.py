# -*- coding: utf-8 -*-

"""
AI 助手模块主类
"""

from PyQt6.QtWidgets import QWidget
from typing import Optional

from core.logger import get_logger
from modules.ai_assistant.ui.chat_window import ChatWindow

logger = get_logger(__name__)


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
        logger.info("AIAssistantModule 初始化")
    
    def initialize(self, config_dir: str):
        """初始化模块
        
        Args:
            config_dir: 配置文件目录路径
        """
        logger.info(f"初始化 AI 助手模块，配置目录: {config_dir}")
        try:
            # AI 助手不需要持久化配置，可以跳过
            logger.info("AI 助手模块初始化完成")
        except Exception as e:
            logger.error(f"AI 助手模块初始化失败: {e}", exc_info=True)
            raise
    
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
            # 如果已经有asset_manager_logic，传递给chat_window
            if self.asset_manager_logic:
                self.chat_window.set_asset_manager_logic(self.asset_manager_logic)
            # 如果已经有config_tool_logic，传递给chat_window
            if self.config_tool_logic:
                self.chat_window.set_config_tool_logic(self.config_tool_logic)
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

