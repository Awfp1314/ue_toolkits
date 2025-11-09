"""错误处理器模块

提供统一的错误处理和格式化功能，将技术性错误转换为用户友好的消息。

设计原则：
1. 优先按异常类型/错误码分类
2. 其次才做字符串匹配
3. 日志脱敏（移除敏感信息）
4. 支持多语言（预留）
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from core.logger import get_logger
import re


@dataclass
class ErrorMessage:
    """错误消息数据类"""
    title: str
    message: str
    suggestions: List[str]
    severity: str  # 'error', 'warning', 'info'


class ErrorHandler:
    """统一错误处理器
    
    设计原则：
    1. 优先按异常类型/错误码分类
    2. 其次才做字符串匹配
    3. 日志脱敏（移除敏感信息）
    4. 支持多语言（预留）
    """
    
    # 错误码映射（优先级最高）
    ERROR_CODE_MAP: Dict[int, ErrorMessage] = {
        401: ErrorMessage(
            title='认证失败',
            message='API 密钥无效或已过期',
            suggestions=['请在设置中检查您的 API 配置'],
            severity='error'
        ),
        403: ErrorMessage(
            title='访问被拒绝',
            message='没有权限访问此资源',
            suggestions=['请检查您的 API 权限配置'],
            severity='error'
        ),
        404: ErrorMessage(
            title='资源不存在',
            message='请求的资源未找到',
            suggestions=['请检查 API 端点配置'],
            severity='error'
        ),
        429: ErrorMessage(
            title='请求过多',
            message='API 请求频率超限',
            suggestions=['请稍后重试', '考虑升级 API 套餐'],
            severity='warning'
        ),
        500: ErrorMessage(
            title='服务器错误',
            message='API 服务器内部错误',
            suggestions=['请稍后重试', '如果问题持续，请联系 API 服务提供商'],
            severity='error'
        ),
        502: ErrorMessage(
            title='网关错误',
            message='API 网关错误',
            suggestions=['请稍后重试'],
            severity='error'
        ),
        503: ErrorMessage(
            title='服务不可用',
            message='API 服务暂时不可用',
            suggestions=['请稍后重试'],
            severity='error'
        ),
        504: ErrorMessage(
            title='网关超时',
            message='API 网关超时',
            suggestions=['请检查网络连接', '稍后重试'],
            severity='error'
        ),
    }
    
    # 异常类型映射（优先级第二）
    EXCEPTION_TYPE_MAP: Dict[str, ErrorMessage] = {
        'ConnectionError': ErrorMessage(
            title='网络连接失败',
            message='无法连接到 API 服务器',
            suggestions=['检查网络连接', '检查防火墙设置', '检查 API 端点配置'],
            severity='error'
        ),
        'TimeoutError': ErrorMessage(
            title='请求超时',
            message='API 请求超时',
            suggestions=['检查网络连接', '稍后重试'],
            severity='error'
        ),
        'Timeout': ErrorMessage(
            title='请求超时',
            message='API 请求超时',
            suggestions=['检查网络连接', '稍后重试'],
            severity='error'
        ),
        'SSLError': ErrorMessage(
            title='SSL 证书错误',
            message='SSL 证书验证失败',
            suggestions=['检查系统时间是否正确', '检查网络代理设置'],
            severity='error'
        ),
        'ProxyError': ErrorMessage(
            title='代理错误',
            message='代理服务器连接失败',
            suggestions=['检查代理配置', '尝试禁用代理'],
            severity='error'
        ),
        'HTTPError': ErrorMessage(
            title='HTTP 错误',
            message='HTTP 请求失败',
            suggestions=['检查 API 配置', '稍后重试'],
            severity='error'
        ),
        'JSONDecodeError': ErrorMessage(
            title='响应解析失败',
            message='无法解析 API 响应',
            suggestions=['API 可能返回了非 JSON 格式的数据', '请联系技术支持'],
            severity='error'
        ),
        'KeyError': ErrorMessage(
            title='数据格式错误',
            message='API 响应缺少必需的字段',
            suggestions=['API 响应格式可能已更改', '请联系技术支持'],
            severity='error'
        ),
        'ValueError': ErrorMessage(
            title='数据值错误',
            message='API 响应包含无效的数据',
            suggestions=['请检查输入参数', '如果问题持续，请联系技术支持'],
            severity='error'
        ),
    }
    
    # 字符串模式映射（优先级最低）
    STRING_PATTERN_MAP: Dict[str, ErrorMessage] = {
        r'does not support tools': ErrorMessage(
            title='功能不支持',
            message='当前模型不支持工具调用功能',
            suggestions=['在设置中禁用工具调用', '或切换到支持的模型（如 GPT-4）'],
            severity='error'
        ),
        r'invalid.*api.*key': ErrorMessage(
            title='API 密钥无效',
            message='提供的 API 密钥无效',
            suggestions=['请在设置中检查您的 API 密钥'],
            severity='error'
        ),
        r'rate.*limit': ErrorMessage(
            title='请求频率限制',
            message='API 请求频率超过限制',
            suggestions=['请稍后重试', '考虑升级 API 套餐'],
            severity='warning'
        ),
        r'quota.*exceed': ErrorMessage(
            title='配额超限',
            message='API 配额已用尽',
            suggestions=['请检查您的 API 配额', '考虑升级套餐'],
            severity='error'
        ),
        r'model.*not.*found': ErrorMessage(
            title='模型不存在',
            message='指定的模型不存在或不可用',
            suggestions=['请检查模型名称配置', '查看可用模型列表'],
            severity='error'
        ),
        r'context.*length.*exceed': ErrorMessage(
            title='上下文长度超限',
            message='对话上下文超过模型最大长度',
            suggestions=['尝试清理对话历史', '使用支持更长上下文的模型'],
            severity='error'
        ),
        r'network.*error': ErrorMessage(
            title='网络错误',
            message='网络连接出现问题',
            suggestions=['检查网络连接', '检查防火墙设置'],
            severity='error'
        ),
        r'connection.*refused': ErrorMessage(
            title='连接被拒绝',
            message='无法连接到服务器',
            suggestions=['检查 API 端点配置', '检查网络连接'],
            severity='error'
        ),
        r'bad.*gateway': ErrorMessage(
            title='网关错误',
            message='API 网关错误',
            suggestions=['请稍后重试'],
            severity='error'
        ),
    }
    
    @staticmethod
    def format_error(
        exception: Exception,
        error_code: Optional[int] = None,
        language: str = 'zh'
    ) -> ErrorMessage:
        """格式化错误消息
        
        Args:
            exception: 原始异常
            error_code: HTTP 错误码（如果有）
            language: 语言代码（'zh', 'en'）
        
        Returns:
            ErrorMessage: 格式化后的错误消息
        """
        logger = get_logger(__name__)
        
        # 1. 优先按错误码匹配
        if error_code and error_code in ErrorHandler.ERROR_CODE_MAP:
            logger.debug(f"错误码匹配: {error_code}")
            return ErrorHandler.ERROR_CODE_MAP[error_code]
        
        # 2. 按异常类型匹配
        exception_type = type(exception).__name__
        if exception_type in ErrorHandler.EXCEPTION_TYPE_MAP:
            logger.debug(f"异常类型匹配: {exception_type}")
            return ErrorHandler.EXCEPTION_TYPE_MAP[exception_type]
        
        # 3. 按字符串模式匹配
        error_str = str(exception)
        for pattern, error_msg in ErrorHandler.STRING_PATTERN_MAP.items():
            if re.search(pattern, error_str, re.IGNORECASE):
                logger.debug(f"字符串模式匹配: {pattern}")
                return error_msg
        
        # 4. 默认错误消息
        logger.debug("使用默认错误消息")
        return ErrorMessage(
            title='发生错误',
            message=f'操作失败：{error_str[:100]}',
            suggestions=['如果问题持续，请联系技术支持'],
            severity='error'
        )
    
    @staticmethod
    def log_error(
        exception: Exception,
        context: str,
        error_code: Optional[int] = None
    ) -> None:
        """记录详细错误日志（脱敏）
        
        Args:
            exception: 原始异常
            context: 错误上下文
            error_code: HTTP 错误码（如果有）
        """
        logger = get_logger(__name__)
        
        # 脱敏处理
        error_str = str(exception)
        error_str = ErrorHandler._sanitize_log(error_str)
        
        # 记录日志
        logger.error(
            f"[{context}] {type(exception).__name__}: {error_str}",
            extra={'error_code': error_code},
            exc_info=True
        )
    
    @staticmethod
    def _sanitize_log(text: str) -> str:
        """脱敏处理（移除敏感信息）
        
        Args:
            text: 原始文本
        
        Returns:
            str: 脱敏后的文本
        """
        # 移除 Bearer tokens (before Authorization header to preserve "Bearer ***")
        text = re.sub(r'Bearer [a-zA-Z0-9]{32,}', 'Bearer ***', text)
        
        # 移除 API Key（sk-xxx）
        text = re.sub(r'sk-[a-zA-Z0-9]{32,}', 'sk-***', text)
        
        # 移除 OpenAI API Key 格式
        text = re.sub(r'sk-proj-[a-zA-Z0-9_-]{32,}', 'sk-proj-***', text)
        
        # 移除其他常见 API Key 格式
        text = re.sub(r'api[_-]?key["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_-]{20,}', 'api_key=***', text, flags=re.IGNORECASE)
        
        # 移除密码
        text = re.sub(r'password["\']?\s*[:=]\s*["\']?[^"\'}\s]+', 'password=***', text, flags=re.IGNORECASE)
        text = re.sub(r'passwd["\']?\s*[:=]\s*["\']?[^"\'}\s]+', 'passwd=***', text, flags=re.IGNORECASE)
        
        # 移除 token
        text = re.sub(r'token["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_-]{20,}', 'token=***', text, flags=re.IGNORECASE)
        
        # 移除 Authorization header (after Bearer to avoid double replacement)
        text = re.sub(r'Authorization["\']?\s*[:=]\s*["\']?(?!Bearer \*\*\*)[^"\'}\s]+', 'Authorization=***', text, flags=re.IGNORECASE)
        
        return text
