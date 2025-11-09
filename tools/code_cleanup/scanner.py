# -*- coding: utf-8 -*-

"""
代码扫描器

负责扫描项目文件系统，构建文件列表和基础信息。
"""

import os
from pathlib import Path
from typing import List, Set
from .models import FileInfo


class CodeScanner:
    """代码扫描器"""
    
    def __init__(self, project_root: Path, exclude_dirs: List[str] = None, exclude_files: List[str] = None):
        """初始化扫描器
        
        Args:
            project_root: 项目根目录
            exclude_dirs: 排除的目录列表
            exclude_files: 排除的文件列表
        """
        self.project_root = Path(project_root)
        self.exclude_dirs = set(exclude_dirs or [])
        self.exclude_files = set(exclude_files or [])
        
        # 默认排除目录
        self.exclude_dirs.update({
            '.git', '__pycache__', '.pytest_cache', 
            'venv', 'env', 'node_modules', '.kiro'
        })
    
    def scan_project(self) -> tuple[List[FileInfo], List[FileInfo], List[FileInfo]]:
        """扫描项目文件
        
        Returns:
            (python_files, config_files, resource_files) 三元组
        """
        python_files = self.scan_python_files()
        config_files = self.scan_config_files()
        resource_files = self.scan_resource_files()
        
        return python_files, config_files, resource_files
    
    def scan_python_files(self) -> List[FileInfo]:
        """扫描 Python 文件"""
        return self._scan_files_by_extension(['.py'])
    
    def scan_config_files(self) -> List[FileInfo]:
        """扫描配置文件"""
        return self._scan_files_by_extension(['.json', '.ini', '.yaml', '.yml', '.toml'])
    
    def scan_resource_files(self) -> List[FileInfo]:
        """扫描资源文件"""
        return self._scan_files_by_extension(['.qss', '.png', '.jpg', '.ico', '.svg'])
    
    def _scan_files_by_extension(self, extensions: List[str]) -> List[FileInfo]:
        """按扩展名扫描文件
        
        Args:
            extensions: 文件扩展名列表
            
        Returns:
            文件信息列表
        """
        files = []
        
        for root, dirs, filenames in os.walk(self.project_root):
            # 过滤排除的目录
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            root_path = Path(root)
            
            for filename in filenames:
                # 跳过排除的文件
                if filename in self.exclude_files:
                    continue
                
                file_path = root_path / filename
                
                # 检查扩展名
                if file_path.suffix.lower() in extensions:
                    try:
                        stat = file_path.stat()
                        file_type = self._get_file_type(file_path)
                        is_test = self._is_test_file(file_path)
                        
                        files.append(FileInfo(
                            path=file_path,
                            file_type=file_type,
                            size=stat.st_size,
                            last_modified=stat.st_mtime,
                            is_test=is_test
                        ))
                    except Exception as e:
                        # 忽略无法访问的文件
                        print(f"警告: 无法访问文件 {file_path}: {e}")
                        continue
        
        return files
    
    def _get_file_type(self, file_path: Path) -> str:
        """获取文件类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件类型: python, config, resource
        """
        ext = file_path.suffix.lower()
        
        if ext == '.py':
            return 'python'
        elif ext in ['.json', '.ini', '.yaml', '.yml', '.toml']:
            return 'config'
        else:
            return 'resource'
    
    def _is_test_file(self, file_path: Path) -> bool:
        """判断是否为测试文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否为测试文件
        """
        # 检查是否在 tests 目录下
        parts = file_path.parts
        if 'tests' in parts or 'test' in parts:
            return True
        
        # 检查文件名是否以 test_ 开头
        if file_path.stem.startswith('test_'):
            return True
        
        return False

