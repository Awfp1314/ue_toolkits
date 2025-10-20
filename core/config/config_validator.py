# -*- coding: utf-8 -*-

"""
配置验证器模块
负责配置数据的完整性和有效性验证
"""

import re
from typing import Dict, Any, Set, Callable, Optional
from dataclasses import dataclass, field

from core.logger import get_logger


@dataclass
class ConfigSchema:
    """配置模式定义
    
    定义配置文件的结构要求，包括必需字段、可选字段、类型约束和自定义验证器。
    """
    required_fields: Set[str] = field(default_factory=lambda: {'_version'})
    """必需字段集合，默认至少需要 _version 字段"""
    
    optional_fields: Set[str] = field(default_factory=set)
    """可选字段集合"""
    
    field_types: Dict[str, type] = field(default_factory=lambda: {'_version': str})
    """字段类型映射，key为字段名，value为期望的类型"""
    
    field_validators: Dict[str, Callable[[Any], bool]] = field(default_factory=dict)
    """自定义字段验证器，key为字段名，value为验证函数"""
    
    allow_unknown_fields: bool = True
    """是否允许未知字段（默认允许但会警告）"""
    
    strict_mode: bool = False
    """严格模式：如果为True，未知字段将导致验证失败"""


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self, module_name: str, config_schema: Optional[ConfigSchema] = None):
        """初始化配置验证器
        
        Args:
            module_name: 模块名称
            config_schema: 配置模式定义（可选），如果不提供将使用默认模式
        """
        self.module_name = module_name
        self.logger = get_logger(f"config_validator.{module_name}")
        self.config_schema = config_schema if config_schema else ConfigSchema()
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置数据的完整性和有效性
        
        此方法执行全面的配置验证，包括：
        1. 基本类型检查
        2. 必需字段检查
        3. 字段类型验证
        4. 版本号严格验证
        5. 自定义验证器执行
        6. 未知字段检测
        
        Args:
            config: 要验证的配置
            
        Returns:
            bool: 配置是否有效
        """
        try:
            if not isinstance(config, dict):
                self.logger.error("配置验证失败: 配置必须是字典类型")
                return False
            
            if not config:
                self.logger.error("配置验证失败: 配置为空")
                return False
            
            missing_fields = self.config_schema.required_fields - set(config.keys())
            if missing_fields:
                self.logger.error(f"配置验证失败: 缺少必需字段 {sorted(missing_fields)}")
                return False
            
            for field_name, expected_type in self.config_schema.field_types.items():
                if field_name in config:
                    actual_value = config[field_name]
                    
                    if not isinstance(actual_value, expected_type):
                        actual_type = type(actual_value).__name__
                        expected_type_name = expected_type.__name__
                        self.logger.error(
                            f"配置验证失败: 字段 '{field_name}' 类型错误，"
                            f"期望 {expected_type_name}，实际 {actual_type}"
                        )
                        return False
            
            if '_version' in config:
                version = config['_version']
                
                if not version:
                    self.logger.error("配置验证失败: 版本号不能为空")
                    return False
                
                # 转换为字符串（兼容数字版本号）
                version_str = str(version)
                
                # 严格验证语义化版本号格式
                if not self._is_valid_semver(version_str):
                    self.logger.error(
                        f"配置验证失败: 版本号格式不正确 '{version_str}'，"
                        f"必须符合语义化版本规范（如 1.0.0）"
                    )
                    return False
                
                self.logger.debug(f"版本号验证通过: {version_str}")
            
            for field_name, validator in self.config_schema.field_validators.items():
                if field_name in config:
                    try:
                        field_value = config[field_name]
                        if not validator(field_value):
                            self.logger.error(
                                f"配置验证失败: 字段 '{field_name}' 未通过自定义验证"
                            )
                            return False
                        self.logger.debug(f"字段 '{field_name}' 通过自定义验证")
                    except Exception as e:
                        self.logger.error(
                            f"配置验证失败: 字段 '{field_name}' 验证时发生异常: {e}"
                        )
                        return False
            
            known_fields = (
                self.config_schema.required_fields | 
                self.config_schema.optional_fields |
                set(self.config_schema.field_types.keys())
            )
            unknown_fields = set(config.keys()) - known_fields
            
            if unknown_fields:
                if self.config_schema.strict_mode:
                    # 严格模式：未知字段导致验证失败
                    self.logger.error(
                        f"配置验证失败（严格模式）: 包含未知字段 {sorted(unknown_fields)}"
                    )
                    return False
                elif self.config_schema.allow_unknown_fields:
                    # 宽松模式：只警告未知字段
                    self.logger.warning(
                        f"配置包含未知字段 {sorted(unknown_fields)}，"
                        f"这些字段将被保留但可能不会被使用"
                    )
                else:
                    # 不允许未知字段
                    self.logger.error(
                        f"配置验证失败: 包含未知字段 {sorted(unknown_fields)}"
                    )
                    return False
            
            self.logger.info("配置验证通过 - 所有检查项均符合要求")
            return True
            
        except Exception as e:
            self.logger.error(f"配置验证时发生异常: {e}", exc_info=True)
            return False
    
    def _is_valid_semver(self, version: str) -> bool:
        """检查是否为有效的语义化版本号
        
        Args:
            version: 版本号字符串
            
        Returns:
            bool: 是否为有效的语义化版本号
        """
        # 简单的语义化版本号正则表达式
        semver_pattern = r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
        return bool(re.match(semver_pattern, version))
    
    def compare_versions(self, version1: str, version2: str) -> int:
        """比较两个版本号
        
        Args:
            version1: 第一个版本号
            version2: 第二个版本号
            
        Returns:
            int: 比较结果 (-1: v1<v2, 0: v1==v2, 1: v1>v2)
        """
        # 简单的版本号比较实现
        def parse_version(v: str) -> tuple:
            # 移除预发布和构建元数据
            main_version = v.split('+')[0].split('-')[0]
            parts = main_version.split('.')
            # 确保有三个部分
            while len(parts) < 3:
                parts.append('0')
            return tuple(int(part) for part in parts[:3])
        
        v1_parts = parse_version(version1)
        v2_parts = parse_version(version2)
        
        if v1_parts < v2_parts:
            return -1
        elif v1_parts > v2_parts:
            return 1
        else:
            return 0

