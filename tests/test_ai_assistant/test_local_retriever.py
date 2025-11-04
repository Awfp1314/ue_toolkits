# -*- coding: utf-8 -*-

"""
LocalDocIndex 单元测试
验证本地文档索引和 Chroma 数据库持久化
"""

import pytest
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modules.ai_assistant.logic.local_retriever import LocalDocIndex


@pytest.fixture
def temp_db():
    """临时数据库目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def local_index(temp_db):
    """创建 LocalDocIndex 实例"""
    return LocalDocIndex(db_path=temp_db)


class TestLocalDocIndex:
    """LocalDocIndex 测试套件"""
    
    def test_initialization(self, local_index):
        """测试初始化"""
        assert local_index is not None
        assert local_index.db_path.exists()
    
    def test_upsert_and_search(self, local_index):
        """测试文档插入和搜索"""
        # 准备测试文档
        docs = [
            {
                'id': 'doc_1',
                'content': '如何使用虚幻引擎的蓝图系统创建游戏逻辑',
                'metadata': {'source': 'test.md', 'type': 'tutorial'}
            },
            {
                'id': 'doc_2',
                'content': '虚幻引擎材质编辑器的基本操作指南',
                'metadata': {'source': 'materials.md', 'type': 'guide'}
            },
            {
                'id': 'doc_3',
                'content': 'Lumen 全局光照系统的配置方法',
                'metadata': {'source': 'lumen.md', 'type': 'config'}
            }
        ]
        
        # 插入文档
        local_index.upsert_docs(docs)
        
        # 搜索：蓝图
        results = local_index.search("蓝图系统", top_k=2)
        
        assert len(results) > 0
        assert '蓝图' in results[0]['content']
        assert 'metadata' in results[0]
        assert 'distance' in results[0]
    
    def test_search_with_metadata_filter(self, local_index):
        """测试带元数据过滤的搜索"""
        docs = [
            {
                'id': 'tutorial_1',
                'content': '蓝图教程内容',
                'metadata': {'type': 'tutorial', 'level': 'beginner'}
            },
            {
                'id': 'guide_1',
                'content': '蓝图指南内容',
                'metadata': {'type': 'guide', 'level': 'advanced'}
            }
        ]
        
        local_index.upsert_docs(docs)
        
        # 只搜索 tutorial 类型
        results = local_index.search(
            "蓝图",
            top_k=5,
            filter_metadata={'type': 'tutorial'}
        )
        
        # 结果应该只包含 tutorial
        for result in results:
            if result['metadata'].get('type'):
                assert result['metadata']['type'] == 'tutorial'
    
    def test_persistence(self, temp_db):
        """测试数据库持久化"""
        # 第一个实例：插入数据
        index1 = LocalDocIndex(db_path=temp_db)
        index1.upsert_docs([{
            'id': 'persistent_doc',
            'content': '这是一个持久化测试文档',
            'metadata': {'test': 'persistence'}
        }])
        
        # 第二个实例：应该能读取到数据
        index2 = LocalDocIndex(db_path=temp_db)
        results = index2.search("持久化测试", top_k=1)
        
        assert len(results) > 0
        assert '持久化' in results[0]['content']
    
    def test_get_stats(self, local_index):
        """测试统计信息"""
        docs = [
            {'id': f'doc_{i}', 'content': f'测试文档 {i}'} 
            for i in range(5)
        ]
        local_index.upsert_docs(docs)
        
        stats = local_index.get_stats()
        
        assert 'total_documents' in stats
        assert stats['total_documents'] >= 5
        assert 'db_path' in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

