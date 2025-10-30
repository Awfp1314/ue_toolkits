# -*- coding: utf-8 -*-

"""
配置管理器模块
基于 JSON 的配置管理系统核心功能
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, Callable

from core.logger import get_logger
from core.utils.path_utils import PathUtils
from core.utils.thread_utils import get_thread_manager
from .config_validator import ConfigValidator, ConfigSchema
from .config_backup import ConfigBackupManager


class ConfigManager:
    """基于 JSON 的配置管理系统
    
    重构后的精简版本，使用独立的验证器和备份管理器模块
    """
    
    def __init__(self, module_name: str, template_path: Optional[Path] = None, 
                 config_schema: Optional[ConfigSchema] = None):
        """初始化配置管理器
        
        Args:
            module_name: 模块名称
            template_path: 配置模板文件路径（可选）
            config_schema: 配置模式定义（可选），如果不提供将使用默认模式
        """
        self.module_name = module_name
        self.template_path = template_path
        self.logger = get_logger(f"config_manager.{module_name}")
        self.path_utils = PathUtils()
        
        # 获取用户配置基目录
        base_config_dir = self.path_utils.get_user_config_dir()
        
        # 为每个模块创建专属的配置目录（除了 "app" 模块，它使用全局 configs 目录）
        if module_name == "app":
            self.user_config_dir = base_config_dir
        else:
            # 其他模块在 configs/{module_name}/ 下创建配置目录
            self.user_config_dir = base_config_dir / module_name
        
        self.user_config_dir.mkdir(parents=True, exist_ok=True)
        
        # 用户配置文件路径
        self.user_config_path = self.user_config_dir / f"{module_name}_config.json"
        
        # 备份目录
        self.backup_dir = self.user_config_dir / "backup"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.validator = ConfigValidator(module_name, config_schema)
        
        self.backup_manager = ConfigBackupManager(
            module_name, 
            self.user_config_path, 
            self.backup_dir
        )
        
        self.thread_manager = get_thread_manager()
        
        # 配置缓存
        self._config_cache: Optional[Dict[str, Any]] = None
        self._cache_timestamp: Optional[float] = None
        
        self.logger.info(f"初始化配置管理器: {module_name}")
        self.logger.info(f"用户配置目录: {self.user_config_dir}")
        self.logger.info(f"用户配置文件: {self.user_config_path}")
        self.logger.info(f"备份目录: {self.backup_dir}")
    
    def load_template(self) -> Dict[str, Any]:
        """加载配置模板
        
        Returns:
            Dict[str, Any]: 配置模板内容
            
        Raises:
            FileNotFoundError: 模板文件不存在
            json.JSONDecodeError: 模板文件格式错误
        """
        if not self.template_path or not self.template_path.exists():
            self.logger.warning(f"配置模板文件不存在: {self.template_path}")
            return {}
            
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                template = json.load(f)
            self.logger.info(f"成功加载配置模板: {self.template_path}")
            return template
        except json.JSONDecodeError as e:
            self.logger.error(f"配置模板文件格式错误: {e}")
            raise
        except Exception as e:
            self.logger.error(f"加载配置模板失败: {e}")
            raise
    
    def load_user_config(self) -> Dict[str, Any]:
        """加载用户配置
        
        Returns:
            Dict[str, Any]: 用户配置内容
            
        Raises:
            json.JSONDecodeError: 配置文件格式错误
        """
        if not self.user_config_path.exists():
            self.logger.info(f"用户配置文件不存在: {self.user_config_path}")
            return {}
            
        try:
            with open(self.user_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.logger.info(f"成功加载用户配置: {self.user_config_path}")
            return config
        except json.JSONDecodeError as e:
            self.logger.error(f"用户配置文件格式错误: {e}")
            raise
        except Exception as e:
            self.logger.error(f"加载用户配置失败: {e}")
            raise
    
    def save_user_config(self, config: Dict[str, Any], backup_reason: str = "manual_save") -> bool:
        """保存用户配置（同步版本，保持向后兼容）
        
        改进的备份策略：
        1. 在保存前自动备份新配置（即将保存的配置）
        2. 验证备份文件的有效性
        3. 使用带时间戳和原因的文件名
        
        Args:
            config: 要保存的配置
            backup_reason: 备份原因（用于文件命名）
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 确保配置目录存在
            self.user_config_dir.mkdir(parents=True, exist_ok=True)
            
            # 备份新配置（即将保存的配置）
            self.logger.debug(f"备份新配置，原因: {backup_reason}")
            if not self.backup_manager.backup_config(reason=backup_reason, config=config):
                self.logger.warning("备份失败，但继续保存新配置")
            
            if not self.validator.validate_config(config):
                self.logger.error("配置验证失败，拒绝保存")
                return False
            
            with open(self.user_config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            # 清除缓存（配置已更新）
            self.clear_cache()
            
            self.logger.info(f"成功保存用户配置: {self.user_config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存用户配置失败: {e}")
            return False
    
    def save_user_config_async(
        self,
        config: Dict[str, Any],
        backup_reason: str = "manual_save",
        on_complete: Optional[Callable[[bool], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ):
        """异步保存用户配置（推荐使用）
        
        Args:
            config: 要保存的配置
            backup_reason: 备份原因
            on_complete: 完成回调
            on_error: 错误回调
        """
        self.logger.info("开始异步保存配置")
        
        def save_task():
            return self.save_user_config(config, backup_reason)
        
        def on_result(success):
            if success:
                self.logger.info("配置异步保存成功")
            else:
                self.logger.error("配置异步保存失败")
            if on_complete:
                on_complete(success)
        
        self.thread_manager.run_in_thread(
            save_task,
            on_result=on_result,
            on_error=on_error
        )
    
    def get_config_version(self, config: Dict[str, Any]) -> str:
        """获取配置版本
        
        Args:
            config: 配置内容
            
        Returns:
            str: 配置版本号
        """
        # 优先从配置中获取版本号，如果没有则使用默认值
        version = config.get('_version', None)
        if version is not None:
            return str(version)
        
        # 如果配置中没有版本号，尝试从模板中获取
        try:
            template = self.load_template()
            template_version = template.get('_version', None)
            if template_version is not None:
                return str(template_version)
        except Exception:
            pass
        
        # 如果模板中也没有版本号，使用默认值
        return '1.0.0'
    
    def merge_config(self, template: Dict[str, Any], user_config: Dict[str, Any]) -> Dict[str, Any]:
        """合并模板配置和用户配置，保留用户设置
        
        Args:
            template: 模板配置
            user_config: 用户配置
            
        Returns:
            Dict[str, Any]: 合并后的配置
        """
        merged_config = template.copy()
        
        # 递归合并配置
        def _merge_recursive(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
            for key, value in override.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    base[key] = _merge_recursive(base[key], value)
                else:
                    base[key] = value
            return base
        
        merged_config = _merge_recursive(merged_config, user_config)
        return merged_config
    
    def upgrade_config(self, template: Dict[str, Any], user_config: Dict[str, Any]) -> Dict[str, Any]:
        """升级配置文件，补全缺失字段
        
        Args:
            template: 模板配置
            user_config: 用户配置
            
        Returns:
            Dict[str, Any]: 升级后的配置
        """
        template_version = self.get_config_version(template)
        user_version = self.get_config_version(user_config)
        
        self.logger.info(f"配置版本检查 - 模板版本: {template_version}, 用户版本: {user_version}")
        
        # 比较版本号
        version_comparison = self.validator.compare_versions(template_version, user_version)
        
        # 如果版本不同，需要升级
        if version_comparison != 0:
            self.logger.info(f"检测到配置版本不匹配，执行升级: {user_version} -> {template_version}")
            # 在升级前备份当前配置
            self.backup_manager.backup_config(reason="auto_upgrade", config=user_config)
        
        # 合并配置
        merged_config = self.merge_config(template, user_config)
        
        merged_config['_version'] = template_version
        
        self.logger.info("配置升级完成")
        return merged_config
    
    def get_module_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """获取模块配置（自动处理模板比对和升级，带缓存机制）
        
        Args:
            force_reload: 是否强制重新加载配置（忽略缓存）
            
        Returns:
            Dict[str, Any]: 模块配置
        """
        if not force_reload and self._is_cache_valid():
            self.logger.debug("使用缓存的配置")
            # 确保缓存不为None再调用copy()
            if self._config_cache is not None:
                return self._config_cache.copy()
            else:
                # 如果缓存为None，则重新加载
                self.logger.debug("缓存为None，重新加载配置")
        
        try:
            self.logger.debug("重新加载配置（缓存失效或强制重新加载）")
            
            template_config = self.load_template()
            
            user_config = self.load_user_config()
            
            if user_config and not self.validator.validate_config(user_config):
                self.logger.warning("用户配置验证失败，尝试从备份恢复")
                # 尝试从备份恢复
                recovered_config = self.backup_manager.restore_from_backup()
                if recovered_config and self.validator.validate_config(recovered_config):
                    user_config = recovered_config
                    self.save_user_config(user_config, backup_reason="restore")
                else:
                    self.logger.warning("无法从备份恢复有效配置，使用模板重新初始化")
                    user_config = {}
            
            # 如果用户配置不存在或无效，直接使用模板配置
            if not user_config:
                self.logger.info("用户配置不存在或无效，使用模板配置初始化")
                # 添加版本信息（从模板获取或使用默认值）
                if '_version' not in template_config:
                    template_config['_version'] = self.get_config_version(template_config)
                self.save_user_config(template_config, backup_reason="init")
                config = template_config
            else:
                # 升级配置
                upgraded_config = self.upgrade_config(template_config, user_config)
                
                # 如果配置有变化，保存更新后的配置
                if upgraded_config != user_config:
                    self.logger.info("配置已更新，保存升级后的配置")
                    self.save_user_config(upgraded_config, backup_reason="upgrade")
                
                config = upgraded_config
            
            self._update_cache(config)
            
            return config.copy()
            
        except Exception as e:
            self.logger.error(f"获取模块配置时发生错误: {e}")
            # 尝试从备份恢复
            recovered_config = self.backup_manager.restore_from_backup()
            if recovered_config:
                self.logger.info("使用备份配置作为回退方案")
                self._update_cache(recovered_config)
                return recovered_config
            else:
                # 最后的回退方案：重新初始化
                self.logger.warning("无法恢复配置，重新初始化")
                template_config = self.load_template()
                if '_version' not in template_config:
                    template_config['_version'] = self.get_config_version(template_config)
                self.save_user_config(template_config, backup_reason="recovery")
                self._update_cache(template_config)
                return template_config
    
    def get_module_config_async(
        self,
        force_reload: bool = False,
        on_complete: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ):
        """异步获取模块配置（推荐使用）
        
        Args:
            force_reload: 是否强制重新加载
            on_complete: 完成回调 (config: Dict) -> None
            on_error: 错误回调
            
        Example:
            def on_config_loaded(config):
                print(f"配置加载完成: {config}")
            
            config_manager.get_module_config_async(
                on_complete=on_config_loaded
            )
        """
        self.logger.info("开始异步加载配置")
        
        def load_task():
            return self.get_module_config(force_reload)
        
        self.thread_manager.run_in_thread(
            load_task,
            on_result=on_complete,
            on_error=on_error
        )
    
    def _is_cache_valid(self) -> bool:
        """检查缓存是否有效
        
        Returns:
            bool: 缓存是否有效
        """
        # 如果没有缓存，返回False
        if self._config_cache is None or self._cache_timestamp is None:
            return False
        
        if not self.user_config_path.exists():
            return False
        
        try:
            file_mtime = self.user_config_path.stat().st_mtime
            if file_mtime > self._cache_timestamp:
                self.logger.debug("配置文件已被修改，缓存失效")
                return False
        except OSError as e:
            self.logger.warning(f"无法获取配置文件修改时间: {e}")
            return False
        
        return True
    
    def _update_cache(self, config: Dict[str, Any]) -> None:
        """更新配置缓存
        
        Args:
            config: 配置数据
        """
        import time
        self._config_cache = config.copy()
        self._cache_timestamp = time.time()
        self.logger.debug("配置缓存已更新")
    
    def clear_cache(self) -> None:
        """清除配置缓存"""
        self._config_cache = None
        self._cache_timestamp = None
        self.logger.debug("配置缓存已清除")
    
    def update_config_value(self, key: str, value: Any) -> bool:
        """更新配置值
        
        Args:
            key: 配置键（支持点号分隔的嵌套键，如 'database.host'）
            value: 配置值
            
        Returns:
            bool: 更新是否成功
        """
        try:
            config = self.get_module_config()
            
            keys = key.split('.')
            current = config
            for k in keys[:-1]:
                if k not in current or not isinstance(current[k], dict):
                    current[k] = {}
                current = current[k]
            
            current[keys[-1]] = value
            
            if not self.validator.validate_config(config):
                self.logger.error("更新后的配置验证失败")
                return False
            
            return self.save_user_config(config, backup_reason="update_value")
        except Exception as e:
            self.logger.error(f"更新配置值失败: {e}")
            return False
    
    
    def backup_config(self, reason: str = "manual") -> bool:
        """备份当前配置文件
        
        Args:
            reason: 备份原因
            
        Returns:
            bool: 备份是否成功
        """
        return self.backup_manager.backup_config(reason)
    
    def list_backups(self):
        """列出所有可用的备份文件"""
        return self.backup_manager.list_backups()
    
    def restore_from_backup(self, backup_index: int = 0) -> bool:
        """从备份恢复配置
        
        Args:
            backup_index: 备份索引
            
        Returns:
            bool: 恢复是否成功
        """
        # 在恢复前备份当前配置
        if self.user_config_path.exists():
            self.logger.info("恢复前备份当前配置")
            try:
                with open(self.user_config_path, 'r', encoding='utf-8') as f:
                    current_config = json.load(f)
                self.backup_manager.backup_config(reason="before_restore", config=current_config)
            except Exception as e:
                self.logger.warning(f"恢复前备份配置失败: {e}")
        
        # 从备份恢复配置数据
        backup_config = self.backup_manager.restore_from_backup(backup_index)
        if not backup_config:
            self.logger.error("恢复配置失败")
            return False
        
        if not self.validator.validate_config(backup_config):
            self.logger.error("恢复的配置验证失败，无法恢复")
            return False
        
        if not self.save_user_config(backup_config, backup_reason="restore"):
            self.logger.error("保存恢复的配置失败")
            return False
        
        self.logger.info("成功从备份恢复配置")
        return True
    
    def get_backup_stats(self):
        """获取备份统计信息"""
        return self.backup_manager.get_backup_stats()
    
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置数据的完整性和有效性
        
        Args:
            config: 要验证的配置
            
        Returns:
            bool: 配置是否有效
        """
        return self.validator.validate_config(config)

