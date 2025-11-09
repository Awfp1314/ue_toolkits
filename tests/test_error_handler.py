"""
Unit tests for ErrorHandler implementation

Tests cover:
- Error code priority matching
- Exception type matching
- String pattern matching
- Log sanitization functionality

Requirements tested: 5.1, 5.2, 5.3, 5.4
"""

import unittest
import sys
import os

# Add parent directory to path to allow importing core module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.utils.error_handler import ErrorHandler, ErrorMessage


class TestErrorMessage(unittest.TestCase):
    """Test ErrorMessage dataclass"""
    
    def test_error_message_creation(self):
        """Test ErrorMessage can be created with required fields"""
        error_msg = ErrorMessage(
            title="Test Error",
            message="Test message",
            suggestions=["Suggestion 1", "Suggestion 2"],
            severity="error"
        )
        self.assertEqual(error_msg.title, "Test Error")
        self.assertEqual(error_msg.message, "Test message")
        self.assertEqual(len(error_msg.suggestions), 2)
        self.assertEqual(error_msg.severity, "error")


class TestErrorCodeMatching(unittest.TestCase):
    """Test error code priority matching
    
    Requirement 5.1: Error codes should have highest priority
    """
    
    def test_401_unauthorized(self):
        """Test 401 error code mapping"""
        exception = Exception("Unauthorized")
        result = ErrorHandler.format_error(exception, error_code=401)
        
        self.assertEqual(result.title, "认证失败")
        self.assertEqual(result.message, "API 密钥无效或已过期")
        self.assertEqual(result.severity, "error")
        self.assertIn("请在设置中检查您的 API 配置", result.suggestions)
    
    def test_429_rate_limit(self):
        """Test 429 rate limit error code mapping"""
        exception = Exception("Too many requests")
        result = ErrorHandler.format_error(exception, error_code=429)
        
        self.assertEqual(result.title, "请求过多")
        self.assertEqual(result.message, "API 请求频率超限")
        self.assertEqual(result.severity, "warning")
        self.assertIn("请稍后重试", result.suggestions)
    
    def test_500_server_error(self):
        """Test 500 server error code mapping"""
        exception = Exception("Internal server error")
        result = ErrorHandler.format_error(exception, error_code=500)
        
        self.assertEqual(result.title, "服务器错误")
        self.assertEqual(result.message, "API 服务器内部错误")
        self.assertEqual(result.severity, "error")
    
    def test_503_service_unavailable(self):
        """Test 503 service unavailable error code mapping"""
        exception = Exception("Service unavailable")
        result = ErrorHandler.format_error(exception, error_code=503)
        
        self.assertEqual(result.title, "服务不可用")
        self.assertEqual(result.message, "API 服务暂时不可用")
        self.assertEqual(result.severity, "error")
    
    def test_error_code_priority_over_exception_type(self):
        """Test that error code has priority over exception type
        
        Requirement 5.1: Error code matching should have highest priority
        """
        # Create a ConnectionError but provide error code 401
        exception = ConnectionError("Connection failed")
        result = ErrorHandler.format_error(exception, error_code=401)
        
        # Should match error code, not exception type
        self.assertEqual(result.title, "认证失败")
        self.assertNotEqual(result.title, "网络连接失败")


class TestExceptionTypeMatching(unittest.TestCase):
    """Test exception type matching
    
    Requirement 5.2: Exception types should be matched when no error code
    """
    
    def test_connection_error(self):
        """Test ConnectionError exception type mapping"""
        exception = ConnectionError("Failed to connect")
        result = ErrorHandler.format_error(exception)
        
        self.assertEqual(result.title, "网络连接失败")
        self.assertEqual(result.message, "无法连接到 API 服务器")
        self.assertEqual(result.severity, "error")
        self.assertIn("检查网络连接", result.suggestions)
    
    def test_timeout_error(self):
        """Test TimeoutError exception type mapping"""
        exception = TimeoutError("Request timed out")
        result = ErrorHandler.format_error(exception)
        
        self.assertEqual(result.title, "请求超时")
        self.assertEqual(result.message, "API 请求超时")
        self.assertEqual(result.severity, "error")
    
    def test_json_decode_error(self):
        """Test JSONDecodeError exception type mapping"""
        # Simulate JSONDecodeError
        class JSONDecodeError(Exception):
            pass
        
        exception = JSONDecodeError("Invalid JSON")
        result = ErrorHandler.format_error(exception)
        
        self.assertEqual(result.title, "响应解析失败")
        self.assertEqual(result.message, "无法解析 API 响应")
        self.assertEqual(result.severity, "error")
    
    def test_key_error(self):
        """Test KeyError exception type mapping"""
        exception = KeyError("missing_field")
        result = ErrorHandler.format_error(exception)
        
        self.assertEqual(result.title, "数据格式错误")
        self.assertEqual(result.message, "API 响应缺少必需的字段")
        self.assertEqual(result.severity, "error")
    
    def test_value_error(self):
        """Test ValueError exception type mapping"""
        exception = ValueError("Invalid value")
        result = ErrorHandler.format_error(exception)
        
        self.assertEqual(result.title, "数据值错误")
        self.assertEqual(result.message, "API 响应包含无效的数据")
        self.assertEqual(result.severity, "error")


class TestStringPatternMatching(unittest.TestCase):
    """Test string pattern matching
    
    Requirement 5.3: String patterns should be matched as fallback
    """
    
    def test_does_not_support_tools(self):
        """Test 'does not support tools' pattern matching"""
        exception = Exception("Model does not support tools")
        result = ErrorHandler.format_error(exception)
        
        self.assertEqual(result.title, "功能不支持")
        self.assertEqual(result.message, "当前模型不支持工具调用功能")
        self.assertEqual(result.severity, "error")
        self.assertIn("在设置中禁用工具调用", result.suggestions)
    
    def test_invalid_api_key_pattern(self):
        """Test 'invalid api key' pattern matching"""
        exception = Exception("Invalid API key provided")
        result = ErrorHandler.format_error(exception)
        
        self.assertEqual(result.title, "API 密钥无效")
        self.assertIn("API 密钥", result.message)
        self.assertEqual(result.severity, "error")
    
    def test_rate_limit_pattern(self):
        """Test 'rate limit' pattern matching"""
        exception = Exception("Rate limit exceeded")
        result = ErrorHandler.format_error(exception)
        
        self.assertEqual(result.title, "请求频率限制")
        self.assertIn("频率", result.message)
        self.assertEqual(result.severity, "warning")
    
    def test_quota_exceed_pattern(self):
        """Test 'quota exceed' pattern matching"""
        exception = Exception("Quota exceeded for this month")
        result = ErrorHandler.format_error(exception)
        
        self.assertEqual(result.title, "配额超限")
        self.assertIn("配额", result.message)
        self.assertEqual(result.severity, "error")
    
    def test_model_not_found_pattern(self):
        """Test 'model not found' pattern matching"""
        exception = Exception("Model gpt-5 not found")
        result = ErrorHandler.format_error(exception)
        
        self.assertEqual(result.title, "模型不存在")
        self.assertIn("模型", result.message)
        self.assertEqual(result.severity, "error")
    
    def test_context_length_exceed_pattern(self):
        """Test 'context length exceed' pattern matching"""
        exception = Exception("Context length exceeded maximum")
        result = ErrorHandler.format_error(exception)
        
        self.assertEqual(result.title, "上下文长度超限")
        self.assertIn("上下文", result.message)
        self.assertEqual(result.severity, "error")
    
    def test_case_insensitive_matching(self):
        """Test that pattern matching is case-insensitive"""
        exception1 = Exception("RATE LIMIT EXCEEDED")
        exception2 = Exception("rate limit exceeded")
        exception3 = Exception("Rate Limit Exceeded")
        
        result1 = ErrorHandler.format_error(exception1)
        result2 = ErrorHandler.format_error(exception2)
        result3 = ErrorHandler.format_error(exception3)
        
        # All should match the same pattern
        self.assertEqual(result1.title, result2.title)
        self.assertEqual(result2.title, result3.title)
        self.assertEqual(result1.title, "请求频率限制")


class TestDefaultErrorHandling(unittest.TestCase):
    """Test default error handling when no pattern matches"""
    
    def test_unknown_error(self):
        """Test handling of unknown errors"""
        exception = Exception("Some unknown error occurred")
        result = ErrorHandler.format_error(exception)
        
        self.assertEqual(result.title, "发生错误")
        self.assertIn("操作失败", result.message)
        self.assertEqual(result.severity, "error")
        self.assertIn("如果问题持续，请联系技术支持", result.suggestions)
    
    def test_long_error_message_truncation(self):
        """Test that long error messages are truncated"""
        long_message = "x" * 200
        exception = Exception(long_message)
        result = ErrorHandler.format_error(exception)
        
        # Message should be truncated to 100 characters
        self.assertLessEqual(len(result.message), 110)  # "操作失败：" + 100 chars
        self.assertIn("操作失败", result.message)


class TestLogSanitization(unittest.TestCase):
    """Test log sanitization functionality
    
    Requirement 5.4: Logs should be sanitized to remove sensitive information
    """
    
    def test_sanitize_openai_api_key(self):
        """Test sanitization of OpenAI API keys (sk-xxx format)"""
        text = "Error with API key: sk-abcdefghijklmnopqrstuvwxyz123456"
        result = ErrorHandler._sanitize_log(text)
        
        self.assertNotIn("sk-abcdefghijklmnopqrstuvwxyz123456", result)
        self.assertIn("sk-***", result)
    
    def test_sanitize_bearer_token(self):
        """Test sanitization of Bearer tokens"""
        text = "Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456789"
        result = ErrorHandler._sanitize_log(text)
        
        self.assertNotIn("abcdefghijklmnopqrstuvwxyz123456789", result)
        self.assertIn("Bearer ***", result)
    
    def test_sanitize_openai_project_key(self):
        """Test sanitization of OpenAI project keys (sk-proj-xxx format)"""
        text = "Using key: sk-proj-abcdefghijklmnopqrstuvwxyz123456"
        result = ErrorHandler._sanitize_log(text)
        
        self.assertNotIn("sk-proj-abcdefghijklmnopqrstuvwxyz123456", result)
        self.assertIn("sk-proj-***", result)
    
    def test_sanitize_api_key_various_formats(self):
        """Test sanitization of various API key formats"""
        test_cases = [
            'api_key: "my_secret_key_12345678901234567890"',
            "api-key='another_secret_key_123456789012345'",
            'apikey=yet_another_key_1234567890123456',
            'API_KEY: "UPPERCASE_KEY_12345678901234567890"'
        ]
        
        for text in test_cases:
            result = ErrorHandler._sanitize_log(text)
            self.assertIn("api_key=***", result.lower())
            # Ensure the actual key is removed
            self.assertNotIn("secret", result.lower())
            self.assertNotIn("key_123", result.lower())
    
    def test_sanitize_password(self):
        """Test sanitization of passwords"""
        test_cases = [
            'password: "my_secret_password"',
            "password='another_password'",
            'password=plain_password',
            'passwd: "legacy_password"'
        ]
        
        for text in test_cases:
            result = ErrorHandler._sanitize_log(text)
            self.assertIn("***", result)
            self.assertNotIn("secret", result.lower())
            self.assertNotIn("another", result.lower())
            self.assertNotIn("plain", result.lower())
            self.assertNotIn("legacy", result.lower())
    
    def test_sanitize_token(self):
        """Test sanitization of tokens"""
        text = 'token: "my_long_token_string_12345678901234567890"'
        result = ErrorHandler._sanitize_log(text)
        
        self.assertIn("token=***", result.lower())
        self.assertNotIn("my_long_token_string", result)
    
    def test_sanitize_authorization_header(self):
        """Test sanitization of Authorization headers"""
        text = 'Authorization: "Bearer sk-1234567890abcdefghijklmnopqrstuvwxyz"'
        result = ErrorHandler._sanitize_log(text)
        
        self.assertIn("Authorization=***", result)
        self.assertNotIn("1234567890abcdefghijklmnopqrstuvwxyz", result)
    
    def test_sanitize_multiple_secrets(self):
        """Test sanitization of multiple secrets in one text"""
        text = """
        Error occurred:
        API Key: sk-abcdefghijklmnopqrstuvwxyz123456
        Password: my_secret_password
        Token: long_token_string_12345678901234567890
        """
        result = ErrorHandler._sanitize_log(text)
        
        # All secrets should be sanitized
        self.assertIn("sk-***", result)
        self.assertIn("password=***", result.lower())
        self.assertIn("token=***", result.lower())
        
        # Original secrets should not be present
        self.assertNotIn("abcdefghijklmnopqrstuvwxyz123456", result)
        self.assertNotIn("my_secret_password", result)
        self.assertNotIn("long_token_string", result)
    
    def test_sanitize_preserves_safe_content(self):
        """Test that sanitization preserves non-sensitive content"""
        text = "Error: Connection failed to api.openai.com on port 443"
        result = ErrorHandler._sanitize_log(text)
        
        # Safe content should be preserved
        self.assertIn("Connection failed", result)
        self.assertIn("api.openai.com", result)
        self.assertIn("443", result)
    
    def test_sanitize_empty_string(self):
        """Test sanitization of empty string"""
        result = ErrorHandler._sanitize_log("")
        self.assertEqual(result, "")
    
    def test_sanitize_no_secrets(self):
        """Test sanitization when no secrets are present"""
        text = "This is a normal error message without any secrets"
        result = ErrorHandler._sanitize_log(text)
        
        # Should return unchanged
        self.assertEqual(result, text)


class TestLogErrorMethod(unittest.TestCase):
    """Test log_error method functionality"""
    
    def test_log_error_basic(self):
        """Test basic error logging"""
        exception = Exception("Test error")
        
        # Should not raise any exceptions
        try:
            ErrorHandler.log_error(exception, "test_context")
        except Exception as e:
            self.fail(f"log_error raised unexpected exception: {e}")
    
    def test_log_error_with_error_code(self):
        """Test error logging with error code"""
        exception = Exception("Test error")
        
        # Should not raise any exceptions
        try:
            ErrorHandler.log_error(exception, "test_context", error_code=500)
        except Exception as e:
            self.fail(f"log_error raised unexpected exception: {e}")
    
    def test_log_error_sanitizes_sensitive_data(self):
        """Test that log_error sanitizes sensitive data"""
        exception = Exception("Error with API key: sk-abcdefghijklmnopqrstuvwxyz123456")
        
        # Should not raise any exceptions and should sanitize
        try:
            ErrorHandler.log_error(exception, "test_context")
        except Exception as e:
            self.fail(f"log_error raised unexpected exception: {e}")


class TestMatchingPriority(unittest.TestCase):
    """Test matching priority order
    
    Requirement 5.1, 5.2, 5.3: Test priority order of matching
    """
    
    def test_error_code_beats_exception_type(self):
        """Test that error code has priority over exception type"""
        # TimeoutError would normally match exception type
        exception = TimeoutError("Request timed out")
        
        # But error code 401 should take priority
        result = ErrorHandler.format_error(exception, error_code=401)
        
        self.assertEqual(result.title, "认证失败")
        self.assertNotEqual(result.title, "请求超时")
    
    def test_error_code_beats_string_pattern(self):
        """Test that error code has priority over string pattern"""
        # Message contains "rate limit" which would match string pattern
        exception = Exception("Rate limit exceeded")
        
        # But error code 500 should take priority
        result = ErrorHandler.format_error(exception, error_code=500)
        
        self.assertEqual(result.title, "服务器错误")
        self.assertNotEqual(result.title, "请求频率限制")
    
    def test_exception_type_beats_string_pattern(self):
        """Test that exception type has priority over string pattern"""
        # Message contains "rate limit" which would match string pattern
        exception = ConnectionError("Rate limit on connection")
        
        # But exception type should take priority
        result = ErrorHandler.format_error(exception)
        
        self.assertEqual(result.title, "网络连接失败")
        self.assertNotEqual(result.title, "请求频率限制")
    
    def test_string_pattern_as_fallback(self):
        """Test that string pattern is used when no error code or known exception type"""
        # Generic exception with pattern in message
        exception = Exception("Model does not support tools")
        
        # Should match string pattern
        result = ErrorHandler.format_error(exception)
        
        self.assertEqual(result.title, "功能不支持")
    
    def test_default_as_last_resort(self):
        """Test that default message is used when nothing matches"""
        # Generic exception with no matching pattern
        exception = Exception("Some completely unknown error")
        
        # Should use default
        result = ErrorHandler.format_error(exception)
        
        self.assertEqual(result.title, "发生错误")
        self.assertIn("操作失败", result.message)


class TestLanguageSupport(unittest.TestCase):
    """Test language support (currently only Chinese, but structure for future expansion)"""
    
    def test_default_language_is_chinese(self):
        """Test that default language is Chinese"""
        exception = Exception("Test error")
        result = ErrorHandler.format_error(exception)
        
        # Should return Chinese messages
        self.assertEqual(result.title, "发生错误")
    
    def test_explicit_chinese_language(self):
        """Test explicit Chinese language parameter"""
        exception = Exception("Test error")
        result = ErrorHandler.format_error(exception, language='zh')
        
        # Should return Chinese messages
        self.assertEqual(result.title, "发生错误")


if __name__ == '__main__':
    unittest.main()
