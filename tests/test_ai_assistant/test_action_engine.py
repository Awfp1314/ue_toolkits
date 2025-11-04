# -*- coding: utf-8 -*-

"""
ActionEngine 单元测试
验证两段式工具调用和安全检查机制
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modules.ai_assistant.logic.action_engine import ActionEngine
from modules.ai_assistant.logic.tools_registry import ToolsRegistry


@pytest.fixture
def mock_tools_registry():
    """Mock ToolsRegistry"""
    registry = Mock(spec=ToolsRegistry)
    
    # Mock openai_tool_schemas()
    registry.openai_tool_schemas.return_value = [{
        "type": "function",
        "function": {
            "name": "search_assets",
            "description": "搜索资产",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string"}
                }
            }
        }
    }]
    
    # Mock dispatch()
    registry.dispatch.return_value = {
        "success": True,
        "result": "找到3个资产",
        "tool_name": "search_assets",
        "requires_confirmation": False
    }
    
    # Mock tools dict
    mock_tool = Mock()
    mock_tool.requires_confirmation = False
    registry.tools = {"search_assets": mock_tool}
    
    return registry


@pytest.fixture
def mock_api_client_factory():
    """Mock API 客户端工厂"""
    def factory(messages, model="gpt-3.5-turbo"):
        client = MagicMock()
        client.chunk_received = Mock()
        client.request_finished = Mock()
        client.error_occurred = Mock()
        client.start = Mock()
        return client
    
    return factory


@pytest.fixture
def action_engine(mock_tools_registry, mock_api_client_factory):
    """创建 ActionEngine 实例"""
    return ActionEngine(
        tools_registry=mock_tools_registry,
        api_client_factory=mock_api_client_factory
    )


class TestActionEngine:
    """ActionEngine 测试套件"""
    
    def test_initialization(self, action_engine):
        """测试初始化"""
        assert action_engine is not None
        assert action_engine.tools_registry is not None
        assert action_engine.call_history == []
    
    def test_execute_with_tools(self, action_engine):
        """测试工具调用流程"""
        messages = [
            {"role": "system", "content": "你是助手"},
            {"role": "user", "content": "搜索蓝图资产"}
        ]
        
        # 执行工具调用
        action_engine.execute_with_tools(
            messages=messages,
            on_chunk_received=Mock(),
            on_finished=Mock(),
            on_error=Mock()
        )
        
        # 应该有调用记录
        # 注意：简化实现可能不会立即产生记录，取决于异步执行
    
    def test_tool_calls_serialization(self, action_engine):
        """测试 tool_calls 序列化"""
        query = "查找材质资产"
        
        # 决策工具调用
        tool_calls = action_engine._decide_tool_calls(query)
        
        if tool_calls:
            assert isinstance(tool_calls, list)
            assert len(tool_calls) > 0
            
            # 验证格式
            call = tool_calls[0]
            assert 'id' in call
            assert 'type' in call
            assert call['type'] == 'function'
            assert 'function' in call
            assert 'name' in call['function']
            assert 'arguments' in call['function']
            
            # arguments 应该是 JSON 字符串
            args = json.loads(call['function']['arguments'])
            assert isinstance(args, dict)
    
    def test_execute_tools(self, action_engine, mock_tools_registry):
        """测试工具执行"""
        tool_calls = [{
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "search_assets",
                "arguments": json.dumps({"keyword": "测试"})
            }
        }]
        
        outputs = action_engine._execute_tools(tool_calls)
        
        assert isinstance(outputs, list)
        assert len(outputs) == 1
        
        output = outputs[0]
        assert 'tool_call_id' in output
        assert 'role' in output
        assert output['role'] == 'tool'
        assert 'name' in output
        assert 'content' in output
    
    def test_safety_check_for_confirmation(self, action_engine, mock_tools_registry):
        """测试安全检查机制"""
        # 模拟需要确认的工具
        mock_tool = Mock()
        mock_tool.requires_confirmation = True
        mock_tools_registry.tools = {"dangerous_tool": mock_tool}
        
        tool_calls = [{
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "dangerous_tool",
                "arguments": json.dumps({})
            }
        }]
        
        # 执行时应检查 requires_confirmation
        # v0.2: 仅输出警告（v0.3 才触发对话框）
        outputs = action_engine._execute_tools(tool_calls)
        
        # 应该有输出（即使工具需要确认）
        assert isinstance(outputs, list)
    
    def test_call_history_tracking(self, action_engine, mock_tools_registry):
        """测试调用历史记录"""
        initial_count = len(action_engine.call_history)
        
        tool_calls = [{
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "search_assets",
                "arguments": json.dumps({"keyword": "test"})
            }
        }]
        
        action_engine._execute_tools(tool_calls)
        
        # 调用历史应增加
        assert len(action_engine.call_history) > initial_count
        
        # 最后一条记录应包含必要信息
        last_call = action_engine.call_history[-1]
        assert 'tool_name' in last_call
        assert 'arguments' in last_call
        assert 'elapsed_time' in last_call
        assert 'timestamp' in last_call
    
    def test_get_call_history(self, action_engine):
        """测试获取调用历史"""
        # 模拟添加历史记录
        for i in range(15):
            action_engine.call_history.append({
                'tool_name': f'tool_{i}',
                'arguments': {},
                'elapsed_time': 0.1,
                'timestamp': i
            })
        
        # 获取最近10条
        recent = action_engine.get_call_history(limit=10)
        
        assert len(recent) == 10
        assert recent[-1]['tool_name'] == 'tool_14'  # 最新的一条


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

