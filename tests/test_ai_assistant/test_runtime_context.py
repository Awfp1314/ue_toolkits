# -*- coding: utf-8 -*-

"""
RuntimeContextManager 单元测试
验证状态管理和持久化功能
"""

import pytest
import sys
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modules.ai_assistant.logic.runtime_context import RuntimeContextManager


@pytest.fixture
def temp_dir():
    """临时目录 fixture"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def runtime_context(temp_dir):
    """创建 RuntimeContextManager 实例"""
    return RuntimeContextManager(user_data_dir=temp_dir)


class TestRuntimeContextManager:
    """RuntimeContextManager 测试套件"""
    
    def test_initialization(self, runtime_context):
        """测试初始化"""
        assert runtime_context is not None
        assert runtime_context.current_module is None
        assert runtime_context.selected_asset is None
        assert runtime_context.recent_ops == []
    
    def test_set_current_module(self, runtime_context):
        """测试设置当前模块"""
        runtime_context.set_current_module("asset_manager")
        
        assert runtime_context.current_module == "asset_manager"
        
        # 应该自动记录操作
        assert len(runtime_context.recent_ops) > 0
        assert runtime_context.recent_ops[-1]['action'] == "switch_module"
    
    def test_set_selected_asset(self, runtime_context):
        """测试设置选中资产"""
        asset_info = {
            'name': '测试资产',
            'type': 'blueprint',
            'path': '/test/path'
        }
        
        runtime_context.set_selected_asset(asset_info)
        
        assert runtime_context.selected_asset is not None
        assert runtime_context.selected_asset['name'] == '测试资产'
    
    def test_record_operation(self, runtime_context):
        """测试操作记录"""
        runtime_context.record_op("test_action", {"param": "value"})
        
        assert len(runtime_context.recent_ops) > 0
        
        last_op = runtime_context.recent_ops[-1]
        assert last_op['action'] == "test_action"
        assert last_op['details']['param'] == "value"
        assert 'timestamp' in last_op
    
    def test_snapshot(self, runtime_context):
        """测试快照功能"""
        runtime_context.set_current_module("config_tool")
        runtime_context.set_selected_asset({'name': '资产1'})
        runtime_context.record_op("search", {})
        
        snapshot = runtime_context.snapshot()
        
        assert snapshot['current_module'] == "config_tool"
        assert snapshot['selected_asset']['name'] == '资产1'
        assert len(snapshot['recent_ops']) > 0
        assert 'timestamp' in snapshot
    
    def test_persistence(self, temp_dir):
        """测试持久化保存与恢复"""
        # 创建第一个实例并设置状态
        ctx1 = RuntimeContextManager(user_data_dir=temp_dir)
        ctx1.set_current_module("ai_assistant")
        ctx1.set_selected_asset({'name': '资产A', 'type': 'material'})
        
        # 验证缓存文件存在
        cache_file = temp_dir / "runtime_context.json"
        assert cache_file.exists(), "缓存文件应该被创建"
        
        # 读取缓存文件验证格式
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['current_module'] == "ai_assistant"
        assert data['selected_asset']['name'] == '资产A'
        
        # 创建第二个实例，应该自动恢复状态
        ctx2 = RuntimeContextManager(user_data_dir=temp_dir)
        
        assert ctx2.current_module == "ai_assistant"
        assert ctx2.selected_asset['name'] == '资产A'
    
    def test_exception_safety_on_load(self, temp_dir):
        """测试读取失败时的异常安全"""
        # 创建损坏的缓存文件
        cache_file = temp_dir / "runtime_context.json"
        with open(cache_file, 'w') as f:
            f.write("invalid json{{{")
        
        # 应该不抛出异常，使用默认值
        ctx = RuntimeContextManager(user_data_dir=temp_dir)
        
        assert ctx.current_module is None  # 应使用默认值
    
    def test_get_formatted_snapshot(self, runtime_context):
        """测试格式化快照输出"""
        runtime_context.set_current_module("asset_manager")
        runtime_context.set_selected_asset({'name': '测试资产', 'type': 'blueprint'})
        runtime_context.record_op("search", {})
        runtime_context.record_op("open", {})
        
        formatted = runtime_context.get_formatted_snapshot()
        
        assert isinstance(formatted, str)
        assert "asset_manager" in formatted
        assert "测试资产" in formatted
        assert "最近操作" in formatted or len(formatted) > 0
    
    def test_clear(self, runtime_context):
        """测试清空状态"""
        runtime_context.set_current_module("test")
        runtime_context.set_selected_asset({'name': 'test'})
        
        runtime_context.clear()
        
        assert runtime_context.current_module is None
        assert runtime_context.selected_asset is None
        assert runtime_context.recent_ops == []


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

