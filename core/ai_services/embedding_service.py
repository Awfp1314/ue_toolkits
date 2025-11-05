# -*- coding: utf-8 -*-

"""
统一的嵌入服务
使用单例模式管理语义模型（BAAI/bge-small-zh-v1.5）
"""

from typing import Optional, Union, List
import numpy as np
from core.logger import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """
    嵌入服务（单例模式）
    
    特性：
    - 全局唯一的 SentenceTransformer 实例
    - 延迟加载（首次调用时才加载模型）
    - 线程安全的单例实现
    """
    
    _instance: Optional['EmbeddingService'] = None
    _embedder = None  # SentenceTransformer 实例
    _model_loaded = False
    _lock = None  # 延迟导入 threading.Lock
    
    def __new__(cls, model_name: str = "BAAI/bge-small-zh-v1.5"):
        """
        单例模式实现
        
        Args:
            model_name: 模型名称或路径
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model_name = model_name
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, model_name: str = "BAAI/bge-small-zh-v1.5"):
        """
        初始化嵌入服务（仅在首次创建时执行）
        
        Args:
            model_name: 模型名称或路径
        """
        # 防止重复初始化
        if self._initialized:
            return
        
        self._model_name = model_name
        self._initialized = True
        
        # 初始化锁（延迟导入以避免循环依赖）
        if EmbeddingService._lock is None:
            import threading
            EmbeddingService._lock = threading.Lock()
        
        logger.info(f"嵌入服务已创建（模型: {model_name}，延迟加载模式）")
    
    def get_embedder(self):
        """
        获取 SentenceTransformer 实例（延迟加载）
        
        Returns:
            SentenceTransformer: 嵌入模型实例，如果加载失败则返回 None
        """
        if not EmbeddingService._model_loaded:
            self._load_model()
        
        return EmbeddingService._embedder
    
    def encode_text(
        self, 
        text: Union[str, List[str]], 
        convert_to_numpy: bool = True,
        normalize_embeddings: bool = False
    ) -> Union[np.ndarray, List[float], None]:
        """
        将文本编码为向量
        
        Args:
            text: 单个文本或文本列表
            convert_to_numpy: 是否转换为 numpy 数组
            normalize_embeddings: 是否归一化向量
            
        Returns:
            向量或向量列表，如果模型未加载则返回 None
        """
        embedder = self.get_embedder()
        
        if embedder is None:
            logger.error("嵌入模型未加载，无法编码文本")
            return None
        
        try:
            embeddings = embedder.encode(
                text, 
                convert_to_numpy=convert_to_numpy,
                normalize_embeddings=normalize_embeddings
            )
            return embeddings
        
        except Exception as e:
            logger.error(f"文本编码失败: {e}", exc_info=True)
            return None
    
    def encode_batch(
        self, 
        texts: List[str], 
        batch_size: int = 32,
        show_progress: bool = False
    ) -> Optional[np.ndarray]:
        """
        批量编码文本（适用于大量文本）
        
        Args:
            texts: 文本列表
            batch_size: 批次大小
            show_progress: 是否显示进度条
            
        Returns:
            向量数组，如果模型未加载则返回 None
        """
        embedder = self.get_embedder()
        
        if embedder is None:
            logger.error("嵌入模型未加载，无法批量编码")
            return None
        
        try:
            embeddings = embedder.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True
            )
            return embeddings
        
        except Exception as e:
            logger.error(f"批量编码失败: {e}", exc_info=True)
            return None
    
    def _load_model(self):
        """
        延迟加载模型（线程安全）
        
        注意：使用全局锁确保多线程环境下只加载一次
        """
        with EmbeddingService._lock:
            # 双重检查锁定模式
            if EmbeddingService._model_loaded:
                return
            
            EmbeddingService._model_loaded = True
            
            try:
                logger.info(f"开始加载语义模型: {self._model_name}...")
                from sentence_transformers import SentenceTransformer
                
                EmbeddingService._embedder = SentenceTransformer(self._model_name)
                
                logger.info(f"✅ 语义模型加载成功: {self._model_name}")
                logger.info(f"   向量维度: {EmbeddingService._embedder.get_sentence_embedding_dimension()}")
                
            except Exception as e:
                logger.error(f"❌ 语义模型加载失败: {e}", exc_info=True)
                EmbeddingService._embedder = None
    
    def is_loaded(self) -> bool:
        """
        检查模型是否已加载
        
        Returns:
            bool: 模型是否已成功加载
        """
        return EmbeddingService._model_loaded and EmbeddingService._embedder is not None
    
    def get_embedding_dimension(self) -> Optional[int]:
        """
        获取嵌入向量的维度
        
        Returns:
            int: 向量维度，如果模型未加载则返回 None
        """
        embedder = self.get_embedder()
        
        if embedder is None:
            return None
        
        try:
            return embedder.get_sentence_embedding_dimension()
        except Exception as e:
            logger.error(f"获取向量维度失败: {e}")
            return None
    
    @classmethod
    def reset(cls):
        """
        重置单例实例（主要用于测试）
        """
        cls._instance = None
        cls._embedder = None
        cls._model_loaded = False
        logger.info("嵌入服务已重置")

