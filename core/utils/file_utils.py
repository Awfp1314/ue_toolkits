# -*- coding: utf-8 -*-

"""
文件操作安全工具类

提供安全的文件操作方法，防止路径遍历攻击和其他文件系统安全问题。
所有文件操作都经过严格的安全验证。
"""

import os
import shutil
from pathlib import Path
from typing import Optional, List
import re

from core.logger import get_logger

logger = get_logger(__name__)


class FileUtils:
    """文件操作安全工具类（线程安全）
    
    提供经过安全验证的文件操作方法，防止：
    1. 路径遍历攻击（Path Traversal）
    2. 符号链接攻击（Symlink Attack）
    3. 任意文件覆盖
    4. 目录遍历
    
    所有方法都会在操作前进行严格的安全检查。
    """
    
    DANGEROUS_PATTERNS = [
        r'\.\.',  # 父目录引用
        r'~',     # 用户目录
        r'\$',    # 环境变量
    ]
    
    DANGEROUS_NAMES = {
        '..',
        '.',
        '',
        'CON', 'PRN', 'AUX', 'NUL',  # Windows保留名
        'COM1', 'COM2', 'COM3', 'COM4',
        'LPT1', 'LPT2', 'LPT3', 'LPT4',
    }
    
    @staticmethod
    def _validate_path(path: Path, base_path: Path) -> bool:
        """验证路径是否安全
        
        此方法检查路径是否在预期的基准路径下，防止路径遍历攻击。
        
        安全检查包括:
        1. 解析为绝对路径（自动处理 '..' 等相对路径符号）
        2. 检查路径是否在基准路径下
        3. 检查是否为符号链接
        4. 验证路径的规范性
        
        Args:
            path: 待验证的路径
            base_path: 基准路径（允许的根目录）
            
        Returns:
            bool: 路径是否安全
            
        Examples:
            >>> FileUtils._validate_path(Path("/tmp/safe/file.txt"), Path("/tmp/safe"))
            True
            >>> FileUtils._validate_path(Path("/tmp/safe/../etc/passwd"), Path("/tmp/safe"))
            False
        """
        try:
            # resolve() 会自动处理 '..'、'.'、符号链接等
            abs_path = path.resolve()
            abs_base = base_path.resolve()
            
            logger.debug(f"验证路径: {abs_path}, 基准路径: {abs_base}")
            
            # 使用 is_relative_to() (Python 3.9+) 或 relative_to() (Python 3.8)
            try:
                # Python 3.9+
                is_safe = abs_path.is_relative_to(abs_base)
            except AttributeError:
                # Python 3.8 兼容性处理
                try:
                    abs_path.relative_to(abs_base)
                    is_safe = True
                except ValueError:
                    is_safe = False
            
            if not is_safe:
                logger.error(
                    f"❌ 路径验证失败: {path} 不在基准路径 {base_path} 下\n"
                    f"   绝对路径: {abs_path}\n"
                    f"   基准路径: {abs_base}"
                )
                return False
            
            # 注意: resolve() 已经解析了符号链接，这里只是额外验证
            if path.exists() and path.is_symlink():
                logger.warning(f"⚠️ 路径是符号链接: {path}")
                # 不阻止，但记录警告
            
            logger.debug(f"✅ 路径验证通过: {path}")
            return True
            
        except (ValueError, OSError, RuntimeError) as e:
            logger.error(f"❌ 路径验证时发生异常: {e}", exc_info=True)
            return False
    
    @staticmethod
    def _is_safe_filename(filename: str) -> bool:
        """验证文件名是否安全
        
        检查文件名是否包含危险字符或模式，防止：
        1. 路径遍历（如 '../../../etc/passwd'）
        2. 特殊字符注入
        3. Windows保留文件名
        4. 隐藏的路径分隔符
        
        Args:
            filename: 待验证的文件名
            
        Returns:
            bool: 文件名是否安全
            
        Examples:
            >>> FileUtils._is_safe_filename("config.ini")
            True
            >>> FileUtils._is_safe_filename("../../../etc/passwd")
            False
            >>> FileUtils._is_safe_filename("con")  # Windows保留名
            False
        """
        if not filename:
            logger.error("❌ 文件名验证失败: 文件名为空")
            return False
        
        if filename.upper() in FileUtils.DANGEROUS_NAMES:
            logger.error(f"❌ 文件名验证失败: '{filename}' 是危险或保留的文件名")
            return False
        
        for pattern in FileUtils.DANGEROUS_PATTERNS:
            if re.search(pattern, filename):
                logger.error(f"❌ 文件名验证失败: '{filename}' 包含危险模式 '{pattern}'")
                return False
        
        # 防止文件名中包含路径分隔符
        if os.sep in filename or (os.altsep and os.altsep in filename):
            logger.error(f"❌ 文件名验证失败: '{filename}' 包含路径分隔符")
            return False
        
        # Windows: < > : " | ? * (文件名中不允许)
        # Unix: 通常只有 / 和 null 不允许
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*']
        for char in dangerous_chars:
            if char in filename:
                logger.warning(f"⚠️ 文件名包含潜在危险字符: '{filename}' 包含 '{char}'")
                # 警告但不阻止（有些系统可能允许）
        
        logger.debug(f"✅ 文件名验证通过: {filename}")
        return True
    
    @staticmethod
    def copy_file(source: Path, destination: Path, base_path: Optional[Path] = None,
                  overwrite: bool = False) -> bool:
        """安全地复制文件
        
        在复制前进行安全验证，确保：
        1. 源文件存在且可读
        2. 目标路径安全（在基准路径内）
        3. 文件名安全
        4. 不会意外覆盖（除非明确指定）
        
        Args:
            source: 源文件路径
            destination: 目标文件路径
            base_path: 基准路径（可选），如果提供则验证目标路径在此路径下
            overwrite: 是否允许覆盖已存在的文件
            
        Returns:
            bool: 复制是否成功
            
        Examples:
            >>> FileUtils.copy_file(
            ...     Path("/source/file.txt"),
            ...     Path("/dest/file.txt"),
            ...     base_path=Path("/dest")
            ... )
            True
        """
        try:
            if not source.exists():
                logger.error(f"❌ 源文件不存在: {source}")
                return False
            
            if not source.is_file():
                logger.error(f"❌ 源路径不是文件: {source}")
                return False
            
            if not FileUtils._is_safe_filename(destination.name):
                logger.error(f"❌ 目标文件名不安全: {destination.name}")
                return False
            
            if base_path:
                if not FileUtils._validate_path(destination, base_path):
                    logger.error(f"❌ 目标路径不安全: {destination}")
                    return False
            
            if destination.exists() and not overwrite:
                logger.warning(f"⚠️ 目标文件已存在且不允许覆盖: {destination}")
                return False
            
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(source, destination)
            logger.info(f"✅ 成功复制文件: {source} -> {destination}")
            return True
            
        except PermissionError as e:
            logger.error(f"❌ 权限不足，无法复制文件: {e}")
            return False
        except OSError as e:
            logger.error(f"❌ 系统错误，复制文件失败: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ 复制文件时发生未知错误: {e}", exc_info=True)
            return False
    
    @staticmethod
    def move_file(source: Path, destination: Path, base_path: Optional[Path] = None,
                  overwrite: bool = False) -> bool:
        """安全地移动文件
        
        在移动前进行安全验证，确保：
        1. 源文件存在且可访问
        2. 目标路径安全（在基准路径内）
        3. 文件名安全
        4. 不会意外覆盖（除非明确指定）
        
        Args:
            source: 源文件路径
            destination: 目标文件路径
            base_path: 基准路径（可选），如果提供则验证目标路径在此路径下
            overwrite: 是否允许覆盖已存在的文件
            
        Returns:
            bool: 移动是否成功
        """
        try:
            if not source.exists():
                logger.error(f"❌ 源文件不存在: {source}")
                return False
            
            if not source.is_file():
                logger.error(f"❌ 源路径不是文件: {source}")
                return False
            
            if not FileUtils._is_safe_filename(destination.name):
                logger.error(f"❌ 目标文件名不安全: {destination.name}")
                return False
            
            if base_path:
                if not FileUtils._validate_path(destination, base_path):
                    logger.error(f"❌ 目标路径不安全: {destination}")
                    return False
            
            if destination.exists() and not overwrite:
                logger.warning(f"⚠️ 目标文件已存在且不允许覆盖: {destination}")
                return False
            
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(source), str(destination))
            logger.info(f"✅ 成功移动文件: {source} -> {destination}")
            return True
            
        except PermissionError as e:
            logger.error(f"❌ 权限不足，无法移动文件: {e}")
            return False
        except OSError as e:
            logger.error(f"❌ 系统错误，移动文件失败: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ 移动文件时发生未知错误: {e}", exc_info=True)
            return False
    
    @staticmethod
    def delete_file(file_path: Path, base_path: Optional[Path] = None) -> bool:
        """安全地删除文件
        
        在删除前进行安全验证，确保：
        1. 文件存在
        2. 路径安全（在基准路径内）
        3. 不是目录
        
        Args:
            file_path: 要删除的文件路径
            base_path: 基准路径（可选），如果提供则验证文件路径在此路径下
            
        Returns:
            bool: 删除是否成功
        """
        try:
            if not file_path.exists():
                logger.warning(f"⚠️ 文件不存在，无需删除: {file_path}")
                return True
            
            if not file_path.is_file():
                logger.error(f"❌ 路径不是文件: {file_path}")
                return False
            
            if base_path:
                if not FileUtils._validate_path(file_path, base_path):
                    logger.error(f"❌ 文件路径不安全: {file_path}")
                    return False
            
            file_path.unlink()
            logger.info(f"✅ 成功删除文件: {file_path}")
            return True
            
        except PermissionError as e:
            logger.error(f"❌ 权限不足，无法删除文件: {e}")
            return False
        except OSError as e:
            logger.error(f"❌ 系统错误，删除文件失败: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ 删除文件时发生未知错误: {e}", exc_info=True)
            return False
    
    @staticmethod
    def delete_directory(dir_path: Path, base_path: Optional[Path] = None,
                        recursive: bool = False) -> bool:
        """安全地删除目录
        
        在删除前进行安全验证，确保：
        1. 目录存在
        2. 路径安全（在基准路径内）
        3. 不是文件
        4. 递归删除需要明确指定
        
        Args:
            dir_path: 要删除的目录路径
            base_path: 基准路径（可选），如果提供则验证目录路径在此路径下
            recursive: 是否递归删除（删除目录及其所有内容）
            
        Returns:
            bool: 删除是否成功
        """
        try:
            if not dir_path.exists():
                logger.warning(f"⚠️ 目录不存在，无需删除: {dir_path}")
                return True
            
            if not dir_path.is_dir():
                logger.error(f"❌ 路径不是目录: {dir_path}")
                return False
            
            if base_path:
                if not FileUtils._validate_path(dir_path, base_path):
                    logger.error(f"❌ 目录路径不安全: {dir_path}")
                    return False
            
            if recursive:
                shutil.rmtree(dir_path)
                logger.info(f"✅ 成功递归删除目录: {dir_path}")
            else:
                dir_path.rmdir()  # 只删除空目录
                logger.info(f"✅ 成功删除空目录: {dir_path}")
            return True
            
        except OSError as e:
            if "not empty" in str(e).lower():
                logger.error(f"❌ 目录不为空，需要递归删除: {dir_path}")
            else:
                logger.error(f"❌ 系统错误，删除目录失败: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ 删除目录时发生未知错误: {e}", exc_info=True)
            return False
    
    @staticmethod
    def list_files(directory: Path, base_path: Optional[Path] = None,
                   pattern: str = "*", recursive: bool = False) -> List[Path]:
        """安全地列出目录中的文件
        
        在列出文件前进行安全验证，确保：
        1. 目录存在
        2. 路径安全（在基准路径内）
        3. 是目录而非文件
        
        Args:
            directory: 要列出的目录路径
            base_path: 基准路径（可选），如果提供则验证目录路径在此路径下
            pattern: 文件匹配模式（如 "*.txt"）
            recursive: 是否递归列出子目录中的文件
            
        Returns:
            List[Path]: 文件路径列表，如果失败返回空列表
        """
        try:
            if not directory.exists():
                logger.error(f"❌ 目录不存在: {directory}")
                return []
            
            if not directory.is_dir():
                logger.error(f"❌ 路径不是目录: {directory}")
                return []
            
            if base_path:
                if not FileUtils._validate_path(directory, base_path):
                    logger.error(f"❌ 目录路径不安全: {directory}")
                    return []
            
            if recursive:
                files = list(directory.rglob(pattern))
            else:
                files = list(directory.glob(pattern))
            
            # 过滤出文件（排除目录）
            files = [f for f in files if f.is_file()]
            
            logger.debug(f"✅ 列出 {len(files)} 个文件从 {directory}")
            return files
            
        except PermissionError as e:
            logger.error(f"❌ 权限不足，无法列出目录: {e}")
            return []
        except OSError as e:
            logger.error(f"❌ 系统错误，列出目录失败: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ 列出目录时发生未知错误: {e}", exc_info=True)
            return []
    
    @staticmethod
    def create_directory(dir_path: Path, base_path: Optional[Path] = None,
                        parents: bool = True) -> bool:
        """安全地创建目录
        
        在创建前进行安全验证，确保：
        1. 路径安全（在基准路径内）
        2. 目录名安全
        3. 不会覆盖已存在的文件
        
        Args:
            dir_path: 要创建的目录路径
            base_path: 基准路径（可选），如果提供则验证目录路径在此路径下
            parents: 是否创建父目录
            
        Returns:
            bool: 创建是否成功
        """
        try:
            if not FileUtils._is_safe_filename(dir_path.name):
                logger.error(f"❌ 目录名不安全: {dir_path.name}")
                return False
            
            if base_path:
                if not FileUtils._validate_path(dir_path, base_path):
                    logger.error(f"❌ 目录路径不安全: {dir_path}")
                    return False
            
            if dir_path.exists():
                if dir_path.is_dir():
                    logger.debug(f"ℹ️ 目录已存在: {dir_path}")
                    return True
                else:
                    logger.error(f"❌ 路径已存在但不是目录: {dir_path}")
                    return False
            
            dir_path.mkdir(parents=parents, exist_ok=True)
            logger.info(f"✅ 成功创建目录: {dir_path}")
            return True
            
        except PermissionError as e:
            logger.error(f"❌ 权限不足，无法创建目录: {e}")
            return False
        except OSError as e:
            logger.error(f"❌ 系统错误，创建目录失败: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ 创建目录时发生未知错误: {e}", exc_info=True)
            return False
