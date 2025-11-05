# -*- coding: utf-8 -*-

"""
统一的嵌入服务（无logger版本用于测试）
使用单例模式管理语义模型（BAAI/bge-small-zh-v1.5）
"""

from typing import Optional, Union, List
import numpy as np


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
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model_name = model_name
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, model_name: str = "BAAI/bge-small-zh-v1.5"):
        if self._initialized:
            return
        
        self._model_name = model_name
        self._initialized = True
        
        if EmbeddingService._lock is None:
            import threading
            EmbeddingService._lock = threading.Lock()
    
    def get_embedder(self):
        if not EmbeddingService._model_loaded:
            self._load_model()
        return EmbeddingService._embedder
    
    def encode_text(self, text: Union[str, List[str]], convert_to_numpy: bool = True) -> Union[np.ndarray, List[float], None]:
        embedder = self.get_embedder()
        if embedder is None:
            return None
        try:
            embeddings = embedder.encode(text, convert_to_numpy=convert_to_numpy)
            return embeddings
        except Exception as e:
            print(f"Encoding error: {e}")
            return None
    
    def _load_model(self):
        with EmbeddingService._lock:
            if EmbeddingService._model_loaded:
                return
            EmbeddingService._model_loaded = True
            try:
                print(f"Loading model: {self._model_name}...")
                from sentence_transformers import SentenceTransformer
                EmbeddingService._embedder = SentenceTransformer(self._model_name)
                print("Model loaded successfully")
            except Exception as e:
                print(f"Model loading failed: {e}")
                EmbeddingService._embedder = None
    
    def is_loaded(self) -> bool:
        return EmbeddingService._model_loaded and EmbeddingService._embedder is not None
    
    def get_embedding_dimension(self) -> Optional[int]:
        embedder = self.get_embedder()
        if embedder is None:
            return None
        try:
            return embedder.get_sentence_embedding_dimension()
        except Exception as e:
            print(f"Error: {e}")
            return None

