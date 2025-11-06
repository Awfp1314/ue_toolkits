# -*- coding: utf-8 -*-

"""
增强型记忆管理器（基于 Mem0 概念）
提供多级记忆、向量检索和智能上下文管理

升级说明：
- 使用 FAISS 替代 ChromaDB（更稳定，Windows 兼容性好）
- FAISS 为主存储，JSON 为备份存储
- 语义检索性能更优
"""

import json
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from collections import deque
from core.logger import get_logger
from core.ai_services import EmbeddingService
from modules.ai_assistant.logic.faiss_memory_store import FaissMemoryStore

# 延迟获取 logger，避免模块导入时卡住
def _get_logger():
    return get_logger(__name__)

logger = None  # 延迟初始化


# 注意：BGEEmbeddingFunctionForMemory 已移除，FAISS 不需要


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
            db_client: 已废弃（兼容性保留，FAISS 不需要此参数）
        """
        self.user_id = user_id
        self.logger = _get_logger()  # 延迟获取 logger
        
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
        self.user_memories: List[Memory] = []      # 用户级（持久化）- JSON 备份
        self.session_memories: List[Memory] = []   # 会话级（临时）
        self.context_buffer = deque(maxlen=10)     # 上下文缓冲（最近10轮）
        self.compressed_summary: Optional[str] = None  # 压缩后的历史摘要
        
        # 记忆压缩器
        self.memory_compressor = memory_compressor
        
        # 向量检索支持（FAISS）
        self.embedding_service = embedding_service or EmbeddingService()
        
        # 初始化 FAISS 向量存储（主存储）
        self.faiss_store = None
        try:
            self.logger.info("🔧 [FAISS] 正在初始化向量存储...")
            self.faiss_store = FaissMemoryStore(
                storage_dir=self.storage_dir,
                vector_dim=512,  # bge-small-zh-v1.5 维度
                user_id=user_id
            )
            self.logger.info(f"✅ FAISS 向量存储已启用（用户: {user_id}，记忆数: {self.faiss_store.count()}）")
        except ImportError as e:
            self.logger.warning(f"⚠️ FAISS 模块未安装，将使用纯 JSON 模式: {e}")
            self.faiss_store = None
        except Exception as e:
            self.logger.error(f"❌ FAISS 初始化失败，将使用纯 JSON 模式: {e}", exc_info=True)
            self.faiss_store = None
        
        # 加载持久化记忆（JSON 备份）
        try:
            self._load_user_memories()
        except Exception as e:
            self.logger.error(f"加载用户记忆时出错（非致命）: {e}", exc_info=True)
        
        # 自动迁移：如果 FAISS 为空但 JSON 有数据，自动迁移
        if self.faiss_store is not None:
            self._auto_migrate_json_to_faiss()
        
        self.logger.info(f"增强型记忆管理器初始化完成（用户: {user_id}，FAISS向量检索: {'已启用' if self.faiss_store else '未启用'}）")
    
    # _init_memory_collection 方法已移除（FAISS 不需要）
    
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
            self._save_user_memories()  # 备份到 JSON（灾难恢复）
            
            # FAISS 向量存储（主存储）
            if self.faiss_store is not None:
                try:
                    # 生成向量
                    vector = self.embedding_service.encode_text([content], convert_to_numpy=True)
                    
                    if vector is not None:
                        # 存入 FAISS
                        self.faiss_store.add(
                            content=content,
                            vector=vector,
                            metadata=metadata,
                            importance=memory.importance
                        )
                        self.logger.debug(f"✅ [FAISS] 记忆已保存: {content[:50]}...")
                    else:
                        self.logger.warning("⚠️ [FAISS] 向量生成失败，已跳过")
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ [FAISS] 存储失败（非致命）: {e}")
                    # FAISS 失败不影响主流程，JSON 已保存
        
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
        
        # 智能保存：只保存有价值的信息，而不是简单的问答
        if auto_classify:
            # 判断用户查询是否包含有价值的信息（陈述句、偏好、身份等）
            if self._contains_valuable_info(user_query_text):
                # 保存用户提供的信息到用户级记忆
                metadata_user = {'type': 'user_info', 'tags': ['偏好', '身份']}
                self.add_memory(user_query_text, MemoryLevel.USER, metadata_user)
                self.logger.info(f"✅ [有价值信息] 保存到用户级记忆: {user_query_text[:50]}...")
            else:
                # 普通问答，只保存到上下文缓冲
                metadata_context = {'type': 'dialogue'}
                dialogue_content = f"Q: {user_query_text[:100]}\nA: {assistant_response[:100]}"
                self.add_memory(dialogue_content, MemoryLevel.CONTEXT, metadata_context)
                self.logger.debug(f"[普通对话] 保存到上下文缓冲")
        else:
            # 不分类，直接保存到上下文
            metadata_context = {'type': 'dialogue'}
            self.add_memory(f"用户: {user_query_text}", MemoryLevel.CONTEXT, metadata_context)
        
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
        
        # 预处理查询词（用于关键词检索）
        query_lower = query.lower()
        query_words = set([w for w in query_lower.split() if len(w) > 1])
        
        # 1. 从 FAISS 向量检索用户级记忆（语义相似度）
        if self.faiss_store is not None and self.faiss_store.count() > 0:
            try:
                self.logger.info("🔮 [FAISS 检索] 启动语义搜索...")
                
                # 生成查询向量
                query_vector = self.embedding_service.encode_text([query], convert_to_numpy=True)
                
                if query_vector is not None:
                    # FAISS 检索
                    faiss_results = self.faiss_store.search(
                        query_vector=query_vector,
                        top_k=limit * 2,
                        min_importance=min_importance
                    )
                    
                    for content, similarity, metadata in faiss_results:
                        results.append((content, similarity, 'faiss_vector'))
                    
                    self.logger.info(f"✅ [FAISS 检索] 找到 {len(results)} 条记忆（语义相似度匹配）")
                else:
                    self.logger.warning("⚠️ [FAISS 检索] 向量生成失败")
                    
            except Exception as e:
                self.logger.error(f"❌ [FAISS 检索] 检索失败: {e}")
        else:
            self.logger.info("⚠️ [FAISS 检索] 向量存储未启用或为空，使用 JSON 备份检索")
            
            # 降级到关键词匹配（FAISS 不可用时）
            for memory in self.user_memories:
                if memory.importance < min_importance:
                    continue
                
                content_lower = memory.content.lower()
                matched_words = sum(1 for word in query_words if word in content_lower)
                if matched_words > 0:
                    similarity_score = matched_words / max(len(query_words), 1)
                    results.append((memory.content, similarity_score, 'json_fallback'))
            
            self.logger.info(f"✅ [JSON 备份检索] 找到 {len(results)} 条记忆")
        
        # 2. 从会话级和上下文级记忆中检索（关键词匹配作为补充）
        self.logger.info("🔍 [关键词检索] 扫描会话级和上下文级记忆...")
        
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
        
        从用户级记忆中提取所有重要的用户相关信息
        
        Returns:
            str: 用户身份信息（如果有）
        """
        if not self.user_memories:
            return ""
        
        # ⚠️ 修复失忆问题：只返回"陈述句"（答案），过滤掉"疑问句"（用户的提问）
        important_memories = []
        
        # 疑问词列表（用于过滤问题）
        question_keywords = ['什么', '怎么', '如何', '为什么', '哪', '吗', '呢', '?', '？']
        
        for memory in self.user_memories:
            content = memory.content
            
            # 只保留高重要性的记忆（>0.7）或明确的"用户相关信息"
            is_user_info = content.startswith("用户相关信息:") or content.startswith("用户偏好:")
            is_important = memory.importance > 0.7
            
            if not (is_user_info or is_important):
                continue
            
            # ⚠️ 关键修复：过滤掉疑问句（用户的提问）
            # 提取核心内容
            core_content = content.replace("用户相关信息:", "").replace("用户偏好:", "").strip()
            
            # 如果包含疑问词，说明这是用户的问题，不是答案，跳过
            is_question = any(keyword in core_content for keyword in question_keywords)
            
            # ✅ 只保留陈述句（答案），比如"我喜欢胡桃"
            if not is_question:
                important_memories.append((memory, core_content))
        
        if not important_memories:
            return ""
        
        # 按重要性排序（重要性高的在后）
        important_memories.sort(key=lambda m: m[0].importance)
        
        # 去重：如果多条记忆内容相似，只保留重要性最高的
        unique_memories = []
        seen_contents = set()
        
        for memory, core_content in important_memories:
            # 简单去重：只保留前30个字符进行比较
            content_key = core_content[:30]
            
            if content_key not in seen_contents:
                unique_memories.append(memory.content)
                seen_contents.add(content_key)
        
        # 限制数量：最多返回10条最重要的记忆（避免Token过多）
        if len(unique_memories) > 10:
            unique_memories = unique_memories[-10:]
        
        # 组合所有记忆，用换行分隔
        result = "\n".join(unique_memories)
        
        # Debug log
        if hasattr(self, 'logger') and self.logger:
            self.logger.info(f"[get_user_identity] 返回 {len(unique_memories)} 条记忆（已过滤疑问句）")
        
        return result
    
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
    
    def _contains_valuable_info(self, text: str) -> bool:
        """判断文本是否包含有价值的信息（陈述句、偏好、身份等）
        
        Args:
            text: 用户输入文本
            
        Returns:
            bool: 是否包含有价值信息
        """
        text_lower = text.lower()
        
        # 强问句标志：直接排除
        strong_question_indicators = [
            '你还记得', '你知道', '你觉得', '是不是', 
            '能不能', '会不会', '有没有'
        ]
        if any(q in text_lower for q in strong_question_indicators):
            return False
        
        # 一般疑问句标志
        question_words = ['吗', '呢', '？', '?', '什么', '怎么', '如何', '为什么', '哪', '谁']
        is_question = any(word in text_lower for word in question_words)
        
        # 陈述关键词（必须在句子开头）
        statement_patterns = [
            '我喜欢玩', '我喜欢', '我是', '我叫', '我在', '我的名字',
            '我想', '我觉得', '我认为', '我需要', '我有', '我用',
            '正在开发', '正在做', '擅长', '最喜欢的'
        ]
        has_statement = any(text_lower.startswith(p) for p in statement_patterns)
        
        # 如果是问句但没有强陈述开头，排除
        if is_question and not has_statement:
            return False
        
        # 必须包含有价值关键词
        return has_statement
    
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
    
    def _auto_migrate_json_to_faiss(self):
        """自动迁移 JSON 记忆到 FAISS（首次启动或 FAISS 为空时）"""
        try:
            # 检查是否需要迁移
            faiss_count = self.faiss_store.count() if self.faiss_store else 0
            json_count = len(self.user_memories)
            
            # FAISS 为空但 JSON 有数据 -> 需要迁移
            if faiss_count == 0 and json_count > 0:
                self.logger.info(f"🔄 [自动迁移] 检测到 {json_count} 条 JSON 记忆，开始迁移到 FAISS...")
                
                success_count = 0
                for memory in self.user_memories:
                    try:
                        # 生成向量
                        vector = self.embedding_service.encode_text([memory.content], convert_to_numpy=True)
                        
                        if vector is not None:
                            # 添加到 FAISS
                            self.faiss_store.add(
                                content=memory.content,
                                vector=vector,
                                metadata=memory.metadata,
                                importance=memory.importance
                            )
                            success_count += 1
                        
                    except Exception as e:
                        self.logger.warning(f"⚠️ 迁移单条记忆失败: {e}")
                        continue
                
                # 强制保存
                if success_count > 0:
                    self.faiss_store._save_to_disk()
                    self.logger.info(f"✅ [自动迁移] 成功迁移 {success_count}/{json_count} 条记忆到 FAISS")
                else:
                    self.logger.warning("⚠️ [自动迁移] 未能迁移任何记忆")
            
            elif faiss_count > 0:
                self.logger.info(f"✅ [FAISS] 已有 {faiss_count} 条记忆，跳过迁移")
            
        except Exception as e:
            self.logger.error(f"❌ [自动迁移] 迁移失败: {e}", exc_info=True)

