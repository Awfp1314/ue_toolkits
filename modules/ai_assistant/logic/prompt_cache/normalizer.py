"""
内容规范化和哈希管理
用于确保相同语义的内容生成相同哈希
"""

import hashlib
import json
import re
from typing import Any, List, Dict


class ContentNormalizer:
    """内容规范化器"""
    
    @staticmethod
    def normalize_content(content: Any, content_type: str = 'text') -> str:
        """
        规范化内容
        
        Args:
            content: 原始内容
            content_type: 内容类型（text/tools/json）
        
        Returns:
            规范化后的字符串
        """
        if content_type == 'text':
            return ContentNormalizer._normalize_text(content)
        elif content_type == 'tools':
            return ContentNormalizer._normalize_tools(content)
        elif content_type == 'json':
            return ContentNormalizer._normalize_json(content)
        else:
            return str(content)
    
    @staticmethod
    def _normalize_text(text: str) -> str:
        """规范化普通文本"""
        if not isinstance(text, str):
            text = str(text)
        
        # 统一换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # 去除首尾空白
        text = text.strip()
        
        # 压缩多余空白（保留单个换行和空格）
        text = re.sub(r' +', ' ', text)  # 多个空格→单个空格
        text = re.sub(r'\n{3,}', '\n\n', text)  # 多个换行→最多2个
        
        return text
    
    @staticmethod
    def _normalize_tools(tools: List[Dict]) -> str:
        """规范化工具定义（排序+格式化）"""
        if not tools:
            return ""
        
        # 按工具名称排序
        sorted_tools = sorted(tools, key=lambda t: t.get('function', {}).get('name', ''))
        
        # 转为紧凑 JSON（无多余空格）
        return json.dumps(sorted_tools, ensure_ascii=False, separators=(',', ':'), sort_keys=True)
    
    @staticmethod
    def _normalize_json(data: Any) -> str:
        """规范化 JSON 数据"""
        return json.dumps(data, ensure_ascii=False, separators=(',', ':'), sort_keys=True)
    
    @staticmethod
    def hash_content(normalized_content: str) -> str:
        """
        对规范化内容生成哈希
        
        Args:
            normalized_content: 规范化后的内容
        
        Returns:
            SHA256 哈希（前16位）
        """
        hash_obj = hashlib.sha256(normalized_content.encode('utf-8'))
        return hash_obj.hexdigest()[:16]  # 前16位足够区分
    
    @staticmethod
    def estimate_tokens(content: str) -> int:
        """
        估算 token 数量
        
        规则：
        - 中文：1字 ≈ 1 token
        - 英文：3.5字符 ≈ 1 token
        - JSON：按实际长度
        
        Args:
            content: 内容字符串
        
        Returns:
            估算的 token 数
        """
        if not content:
            return 0
        
        # 统计中文字符
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
        
        # 统计非中文字符
        non_chinese_chars = len(content) - chinese_chars
        
        # 估算
        chinese_tokens = chinese_chars
        english_tokens = non_chinese_chars / 3.5
        
        return int(chinese_tokens + english_tokens)

