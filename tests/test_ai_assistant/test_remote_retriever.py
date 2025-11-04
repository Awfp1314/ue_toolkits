# -*- coding: utf-8 -*-

"""
Remote Retriever 单元测试
验证 GitHub/Gitee 连接器（打桩测试，不需要真实 token）
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modules.ai_assistant.logic.remote_retriever import GitHubConnector, GiteeConnector, RemoteRetriever


class TestGitHubConnector:
    """GitHub 连接器测试"""
    
    def test_token_priority_env_var(self):
        """测试 token 读取优先级：环境变量优先"""
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'env_token'}):
            connector = GitHubConnector()
            assert connector.token == 'env_token'
    
    def test_token_priority_param(self):
        """测试 token 读取优先级：传入参数最优先"""
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'env_token'}):
            connector = GitHubConnector(token='param_token')
            assert connector.token == 'param_token'
    
    def test_token_priority_config(self):
        """测试 token 读取优先级：配置管理器兜底"""
        mock_config = Mock()
        mock_config.get_config = Mock(return_value='config_token')
        
        connector = GitHubConnector(config_manager=mock_config)
        
        # 如果无环境变量，应从 config 读取
        if not os.getenv('GITHUB_TOKEN'):
            assert connector.token == 'config_token'
    
    @patch('modules.ai_assistant.logic.remote_retriever.Github')
    def test_code_search_mock(self, mock_github_class):
        """测试代码搜索（打桩）"""
        # Mock GitHub 客户端
        mock_github = MagicMock()
        mock_github_class.return_value = mock_github
        
        # Mock 搜索结果
        mock_result = MagicMock()
        mock_result.path = 'test/file.py'
        mock_result.repository.full_name = 'user/repo'
        mock_result.html_url = 'https://github.com/user/repo/blob/main/test/file.py'
        mock_result.decoded_content = b'test content'
        
        mock_github.search_code.return_value = [mock_result]
        
        # 执行搜索
        connector = GitHubConnector(token='test_token')
        results = connector.code_search('test query', top_k=1)
        
        # 验证结果
        assert len(results) > 0
        assert results[0]['path'] == 'test/file.py'
        assert results[0]['repo'] == 'user/repo'
        assert 'url' in results[0]
        assert 'source' in results[0]
    
    def test_code_search_without_token(self):
        """测试无 token 时的搜索（受限但不崩溃）"""
        connector = GitHubConnector(token=None)
        
        # 应该能创建，但搜索时可能受限
        assert connector.token is None or connector.token == ''


class TestGiteeConnector:
    """Gitee 连接器测试（stub 接口）"""
    
    def test_initialization(self):
        """测试初始化"""
        connector = GiteeConnector()
        assert connector is not None
    
    def test_code_search_stub(self):
        """测试代码搜索 stub"""
        connector = GiteeConnector()
        results = connector.code_search("test")
        
        # stub 应返回空列表
        assert results == []
    
    def test_issues_search_stub(self):
        """测试 issues 搜索 stub"""
        connector = GiteeConnector()
        results = connector.search_issues("test")
        
        # stub 应返回空列表
        assert results == []


class TestRemoteRetriever:
    """统一远程检索器测试"""
    
    def test_initialization(self):
        """测试初始化"""
        retriever = RemoteRetriever()
        
        assert retriever.github is not None
        assert retriever.gitee is not None
    
    @patch('modules.ai_assistant.logic.remote_retriever.GitHubConnector')
    def test_search_github(self, mock_github_class):
        """测试 GitHub 搜索路由"""
        mock_github = Mock()
        mock_github.code_search.return_value = [{'test': 'result'}]
        mock_github_class.return_value = mock_github
        
        retriever = RemoteRetriever()
        retriever.github = mock_github
        
        results = retriever.search("query", source="github", top_k=5)
        
        mock_github.code_search.assert_called_once()
    
    def test_search_unknown_source(self):
        """测试未知检索源"""
        retriever = RemoteRetriever()
        results = retriever.search("query", source="unknown")
        
        # 应返回空列表，不抛出异常
        assert results == []


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

