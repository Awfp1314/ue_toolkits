# -*- coding: utf-8 -*-

"""
废弃代码分析器

识别标记为废弃的代码。
"""

import ast
import re
from typing import List
from pathlib import Path
from .base import BaseAnalyzer
from ..models import Issue, AnalysisContext
from ..ast_parser import ASTParser


class DeprecatedAnalyzer(BaseAnalyzer):
    """废弃代码分析器"""
    
    def __init__(self, config: dict = None):
        """初始化分析器"""
        super().__init__(config)
        self.parser = ASTParser()
        self.keywords = self.config.get('keywords', ['deprecated', '废弃', '已弃用', 'DEPRECATED'])
    
    def get_category(self) -> str:
        """获取分析类别"""
        return "deprecated"
    
    def analyze(self, context: AnalysisContext) -> List[Issue]:
        """执行分析"""
        issues = []
        
        for file_info in context.python_files:
            tree = self.parser.parse_file(file_info.path)
            if tree is None:
                continue
            
            # 读取文件内容以检查注释
            try:
                with open(file_info.path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
            except Exception:
                continue
            
            # 检测装饰器
            issues.extend(self._detect_deprecated_decorators(tree, file_info.path))
            
            # 检测注释
            issues.extend(self._detect_deprecated_comments(lines, file_info.path))
        
        return issues
    
    def _detect_deprecated_decorators(self, tree: ast.Module, file_path: Path) -> List[Issue]:
        """检测 @deprecated 装饰器"""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                for decorator in node.decorator_list:
                    decorator_name = self._get_decorator_name(decorator)
                    if 'deprecated' in decorator_name.lower():
                        issues.append(Issue(
                            category="deprecated",
                            severity="medium",
                            file_path=file_path,
                            line_number=node.lineno,
                            description=f"废弃的 {node.__class__.__name__}: {node.name}",
                            suggestion=f"考虑删除第 {node.lineno} 行的废弃代码，或更新为新的实现"
                        ))
        
        return issues
    
    def _detect_deprecated_comments(self, lines: List[str], file_path: Path) -> List[Issue]:
        """检测废弃注释"""
        issues = []
        
        for i, line in enumerate(lines, 1):
            # 检查注释中是否包含废弃关键词
            if '#' in line:
                comment = line[line.index('#'):]
                for keyword in self.keywords:
                    if keyword in comment:
                        issues.append(Issue(
                            category="deprecated",
                            severity="low",
                            file_path=file_path,
                            line_number=i,
                            description=f"包含废弃标记的代码",
                            suggestion=f"检查第 {i} 行附近的代码是否可以删除"
                        ))
                        break
        
        return issues
    
    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """获取装饰器名称"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id
            elif isinstance(decorator.func, ast.Attribute):
                return decorator.func.attr
        return ''

