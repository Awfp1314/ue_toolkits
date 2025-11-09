# -*- coding: utf-8 -*-

"""
重复代码分析器

使用 Rabin-Karp 算法检测重复代码。
"""

import ast
from typing import List, Dict, Set, Tuple
from pathlib import Path
from collections import defaultdict
from .base import BaseAnalyzer
from ..models import Issue, AnalysisContext
from ..ast_parser import ASTParser


class DuplicateAnalyzer(BaseAnalyzer):
    """重复代码分析器"""
    
    def __init__(self, config: dict = None):
        """初始化分析器"""
        super().__init__(config)
        self.parser = ASTParser()
        self.min_lines = self.config.get('min_lines', 5)  # 最小重复行数
        self.similarity_threshold = self.config.get('similarity_threshold', 0.8)  # 相似度阈值
        self.prime = 101  # Rabin-Karp 算法使用的质数
        self.base = 256   # 字符集大小
    
    def get_category(self) -> str:
        """获取分析类别"""
        return "duplicate_code"
    
    def analyze(self, context: AnalysisContext) -> List[Issue]:
        """执行分析"""
        issues = []
        
        # 提取所有函数的代码块
        code_blocks = self._extract_code_blocks(context)
        
        # 使用 Rabin-Karp 算法查找重复
        duplicates = self._find_duplicates(code_blocks)
        
        # 生成问题报告
        for (hash_val, normalized_code), locations in duplicates.items():
            if len(locations) < 2:
                continue
            
            # 计算代码行数
            lines = normalized_code.count('\n') + 1
            
            # 生成问题描述
            locations_str = ', '.join([f"{loc[0]}:{loc[1]}" for loc in locations[:3]])
            if len(locations) > 3:
                locations_str += f" 等 {len(locations)} 处"
            
            # 为每个重复位置创建一个问题
            for file_path, line_number, original_code in locations:
                issues.append(Issue(
                    category="duplicate_code",
                    severity="medium",
                    file_path=file_path,
                    line_number=line_number,
                    description=f"发现重复代码 ({lines} 行)，在 {len(locations)} 个位置重复",
                    suggestion=f"考虑将重复代码提取为公共函数。重复位置: {locations_str}",
                    code_snippet=original_code[:200] if len(original_code) > 200 else original_code
                ))
        
        return issues
    
    def _extract_code_blocks(self, context: AnalysisContext) -> List[Tuple[Path, int, str, str]]:
        """提取所有代码块
        
        Returns:
            List of (file_path, line_number, original_code, normalized_code)
        """
        code_blocks = []
        
        for file_info in context.python_files:
            if file_info.is_test:
                continue
            
            tree = self.parser.parse_file(file_info.path)
            if tree is None:
                continue
            
            # 读取文件内容
            try:
                with open(file_info.path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            except Exception:
                continue
            
            # 提取函数体
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if len(node.body) < self.min_lines:
                        continue
                    
                    # 获取函数体代码
                    start_line = node.body[0].lineno - 1
                    end_line = node.body[-1].end_lineno if hasattr(node.body[-1], 'end_lineno') else node.body[-1].lineno
                    
                    if start_line < len(lines) and end_line <= len(lines):
                        original_code = ''.join(lines[start_line:end_line])
                        normalized_code = self._normalize_code(original_code)
                        
                        if len(normalized_code.strip()) > 0:
                            code_blocks.append((
                                file_info.path,
                                node.lineno,
                                original_code,
                                normalized_code
                            ))
        
        return code_blocks
    
    def _normalize_code(self, code: str) -> str:
        """标准化代码（去除空白、注释等）"""
        lines = []
        for line in code.split('\n'):
            # 去除注释
            if '#' in line:
                line = line[:line.index('#')]
            # 去除前后空白
            line = line.strip()
            if line:
                lines.append(line)
        return '\n'.join(lines)
    
    def _find_duplicates(self, code_blocks: List[Tuple[Path, int, str, str]]) -> Dict[Tuple[int, str], List[Tuple[Path, int, str]]]:
        """使用 Rabin-Karp 算法查找重复代码"""
        hash_map = defaultdict(list)
        
        for file_path, line_number, original_code, normalized_code in code_blocks:
            # 计算哈希值
            hash_val = self._rolling_hash(normalized_code)
            
            # 存储到哈希表
            hash_map[(hash_val, normalized_code)].append((file_path, line_number, original_code))
        
        # 过滤出真正的重复（相似度检查）
        duplicates = {}
        for key, locations in hash_map.items():
            if len(locations) >= 2:
                # 验证相似度
                if self._verify_similarity(locations):
                    duplicates[key] = locations
        
        return duplicates
    
    def _rolling_hash(self, text: str) -> int:
        """计算滚动哈希值（Rabin-Karp 算法）"""
        hash_val = 0
        for char in text:
            hash_val = (hash_val * self.base + ord(char)) % self.prime
        return hash_val
    
    def _verify_similarity(self, locations: List[Tuple[Path, int, str]]) -> bool:
        """验证代码块之间的相似度"""
        if len(locations) < 2:
            return False
        
        # 简单验证：检查第一个和第二个代码块的相似度
        code1 = locations[0][2]
        code2 = locations[1][2]
        
        # 使用简单的字符串相似度
        similarity = self._calculate_similarity(code1, code2)
        return similarity >= self.similarity_threshold
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度（简化版 Jaccard 相似度）"""
        # 标准化
        norm1 = self._normalize_code(text1)
        norm2 = self._normalize_code(text2)
        
        # 分词
        tokens1 = set(norm1.split())
        tokens2 = set(norm2.split())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        # Jaccard 相似度
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        
        return intersection / union if union > 0 else 0.0

