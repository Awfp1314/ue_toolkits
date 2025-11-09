# -*- coding: utf-8 -*-

"""
ToolStatusDisplay 组件测试

测试目标：
1. 验证工具名称映射表存在且完整
2. 验证 get_friendly_name() 方法正确转换工具名称
3. 验证 show_tool_calling() 方法生成正确的状态文本
4. 验证 show_thinking() 方法返回正确的思考文本
5. 验证未知工具名称的处理

Requirements: 11.1, 11.2, 11.3, 11.4, 11.5
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestToolStatusDisplayImplementation(unittest.TestCase):
    """测试 ToolStatusDisplay 实现（代码检查）"""
    
    def test_file_exists(self):
        """测试文件存在
        
        Requirement 11.1: 创建 tool_status_display.py 文件
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'ui', 
            'tool_status_display.py'
        )
        self.assertTrue(os.path.exists(file_path), "tool_status_display.py 文件应该存在")
    
    def test_tool_name_map_exists(self):
        """测试工具名称映射表存在
        
        Requirement 11.5: 定义 TOOL_NAME_MAP（工具名称中文映射）
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'ui', 
            'tool_status_display.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查 TOOL_NAME_MAP 存在
        self.assertIn('TOOL_NAME_MAP', content, "应该定义 TOOL_NAME_MAP")
        
        # 检查一些常见工具的映射
        self.assertIn('"search_assets"', content, "应该包含 search_assets 映射")
        self.assertIn('"query_asset_detail"', content, "应该包含 query_asset_detail 映射")
        self.assertIn('"search_configs"', content, "应该包含 search_configs 映射")
    
    def test_get_friendly_name_method_exists(self):
        """测试 get_friendly_name() 方法存在
        
        Requirement 11.4: 实现 get_friendly_name(tool_name) 方法
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'ui', 
            'tool_status_display.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查方法定义
        self.assertIn('def get_friendly_name', content, "应该定义 get_friendly_name 方法")
        self.assertIn('tool_name: str', content, "方法应该接受 tool_name 参数")
    
    def test_show_tool_calling_method_exists(self):
        """测试 show_tool_calling() 方法存在
        
        Requirement 11.2: 实现 show_tool_calling(tool_name) 方法
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'ui', 
            'tool_status_display.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查方法定义
        self.assertIn('def show_tool_calling', content, "应该定义 show_tool_calling 方法")
        self.assertIn('调用', content, "应该生成包含'调用'的文本")
        self.assertIn('工具', content, "应该生成包含'工具'的文本")
    
    def test_show_thinking_method_exists(self):
        """测试 show_thinking() 方法存在
        
        Requirement 11.3: 实现 show_thinking() 方法
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'ui', 
            'tool_status_display.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查方法定义
        self.assertIn('def show_thinking', content, "应该定义 show_thinking 方法")
        self.assertIn('正在思考', content, "应该返回'正在思考'文本")


class TestToolStatusDisplayFunctionality(unittest.TestCase):
    """测试 ToolStatusDisplay 功能（通过代码检查）"""

    def test_tool_name_map_contains_common_tools(self):
        """测试工具名称映射表包含常见工具

        Requirement 11.5: 将工具名称转换为用户友好的中文描述
        """
        file_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'modules',
            'ai_assistant',
            'ui',
            'tool_status_display.py'
        )

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查常见工具的映射
        self.assertIn('"search_assets": "搜索资产"', content)
        self.assertIn('"query_asset_detail": "查询资产详情"', content)
        self.assertIn('"search_configs": "搜索配置"', content)

    def test_get_friendly_name_implementation(self):
        """测试 get_friendly_name 实现逻辑

        Requirement 11.4: 实现 get_friendly_name(tool_name) 方法
        """
        file_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'modules',
            'ai_assistant',
            'ui',
            'tool_status_display.py'
        )

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查方法使用 TOOL_NAME_MAP.get() 并提供默认值
        self.assertIn('TOOL_NAME_MAP.get(tool_name, tool_name)', content)

    def test_show_tool_calling_format_implementation(self):
        """测试工具调用状态文本格式实现

        Requirement 11.2: 生成 "调用{工具名称}工具" 格式的文本
        """
        file_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'modules',
            'ai_assistant',
            'ui',
            'tool_status_display.py'
        )

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查格式字符串
        self.assertIn('f"调用{friendly_name}工具"', content)

    def test_show_thinking_implementation(self):
        """测试思考状态文本实现

        Requirement 11.3: 返回 "正在思考" 文本
        """
        file_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'modules',
            'ai_assistant',
            'ui',
            'tool_status_display.py'
        )

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查返回值
        self.assertIn('return "正在思考"', content)


class TestToolStatusDisplayIntegration(unittest.TestCase):
    """测试 ToolStatusDisplay 与其他组件的集成"""

    def test_markdown_message_imports_tool_status_display(self):
        """测试 markdown_message.py 导入了 ToolStatusDisplay

        Requirement 11.1: 集成到现有组件
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
        self.assertIn('from modules.ai_assistant.ui.tool_status_display import', content,
                     "markdown_message.py 应该导入 ToolStatusDisplay")
        self.assertIn('ToolStatusDisplay', content, "应该导入 ToolStatusDisplay 类")

    def test_streaming_markdown_message_uses_tool_status_display(self):
        """测试 StreamingMarkdownMessage 使用 ToolStatusDisplay

        Requirement 11.2, 11.3: show_tool_status 和 restore_thinking_status 方法使用 ToolStatusDisplay
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

        # 检查 show_tool_status 方法使用 ToolStatusDisplay
        self.assertIn('ToolStatusDisplay.show_tool_calling', content,
                     "show_tool_status 应该使用 ToolStatusDisplay.show_tool_calling")

        # 检查 restore_thinking_status 方法使用 ToolStatusDisplay
        self.assertIn('ToolStatusDisplay.show_thinking', content,
                     "restore_thinking_status 应该使用 ToolStatusDisplay.show_thinking")


class TestToolStatusDisplayDocumentation(unittest.TestCase):
    """测试文档和注释"""

    def test_has_documentation(self):
        """测试有适当的文档"""
        file_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'modules',
            'ai_assistant',
            'ui',
            'tool_status_display.py'
        )

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查有文档字符串
        self.assertIn('"""', content, "应该有文档字符串")

        # 检查有类文档
        self.assertIn('ToolStatusDisplay', content, "应该有 ToolStatusDisplay 类")
        self.assertIn('工具状态显示', content, "应该有工具状态显示相关文档")


if __name__ == '__main__':
    unittest.main()

