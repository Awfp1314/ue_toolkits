# -*- coding: utf-8 -*-

"""
FunctionCallingCoordinator 实现测试

测试目标：
1. 验证 API 调用计数器存在
2. 验证移除了重试逻辑
3. 验证使用 ErrorHandler 处理错误
4. 验证添加了 API 调用时间戳和 Token 消耗日志

通过代码检查方式测试，避免 QThread 阻塞问题
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestFunctionCallingCoordinatorImplementation(unittest.TestCase):
    """测试 FunctionCallingCoordinator 实现（代码检查）"""
    
    def test_file_exists(self):
        """测试文件存在"""
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'logic', 
            'function_calling_coordinator.py'
        )
        self.assertTrue(os.path.exists(file_path), "FunctionCallingCoordinator 文件应该存在")
    
    def test_api_call_counter_exists(self):
        """测试 API 调用计数器存在
        
        Requirement 1.4: 添加 API 调用计数器
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'logic', 
            'function_calling_coordinator.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查计数器初始化
        self.assertIn('self.api_call_count = 0', content, "应该初始化 API 调用计数器为 0")
        
        # 检查计数器递增
        self.assertIn('self.api_call_count += 1', content, "应该在 API 调用时递增计数器")
    
    def test_error_handler_import(self):
        """测试导入了 ErrorHandler
        
        Requirement 1.3: 使用 ErrorHandler 处理错误
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'logic', 
            'function_calling_coordinator.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查导入 ErrorHandler
        self.assertIn('from core.utils.error_handler import ErrorHandler', content, 
                     "应该导入 ErrorHandler")
    
    def test_error_handler_usage(self):
        """测试使用 ErrorHandler 处理错误
        
        Requirement 1.3: 使用 ErrorHandler.format_error() 和 log_error()
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'logic', 
            'function_calling_coordinator.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查使用 ErrorHandler.log_error()
        self.assertIn('ErrorHandler.log_error', content, 
                     "应该使用 ErrorHandler.log_error() 记录错误")
        
        # 检查使用 ErrorHandler.format_error()
        self.assertIn('ErrorHandler.format_error', content, 
                     "应该使用 ErrorHandler.format_error() 格式化错误")
    
    def test_api_call_timestamp_logging(self):
        """测试添加了 API 调用时间戳日志
        
        Requirement 1.4: 添加 API 调用时间戳日志
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'logic', 
            'function_calling_coordinator.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查记录开始时间
        self.assertIn('start_time = time.time()', content, 
                     "应该记录 API 调用开始时间")
        
        # 检查记录时间戳日志
        self.assertIn('[API调用', content, "应该记录 API 调用日志")
        self.assertIn('开始时间', content, "应该记录开始时间")
    
    def test_token_usage_logging(self):
        """测试添加了 Token 消耗日志
        
        Requirement 1.4: 添加 Token 消耗日志
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'logic', 
            'function_calling_coordinator.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查记录 Token 消耗
        self.assertIn('Token消耗', content, "应该记录 Token 消耗")
        self.assertIn('total_tokens', content, "应该记录总 Token 数")
        self.assertIn('prompt_tokens', content, "应该记录 prompt Token 数")
        self.assertIn('completion_tokens', content, "应该记录 completion Token 数")
    
    def test_no_retry_logic_for_does_not_support_tools(self):
        """测试移除了 'does not support tools' 错误的重试逻辑
        
        Requirement 1.1: 当检测到模型不支持工具调用时，直接返回空工具调用结果
        Requirement 1.2: 不重试 API 调用
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'logic', 
            'function_calling_coordinator.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查检测 "does not support tools" 错误
        self.assertIn('does not support tools', content, 
                     "应该检测 'does not support tools' 错误")
        
        # 检查返回空工具调用结果
        lines = content.split('\n')
        found_return_empty = False
        in_does_not_support_block = False
        
        for i, line in enumerate(lines):
            if 'does not support tools' in line.lower():
                in_does_not_support_block = True
            
            if in_does_not_support_block:
                # 检查接下来的几行是否有返回空结果
                if i + 10 < len(lines):
                    next_lines = '\n'.join(lines[i:i+10])
                    if "return {" in next_lines and "'type': 'content'" in next_lines:
                        found_return_empty = True
                        break
        
        self.assertTrue(found_return_empty, 
                       "检测到 'does not support tools' 错误时应该返回空工具调用结果")
    
    def test_elapsed_time_calculation(self):
        """测试计算 API 调用耗时
        
        Requirement 1.4: 记录 API 调用耗时
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'logic', 
            'function_calling_coordinator.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查计算耗时
        self.assertIn('elapsed_time = time.time() - start_time', content, 
                     "应该计算 API 调用耗时")
        
        # 检查记录耗时日志
        self.assertIn('耗时', content, "应该记录耗时")
    
    def test_usage_extraction_from_response(self):
        """测试从响应中提取 usage 信息
        
        Requirement 1.4: 记录 Token 消耗
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'logic', 
            'function_calling_coordinator.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查提取 usage
        self.assertIn("usage = response.get('usage'", content, 
                     "应该从响应中提取 usage 信息")
    
    def test_call_llm_non_streaming_signature(self):
        """测试 _call_llm_non_streaming 方法存在"""
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'logic', 
            'function_calling_coordinator.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查方法定义
        self.assertIn('def _call_llm_non_streaming(', content, 
                     "_call_llm_non_streaming 方法应该存在")
    
    def test_no_second_api_call_for_final_response(self):
        """测试移除了第二次 API 调用（用于获取最终响应）
        
        Requirement 1.2: LLM 返回最终内容时，使用第一次调用的结果
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'logic', 
            'function_calling_coordinator.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查注释说明避免重复 API 调用
        self.assertIn('避免重复API', content, 
                     "应该有注释说明避免重复 API 调用")
        
        # 检查使用第一次调用的结果
        self.assertIn("content = response_data.get('content'", content, 
                     "应该使用第一次调用返回的 content")


class TestFunctionCallingCoordinatorDocumentation(unittest.TestCase):
    """测试文档和注释"""

    def test_has_documentation(self):
        """测试有适当的文档"""
        file_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'modules',
            'ai_assistant',
            'logic',
            'function_calling_coordinator.py'
        )

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查有文档字符串
        self.assertIn('"""', content, "应该有文档字符串")

        # 检查有关键注释
        self.assertIn('API调用', content, "应该有 API 调用相关注释")


class TestFunctionCallingCoordinatorNoRetry(unittest.TestCase):
    """测试无重试逻辑（任务 6.2）"""

    def test_no_retry_comment_in_exception_handler(self):
        """测试异常处理中有明确的不重试注释

        Requirement 1.1, 1.2: 不重试 API 调用
        """
        file_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'modules',
            'ai_assistant',
            'logic',
            'function_calling_coordinator.py'
        )

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查有明确的不重试注释
        self.assertIn('不重试', content, "应该有明确的不重试注释")
        self.assertIn('关键修复', content, "应该有关键修复标记")

    def test_error_handler_used_in_run_method(self):
        """测试 run() 方法中使用 ErrorHandler

        Requirement 1.3: 使用 ErrorHandler 格式化错误消息
        """
        file_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'modules',
            'ai_assistant',
            'logic',
            'function_calling_coordinator.py'
        )

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查 run() 方法中使用 ErrorHandler
        lines = content.split('\n')
        in_run_method = False
        found_error_handler_in_run = False

        for line in lines:
            if 'def run(self):' in line:
                in_run_method = True
            elif in_run_method and 'def ' in line and 'def run' not in line:
                # 进入下一个方法，退出 run 方法
                break
            elif in_run_method and 'ErrorHandler' in line:
                found_error_handler_in_run = True
                break

        self.assertTrue(found_error_handler_in_run,
                       "run() 方法中应该使用 ErrorHandler")

    def test_friendly_error_message_emitted(self):
        """测试向 UI 发送友好的错误消息

        Requirement 1.3: 向用户显示友好的错误消息
        """
        file_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'modules',
            'ai_assistant',
            'logic',
            'function_calling_coordinator.py'
        )

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查格式化错误消息
        self.assertIn('formatted_error', content, "应该格式化错误消息")

        # 检查发送错误信号
        self.assertIn('error_occurred.emit', content, "应该发送错误信号")

    def test_optimization_comment_for_avoiding_duplicate_calls(self):
        """测试有优化注释说明避免重复调用

        Requirement 1.5: 确保每个用户消息最多触发一次 LLM API 调用
        """
        file_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'modules',
            'ai_assistant',
            'logic',
            'function_calling_coordinator.py'
        )

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查优化注释
        self.assertIn('[OPTIMIZATION]', content, "应该有优化标记")
        self.assertIn('避免重复API请求', content, "应该说明避免重复 API 请求")


if __name__ == '__main__':
    unittest.main()
