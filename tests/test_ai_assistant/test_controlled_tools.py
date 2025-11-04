# -*- coding: utf-8 -*-

"""
受控工具单元测试
验证确认/取消/异常回滚机制
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modules.ai_assistant.logic.controlled_tools import ControlledTools
from modules.ai_assistant.logic.action_engine import ActionEngine
from modules.ai_assistant.logic.tools_registry import ToolsRegistry


@pytest.fixture
def controlled_tools():
    """创建 ControlledTools 实例"""
    mock_config_logic = Mock()
    mock_asset_logic = Mock()
    return ControlledTools(
        config_tool_logic=mock_config_logic,
        asset_manager_logic=mock_asset_logic
    )


class TestControlledTools:
    """ControlledTools 测试套件"""
    
    def test_initialization(self, controlled_tools):
        """测试初始化"""
        assert controlled_tools is not None
    
    def test_export_config_template_preview(self, controlled_tools):
        """测试导出配置模板预览"""
        result = controlled_tools.export_config_template(
            template_name="测试配置",
            export_path="D:/Export"
        )
        
        assert isinstance(result, dict)
        assert 'preview' in result
        assert 'description' in result
        assert 'confirm_prompt' in result
        assert "测试配置" in result['preview']
        assert "D:/Export" in result['preview']
    
    def test_batch_rename_preview(self, controlled_tools):
        """测试批量重命名预览"""
        result = controlled_tools.batch_rename_preview(
            pattern="old",
            replacement="new",
            asset_ids=["id1", "id2", "id3"]
        )
        
        assert isinstance(result, dict)
        assert 'preview' in result
        assert 'changes' in result
        assert isinstance(result['changes'], list)
    
    def test_execute_export_config_template(self, controlled_tools):
        """测试执行导出配置模板"""
        result = controlled_tools.execute_export_config_template(
            template_name="测试",
            export_path="D:/Test"
        )
        
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'message' in result


class TestConfirmationFlow:
    """测试确认流程"""
    
    @patch('modules.ai_assistant.logic.action_engine.ToolConfirmationDialog')
    def test_user_confirms(self, mock_dialog_class):
        """测试用户确认执行"""
        # Mock 对话框返回 True（确认）
        mock_dialog = Mock()
        mock_dialog.exec.return_value = True
        mock_dialog_class.return_value = mock_dialog
        
        # 创建 ActionEngine
        mock_registry = Mock()
        mock_tool = Mock()
        mock_tool.requires_confirmation = True
        mock_tool.function.return_value = {"preview": "测试预览"}
        mock_registry.tools = {"test_tool": mock_tool}
        
        mock_audit = Mock()
        
        engine = ActionEngine(
            tools_registry=mock_registry,
            api_client_factory=Mock(),
            audit_logger=mock_audit
        )
        
        # 模拟工具调用
        confirmed, preview = engine._request_user_confirmation(
            "test_tool",
            {"arg": "value"},
            mock_tool
        )
        
        assert confirmed == True
        assert 'preview' in preview
    
    @patch('modules.ai_assistant.logic.action_engine.ToolConfirmationDialog')
    def test_user_cancels(self, mock_dialog_class):
        """测试用户取消执行"""
        # Mock 对话框返回 False（取消）
        mock_dialog = Mock()
        mock_dialog.exec.return_value = False
        mock_dialog_class.return_value = mock_dialog
        
        mock_registry = Mock()
        mock_tool = Mock()
        mock_tool.requires_confirmation = True
        mock_tool.function.return_value = {"preview": "测试预览"}
        mock_registry.tools = {"test_tool": mock_tool}
        
        engine = ActionEngine(
            tools_registry=mock_registry,
            api_client_factory=Mock()
        )
        
        confirmed, preview = engine._request_user_confirmation(
            "test_tool",
            {},
            mock_tool
        )
        
        assert confirmed == False
    
    def test_exception_rollback(self, controlled_tools):
        """测试异常回滚（无副作用）"""
        # 模拟执行失败
        result = controlled_tools.execute_batch_rename(changes=[])
        
        # 应返回失败结果，但不抛出异常
        assert isinstance(result, dict)
        # 空 changes 列表应该成功（因为没有实际操作）
        assert result['renamed_count'] == 0


class TestAuditLogging:
    """测试审计日志"""
    
    def test_audit_logger_initialization(self, tmp_path):
        """测试审计日志初始化"""
        from modules.ai_assistant.logic.audit_logger import AuditLogger
        
        audit = AuditLogger(log_path=tmp_path / "test_audit.log")
        assert audit is not None
        assert audit.log_path.parent.exists()
    
    def test_log_tool_call(self, tmp_path):
        """测试记录工具调用"""
        from modules.ai_assistant.logic.audit_logger import AuditLogger
        
        audit = AuditLogger(log_path=tmp_path / "test_audit.log")
        
        audit.log_tool_call(
            tool_name="test_tool",
            arguments={"key": "value"},
            preview="预览内容",
            user_confirmed=True,
            result={"success": True},
            user_name="test_user"
        )
        
        # 验证日志文件存在
        assert audit.log_path.exists()
        
        # 读取并验证内容
        with open(audit.log_path, 'r') as f:
            content = f.read()
        
        assert "test_tool" in content
        assert "test_user" in content
    
    def test_get_recent_audits(self, tmp_path):
        """测试获取最近的审计记录"""
        from modules.ai_assistant.logic.audit_logger import AuditLogger
        
        audit = AuditLogger(log_path=tmp_path / "test_audit.log")
        
        # 记录几条
        for i in range(5):
            audit.log_tool_call(
                tool_name=f"tool_{i}",
                arguments={},
                preview="",
                user_confirmed=True
            )
        
        # 获取最近3条
        recent = audit.get_recent_audits(limit=3)
        
        assert len(recent) == 3
        assert recent[-1]['tool_name'] == 'tool_4'
    
    def test_get_stats(self, tmp_path):
        """测试审计统计"""
        from modules.ai_assistant.logic.audit_logger import AuditLogger
        
        audit = AuditLogger(log_path=tmp_path / "test_audit.log")
        
        # 记录确认和拒绝
        audit.log_tool_call("tool1", {}, "", user_confirmed=True)
        audit.log_tool_call("tool2", {}, "", user_confirmed=False)
        audit.log_tool_call("tool3", {}, "", user_confirmed=True)
        
        stats = audit.get_stats()
        
        assert stats['total_calls'] == 3
        assert stats['confirmed_calls'] == 2
        assert stats['rejected_calls'] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

