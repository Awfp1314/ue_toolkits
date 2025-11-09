"""
FAISS 向量存储管理器

功能：
- 使用 FAISS 作为主存储引擎
- 高效的向量相似度检索
- 支持元数据存储和过滤
- 自动持久化到磁盘
- JSON 备份机制

作者：AI Assistant
日期：2025-11-06
"""

import json
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import logging


def _get_logger():
    """获取日志记录器"""
    return logging.getLogger("ue_toolkit.modules.ai_assistant.logic.faiss_memory_store")


class FaissMemoryStore:
    """FAISS 向量存储管理器
    
    架构设计：
    1. FAISS 索引：存储向量，支持高效检索
    2. 元数据映射：ID -> {content, metadata, timestamp, importance}
    3. 磁盘持久化：定期保存到磁盘
    4. JSON 备份：灾难恢复
    """
    
    def __init__(self, storage_dir: Path, vector_dim: int = 512, user_id: str = "default",
                 batch_delete_threshold: int = 50):
        """初始化 FAISS 存储

        Args:
            storage_dir: 存储目录
            vector_dim: 向量维度（默认 512，匹配 bge-small-zh-v1.5）
            user_id: 用户 ID
            batch_delete_threshold: 批量删除阈值（默认 50）
        """
        self.logger = _get_logger()
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.user_id = user_id
        self.vector_dim = vector_dim
        self.batch_delete_threshold = batch_delete_threshold

        # 文件路径
        self.index_file = self.storage_dir / f"{user_id}_faiss.index"
        self.metadata_file = self.storage_dir / f"{user_id}_metadata.pkl"
        self.backup_file = self.storage_dir / f"{user_id}_backup.json"

        # 初始化 FAISS 索引
        self.index = None
        self.id_to_metadata = {}  # {memory_id: {content, metadata, timestamp, importance, deleted}}
        self.next_id = 0

        # ⚡ Requirement 7.1, 7.2: 延迟删除优化
        self._pending_deletes = 0  # 待删除计数器

        # 加载现有数据
        self._load_from_disk()

        self.logger.info(f"✅ FAISS 存储初始化完成（用户: {user_id}, 向量维度: {vector_dim}, 已有记忆: {self.count()}, 批量删除阈值: {batch_delete_threshold}）")
    
    def _load_from_disk(self):
        """从磁盘加载索引和元数据"""
        try:
            # 尝试加载 FAISS 索引
            if self.index_file.exists():
                import faiss
                self.index = faiss.read_index(str(self.index_file))
                self.logger.info(f"📂 已加载 FAISS 索引: {self.index.ntotal} 条记录")
            else:
                # 创建新索引（使用 L2 距离）
                import faiss
                self.index = faiss.IndexFlatL2(self.vector_dim)
                self.logger.info("📂 创建新 FAISS 索引")
            
            # 加载元数据
            if self.metadata_file.exists():
                with open(self.metadata_file, 'rb') as f:
                    data = pickle.load(f)
                    self.id_to_metadata = data.get('id_to_metadata', {})
                    self.next_id = data.get('next_id', 0)
                    # ⚡ Requirement 7.5: 加载待删除计数器
                    self._pending_deletes = data.get('pending_deletes', 0)
                self.logger.info(f"📂 已加载元数据: {len(self.id_to_metadata)} 条记录（待删除: {self._pending_deletes}）")
            
        except Exception as e:
            self.logger.warning(f"⚠️ 加载 FAISS 存储时出错: {e}，将创建新存储")
            import faiss
            self.index = faiss.IndexFlatL2(self.vector_dim)
            self.id_to_metadata = {}
            self.next_id = 0
    
    def add(self, content: str, vector: np.ndarray, metadata: Optional[Dict] = None, 
            importance: float = 0.5) -> str:
        """添加记忆到存储
        
        Args:
            content: 记忆内容
            vector: 向量（shape: (vector_dim,) 或 (1, vector_dim)）
            metadata: 元数据
            importance: 重要性评分
            
        Returns:
            str: 记忆 ID
        """
        try:
            # 确保向量格式正确
            vector = self._prepare_vector(vector)
            
            # 生成唯一 ID
            memory_id = str(self.next_id)
            self.next_id += 1
            
            # 添加到 FAISS 索引
            self.index.add(vector)
            
            # 保存元数据
            self.id_to_metadata[memory_id] = {
                'content': content,
                'metadata': metadata or {},
                'timestamp': datetime.now().isoformat(),
                'importance': importance,
                'deleted': False  # ⚡ Requirement 7.1: 添加删除标记
            }
            
            self.logger.debug(f"✅ [FAISS] 已添加记忆 ID={memory_id}: {content[:50]}...")
            
            # 定期持久化
            if len(self.id_to_metadata) % 10 == 0:
                self._save_to_disk()
            
            return memory_id
            
        except Exception as e:
            self.logger.error(f"❌ [FAISS] 添加记忆失败: {e}", exc_info=True)
            raise
    
    def search(self, query_vector: np.ndarray, top_k: int = 5, 
               min_importance: float = 0.3) -> List[Tuple[str, float, Dict]]:
        """语义检索
        
        Args:
            query_vector: 查询向量
            top_k: 返回数量
            min_importance: 最小重要性阈值
            
        Returns:
            List[Tuple[content, similarity_score, metadata]]: 检索结果
        """
        try:
            if self.count() == 0:
                return []
            
            # 确保向量格式正确
            query_vector = self._prepare_vector(query_vector)
            
            # FAISS 检索
            distances, indices = self.index.search(query_vector, min(top_k * 2, self.count()))
            
            # 转换为相似度分数（L2 距离 -> 相似度）
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx == -1:  # FAISS 返回 -1 表示无结果
                    continue

                memory_id = str(idx)
                if memory_id not in self.id_to_metadata:
                    continue

                meta = self.id_to_metadata[memory_id]

                # ⚡ Requirement 7.3: 过滤已删除的记忆
                if meta.get('deleted', False):
                    continue

                # 过滤低重要性
                if meta['importance'] < min_importance:
                    continue
                
                # 转换距离为相似度（距离越小，相似度越高）
                similarity = 1.0 / (1.0 + distance)
                
                results.append((
                    meta['content'],
                    float(similarity),
                    meta['metadata']
                ))
            
            # 按相似度排序并限制数量
            results.sort(key=lambda x: x[1], reverse=True)
            results = results[:top_k]
            
            self.logger.debug(f"🔍 [FAISS] 检索到 {len(results)} 条记忆")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ [FAISS] 检索失败: {e}", exc_info=True)
            return []
    
    def update(self, memory_id: str, content: Optional[str] = None, 
               vector: Optional[np.ndarray] = None, metadata: Optional[Dict] = None,
               importance: Optional[float] = None):
        """更新记忆
        
        注意：FAISS 不支持原地更新向量，需要重建索引
        """
        if memory_id not in self.id_to_metadata:
            self.logger.warning(f"⚠️ [FAISS] 记忆 ID={memory_id} 不存在")
            return
        
        # 更新元数据
        meta = self.id_to_metadata[memory_id]
        if content is not None:
            meta['content'] = content
        if metadata is not None:
            meta['metadata'].update(metadata)
        if importance is not None:
            meta['importance'] = importance
        
        # 如果更新向量，需要重建索引
        if vector is not None:
            self.logger.warning("⚠️ [FAISS] 更新向量需要重建索引，操作较慢")
            self._rebuild_index()
        
        self.logger.debug(f"✅ [FAISS] 已更新记忆 ID={memory_id}")
    
    def delete(self, memory_id: str):
        """删除记忆

        ⚡ Requirement 7.1, 7.2: 使用延迟删除优化
        - 标记为删除而不是立即重建索引
        - 达到阈值时批量重建
        """
        if memory_id not in self.id_to_metadata:
            self.logger.warning(f"⚠️ [FAISS] 记忆 ID={memory_id} 不存在")
            return

        # 标记为删除
        if not self.id_to_metadata[memory_id].get('deleted', False):
            self.id_to_metadata[memory_id]['deleted'] = True
            self._pending_deletes += 1
            self.logger.debug(f"✅ [FAISS] 已标记删除 ID={memory_id}（待删除: {self._pending_deletes}/{self.batch_delete_threshold}）")

            # 达到阈值时批量重建
            if self._pending_deletes >= self.batch_delete_threshold:
                self.logger.info(f"🔄 [FAISS] 达到批量删除阈值（{self._pending_deletes}），开始重建索引...")
                self._rebuild_index()
                self._pending_deletes = 0
            else:
                # 未达到阈值，只保存元数据
                self._save_to_disk()
    
    def count(self) -> int:
        """获取记忆数量（包括已删除但未清理的）"""
        return self.index.ntotal if self.index else 0

    def count_active(self) -> int:
        """获取活跃记忆数量（不包括已删除的）

        ⚡ Requirement 7.3: 提供活跃记忆计数
        """
        return sum(1 for meta in self.id_to_metadata.values() if not meta.get('deleted', False))

    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息

        Returns:
            Dict: {
                'total': 总记忆数（包括已删除）,
                'active': 活跃记忆数,
                'deleted': 已删除但未清理的记忆数,
                'pending_deletes': 待删除计数器,
                'threshold': 批量删除阈值
            }
        """
        total = len(self.id_to_metadata)
        active = self.count_active()
        deleted = total - active

        return {
            'total': total,
            'active': active,
            'deleted': deleted,
            'pending_deletes': self._pending_deletes,
            'threshold': self.batch_delete_threshold,
            'needs_rebuild': self._pending_deletes >= self.batch_delete_threshold
        }
    
    def get_all_metadata(self) -> Dict:
        """获取所有元数据（用于备份）"""
        return {
            'id_to_metadata': self.id_to_metadata,
            'next_id': self.next_id,
            'user_id': self.user_id,
            'vector_dim': self.vector_dim,
            'count': self.count(),
            'last_updated': datetime.now().isoformat()
        }
    
    def _prepare_vector(self, vector: np.ndarray) -> np.ndarray:
        """准备向量格式（FAISS 要求 float32, shape: (1, dim)）"""
        if not isinstance(vector, np.ndarray):
            vector = np.array(vector, dtype=np.float32)
        
        if vector.dtype != np.float32:
            vector = vector.astype(np.float32)
        
        if vector.ndim == 1:
            vector = vector.reshape(1, -1)
        
        if vector.shape[1] != self.vector_dim:
            raise ValueError(f"向量维度不匹配: 期望 {self.vector_dim}, 实际 {vector.shape[1]}")
        
        return vector
    
    def _rebuild_index(self):
        """重建 FAISS 索引（用于删除/更新操作）

        ⚡ Requirement 7.4: 重建时移除已删除的记忆
        """
        try:
            import faiss
            from core.ai_services.embedding_service import EmbeddingService

            # ⚡ 第一步：移除已删除的记忆
            deleted_ids = [mid for mid, meta in self.id_to_metadata.items() if meta.get('deleted', False)]
            for memory_id in deleted_ids:
                del self.id_to_metadata[memory_id]

            if deleted_ids:
                self.logger.info(f"🗑️ [FAISS] 重建时移除 {len(deleted_ids)} 条已删除记忆")

            # 创建新索引
            new_index = faiss.IndexFlatL2(self.vector_dim)

            # 重新生成所有向量并添加（只添加未删除的）
            embedding_service = EmbeddingService()

            for memory_id, meta in self.id_to_metadata.items():
                # 跳过已删除的（防御性检查）
                if meta.get('deleted', False):
                    continue

                content = meta['content']
                vector = embedding_service.encode_text([content], convert_to_numpy=True)
                if vector is not None:
                    vector = self._prepare_vector(vector)
                    new_index.add(vector)

            self.index = new_index
            self.logger.info(f"✅ [FAISS] 索引重建完成: {self.count()} 条记录")

            # 立即持久化
            self._save_to_disk()

        except Exception as e:
            self.logger.error(f"❌ [FAISS] 索引重建失败: {e}", exc_info=True)
    
    def _save_to_disk(self):
        """保存到磁盘

        ⚡ Requirement 7.5: 持久化删除标记和待删除计数器
        """
        try:
            import faiss

            # 保存 FAISS 索引
            faiss.write_index(self.index, str(self.index_file))

            # 保存元数据（包括删除标记和待删除计数器）
            with open(self.metadata_file, 'wb') as f:
                pickle.dump({
                    'id_to_metadata': self.id_to_metadata,
                    'next_id': self.next_id,
                    'pending_deletes': self._pending_deletes  # ⚡ 持久化待删除计数器
                }, f)
            
            # 保存 JSON 备份
            self._backup_to_json()
            
            self.logger.debug(f"💾 [FAISS] 已保存到磁盘: {self.count()} 条记录")
            
        except Exception as e:
            self.logger.error(f"❌ [FAISS] 保存失败: {e}", exc_info=True)
    
    def _backup_to_json(self):
        """备份到 JSON（用于灾难恢复）

        ⚡ Requirement 7.5: 备份时跳过已删除的记忆
        """
        try:
            backup_data = {
                'user_id': self.user_id,
                'vector_dim': self.vector_dim,
                'count': self.count(),
                'memories': []
            }

            for memory_id, meta in self.id_to_metadata.items():
                # ⚡ 跳过已删除的记忆
                if meta.get('deleted', False):
                    continue

                backup_data['memories'].append({
                    'id': memory_id,
                    'content': meta['content'],
                    'metadata': meta['metadata'],
                    'timestamp': meta['timestamp'],
                    'importance': meta['importance']
                })
            
            with open(self.backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"💾 [JSON备份] 已备份 {len(backup_data['memories'])} 条记忆")
            
        except Exception as e:
            self.logger.warning(f"⚠️ [JSON备份] 备份失败: {e}")
    
    def force_rebuild(self):
        """强制重建索引（清理所有已删除的记忆）

        ⚡ Requirement 7.2: 提供手动触发重建的接口
        """
        if self._pending_deletes > 0:
            self.logger.info(f"🔄 [FAISS] 手动触发重建，清理 {self._pending_deletes} 条已删除记忆")
            self._rebuild_index()
            self._pending_deletes = 0
        else:
            self.logger.info("ℹ️ [FAISS] 无需重建，没有待删除的记忆")

    def close(self):
        """关闭存储（保存数据）

        ⚡ 关闭前检查是否需要清理
        """
        # 如果有大量待删除记忆，在关闭前清理
        if self._pending_deletes > 0:
            self.logger.info(f"🔄 [FAISS] 关闭前清理 {self._pending_deletes} 条已删除记忆")
            self._rebuild_index()
            self._pending_deletes = 0
        else:
            self._save_to_disk()

        self.logger.info("✅ [FAISS] 存储已关闭并保存")

