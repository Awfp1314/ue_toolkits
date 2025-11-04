# -*- coding: utf-8 -*-

"""
ToolsRegistry 单元测试
验证工具注册、schema 生成和调度
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modules.ai_assistant.logic.tools_registry import ToolsRegistry, ToolDefinition


@pytest.fixture
def mock_readers():
    """Mock 数据读取器"""
    return {
        'asset_reader': Mock(),
        'config_reader': Mock(),
        'log_analyzer': Mock(),
        'document_reader': Mock()
    }


@pytest.fixture
def tools_registry(mock_readers):
    """创建 ToolsRegistry 实例"""
    return ToolsRegistry(**mock_readers)


class TestToolsRegistry:
    """ToolsRegistry 测试套件"""
    
    def test_initialization(self, tools_registry):
        """测试初始化"""
        assert tools_registry is not None
        assert len(tools_registry.tools) == 6  # 6个只读工具
    
    def test_registered_tools(self, tools_registry):
        """测试工具注册"""
        expected_tools = [
            "search_assets",
            "query_asset_detail",
            "search_configs",
            "diff_config",
            "search_logs",
            "search_docs"
        ]
        
        for tool_name in expected_tools:
            assert tool_name in tools_registry.tools
            tool = tools_registry.tools[tool_name]
            assert isinstance(tool, ToolDefinition)
            assert tool.requires_confirmation == False  # 只读工具不需要确认
    
    def test_openai_tool_schemas(self, tools_registry):
        """测试 OpenAI tools schema 生成"""
        schemas = tools_registry.openai_tool_schemas()
        
        assert isinstance(schemas, list)
        assert len(schemas) == 6
        
        # 验证 schema 格式符合 OpenAI 规范
        for schema in schemas:
            assert schema['type'] == 'function'
            assert 'function' in schema
            assert 'name' in schema['function']
            assert 'description' in schema['function']
            assert 'parameters' in schema['function']
            
            # 验证 parameters 是 JSON Schema 格式
            params = schema['function']['parameters']
            assert 'type' in params
            assert params['type'] == 'object'
            assert 'properties' in params
    
    def test_dispatch_search_assets(self, tools_registry, mock_readers):
        """测试工具调度 - 搜索资产"""
        # Mock 返回值
        mock_readers['asset_reader'].search_assets.return_value = "找到3个资产"
        
        # 调度工具
        result = tools_registry.dispatch("search_assets", {"keyword": "蓝图"})
        
        # 验证结果
        assert result['success'] == True
        assert result['tool_name'] == "search_assets"
        assert result['requires_confirmation'] == False
        assert "找到3个资产" in result['result']
        
        # 验证 mock 被调用
        mock_readers['asset_reader'].search_assets.assert_called_once_with(keyword="蓝图")
    
    def test_dispatch_unknown_tool(self, tools_registry):
        """测试调度未知工具"""
        result = tools_registry.dispatch("unknown_tool", {})
        
        assert result['success'] == False
        assert 'error' in result
        assert "未知工具" in result['error']
    
    def test_permission_declaration(self, tools_registry):
        """测试权限声明字段"""
        for tool_name, tool_def in tools_registry.tools.items():
            # v0.2: 所有只读工具的 requires_confirmation 应为 False
            assert hasattr(tool_def, 'requires_confirmation')
            assert tool_def.requires_confirmation == False, \
                f"只读工具 {tool_name} 不应需要确认"
    
    def test_custom_tool_registration(self):
        """测试自定义工具注册"""
        registry = ToolsRegistry()
        
        def custom_func(arg1, arg2):
            return f"执行自定义工具: {arg1}, {arg2}"
        
        custom_tool = ToolDefinition(
            name="custom_tool",
            description="自定义测试工具",
            parameters={
                "type": "object",
                "properties": {
                    "arg1": {"type": "string"},
                    "arg2": {"type": "string"}
                },
                "required": ["arg1", "arg2"]
            },
            function=custom_func,
            requires_confirmation=True  # 需要确认
        )
        
        registry.register_tool(custom_tool)
        
        assert "custom_tool" in registry.tools
        assert registry.tools["custom_tool"].requires_confirmation == True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

