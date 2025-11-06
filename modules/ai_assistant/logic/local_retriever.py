# -*- coding: utf-8 -*-

"""
本地文档检索器
基于 Chroma 向量数据库的本地知识检索
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from core.logger import get_logger
from core.ai_services import EmbeddingService

# 延迟获取 logger
def _get_logger():
    return get_logger(__name__)

logger = None


class BGEEmbeddingFunction:
    """
    适配 ChromaDB 的嵌入函数包装器
    使用统一的 EmbeddingService (bge-small-zh-v1.5)
    """
    
    def __init__(self, embedding_service: EmbeddingService):
        """
        初始化嵌入函数
        
        Args:
            embedding_service: 统一的嵌入服务实例
        """
        self.embedding_service = embedding_service
    
    def name(self) -> str:
        """ChromaDB 需要的方法（不是属性）"""
        return "bge-small-zh-v1.5"
    
    def __call__(self, input: List[str]) -> List[List[float]]:
        """
        ChromaDB 要求的接口：接收文本列表，返回向量列表
        
        Args:
            input: 文本列表
            
        Returns:
            List[List[float]]: 向量列表
        """
        # 使用 EmbeddingService 批量编码
        embeddings = self.embedding_service.encode_text(input, convert_to_numpy=False)
        
        if embeddings is None:
            # 如果编码失败，返回零向量
            dimension = self.embedding_service.get_embedding_dimension() or 384
            return [[0.0] * dimension for _ in input]
        
        # 转换为列表格式（ChromaDB 需要）
        if hasattr(embeddings, 'tolist'):
            return embeddings.tolist()
        return list(embeddings)


class LocalDocIndex:
    """
    本地文档索引
    
    基于 Chroma 向量数据库，用于检索本地文档、README、配置模板等
    """
    
    def __init__(self, db_path: Optional[Path] = None, embedding_service: Optional[EmbeddingService] = None):
        """
        初始化本地文档索引
        
        Args:
            db_path: Chroma 数据库路径（默认由 PathUtils 提供）
            embedding_service: 嵌入服务实例（默认创建新实例）
        """
        self.logger = _get_logger()  # 延迟获取
        
        # 数据库路径
        if db_path is None:
            try:
                from core.utils.path_utils import PathUtils
                path_utils = PathUtils()
                self.db_path = path_utils.get_user_data_dir() / "chroma_db"
            except Exception as e:
                self.logger.warning(f"无法获取用户数据目录，使用默认路径: {e}")
                self.db_path = Path.home() / ".ue_toolkit" / "chroma_db"
        else:
            self.db_path = db_path
        
        # 确保目录存在
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        # 使用统一的 EmbeddingService（单例模式）
        self.embedding_service = embedding_service or EmbeddingService()
        
        # 创建适配 ChromaDB 的嵌入函数
        self._embedding_function = BGEEmbeddingFunction(self.embedding_service)
        
        # 延迟初始化 Chroma（避免启动时加载）
        self._client = None
        self._collection = None
        
        self.logger.info(f"本地文档索引初始化（数据库路径: {self.db_path}，使用统一嵌入服务）")
    
    def _init_chroma(self):
        """延迟初始化 Chroma 客户端"""
        if self._client is not None:
            return
        
        try:
            import chromadb
            from chromadb.config import Settings
            
            # 创建持久化客户端
            self._client = chromadb.PersistentClient(
                path=str(self.db_path),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # 获取或创建集合（使用 get_or_create，让 ChromaDB 处理冲突）
            self._collection = self._client.get_or_create_collection(
                name="ue_toolkit_docs",
                metadata={"description": "UE Toolkit local documentation index (bge-small-zh-v1.5)"},
                embedding_function=self._embedding_function
            )
            self.logger.info(f"文档集合已就绪: ue_toolkit_docs")
            
            # 不调用 count()，避免触发崩溃
            self.logger.info(f"Chroma 客户端初始化成功（使用 bge-small-zh-v1.5）")
            
        except Exception as e:
            self.logger.error(f"初始化 Chroma 失败: {e}", exc_info=True)
            raise
    
    def upsert_docs(self, docs: List[Dict[str, Any]]):
        """
        插入或更新文档到索引
        
        Args:
            docs: 文档列表，每个文档包含 {'id', 'content', 'metadata'}
                 例如：[{
                     'id': 'doc_1',
                     'content': '文档内容...',
                     'metadata': {'source': 'README.md', 'path': '/path/to/file'}
                 }]
        """
        try:
            self._init_chroma()
            
            if not docs:
                self.logger.warning("文档列表为空，跳过索引")
                return
            
            # 准备数据
            ids = [doc['id'] for doc in docs]
            documents = [doc['content'] for doc in docs]
            metadatas = [doc.get('metadata', {}) for doc in docs]
            
            # 添加时间戳
            for metadata in metadatas:
                metadata['indexed_at'] = datetime.now().isoformat()
            
            # 批量插入
            self._collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
            self.logger.info(f"成功索引 {len(docs)} 个文档")
            
        except Exception as e:
            self.logger.error(f"索引文档失败: {e}", exc_info=True)
    
    def search(self, query: str, top_k: int = 5, filter_metadata: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        搜索相关文档
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            filter_metadata: 元数据过滤条件（可选）
        
        Returns:
            List[Dict]: 搜索结果列表，每个结果包含 {'content', 'metadata', 'distance'}
        """
        try:
            self._init_chroma()
            
            self.logger.info(f"📚 [文档向量检索] 启动 ChromaDB 文档语义搜索（查询: '{query[:30]}...'）")
            
            # 执行查询
            results = self._collection.query(
                query_texts=[query],
                n_results=top_k,
                where=filter_metadata
            )
            
            # 格式化结果
            formatted_results = []
            
            if results['documents'] and len(results['documents']) > 0:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else 0.0
                    })
            
            if formatted_results:
                self.logger.info(f"✅ [文档向量检索] ChromaDB 成功检索到 {len(formatted_results)} 个相关文档片段")
            else:
                self.logger.info("⚠️ [文档向量检索] ChromaDB 未找到匹配文档")
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"搜索文档失败: {e}", exc_info=True)
            return []
    
    def index_project_docs(self, project_root: Path):
        """
        索引项目文档
        
        Args:
            project_root: 项目根目录
        """
        try:
            docs_to_index = []
            
            # 1. 索引 docs/ 目录
            docs_dir = project_root / "docs"
            if docs_dir.exists():
                docs_to_index.extend(self._scan_directory(docs_dir, "docs"))
            
            # 2. 索引 README.md 文件
            readme_files = [
                project_root / "README.md",
                project_root / "Ue_Toolkit使用文档.md",
                project_root / "虚幻资产工具箱使用文档.md"
            ]
            for readme in readme_files:
                if readme.exists():
                    docs_to_index.extend(self._index_file(readme, "readme"))
            
            # 3. 索引模块 README
            modules_dir = project_root / "modules"
            if modules_dir.exists():
                for module_dir in modules_dir.iterdir():
                    if module_dir.is_dir():
                        module_readme = module_dir / "README.md"
                        if module_readme.exists():
                            docs_to_index.extend(self._index_file(module_readme, f"module:{module_dir.name}"))
            
            # 4. 索引配置模板描述
            config_templates_dir = project_root / "core" / "config_templates"
            if config_templates_dir.exists():
                docs_to_index.extend(self._scan_directory(config_templates_dir, "config_template"))
            
            # 执行批量索引
            if docs_to_index:
                self.upsert_docs(docs_to_index)
                self.logger.info(f"项目文档索引完成，共 {len(docs_to_index)} 个文档")
            else:
                self.logger.warning("未找到可索引的文档")
            
        except Exception as e:
            self.logger.error(f"索引项目文档失败: {e}", exc_info=True)
    
    def _scan_directory(self, directory: Path, source_type: str) -> List[Dict[str, Any]]:
        """扫描目录并准备文档"""
        docs = []
        
        try:
            for file_path in directory.rglob("*.md"):
                docs.extend(self._index_file(file_path, source_type))
            
            # 也索引 .txt 文件
            for file_path in directory.rglob("*.txt"):
                docs.extend(self._index_file(file_path, source_type))
                
        except Exception as e:
            self.logger.error(f"扫描目录失败: {e}")
        
        return docs
    
    def _index_file(self, file_path: Path, source_type: str) -> List[Dict[str, Any]]:
        """索引单个文件（分段）"""
        docs = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 按段落分割（避免单个文档过大）
            chunks = self._split_content(content, max_length=1000)
            
            for i, chunk in enumerate(chunks):
                doc_id = f"{file_path.stem}_{i}_{hash(chunk) % 100000}"
                
                docs.append({
                    'id': doc_id,
                    'content': chunk,
                    'metadata': {
                        'source': str(file_path.name),
                        'path': str(file_path),
                        'source_type': source_type,
                        'chunk_index': i,
                        'total_chunks': len(chunks)
                    }
                })
        
        except Exception as e:
            self.logger.error(f"索引文件失败 {file_path}: {e}")
        
        return docs
    
    def _split_content(self, content: str, max_length: int = 1000) -> List[str]:
        """分割长文本为多个段落"""
        if len(content) <= max_length:
            return [content]
        
        # 按段落分割
        paragraphs = content.split('\n\n')
        
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) <= max_length:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [content[:max_length]]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取索引统计信息
        
        注意：不调用 count()，因为会导致崩溃
        """
        try:
            self._init_chroma()
            
            return {
                'total_documents': 'N/A',  # 不调用 count() 避免崩溃
                'db_path': str(self.db_path),
                'collection_name': self._collection.name if self._collection else None,
                'status': 'active'
            }
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            return {'total_documents': 'N/A', 'db_path': str(self.db_path), 'status': 'error'}

