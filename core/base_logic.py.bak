# -*- coding: utf-8 -*-

"""
业务逻辑基类 - 提供通用的配置管理和日志功能

所有模块的业务逻辑类都应继承此基类，以获得：
1. 统一的配置管理
2. 自动的日志记录器
3. 通用的初始化流程
4. 配置文件的自动保存/加载
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional
import json
import time
import shutil
from core.logger import get_logger

logger = get_logger(__name__)


class BaseLogic(ABC):
    """业务逻辑基类（增强版：支持配置版本迁移）
    
    提供配置管理和日志记录的基础功能，包括配置版本管理和自动迁移
    
    子类需要实现:
        - get_config_name(): 返回配置文件名
        - get_default_config(): 返回默认配置
        - migrate_config(): (可选) 实现配置迁移逻辑
    
    子类可以覆盖:
        - CURRENT_CONFIG_VERSION: 当前配置版本号
    
    Example:
        class MyModuleLogic(BaseLogic):
            CURRENT_CONFIG_VERSION = "2.0.0"  # 当前版本
            
            def get_config_name(self) -> str:
                return "my_module_config"
            
            def get_default_config(self) -> Dict[str, Any]:
                return {
                    "version": "2.0.0",
                    "enabled": True,
                    "settings": {}
                }
            
            def migrate_config(self, from_version: str, to_version: str) -> bool:
                # 实现从旧版本到新版本的迁移
                if from_version == "1.0.0" and to_version == "2.0.0":
                    self.config["new_field"] = "default_value"
                    return True
                return False
            
            def my_business_method(self):
                # 使用 self.config 访问配置
                if self.config.get("enabled"):
                    self.logger.info("模块已启用")
    """
    
    # 子类应该覆盖此属性以指定当前配置版本
    CURRENT_CONFIG_VERSION = "1.0.0"
    
    def __init__(self, config_dir: str, watch_changes: bool = False):
        """初始化业务逻辑基类
        
        Args:
            config_dir: 配置目录路径
            watch_changes: 是否监听配置文件变化（需要watchdog库）
        """
        # 路径管理
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / f"{self.get_config_name()}.json"
        
        # 配置数据
        self.config: Dict[str, Any] = {}
        
        self.logger = get_logger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )
        
        # 配置监听器
        self._watcher = None
        self._observer = None
        
        self.logger.info(f"初始化 {self.__class__.__name__}，配置目录: {config_dir}")
        self._load_config()
        
        # 可选：启动配置热重载
        if watch_changes:
            self._start_config_watcher()
    
    @abstractmethod
    def get_config_name(self) -> str:
        """获取配置文件名（不含扩展名）
        
        Returns:
            str: 配置文件名，如 "site_config"
            
        Example:
            def get_config_name(self) -> str:
                return "site_config"
        """
        pass
    
    @abstractmethod
    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置
        
        返回的配置应该包含所有必需的字段
        
        Returns:
            Dict[str, Any]: 默认配置字典
            
        Example:
            def get_default_config(self) -> Dict[str, Any]:
                return {
                    "version": "1.0.0",
                    "enabled": True,
                    "max_items": 100
                }
        """
        pass
    
    def _load_config(self):
        """加载配置文件（内部方法 - 支持版本迁移）
        
        自动处理配置文件不存在的情况，并执行版本检查和迁移
        """
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                self.logger.info(f"配置文件加载成功: {self.config_file}")
                
                # ✅ 检查配置版本
                config_version = self.config.get("version", "0.0.0")
                current_version = self.CURRENT_CONFIG_VERSION
                
                if config_version != current_version:
                    self.logger.info(f"检测到配置版本不匹配: {config_version} -> {current_version}")
                    
                    # 备份旧配置
                    self._backup_config_for_migration(config_version)
                    
                    # 尝试迁移
                    if self.migrate_config(config_version, current_version):
                        self.config["version"] = current_version
                        self.save_config()
                        self.logger.info(f"配置成功从 {config_version} 迁移到 {current_version}")
                    else:
                        self.logger.warning(
                            f"配置迁移不支持或失败 ({config_version} -> {current_version})，"
                            "使用默认配置"
                        )
                        self.config = self.get_default_config()
                        self.save_config()
                
                if self.validate_config(self.config):
                    self.logger.debug("配置验证通过")
                else:
                    self.logger.warning("配置验证失败，使用默认配置")
                    self.config = self.get_default_config()
                    self.save_config()
            else:
                self.logger.info("配置文件不存在，创建默认配置")
                self.config = self.get_default_config()
                self.save_config()
                
        except json.JSONDecodeError as e:
            self.logger.error(f"配置文件格式错误: {e}，使用默认配置")
            self.config = self.get_default_config()
            # 备份损坏的配置文件
            self._backup_corrupted_config()
            self.save_config()
            
        except Exception as e:
            self.logger.error(f"加载配置文件时出错: {e}，使用默认配置", exc_info=True)
            self.config = self.get_default_config()
    
    def save_config(self) -> bool:
        """保存配置文件
        
        Returns:
            bool: 保存是否成功
            
        Example:
            self.config["enabled"] = True
            if self.save_config():
                print("保存成功")
        """
        try:
            # 确保目录存在
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            if not self.validate_config(self.config):
                self.logger.error("配置验证失败，拒绝保存")
                return False
            
            # 原子写入（先写临时文件）
            temp_file = self.config_file.with_suffix('.tmp')
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            # 替换原文件
            temp_file.replace(self.config_file)
            
            self.logger.info(f"配置文件保存成功: {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存配置文件时出错: {e}", exc_info=True)
            return False
    
    def reload_config(self) -> bool:
        """重新加载配置文件
        
        Returns:
            bool: 重新加载是否成功
        """
        try:
            self._load_config()
            self.logger.info("配置重新加载成功")
            return True
        except Exception as e:
            self.logger.error(f"重新加载配置失败: {e}")
            return False
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置（子类可以重写）
        
        Args:
            config: 要验证的配置
            
        Returns:
            bool: 配置是否有效
            
        Example:
            def validate_config(self, config: Dict[str, Any]) -> bool:
                if "version" not in config:
                    return False
                if config.get("max_items", 0) < 0:
                    return False
                return True
        """
        # 基本验证：检查是否是字典且非空
        if not isinstance(config, dict):
            self.logger.error("配置必须是字典类型")
            return False
        
        if not config:
            self.logger.error("配置不能为空")
            return False
        
        # 默认通过，子类可以添加更多验证
        return True
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值（支持点号分隔的嵌套键）
        
        Args:
            key: 配置键，支持 "section.subsection.key" 格式
            default: 默认值
            
        Returns:
            Any: 配置值
            
        Example:
            max_items = self.get_config_value("settings.max_items", 100)
        """
        try:
            keys = key.split('.')
            value = self.config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except Exception:
            return default
    
    def set_config_value(self, key: str, value: Any) -> bool:
        """设置配置值（支持点号分隔的嵌套键）
        
        Args:
            key: 配置键，支持 "section.subsection.key" 格式
            value: 配置值
            
        Returns:
            bool: 设置是否成功
            
        Example:
            self.set_config_value("settings.max_items", 200)
        """
        try:
            keys = key.split('.')
            current = self.config
            
            # 遍历到倒数第二个键
            for k in keys[:-1]:
                if k not in current or not isinstance(current[k], dict):
                    current[k] = {}
                current = current[k]
            
            # 设置最后一个键的值
            current[keys[-1]] = value
            
            # 自动保存
            return self.save_config()
            
        except Exception as e:
            self.logger.error(f"设置配置值失败 ({key}): {e}")
            return False
    
    def _backup_corrupted_config(self):
        """备份损坏的配置文件"""
        try:
            if self.config_file.exists():
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_file = self.config_file.with_suffix(f'.corrupted_{timestamp}.json')
                
                self.config_file.rename(backup_file)
                self.logger.info(f"损坏的配置文件已备份到: {backup_file}")
                
        except Exception as e:
            self.logger.error(f"备份配置文件失败: {e}")
    
    def reset_to_default(self) -> bool:
        """重置配置为默认值
        
        Returns:
            bool: 重置是否成功
        """
        try:
            self.logger.info("重置配置为默认值")
            self.config = self.get_default_config()
            return self.save_config()
        except Exception as e:
            self.logger.error(f"重置配置失败: {e}")
            return False
    
    def export_config(self, output_path: Path) -> bool:
        """导出配置到文件
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            bool: 导出是否成功
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"配置导出成功: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出配置失败: {e}")
            return False
    
    def import_config(self, input_path: Path) -> bool:
        """从文件导入配置
        
        Args:
            input_path: 输入文件路径
            
        Returns:
            bool: 导入是否成功
        """
        try:
            input_path = Path(input_path)
            
            if not input_path.exists():
                self.logger.error(f"配置文件不存在: {input_path}")
                return False
            
            with open(input_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            if not self.validate_config(imported_config):
                self.logger.error("导入的配置验证失败")
                return False
            
            # 备份当前配置
            self._backup_current_config()
            
            self.config = imported_config
            
            if self.save_config():
                self.logger.info(f"配置导入成功: {input_path}")
                return True
            else:
                self.logger.error("保存导入的配置失败")
                return False
                
        except Exception as e:
            self.logger.error(f"导入配置失败: {e}")
            return False
    
    def _backup_current_config(self):
        """备份当前配置"""
        try:
            if self.config_file.exists():
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_file = self.config_file.with_suffix(f'.backup_{timestamp}.json')
                
                shutil.copy2(self.config_file, backup_file)
                
                self.logger.info(f"当前配置已备份到: {backup_file}")
                
        except Exception as e:
            self.logger.error(f"备份配置失败: {e}")
    
    def _backup_config_for_migration(self, old_version: str):
        """为配置迁移创建备份
        
        Args:
            old_version: 旧版本号
        """
        try:
            if self.config_file.exists():
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_file = self.config_file.with_suffix(f'.v{old_version}_{timestamp}.json')
                shutil.copy2(self.config_file, backup_file)
                
                self.logger.info(f"配置迁移备份已创建: {backup_file}")
                
        except Exception as e:
            self.logger.error(f"创建迁移备份失败: {e}")
    
    def migrate_config(self, from_version: str, to_version: str) -> bool:
        """迁移配置（子类可以重写）
        
        Args:
            from_version: 原始版本
            to_version: 目标版本
            
        Returns:
            bool: 迁移是否成功
            
        Example:
            def migrate_config(self, from_version, to_version):
                # 从 1.0.0 迁移到 2.0.0
                if from_version == "1.0.0" and to_version == "2.0.0":
                    # 添加新字段
                    if "new_field" not in self.config:
                        self.config["new_field"] = "default_value"
                    return True
                
                # 从 2.0.0 迁移到 3.0.0
                if from_version == "2.0.0" and to_version == "3.0.0":
                    # 重命名字段
                    if "old_field" in self.config:
                        self.config["new_field_name"] = self.config.pop("old_field")
                    return True
                
                # 不支持的迁移路径
                return False
        
        Note:
            - 默认实现不执行任何迁移，直接返回 False
            - 子类应该实现特定的迁移逻辑
            - 迁移应该是幂等的（可以安全地重复执行）
            - 返回 True 表示迁移成功，False 表示失败或不支持
        """
        self.logger.warning(
            f"未实现配置迁移逻辑: {from_version} -> {to_version}，"
            "将使用默认配置"
        )
        return False
    
    def _start_config_watcher(self):
        """启动配置文件监听（热重载）
        
        使用watchdog库监听配置文件的变化，自动重新加载
        
        Note:
            - 需要安装 watchdog 库: pip install watchdog
            - 如果未安装watchdog，将优雅地降级
        """
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            
            class ConfigFileHandler(FileSystemEventHandler):
                """配置文件变化处理器"""
                
                def __init__(self, logic_instance):
                    super().__init__()
                    self.logic = logic_instance
                    self._last_modified = 0
                    self._debounce_seconds = 1  # 防抖动时间
                
                def on_modified(self, event):
                    """文件修改事件"""
                    # 只处理目标配置文件
                    if event.src_path != str(self.logic.config_file):
                        return
                    
                    # 防止重复触发（某些编辑器会多次触发modified事件）
                    current_time = time.time()
                    if current_time - self._last_modified < self._debounce_seconds:
                        return
                    
                    self._last_modified = current_time
                    
                    # 重新加载配置
                    self.logic.logger.info("检测到配置文件变化，重新加载配置")
                    try:
                        self.logic.reload_config()
                        self.logic.logger.info("配置热重载成功")
                    except Exception as e:
                        self.logic.logger.error(f"配置热重载失败: {e}", exc_info=True)
            
            self._observer = Observer()
            self._watcher = ConfigFileHandler(self)
            
            # 监听配置目录
            self._observer.schedule(
                self._watcher,
                str(self.config_dir),
                recursive=False
            )
            
            # 启动观察器
            self._observer.start()
            
            self.logger.info(
                f"配置热重载已启动，监听文件: {self.config_file}"
            )
            
        except ImportError:
            self.logger.warning(
                "watchdog库未安装，无法启用配置热重载。"
                "安装方法: pip install watchdog"
            )
        except Exception as e:
            self.logger.error(f"启动配置监听失败: {e}", exc_info=True)
    
    def stop_config_watcher(self):
        """停止配置文件监听
        
        在不需要热重载或关闭时调用此方法
        
        Example:
            logic.stop_config_watcher()
        """
        if self._observer:
            try:
                self._observer.stop()
                self._observer.join(timeout=2)
                self.logger.info("配置热重载已停止")
            except Exception as e:
                self.logger.error(f"停止配置监听失败: {e}")
            finally:
                self._observer = None
                self._watcher = None
    
    def __del__(self):
        """清理资源"""
        # 停止配置监听器
        if self._observer:
            try:
                self._observer.stop()
                self._observer.join(timeout=1)
            except:
                pass

