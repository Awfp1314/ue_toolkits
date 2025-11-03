# -*- coding: utf-8 -*-

"""
模块接口抽象层
定义模块与主窗口交互的标准协议
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from PyQt6.QtWidgets import QWidget
from dataclasses import dataclass


@dataclass
class ModuleMetadata:
    """模块元数据"""
    name: str
    display_name: str
    version: str
    description: str
    author: str = ""
    enabled: bool = True


class IModule(ABC):
    """模块接口
    
    定义模块必须实现的标准方法，用于与主窗口交互
    """
    
    @abstractmethod
    def get_metadata(self) -> ModuleMetadata:
        """获取模块元数据
        
        Returns:
            ModuleMetadata: 模块元数据信息
        """
        pass
    
    @abstractmethod
    def get_widget(self) -> QWidget:
        """获取模块的UI组件
        
        Returns:
            QWidget: 模块的主UI组件
        """
        pass
    
    @abstractmethod
    def initialize(self) -> bool:
        """初始化模块
        
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """清理模块资源"""
        pass
    
    def is_enabled(self) -> bool:
        """检查模块是否启用
        
        Returns:
            bool: 模块是否启用
        """
        return True
    
    def on_activated(self) -> None:
        """模块被激活时调用（用户切换到该模块）"""
        pass
    
    def on_deactivated(self) -> None:
        """模块被停用时调用（用户切换到其他模块）"""
        pass


class IModuleProvider(ABC):
    """模块提供者接口
    
    定义模块提供者必须实现的方法，用于向主窗口提供模块
    """
    
    @abstractmethod
    def get_all_modules(self) -> Dict[str, IModule]:
        """获取所有可用模块
        
        Returns:
            Dict[str, IModule]: 模块名称到模块实例的映射
        """
        pass
    
    @abstractmethod
    def get_module(self, module_name: str) -> Optional[IModule]:
        """根据名称获取模块
        
        Args:
            module_name: 模块名称
            
        Returns:
            Optional[IModule]: 模块实例，如果不存在返回None
        """
        pass
    
    @abstractmethod
    def get_module_names(self) -> List[str]:
        """获取所有模块名称列表
        
        Returns:
            List[str]: 模块名称列表
        """
        pass
    
    def reload_modules(self) -> bool:
        """重新加载所有模块
        
        Returns:
            bool: 重新加载是否成功
        """
        return True


class ModuleAdapter(IModule):
    """模块适配器
    
    将现有的模块实例适配到新的接口标准
    """
    
    def __init__(self, module_instance: Any, module_info: Any):
        """初始化适配器
        
        Args:
            module_instance: 原始模块实例
            module_info: 模块信息对象
        """
        self.instance = module_instance
        self.info = module_info
        self._widget: Optional[QWidget] = None
    
    def get_metadata(self) -> ModuleMetadata:
        """获取模块元数据"""
        return ModuleMetadata(
            name=self.info.name,
            display_name=self._get_display_name(),
            version=self.info.version,
            description=self.info.description,
            enabled=True
        )
    
    def _get_display_name(self) -> str:
        """获取模块显示名称
        
        优先使用模块信息中的 display_name 字段，
        如果不存在则使用模块名称作为回退
        """
        # 优先使用 ModuleInfo 中的 display_name
        if hasattr(self.info, 'display_name') and self.info.display_name:
            return self.info.display_name
        # 回退到模块名称
        return self.info.name
    
    def get_widget(self) -> QWidget:
        """获取模块UI组件"""
        if self._widget is None:
            # 调用原始模块的get_widget方法
            if hasattr(self.instance, 'get_widget'):
                self._widget = self.instance.get_widget()
        return self._widget
    
    def initialize(self) -> bool:
        """初始化模块"""
        # 原始模块已经在ModuleManager中初始化
        return True
    
    def cleanup(self) -> None:
        """清理模块资源"""
        if hasattr(self.instance, 'cleanup'):
            self.instance.cleanup()
    
    def is_enabled(self) -> bool:
        """检查模块是否启用"""
        return self.info.state.name == "INITIALIZED"


class ModuleProviderAdapter(IModuleProvider):
    """模块提供者适配器
    
    将ModuleManager适配到新的接口标准
    """
    
    def __init__(self, module_manager: Any):
        """初始化适配器
        
        Args:
            module_manager: 模块管理器实例
        """
        self.module_manager = module_manager
        self._module_cache: Dict[str, ModuleAdapter] = {}
    
    def get_all_modules(self) -> Dict[str, IModule]:
        """获取所有可用模块（按自定义顺序排序）"""
        modules = {}
        all_modules = self.module_manager.get_all_modules()
        
        for module_name, module_info in all_modules.items():
            # 只返回已初始化的模块
            if module_info.state.name == "INITIALIZED" and module_info.instance:
                if module_name not in self._module_cache:
                    self._module_cache[module_name] = ModuleAdapter(
                        module_info.instance,
                        module_info
                    )
                modules[module_name] = self._module_cache[module_name]
        
        # 自定义模块显示顺序
        module_order = [
            "asset_manager",      # 资产管理器
            "ai_assistant",       # AI 助手
            "config_tool",        # 配置工具
            "site_recommendations" # 网站推荐
        ]
        
        # 按照自定义顺序重新排序
        sorted_modules = {}
        
        # 首先添加在顺序列表中的模块
        for module_name in module_order:
            if module_name in modules:
                sorted_modules[module_name] = modules[module_name]
        
        # 然后添加不在顺序列表中的其他模块
        for module_name, module in modules.items():
            if module_name not in sorted_modules:
                sorted_modules[module_name] = module
        
        return sorted_modules
    
    def get_module(self, module_name: str) -> Optional[IModule]:
        """根据名称获取模块"""
        all_modules = self.get_all_modules()
        return all_modules.get(module_name)
    
    def get_module_names(self) -> List[str]:
        """获取所有模块名称列表"""
        return list(self.get_all_modules().keys())
    
    def reload_modules(self) -> bool:
        """重新加载所有模块"""
        # 清除缓存
        self._module_cache.clear()
        # 可以在这里实现重新加载逻辑
        return True

