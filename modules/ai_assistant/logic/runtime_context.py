# -*- coding: utf-8 -*-

"""
运行态上下文管理器
负责维护和持久化程序运行时的状态信息
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from core.logger import get_logger

logger = get_logger(__name__)


class RuntimeContextManager:
    """
    运行态上下文管理器
    
    特性：
    - 持久化：状态自动保存到 user_data_dir/runtime_context.json
    - 自动恢复：启动时从缓存文件恢复上次状态
    - 异常安全：读取失败时返回默认值，不抛出异常
    - 独立运行：无外部依赖，可独立加载
    """
    
    # 模块名称映射（技术名称 -> 中文名称）
    MODULE_NAME_MAP = {
        'asset_manager': '资产管理器',
        'config_tool': '配置工具',
        'ai_assistant': 'AI助手',
        'document_viewer': '文档查看器',
        'log_analyzer': '日志分析器'
    }
    
    def __init__(self, user_data_dir: Optional[Path] = None):
        """
        初始化运行态上下文管理器
        
        Args:
            user_data_dir: 用户数据目录（由 PathUtils.get_user_data_dir() 提供）
        """
        self.logger = logger
        
        # 状态数据
        self.current_module: Optional[str] = None
        self.selected_asset: Optional[Dict[str, Any]] = None
        self.selected_config: Optional[Dict[str, Any]] = None
        self.recent_ops: List[Dict[str, Any]] = []
        self.last_error: Optional[Dict[str, Any]] = None
        
        # 缓存文件路径
        if user_data_dir is None:
            # 尝试获取用户数据目录
            try:
                from core.utils.path_utils import PathUtils
                path_utils = PathUtils()
                self.cache_file = path_utils.get_user_data_dir() / "runtime_context.json"
            except Exception as e:
                # 降级到临时目录
                self.logger.warning(f"无法获取用户数据目录，使用临时路径: {e}")
                self.cache_file = Path.home() / ".ue_toolkit" / "runtime_context.json"
        else:
            self.cache_file = user_data_dir / "runtime_context.json"
        
        # 确保目录存在
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.error(f"创建缓存目录失败: {e}")
        
        # 启动时自动恢复上次状态
        self._load_from_cache()
        
        self.logger.info(f"运行态上下文管理器初始化完成（缓存路径: {self.cache_file}）")
    
    def snapshot(self) -> Dict[str, Any]:
        """
        获取当前运行态快照
        
        Returns:
            Dict: 包含所有状态信息的字典
        """
        return {
            'current_module': self.current_module,
            'selected_asset': self.selected_asset,
            'selected_config': self.selected_config,
            'recent_ops': self.recent_ops[-10:],  # 最近10条操作
            'last_error': self.last_error,
            'timestamp': datetime.now().isoformat()
        }
    
    def set_current_module(self, module_name: str):
        """
        设置当前激活的模块
        
        Args:
            module_name: 模块名称（如 "asset_manager", "config_tool"）
        """
        try:
            self.current_module = module_name
            self.record_op("switch_module", {"module": module_name})
            self._save_to_cache()
            self.logger.debug(f"当前模块切换到: {module_name}")
        except Exception as e:
            self.logger.error(f"设置当前模块失败: {e}")
    
    def set_selected_asset(self, asset_info: Dict[str, Any]):
        """
        设置当前选中的资产
        
        Args:
            asset_info: 资产信息字典（如 {'name': 'xxx', 'type': 'yyy', 'path': 'zzz'}）
        """
        try:
            self.selected_asset = asset_info
            self.record_op("select_asset", {"asset": asset_info.get('name', 'unknown')})
            self._save_to_cache()
            self.logger.debug(f"选中资产: {asset_info.get('name')}")
        except Exception as e:
            self.logger.error(f"设置选中资产失败: {e}")
    
    def set_selected_config(self, config_info: Dict[str, Any]):
        """
        设置当前选中的配置
        
        Args:
            config_info: 配置信息字典
        """
        try:
            self.selected_config = config_info
            self.record_op("select_config", {"config": config_info.get('name', 'unknown')})
            self._save_to_cache()
            self.logger.debug(f"选中配置: {config_info.get('name')}")
        except Exception as e:
            self.logger.error(f"设置选中配置失败: {e}")
    
    def record_op(self, action: str, details: Optional[Dict[str, Any]] = None):
        """
        记录用户操作
        
        Args:
            action: 操作类型（如 "open_file", "search", "export"）
            details: 操作详情
        """
        try:
            op_record = {
                'action': action,
                'details': details or {},
                'timestamp': datetime.now().isoformat()
            }
            
            self.recent_ops.append(op_record)
            
            # 只保留最近50条操作记录
            if len(self.recent_ops) > 50:
                self.recent_ops = self.recent_ops[-50:]
            
            # 记录操作不立即保存，避免频繁 I/O
            # 由其他状态变更触发保存
            
        except Exception as e:
            self.logger.error(f"记录操作失败: {e}")
    
    def set_last_error(self, error_info: Dict[str, Any]):
        """
        记录最后一次错误
        
        Args:
            error_info: 错误信息字典（如 {'type': 'xxx', 'message': 'yyy'}）
        """
        try:
            self.last_error = {
                **error_info,
                'timestamp': datetime.now().isoformat()
            }
            self._save_to_cache()
            self.logger.debug(f"记录错误: {error_info.get('message', 'unknown')}")
        except Exception as e:
            self.logger.error(f"设置错误信息失败: {e}")
    
    def clear(self):
        """清空所有状态"""
        try:
            self.current_module = None
            self.selected_asset = None
            self.selected_config = None
            self.recent_ops = []
            self.last_error = None
            self._save_to_cache()
            self.logger.info("运行态上下文已清空")
        except Exception as e:
            self.logger.error(f"清空上下文失败: {e}")
    
    def _save_to_cache(self):
        """
        保存状态到缓存文件
        
        异常安全：保存失败不影响程序运行
        """
        try:
            snapshot = self.snapshot()
            
            # 写入缓存文件
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(snapshot, f, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"状态已保存到缓存: {self.cache_file}")
            
        except Exception as e:
            # 保存失败不抛出异常，只记录日志
            self.logger.warning(f"保存运行态缓存失败（不影响程序运行）: {e}")
    
    def _load_from_cache(self):
        """
        从缓存文件恢复状态
        
        异常安全：读取失败时使用默认值
        """
        try:
            if not self.cache_file.exists():
                self.logger.info("缓存文件不存在，使用默认状态")
                return
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 恢复状态（使用 get 避免 KeyError）
            self.current_module = data.get('current_module')
            self.selected_asset = data.get('selected_asset')
            self.selected_config = data.get('selected_config')
            self.recent_ops = data.get('recent_ops', [])
            self.last_error = data.get('last_error')
            
            self.logger.info(f"已从缓存恢复运行态（模块: {self.current_module}）")
            
        except json.JSONDecodeError as e:
            # JSON 格式错误，使用默认值
            self.logger.warning(f"缓存文件格式错误，使用默认状态: {e}")
        except Exception as e:
            # 其他错误，使用默认值
            self.logger.warning(f"加载运行态缓存失败，使用默认状态: {e}")
    
    def get_formatted_snapshot(self) -> str:
        """
        获取格式化的运行态快照（用于上下文拼接）
        
        Returns:
            str: Markdown 格式的快照文本
        """
        try:
            snapshot = self.snapshot()
            
            parts = ["[运行态上下文]"]
            
            # 当前模块（使用中文名称）
            if snapshot.get('current_module'):
                module_name = snapshot['current_module']
                display_name = self.MODULE_NAME_MAP.get(module_name, module_name)
                parts.append(f"**当前模块**: {display_name}")
            
            # 选中资产
            if snapshot.get('selected_asset'):
                asset = snapshot['selected_asset']
                asset_name = asset.get('name', 'unknown')
                asset_type = asset.get('type', '')
                parts.append(f"**选中资产**: {asset_name} ({asset_type})")
            
            # 选中配置
            if snapshot.get('selected_config'):
                config = snapshot['selected_config']
                config_name = config.get('name', 'unknown')
                parts.append(f"**选中配置**: {config_name}")
            
            # 最近操作（包含详细信息，使用中文名称）
            if snapshot.get('recent_ops'):
                recent = snapshot['recent_ops'][-3:]  # 最近3条
                ops_list = []
                for op in recent:
                    action = op.get('action', 'unknown')
                    details = op.get('details', {})
                    
                    # 根据操作类型格式化详细信息
                    if action == 'switch_module' and 'module' in details:
                        module_name = details['module']
                        display_name = self.MODULE_NAME_MAP.get(module_name, module_name)
                        ops_list.append(f"切换到{display_name}")
                    elif action == 'select_asset' and 'name' in details:
                        ops_list.append(f"选中资产「{details['name']}」")
                    elif action == 'select_config' and 'config' in details:
                        ops_list.append(f"选中配置「{details['config']}」")
                    else:
                        ops_list.append(action)
                
                ops_text = " → ".join(ops_list)
                parts.append(f"**最近操作**: {ops_text}")
            
            # 最后错误
            if snapshot.get('last_error'):
                error = snapshot['last_error']
                error_msg = error.get('message', 'unknown')
                parts.append(f"**最后错误**: {error_msg}")
            
            return "\n".join(parts) if len(parts) > 1 else ""
            
        except Exception as e:
            self.logger.error(f"格式化快照失败: {e}")
            return ""

