# -*- coding: utf-8 -*-

"""
增强型记忆管理器（基于 Mem0 概念）
提供多级记忆、向量检索和智能上下文管理
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from collections import deque
from core.logger import get_logger
from core.ai_services import EmbeddingService

logger = get_logger(__name__)


class MemoryLevel:
    """记忆级别枚举"""
    USER = "user"           # 用户级（跨会话持久化）
    SESSION = "session"     # 会话级（当前会话）
    CONTEXT = "context"     # 上下文级（最近几轮）


class Memory:
    """记忆项"""
    
    def __init__(self, content: str, level: str = MemoryLevel.SESSION, 
                 metadata: Optional[Dict] = None, timestamp: Optional[str] = None):
        self.content = content
        self.level = level
        self.metadata = metadata or {}
        self.timestamp = timestamp or datetime.now().isoformat()
        self.importance = self.metadata.get('importance', 0.5)  # 0-1，重要性评分


class EnhancedMemoryManager:
    """增强型记忆管理器
    
    参考 Mem0 设计理念：
    - 多级记忆（用户/会话/上下文）
    - 智能检索和过滤
    - 记忆重要性评分
    - 持久化存储
    """
    
    def __init__(self, user_id: str = "default", storage_dir: Optional[Path] = None, memory_compressor=None,
                 embedding_service: Optional[EmbeddingService] = None, db_client=None):
        """初始化记忆管理器
        
        Args:
            user_id: 用户ID（用于用户级记忆）
            storage_dir: 存储目录（用于持久化）
            memory_compressor: 记忆压缩器实例（可选）
            embedding_service: 嵌入服务实例（用于向量化）
            db_client: ChromaDB 客户端实例（用于向量存储）
        """
        self.user_id = user_id
        self.logger = logger
        
        # 存储目录
        if storage_dir:
            self.storage_dir = Path(storage_dir)
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        else:
            from core.utils.path_utils import PathUtils
            path_utils = PathUtils()
            self.storage_dir = path_utils.get_user_data_dir() / "ai_memory"
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.memory_file = self.storage_dir / f"{user_id}_memory.json"
        
        # 记忆存储
        self.user_memories: List[Memory] = []      # 用户级（持久化）
        self.session_memories: List[Memory] = []   # 会话级（临时）
        self.context_buffer = deque(maxlen=10)     # 上下文缓冲（最近10轮）
        self.compressed_summary: Optional[str] = None  # 压缩后的历史摘要
        
        # 记忆压缩器
        self.memory_compressor = memory_compressor
        
        # 向量检索支持
        self.embedding_service = embedding_service or EmbeddingService()
        self.db_client = db_client
        self._memory_collection = None
        
        # 初始化 ChromaDB 集合（如果提供了 db_client）
        if self.db_client is not None:
            self._init_memory_collection()
        
        # 加载持久化记忆
        self._load_user_memories()
        
        self.logger.info(f"增强型记忆管理器初始化完成（用户: {user_id}，向量检索: {'已启用' if self.db_client else '未启用'}）")
    
    def _init_memory_collection(self):
        """初始化 ChromaDB 记忆集合"""
        try:
            from modules.ai_assistant.logic.local_retriever import BGEEmbeddingFunction
            
            # 创建嵌入函数包装器
            embedding_func = BGEEmbeddingFunction(self.embedding_service)
            
            # 获取或创建记忆集合
            self._memory_collection = self.db_client.get_or_create_collection(
                name=f"user_memory_{self.user_id}",
                metadata={"description": f"User memory for {self.user_id} (bge-small-zh-v1.5)"},
                embedding_function=embedding_func
            )
            
            self.logger.info(f"ChromaDB 记忆集合初始化成功，记忆数量: {self._memory_collection.count()}")
            
        except Exception as e:
            self.logger.error(f"初始化 ChromaDB 记忆集合失败: {e}", exc_info=True)
            self._memory_collection = None
    
    def add_memory(self, content: str, level: str = MemoryLevel.SESSION, 
                   metadata: Optional[Dict] = None, auto_evaluate: bool = True):
        """添加记忆
        
        Args:
            content: 记忆内容
            level: 记忆级别
            metadata: 元数据（如类型、标签等）
            auto_evaluate: 是否自动评估重要性
        """
        memory = Memory(content, level, metadata)
        
        # 自动评估重要性（简单规则，可扩展为 AI 评估）
        if auto_evaluate:
            memory.importance = self._evaluate_importance(content, metadata)
        
        # 根据级别添加到对应存储
        if level == MemoryLevel.USER:
            self.user_memories.append(memory)
            self._save_user_memories()  # 持久化到 JSON（冷备份）
            
            # 同时存储到 ChromaDB 向量数据库
            if self._memory_collection is not None:
                try:
                    # 生成唯一 ID
                    memory_id = f"{self.user_id}_{memory.timestamp}_{hash(content) % 100000}"
                    
                    # 准备元数据
                    chroma_metadata = {
                        'timestamp': memory.timestamp,
                        'importance': memory.importance,
                        'level': level,
                        'user_id': self.user_id
                    }
                    # 合并用户提供的元数据
                    if metadata:
                        chroma_metadata.update({k: str(v) for k, v in metadata.items()})
                    
                    # 存入 ChromaDB（会自动向量化）
                    self._memory_collection.upsert(
                        ids=[memory_id],
                        documents=[content],
                        metadatas=[chroma_metadata]
                    )
                    
                    self.logger.debug(f"记忆已向量化并存入 ChromaDB: {memory_id}")
                    
                except Exception as e:
                    self.logger.error(f"存储记忆到 ChromaDB 失败: {e}", exc_info=True)
        
        elif level == MemoryLevel.SESSION:
            self.session_memories.append(memory)
        elif level == MemoryLevel.CONTEXT:
            self.context_buffer.append(memory)
        
        self.logger.debug(f"添加记忆 [{level}]: {content[:50]}... (重要性: {memory.importance:.2f})")
    
    def add_dialogue(self, user_query, assistant_response: str, 
                    auto_classify: bool = True):
        """添加对话到记忆
        
        Args:
            user_query: 用户查询（字符串或列表）
            assistant_response: AI 回复
            auto_classify: 是否自动分类重要性并选择存储级别
        """
        # 处理列表类型的 user_query
        if isinstance(user_query, list):
            # 提取所有文本内容
            user_query_text = " ".join(str(item.get("text", item)) if isinstance(item, dict) else str(item) for item in user_query)
        else:
            user_query_text = str(user_query)
        
        # 添加用户查询
        metadata_user = {'type': 'user_query'}
        level = MemoryLevel.CONTEXT  # 默认上下文级
        
        if auto_classify:
            # 智能判断是否值得长期保存
            if self._is_important_query(user_query_text):
                level = MemoryLevel.USER
                metadata_user['tags'] = ['重要查询']
                self.logger.info(f"[重要查询] 保存到用户级记忆: {user_query_text[:50]}...")
        
        self.add_memory(f"用户: {user_query_text}", level, metadata_user)
        
        # 添加 AI 回复（精简版）
        response_summary = assistant_response[:200] + "..." if len(assistant_response) > 200 else assistant_response
        metadata_assistant = {'type': 'assistant_response'}
        self.add_memory(f"助手: {response_summary}", MemoryLevel.CONTEXT, metadata_assistant)
        
        self.logger.info(f"[对话已保存] 用户级:{len(self.user_memories)}, 会话级:{len(self.session_memories)}, 上下文:{len(self.context_buffer)}")
    
    def get_relevant_memories(self, query: str, limit: int = 5, 
                             min_importance: float = 0.3) -> List[str]:
        """获取相关记忆（基于向量语义检索）
        
        Args:
            query: 查询内容
            limit: 返回数量限制
            min_importance: 最小重要性阈值
            
        Returns:
            List[str]: 相关记忆列表
        """
        self.logger.info(f"[记忆检索] 查询: '{query[:50]}...'")
        
        results = []
        
        # 1. 从 ChromaDB 向量检索用户级记忆（语义相似度）
        if self._memory_collection is not None:
            try:
                # 使用向量相似度搜索
                search_results = self._memory_collection.query(
                    query_texts=[query],
                    n_results=min(limit, 10),  # 多取一些备选
                    where={"user_id": self.user_id}  # 过滤当前用户
                )
                
                if search_results['documents'] and len(search_results['documents']) > 0:
                    for i, content in enumerate(search_results['documents'][0]):
                        metadata = search_results['metadatas'][0][i] if search_results['metadatas'] else {}
                        distance = search_results['distances'][0][i] if search_results['distances'] else 1.0
                        importance = float(metadata.get('importance', 0.5))
                        
                        # 过滤低重要性记忆
                        if importance < min_importance:
                            continue
                        
                        # 向量相似度得分（距离越小越相似）
                        similarity_score = 1.0 - distance
                        
                        results.append((content, similarity_score, 'vector_user'))
                        
                    self.logger.info(f"从 ChromaDB 检索到 {len(results)} 条用户级记忆")
            
            except Exception as e:
                self.logger.error(f"ChromaDB 向量检索失败: {e}", exc_info=True)
        
        # 2. 从会话级和上下文级记忆中检索（关键词匹配作为补充）
        query_lower = query.lower()
        query_words = [w for w in query_lower.split() if len(w) > 1]
        
        # 会话级记忆
        for memory in self.session_memories:
            if memory.importance < min_importance:
                continue
            
            content_lower = memory.content.lower()
            matches = sum(1 for word in query_words if word in content_lower)
            
            if matches > 0:
                score = matches * 0.5 + memory.importance * 0.3
                results.append((memory.content, score, 'keyword_session'))
        
        # 上下文级记忆（最近对话）
        for memory in list(self.context_buffer):
            content_lower = memory.content.lower()
            matches = sum(1 for word in query_words if word in content_lower)
            
            if matches > 0:
                score = matches * 0.3 + memory.importance * 0.2
                results.append((memory.content, score, 'keyword_context'))
        
        # 3. 合并并排序结果
        results.sort(key=lambda x: x[1], reverse=True)
        
        # 调试日志
        self.logger.info(f"[记忆检索] 共找到 {len(results)} 条相关记忆")
        self.logger.info(f"[记忆评分] 前 {min(5, len(results))} 条记忆:")
        for i, (content, score, source) in enumerate(results[:5], 1):
            self.logger.info(f"  {i}. [{source}] 评分:{score:.2f} | {content[:60]}...")
        
        # 返回前 N 条
        return [content for content, score, source in results[:limit]]
    
    def get_recent_context(self, limit: int = 5) -> str:
        """获取最近的上下文（格式化为字符串）
        
        Args:
            limit: 获取数量
            
        Returns:
            str: 格式化的上下文（包含压缩摘要）
        """
        formatted = []
        
        # 如果有压缩摘要，先添加
        if self.compressed_summary:
            formatted.append(self.compressed_summary)
        
        # 添加最近的原始对话
        recent = list(self.context_buffer)[-limit:]
        if recent:
            formatted.append("[最近对话上下文]")
            for memory in recent:
                formatted.append(memory.content)
        
        return "\n".join(formatted) if formatted else ""
    
    def get_user_identity(self) -> str:
        """获取用户身份信息（应该融入AI角色设定的记忆）
        
        从用户级记忆中提取身份、角色、人设相关的信息
        
        Returns:
            str: 用户身份信息（如果有）
        """
        if not self.user_memories:
            return ""
        
        # 检索身份相关的记忆（使用更精确的匹配规则）
        # 只匹配明确的身份设定语句，避免匹配普通对话
        identity_patterns = [
            '从现在开始你是',
            '从现在开始你不是', 
            '你现在是',
            '扮演猫娘',
            '你是猫娘',
            '不是猫娘了',
            '恢复你的原来身份',
            '你的身份是',
            '你的角色是'
        ]
        identity_memories = []
        
        # 只检查用户级记忆（Memory类型）中标记为"用户相关信息"的记忆
        for memory in self.user_memories:
            content = memory.content
            # 必须同时满足：1) 包含"用户相关信息"或"用户偏好" 2) 包含身份设定短语
            is_user_info = content.startswith("用户相关信息:") or content.startswith("用户偏好:")
            has_identity_pattern = any(pattern in content for pattern in identity_patterns)
            
            if is_user_info and has_identity_pattern:
                identity_memories.append(memory)
        
        if not identity_memories:
            return ""
        
        # 返回最新的身份记忆（按时间戳排序，只取最后一条）
        # 避免返回多条矛盾的身份设定
        identity_memories.sort(key=lambda m: m.timestamp)
        latest_identity = identity_memories[-1].content
        return latest_identity  # 只返回最新的1条身份记忆
    
    def get_user_profile(self) -> str:
        """获取用户画像（从用户级记忆中提取，排除身份信息）
        
        Returns:
            str: 用户画像信息
        """
        if not self.user_memories:
            return ""
        
        # 提取高重要性记忆，但排除身份相关的（避免重复）
        identity_keywords = ['猫娘', '身份', '我是', '叫我', '角色', '人设', '喵']
        important_memories = [
            m for m in self.user_memories 
            if m.importance > 0.7 and not any(keyword in m.content.lower() for keyword in identity_keywords)
        ]
        
        if not important_memories:
            return ""
        
        profile = ["[用户习惯和偏好]"]
        for memory in important_memories[-5:]:  # 最近5条重要记忆
            profile.append(f"- {memory.content}")
        
        return "\n".join(profile)
    
    def compress_old_context(self, conversation_history: List[Dict[str, str]]) -> bool:
        """压缩旧对话历史为摘要
        
        当对话历史过长时，自动触发压缩，将旧消息压缩为摘要
        
        Args:
            conversation_history: 完整的对话历史列表
            
        Returns:
            bool: 是否成功压缩
        """
        if not self.memory_compressor:
            self.logger.warning("记忆压缩器未设置，无法压缩")
            return False
        
        # 检查是否需要压缩
        if not self.memory_compressor.should_compress(len(conversation_history)):
            return False
        
        try:
            # 获取需要压缩的旧消息（保留最近的几条）
            keep_recent = self.memory_compressor.keep_recent
            old_messages = conversation_history[:-keep_recent] if len(conversation_history) > keep_recent else []
            
            if not old_messages:
                return False
            
            # 生成压缩摘要
            summary = self.memory_compressor.compress_history(old_messages)
            
            if summary:
                self.compressed_summary = summary
                self.logger.info(f"✅ 成功压缩 {len(old_messages)} 条历史消息")
                return True
            
            return False
        
        except Exception as e:
            self.logger.error(f"压缩历史时出错: {e}", exc_info=True)
            return False
    
    def clear_session(self):
        """清空会话级记忆"""
        self.session_memories.clear()
        self.context_buffer.clear()
        self.compressed_summary = None  # 清空压缩摘要
        self.logger.info("会话记忆已清空")
    
    def _evaluate_importance(self, content: str, metadata: Optional[Dict] = None) -> float:
        """评估记忆重要性（简单规则，可扩展为 AI 评分）
        
        Args:
            content: 内容
            metadata: 元数据
            
        Returns:
            float: 重要性评分 (0-1)
        """
        score = 0.5  # 默认中等重要性
        
        # 规则1：包含特定关键词提升重要性
        important_keywords = ['错误', '配置', '路径', '文件', '资产', '设置', '问题']
        content_lower = content.lower()
        matches = sum(1 for keyword in important_keywords if keyword in content_lower)
        score += matches * 0.1
        
        # 规则2：内容长度（过长或过短降低重要性）
        if 20 < len(content) < 200:
            score += 0.1
        
        # 规则3：元数据标签
        if metadata and 'tags' in metadata:
            if '重要' in str(metadata['tags']):
                score += 0.2
        
        return min(1.0, max(0.0, score))
    
    def _is_important_query(self, query) -> bool:
        """判断查询是否重要（值得长期保存）
        
        Args:
            query: 查询内容（字符串或列表）
            
        Returns:
            bool: 是否重要
        """
        # 处理列表类型（多部分消息）
        if isinstance(query, list):
            # 提取所有文本内容
            query_text = " ".join(str(item.get("text", item)) if isinstance(item, dict) else str(item) for item in query)
        else:
            query_text = str(query)
        
        # 包含特定关键词的查询视为重要
        important_indicators = ['怎么', '如何', '为什么', '配置', '设置', '问题', '错误']
        query_lower = query_text.lower()
        
        return any(indicator in query_lower for indicator in important_indicators)
    
    def _load_user_memories(self):
        """从文件加载用户级记忆"""
        try:
            if self.memory_file.exists():
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for item in data.get('memories', []):
                    memory = Memory(
                        content=item['content'],
                        level=MemoryLevel.USER,
                        metadata=item.get('metadata', {}),
                        timestamp=item.get('timestamp')
                    )
                    memory.importance = item.get('importance', 0.5)
                    self.user_memories.append(memory)
                
                self.logger.info(f"加载了 {len(self.user_memories)} 条用户记忆")
        
        except Exception as e:
            self.logger.error(f"加载用户记忆失败: {e}")
    
    def _save_user_memories(self):
        """保存用户级记忆到文件"""
        try:
            data = {
                'user_id': self.user_id,
                'updated_at': datetime.now().isoformat(),
                'memories': [
                    {
                        'content': m.content,
                        'importance': m.importance,
                        'metadata': m.metadata,
                        'timestamp': m.timestamp
                    }
                    for m in self.user_memories
                ]
            }
            
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"保存了 {len(self.user_memories)} 条用户记忆")
        
        except Exception as e:
            self.logger.error(f"保存用户记忆失败: {e}")

