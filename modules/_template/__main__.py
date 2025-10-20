# -*- coding: utf-8 -*-

"""
模块主入口文件
定义模块的生命周期和接口
"""

from PyQt6.QtWidgets import QWidget
from typing import Optional

# 使用统一的日志系统
from core.logger import get_logger

from modules.module_name.logic.module_logic import ModuleLogic
from modules.module_name.ui.module_ui import ModuleUI

logger = get_logger(__name__)


class ModuleNameModule:
    """模块主类
    
    这是模块的入口类，负责：
    1. 模块生命周期管理（初始化、启动、停止、清理）
    2. UI和逻辑层的协调
    3. 与主程序的接口
    """
    
    def __init__(self, parent=None):
        """初始化模块
        
        Args:
            parent: 父组件（可选）
        """
        self.parent = parent
        self.ui: Optional[ModuleUI] = None  # UI层，延迟初始化
        self.logic: Optional[ModuleLogic] = None  # 逻辑层
        logger.info("ModuleNameModule 初始化")
    
    def initialize(self, config_dir: str):
        """初始化模块
        
        在模块加载后调用，用于初始化业务逻辑层
        
        Args:
            config_dir: 配置文件目录路径
        """
        logger.info(f"初始化模块，配置目录: {config_dir}")
        try:
            self.logic = ModuleLogic(config_dir)
            logger.info("模块初始化完成")
        except Exception as e:
            logger.error(f"模块初始化失败: {e}", exc_info=True)
            raise
    
    def get_widget(self) -> QWidget:
        """获取模块的UI组件
        
        返回模块的主UI组件，用于显示在主窗口中
        延迟初始化UI，确保只创建一次
        
        Returns:
            QWidget: 模块的主UI组件
        """
        logger.info("获取模块UI组件")
        
        if self.ui is None:
            logger.info("创建新的UI实例")
            self.ui = ModuleUI()
            
            # 连接UI和逻辑层
            if self.logic:
                self.ui.set_logic(self.logic)
            
            # 设置信号连接
            self._setup_connections()
            
            self._initialize_ui_data()
        else:
            logger.info("返回已存在的UI实例")
        
        return self.ui
    
    def _setup_connections(self):
        """设置信号槽连接
        
        连接UI层的信号到对应的处理函数
        """
        if not self.ui:
            return
        
        # 在这里连接UI信号
        # 示例：
        # self.ui.some_button.clicked.connect(self.on_button_clicked)
        
        logger.info("信号槽连接设置完成")
    
    def _initialize_ui_data(self):
        """初始化UI数据
        
        从逻辑层加载数据并更新UI显示
        """
        if not self.ui or not self.logic:
            return
        
        # 在这里初始化UI数据
        # 示例：
        # data = self.logic.get_data()
        # self.ui.update_display(data)
        
        logger.info("UI数据初始化完成")
    
    def cleanup(self):
        """清理资源
        
        在模块卸载前调用，用于保存数据和释放资源
        """
        logger.info("清理模块资源")
        try:
            if self.logic:
                self.logic.save_config()
            
            if self.ui:
                self.ui = None
            
            logger.info("模块资源清理完成")
        except Exception as e:
            logger.error(f"清理模块资源时发生错误: {e}", exc_info=True)


