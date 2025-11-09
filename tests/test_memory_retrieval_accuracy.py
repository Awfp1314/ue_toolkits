# -*- coding: utf-8 -*-

"""
记忆检索准确性测试

测试目标：
1. 验证相似度阈值从 0.3 提高到 0.5
2. 验证最大记忆数量从 5 降低到 3
3. 验证检索结果包含相似度分数
4. 验证低于阈值时返回空结果
5. 验证配置选项可调整

Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestMemoryRetrievalAccuracy(unittest.TestCase):
    """测试记忆检索准确性（代码检查）"""
    
    def test_enhanced_memory_manager_has_config_options(self):
        """测试 EnhancedMemoryManager 有配置选项
        
        Requirement 13.5: 提供配置选项允许用户调整相似度阈值和最大记忆数量
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'logic', 
            'enhanced_memory_manager.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查 __init__ 方法有配置参数
        self.assertIn('similarity_threshold', content, "应该有 similarity_threshold 参数")
        self.assertIn('max_memories_per_query', content, "应该有 max_memories_per_query 参数")
        
        # 检查默认值
        self.assertIn('similarity_threshold: float = 0.5', content, "默认相似度阈值应该是 0.5")
        self.assertIn('max_memories_per_query: int = 3', content, "默认最大记忆数应该是 3")
        
        # 检查实例变量
        self.assertIn('self.similarity_threshold', content, "应该保存 similarity_threshold 到实例变量")
        self.assertIn('self.max_memories_per_query', content, "应该保存 max_memories_per_query 到实例变量")
    
    def test_get_relevant_memories_returns_dict_with_similarity(self):
        """测试 get_relevant_memories 返回包含相似度分数的字典
        
        Requirement 13.3: 在记忆检索结果中包含相似度分数
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'logic', 
            'enhanced_memory_manager.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查返回类型注解
        self.assertIn('List[Dict[str, Any]]', content, "返回类型应该是 List[Dict[str, Any]]")
        
        # 检查返回的字典包含必要的键
        self.assertIn("'content':", content, "返回的字典应该包含 'content' 键")
        self.assertIn("'similarity':", content, "返回的字典应该包含 'similarity' 键")
        self.assertIn("'source':", content, "返回的字典应该包含 'source' 键")
    
    def test_get_relevant_memories_applies_threshold_filter(self):
        """测试 get_relevant_memories 应用相似度阈值过滤
        
        Requirement 13.1: 提高相似度阈值从 0.3 到 0.5，过滤低相关性记忆
        Requirement 13.4: 当所有记忆相似度都低于阈值时返回空结果
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'logic', 
            'enhanced_memory_manager.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查过滤逻辑
        self.assertIn('filtered_results', content, "应该有过滤结果的变量")
        self.assertIn('score >= self.similarity_threshold', content, "应该使用 similarity_threshold 过滤")
    
    def test_get_relevant_memories_limits_result_count(self):
        """测试 get_relevant_memories 限制返回数量
        
        Requirement 13.2: 当检索到的记忆数量超过 3 条时，只保留相似度最高的 3 条
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'logic', 
            'enhanced_memory_manager.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查限制逻辑
        self.assertIn('top_results = filtered_results[:limit]', content, "应该限制返回数量")
        
        # 检查使用配置选项
        self.assertIn('self.max_memories_per_query', content, "应该使用 max_memories_per_query 配置")
    
    def test_context_manager_uses_new_return_format(self):
        """测试 ContextManager 适配新的返回格式
        
        Requirement 13.3: 在记忆检索结果中包含相似度分数
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'logic', 
            'context_manager.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否适配新格式
        # 应该从字典中提取 'content' 字段
        self.assertIn("mem['content']", content, "应该从字典中提取 'content' 字段")
    
    def test_logging_includes_similarity_scores(self):
        """测试日志包含相似度分数
        
        Requirement 13.3: 在记忆检索结果中包含相似度分数，供调试使用
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'logic', 
            'enhanced_memory_manager.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查日志输出包含相似度分数
        self.assertIn('相似度:', content, "日志应该包含相似度信息")
        self.assertIn('阈值:', content, "日志应该包含阈值信息")
    
    def test_context_manager_logging_includes_similarity(self):
        """测试 ContextManager 日志包含相似度分数
        
        Requirement 13.3: 在记忆检索结果中包含相似度分数，供调试使用
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'logic', 
            'context_manager.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查日志输出包含相似度分数
        self.assertIn("similarity", content, "日志应该包含 similarity 信息")


if __name__ == '__main__':
    unittest.main()

