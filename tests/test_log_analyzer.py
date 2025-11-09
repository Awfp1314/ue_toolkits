# -*- coding: utf-8 -*-

"""
测试日志分析器的文件读取优化
"""

import pytest
import tempfile
from pathlib import Path
from collections import deque


def test_deque_memory_efficiency():
    """测试 deque 的内存效率（不依赖 LogAnalyzer）"""
    # 模拟读取大文件，只保留最后 100 行
    max_lines = 100
    lines_deque = deque(maxlen=max_lines)
    
    # 模拟读取 10000 行
    for i in range(10000):
        lines_deque.append(f"Line {i}")
    
    # 验证只保留了最后 100 行
    result = list(lines_deque)
    assert len(result) == 100
    assert result[0] == "Line 9900"
    assert result[-1] == "Line 9999"


def test_read_last_n_lines_basic():
    """测试基本的读取最后 N 行功能（不依赖 LogAnalyzer）"""
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.log') as f:
        temp_path = Path(f.name)
        # 写入 100 行
        for i in range(100):
            f.write(f"Line {i}\n")
    
    try:
        # 使用 deque 读取最后 10 行
        max_lines = 10
        lines_deque = deque(maxlen=max_lines)
        
        with open(temp_path, 'r', encoding='utf-8') as f:
            for line in f:
                lines_deque.append(line.rstrip('\n\r'))
        
        lines = list(lines_deque)
        
        assert len(lines) == 10
        assert lines[0] == "Line 90"
        assert lines[-1] == "Line 99"
    finally:
        temp_path.unlink()


def test_read_last_n_lines_less_than_n():
    """测试文件行数少于 N 的情况"""
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.log') as f:
        temp_path = Path(f.name)
        # 只写入 5 行
        for i in range(5):
            f.write(f"Line {i}\n")
    
    try:
        # 尝试读取 10 行
        max_lines = 10
        lines_deque = deque(maxlen=max_lines)
        
        with open(temp_path, 'r', encoding='utf-8') as f:
            for line in f:
                lines_deque.append(line.rstrip('\n\r'))
        
        lines = list(lines_deque)
        
        # 应该只返回 5 行
        assert len(lines) == 5
        assert lines[0] == "Line 0"
        assert lines[-1] == "Line 4"
    finally:
        temp_path.unlink()


def test_read_large_file_memory_efficiency():
    """测试读取大文件时的内存效率"""
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.log') as f:
        temp_path = Path(f.name)
        # 写入 10000 行
        for i in range(10000):
            f.write(f"Line {i}\n")
    
    try:
        # 只读取最后 100 行
        max_lines = 100
        lines_deque = deque(maxlen=max_lines)
        
        with open(temp_path, 'r', encoding='utf-8') as f:
            for line in f:
                lines_deque.append(line.rstrip('\n\r'))
        
        lines = list(lines_deque)
        
        # 验证只保留了最后 100 行
        assert len(lines) == 100
        assert lines[0] == "Line 9900"
        assert lines[-1] == "Line 9999"
    finally:
        temp_path.unlink()


class TestLogAnalyzer:
    """测试 LogAnalyzer 的优化功能"""

    @pytest.fixture
    def analyzer(self):
        """创建 LogAnalyzer 实例的 fixture"""
        # 延迟导入，避免初始化问题
        from unittest.mock import Mock, patch, MagicMock

        # Mock PathUtils and ConfigManager to avoid file system dependencies
        with patch('modules.ai_assistant.logic.log_analyzer.PathUtils') as mock_path_utils_class, \
             patch('modules.ai_assistant.logic.log_analyzer.ConfigManager') as mock_config_class:

            # Create mock instances
            mock_path_utils = MagicMock()
            mock_path_utils.get_user_logs_dir.return_value = Path(tempfile.gettempdir())
            mock_path_utils_class.return_value = mock_path_utils

            mock_config = MagicMock()
            mock_config.get_module_config.return_value = {
                'log_analyzer': {'max_log_lines': 1000}
            }
            mock_config_class.return_value = mock_config

            from modules.ai_assistant.logic.log_analyzer import LogAnalyzer
            analyzer = LogAnalyzer()

            # Yield the analyzer so it can be used in tests
            yield analyzer
    
    def test_read_last_n_lines_basic(self, analyzer):
        """测试基本的读取最后 N 行功能"""
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.log') as f:
            temp_path = Path(f.name)
            # 写入 100 行
            for i in range(100):
                f.write(f"Line {i}\n")
        
        try:
            # 读取最后 10 行
            lines = analyzer.read_last_n_lines(temp_path, 10)
            
            assert len(lines) == 10
            assert lines[0] == "Line 90"
            assert lines[-1] == "Line 99"
        finally:
            temp_path.unlink()
    
    def test_read_last_n_lines_less_than_n(self, analyzer):
        """测试文件行数少于 N 的情况"""
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.log') as f:
            temp_path = Path(f.name)
            # 只写入 5 行
            for i in range(5):
                f.write(f"Line {i}\n")
        
        try:
            # 尝试读取 10 行
            lines = analyzer.read_last_n_lines(temp_path, 10)
            
            # 应该只返回 5 行
            assert len(lines) == 5
            assert lines[0] == "Line 0"
            assert lines[-1] == "Line 4"
        finally:
            temp_path.unlink()
    
    def test_read_last_n_lines_memory_efficiency(self, analyzer):
        """测试使用 deque 的内存效率"""
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.log') as f:
            temp_path = Path(f.name)
            # 写入 10000 行
            for i in range(10000):
                f.write(f"Line {i}\n")
        
        try:
            # 只读取最后 100 行
            lines = analyzer.read_last_n_lines(temp_path, 100)
            
            # 验证只保留了最后 100 行
            assert len(lines) == 100
            assert lines[0] == "Line 9900"
            assert lines[-1] == "Line 9999"
        finally:
            temp_path.unlink()
    
    def test_read_last_n_lines_file_not_found(self, analyzer):
        """测试文件不存在的错误处理"""
        
        with pytest.raises(FileNotFoundError):
            analyzer.read_last_n_lines(Path("/nonexistent/file.log"), 10)
    
    def test_read_last_n_lines_default_max_lines(self, analyzer):
        """测试使用默认的 max_log_lines 配置"""
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.log') as f:
            temp_path = Path(f.name)
            # 写入 2000 行
            for i in range(2000):
                f.write(f"Line {i}\n")
        
        try:
            # 不指定 n，应该使用 max_log_lines（默认 1000）
            lines = analyzer.read_last_n_lines(temp_path)
            
            # 应该只返回最后 1000 行
            assert len(lines) == analyzer.max_log_lines
            assert lines[0] == f"Line {2000 - analyzer.max_log_lines}"
            assert lines[-1] == "Line 1999"
        finally:
            temp_path.unlink()
    
    def test_config_max_log_lines(self, analyzer):
        """测试从配置读取 max_log_lines"""
        
        # 验证配置已加载
        assert hasattr(analyzer, 'max_log_lines')
        assert isinstance(analyzer.max_log_lines, int)
        assert analyzer.max_log_lines > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
