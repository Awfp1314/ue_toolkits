# -*- coding: utf-8 -*-

"""
ConfigValidator 单元测试
"""

import pytest
from core.config.config_validator import ConfigValidator, ConfigSchema


class TestConfigValidator:
    """ConfigValidator 测试类"""
    
    def test_validate_config_valid(self, sample_config):
        """测试验证有效配置"""
        validator = ConfigValidator("test_module")
        assert validator.validate_config(sample_config)
    
    def test_validate_config_empty(self):
        """测试验证空配置"""
        validator = ConfigValidator("test_module")
        assert not validator.validate_config({})
    
    def test_validate_config_not_dict(self):
        """测试验证非字典类型"""
        validator = ConfigValidator("test_module")
        assert not validator.validate_config("not a dict")
        assert not validator.validate_config([1, 2, 3])
        assert not validator.validate_config(None)
    
    def test_validate_config_missing_version(self):
        """测试缺少版本号"""
        validator = ConfigValidator("test_module")
        config = {"setting": "value"}
        assert not validator.validate_config(config)
    
    def test_validate_config_invalid_version_format(self):
        """测试无效版本号格式"""
        validator = ConfigValidator("test_module")
        
        # 无效格式
        assert not validator.validate_config({"_version": "1.0"})
        assert not validator.validate_config({"_version": "1"})
        assert not validator.validate_config({"_version": "abc"})
        assert not validator.validate_config({"_version": ""})
    
    def test_validate_config_valid_version_formats(self):
        """测试有效版本号格式"""
        validator = ConfigValidator("test_module")
        
        # 有效格式
        assert validator.validate_config({"_version": "1.0.0"})
        assert validator.validate_config({"_version": "2.1.3"})
        assert validator.validate_config({"_version": "1.0.0-alpha"})
        assert validator.validate_config({"_version": "1.0.0+build"})
    
    def test_compare_versions(self):
        """测试版本号比较"""
        validator = ConfigValidator("test_module")
        
        # 相等
        assert validator.compare_versions("1.0.0", "1.0.0") == 0
        
        # 小于
        assert validator.compare_versions("1.0.0", "1.0.1") == -1
        assert validator.compare_versions("1.0.0", "1.1.0") == -1
        assert validator.compare_versions("1.0.0", "2.0.0") == -1
        
        # 大于
        assert validator.compare_versions("1.0.1", "1.0.0") == 1
        assert validator.compare_versions("1.1.0", "1.0.0") == 1
        assert validator.compare_versions("2.0.0", "1.0.0") == 1
    
    def test_custom_schema(self):
        """测试自定义配置模式"""
        schema = ConfigSchema(
            required_fields={"_version", "required_field"},
            optional_fields={"optional_field"},
            field_types={"_version": str, "required_field": str},
            allow_unknown_fields=False
        )
        
        validator = ConfigValidator("test_module", schema)
        
        # 缺少必需字段
        assert not validator.validate_config({"_version": "1.0.0"})
        
        # 包含所有必需字段
        assert validator.validate_config({
            "_version": "1.0.0",
            "required_field": "value"
        })
        
        # 包含未知字段（不允许）
        assert not validator.validate_config({
            "_version": "1.0.0",
            "required_field": "value",
            "unknown_field": "value"
        })
    
    def test_field_type_validation(self):
        """测试字段类型验证"""
        schema = ConfigSchema(
            required_fields={"_version", "string_field", "int_field"},
            field_types={
                "_version": str,
                "string_field": str,
                "int_field": int
            }
        )
        
        validator = ConfigValidator("test_module", schema)
        
        # 正确类型
        assert validator.validate_config({
            "_version": "1.0.0",
            "string_field": "text",
            "int_field": 123
        })
        
        assert not validator.validate_config({
            "_version": "1.0.0",
            "string_field": 123,  # 应该是字符串
            "int_field": "text"   # 应该是整数
        })

