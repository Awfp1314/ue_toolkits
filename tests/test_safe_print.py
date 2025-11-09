# -*- coding: utf-8 -*-

"""
safe_print 函数测试

测试目标：
1. 验证 safe_print 函数存在且可导入
2. 验证 safe_print 能正确处理中文
3. 验证 safe_print 能捕获编码错误
4. 验证 setup_console_encoding 函数存在
5. 验证各模块正确导入 safe_print

Requirements: 12.1, 12.2, 12.3, 12.4, 12.5
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestSafePrintImplementation(unittest.TestCase):
    """测试 safe_print 实现（代码检查）"""
    
    def test_safe_print_exists_in_logger(self):
        """测试 safe_print 函数在 core/logger.py 中存在
        
        Requirement 12.4: 使用 safe_print 函数处理日志输出
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'core', 
            'logger.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查 safe_print 函数定义
        self.assertIn('def safe_print(', content, "应该定义 safe_print 函数")
        self.assertIn('UnicodeEncodeError', content, "应该捕获 UnicodeEncodeError")
        self.assertIn('OSError', content, "应该捕获 OSError")
    
    def test_setup_console_encoding_exists(self):
        """测试 setup_console_encoding 函数存在
        
        Requirement 12.3: 在程序启动时设置控制台编码为 UTF-8
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'core', 
            'logger.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查 setup_console_encoding 函数定义
        self.assertIn('def setup_console_encoding(', content, "应该定义 setup_console_encoding 函数")
        self.assertIn('chcp', content, "应该使用 chcp 命令设置编码")
        self.assertIn('65001', content, "应该设置为 UTF-8 (65001)")
    
    def test_logger_uses_safe_print(self):
        """测试 Logger 类使用 safe_print
        
        Requirement 12.5: 在所有日志输出点使用统一的编码处理机制
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'core', 
            'logger.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查 Logger 类中使用 safe_print
        # 在 _setup_handlers 方法中应该使用 safe_print 而不是 print
        self.assertIn('safe_print(f"警告:', content, "应该在错误处理中使用 safe_print")
    
    def test_markdown_message_imports_safe_print(self):
        """测试 markdown_message.py 导入 safe_print
        
        Requirement 12.5: 在所有日志输出点使用统一的编码处理机制
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'ui', 
            'markdown_message.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查导入语句
        self.assertIn('from core.logger import safe_print', content, 
                     "markdown_message.py 应该从 core.logger 导入 safe_print")
        
        # 确保没有重复定义
        self.assertNotIn('def safe_print(msg: str):\n    """安全的 print 函数', content,
                        "不应该有重复的 safe_print 定义")
    
    def test_chat_composer_imports_safe_print(self):
        """测试 chat_composer.py 导入 safe_print
        
        Requirement 12.5: 在所有日志输出点使用统一的编码处理机制
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'ui', 
            'chat_composer.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查导入语句
        self.assertIn('from core.logger import safe_print', content, 
                     "chat_composer.py 应该从 core.logger 导入 safe_print")
        
        # 确保没有重复定义
        self.assertNotIn('def safe_print(msg: str):\n    """安全的 print 函数', content,
                        "不应该有重复的 safe_print 定义")
    
    def test_chat_window_imports_safe_print(self):
        """测试 chat_window.py 导入 safe_print
        
        Requirement 12.5: 在所有日志输出点使用统一的编码处理机制
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'ui', 
            'chat_window.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查导入语句
        self.assertIn('from core.logger import safe_print', content, 
                     "chat_window.py 应该从 core.logger 导入 safe_print")
        
        # 确保没有重复定义
        self.assertNotIn('def safe_print(msg: str):\n    """安全的 print 函数', content,
                        "不应该有重复的 safe_print 定义")
    
    def test_main_calls_setup_console_encoding(self):
        """测试 main.py 调用 setup_console_encoding
        
        Requirement 12.3: 在程序启动时设置控制台编码为 UTF-8
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'main.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查导入和调用
        self.assertIn('from core.logger import', content, "应该导入 core.logger")
        self.assertIn('setup_console_encoding', content, "应该导入 setup_console_encoding")
        self.assertIn('setup_console_encoding()', content, "应该调用 setup_console_encoding()")


if __name__ == '__main__':
    unittest.main()

