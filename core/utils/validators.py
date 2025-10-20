# -*- coding: utf-8 -*-

"""
输入验证工具 - 用于验证和清理用户输入

提供对路径、URL、文件名等常见输入的验证功能
"""

from pathlib import Path
from typing import Union, Optional, List
import re
from urllib.parse import urlparse
from core.logger import get_logger

logger = get_logger(__name__)


class InputValidator:
    """输入验证器
    
    提供各种输入验证功能，防止安全问题和错误输入
    """
    
    @staticmethod
    def validate_path(path: Union[str, Path],
                      must_exist: bool = False,
                      must_be_file: bool = False,
                      must_be_dir: bool = False,
                      allowed_extensions: Optional[List[str]] = None,
                      max_length: int = 260) -> tuple[bool, str]:
        """验证文件路径
        
        Args:
            path: 要验证的路径
            must_exist: 路径必须存在
            must_be_file: 必须是文件
            must_be_dir: 必须是目录
            allowed_extensions: 允许的扩展名列表 (如 ['.json', '.txt'])
            max_length: 最大路径长度
            
        Returns:
            tuple[bool, str]: (是否有效, 错误消息)
            
        Example:
            valid, error = InputValidator.validate_path(
                user_path,
                must_exist=True,
                allowed_extensions=['.json']
            )
            if not valid:
                print(f"路径无效: {error}")
        """
        try:
            # 转换为Path对象
            p = Path(path)
            
            if len(str(p)) > max_length:
                return False, f"路径长度超过限制 ({max_length} 字符)"
            
            if ".." in p.parts:
                return False, "路径不能包含 '..' (路径遍历攻击)"
            
            if must_exist and not p.exists():
                return False, f"路径不存在: {p}"
            
            if must_be_file and p.exists() and not p.is_file():
                return False, f"路径不是文件: {p}"
            
            if must_be_dir and p.exists() and not p.is_dir():
                return False, f"路径不是目录: {p}"
            
            if allowed_extensions and p.suffix.lower() not in [ext.lower() for ext in allowed_extensions]:
                return False, f"不允许的文件类型: {p.suffix}，允许的类型: {', '.join(allowed_extensions)}"
            
            # 检查文件名中的非法字符（Windows）
            illegal_chars = r'<>"|?*'
            if any(char in str(p.name) for char in illegal_chars):
                return False, f"文件名包含非法字符: {illegal_chars}"
            
            return True, ""
            
        except Exception as e:
            return False, f"路径验证失败: {str(e)}"
    
    @staticmethod
    def validate_url(url: str,
                     allowed_schemes: Optional[List[str]] = None,
                     require_netloc: bool = True,
                     max_length: int = 2048,
                     check_reachable: bool = False) -> tuple[bool, str]:
        """验证URL（增强版：支持域名格式和安全检查）
        
        Args:
            url: 要验证的URL
            allowed_schemes: 允许的协议列表 (如 ['http', 'https'])
            require_netloc: 是否要求有网络位置（域名）
            max_length: 最大URL长度
            check_reachable: 是否检查URL可达性（需要网络请求）
            
        Returns:
            tuple[bool, str]: (是否有效, 错误消息)
            
        Example:
            valid, error = InputValidator.validate_url(
                user_url,
                allowed_schemes=['http', 'https'],
                check_reachable=True
            )
        """
        try:
            if not url or not url.strip():
                return False, "URL不能为空"
            
            url = url.strip()
            
            if len(url) > max_length:
                return False, f"URL长度超过限制 ({max_length} 字符)"
            
            # 解析URL
            result = urlparse(url)
            
            if allowed_schemes is None:
                allowed_schemes = ['http', 'https', 'ftp', 'file']
            
            if not result.scheme:
                return False, "URL缺少协议（如 http://）"
            
            if result.scheme not in allowed_schemes:
                return False, f"不允许的协议: {result.scheme}，允许的协议: {', '.join(allowed_schemes)}"
            
            if require_netloc and not result.netloc:
                return False, "URL缺少域名"
            
            # ✅ 增强：验证域名格式
            if result.netloc:
                domain = result.netloc.split(':')[0]  # 移除端口号
                domain = domain.split('@')[-1]  # 移除用户信息（如果有）
                
                # 允许localhost和本地IP
                if domain not in ['localhost', '127.0.0.1', '0.0.0.0']:
                    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
                    if re.match(ip_pattern, domain):
                        parts = domain.split('.')
                        for part in parts:
                            if int(part) > 255:
                                return False, f"无效的IP地址: {domain}"
                    else:
                        # 域名可以包含字母、数字、连字符和点
                        # 不能以连字符开始或结束
                        domain_pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$'
                        if not re.match(domain_pattern, domain):
                            return False, f"域名格式不正确: {domain}"
                        
                        if len(domain) > 253:
                            return False, f"域名过长: {domain}"
                        
                        # 检查每个标签的长度（不超过63个字符）
                        labels = domain.split('.')
                        for label in labels:
                            if len(label) > 63:
                                return False, f"域名标签过长: {label}"
            
            # ✅ 增强：检查危险字符和潜在攻击
            dangerous_chars = ['<', '>', '"', '{', '}', '|', '\\', '^', '`', '\n', '\r', '\t']
            for char in dangerous_chars:
                if char in url:
                    return False, f"URL包含不安全字符: {repr(char)}"
            
            # ✅ 增强：检查常见的恶意URL模式
            if url.lower().startswith('javascript:'):
                return False, "不允许的JavaScript URL"
            
            if url.lower().startswith('data:'):
                return False, "不允许的Data URL"
            
            if url.lower().startswith('vbscript:'):
                return False, "不允许的VBScript URL"
            
            # ✅ 可选：检查URL可达性
            if check_reachable and result.scheme in ['http', 'https']:
                try:
                    import requests
                    # 短超时，仅检查连通性
                    response = requests.head(url, timeout=3, allow_redirects=True)
                    if response.status_code >= 400:
                        return False, f"URL无法访问 (HTTP {response.status_code})"
                except ImportError:
                    logger.warning("requests库未安装，跳过URL可达性检查")
                except requests.exceptions.Timeout:
                    return False, "URL请求超时"
                except requests.exceptions.ConnectionError:
                    return False, "无法连接到URL"
                except requests.exceptions.RequestException as e:
                    return False, f"URL访问失败: {str(e)}"
            
            return True, ""
            
        except Exception as e:
            return False, f"URL验证失败: {str(e)}"
    
    @staticmethod
    def sanitize_filename(filename: str,
                          max_length: int = 255,
                          replacement: str = '_') -> str:
        """清理文件名，移除不安全字符
        
        Args:
            filename: 原始文件名
            max_length: 最大文件名长度
            replacement: 替换字符
            
        Returns:
            str: 清理后的文件名
            
        Example:
            safe_name = InputValidator.sanitize_filename(
                "my<file>name?.txt"
            )
            # 结果: "my_file_name_.txt"
        """
        # 移除Windows和Unix不允许的字符
        # Windows: < > : " / \ | ? *
        # Unix: / (null)
        unsafe_pattern = r'[<>:"/\\|?*\x00-\x1f]'
        safe_filename = re.sub(unsafe_pattern, replacement, filename)
        
        # 移除首尾空格和点
        safe_filename = safe_filename.strip('. ')
        
        # 限制长度（保留扩展名）
        if len(safe_filename) > max_length:
            name, ext = Path(safe_filename).stem, Path(safe_filename).suffix
            max_name_length = max_length - len(ext)
            safe_filename = name[:max_name_length] + ext
        
        # 如果结果为空，使用默认名称
        if not safe_filename:
            safe_filename = 'unnamed'
        
        return safe_filename
    
    @staticmethod
    def validate_json_string(json_str: str,
                             max_size: int = 10 * 1024 * 1024) -> tuple[bool, str]:
        """验证JSON字符串
        
        Args:
            json_str: JSON字符串
            max_size: 最大大小（字节）
            
        Returns:
            tuple[bool, str]: (是否有效, 错误消息)
        """
        try:
            import json
            
            if len(json_str.encode('utf-8')) > max_size:
                return False, f"JSON大小超过限制 ({max_size} 字节)"
            
            # 尝试解析
            json.loads(json_str)
            
            return True, ""
            
        except json.JSONDecodeError as e:
            return False, f"JSON格式错误: {str(e)}"
        except Exception as e:
            return False, f"JSON验证失败: {str(e)}"
    
    @staticmethod
    def validate_version(version: str) -> tuple[bool, str]:
        """验证语义化版本号
        
        Args:
            version: 版本号字符串 (如 "1.0.0")
            
        Returns:
            tuple[bool, str]: (是否有效, 错误消息)
            
        Example:
            valid, error = InputValidator.validate_version("1.0.0")
        """
        # 语义化版本号正则表达式
        semver_pattern = r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
        
        if not re.match(semver_pattern, version):
            return False, f"版本号格式不正确: '{version}'，应该是 'major.minor.patch' 格式 (如 '1.0.0')"
        
        return True, ""
    
    @staticmethod
    def validate_port(port: Union[int, str]) -> tuple[bool, str]:
        """验证端口号
        
        Args:
            port: 端口号
            
        Returns:
            tuple[bool, str]: (是否有效, 错误消息)
        """
        try:
            port_int = int(port)
            
            if not (0 <= port_int <= 65535):
                return False, f"端口号必须在 0-65535 之间，当前值: {port_int}"
            
            if port_int < 1024:
                logger.warning(f"使用特权端口 {port_int}，可能需要管理员权限")
            
            return True, ""
            
        except ValueError:
            return False, f"端口号必须是数字，当前值: {port}"
        except Exception as e:
            return False, f"端口验证失败: {str(e)}"
    
    @staticmethod
    def is_safe_path(path: Union[str, Path],
                     base_dir: Union[str, Path]) -> bool:
        """检查路径是否在基准目录内（防止路径遍历）
        
        Args:
            path: 要检查的路径
            base_dir: 基准目录
            
        Returns:
            bool: 路径是否安全
            
        Example:
            safe = InputValidator.is_safe_path(
                user_path,
                base_dir="/app/data"
            )
        """
        try:
            # 转换为绝对路径
            path = Path(path).resolve()
            base_dir = Path(base_dir).resolve()
            
            return str(path).startswith(str(base_dir))
            
        except Exception:
            return False


# 便捷函数
def validate_user_path(path: str, **kwargs) -> tuple[bool, str]:
    """便捷函数：验证用户输入的路径"""
    return InputValidator.validate_path(path, **kwargs)


def validate_user_url(url: str, **kwargs) -> tuple[bool, str]:
    """便捷函数：验证用户输入的URL"""
    return InputValidator.validate_url(url, **kwargs)


def safe_filename(filename: str) -> str:
    """便捷函数：获取安全的文件名"""
    return InputValidator.sanitize_filename(filename)

