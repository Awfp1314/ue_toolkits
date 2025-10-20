# -*- coding: utf-8 -*-

"""
pytest 配置文件
定义全局 fixtures 和测试配置
"""

import sys
from pathlib import Path
import pytest

# 将项目根目录添加到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_config_dir(tmp_path):
    """创建临时配置目录"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def temp_module_dir(tmp_path):
    """创建临时模块目录"""
    module_dir = tmp_path / "modules"
    module_dir.mkdir()
    return module_dir


@pytest.fixture
def sample_manifest():
    """示例模块清单"""
    return {
        "name": "test_module",
        "display_name": "测试模块",
        "version": "1.0.0",
        "description": "用于测试的模块",
        "author": "Test Author",
        "icon": "",
        "dependencies": [],
        "entry_point": "__main__:TestModule"
    }


@pytest.fixture
def sample_config():
    """示例配置"""
    return {
        "_version": "1.0.0",
        "setting1": "value1",
        "setting2": 123,
        "nested": {
            "key": "value"
        }
    }

