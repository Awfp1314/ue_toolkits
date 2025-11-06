# -*- coding: utf-8 -*-

"""
上下文管理器
协调资产、文档、日志、配置等各种数据源，为 AI 助手提供智能上下文
"""

import re
from typing import Optional, Dict, Any, List
from pathlib import Path
from core.logger import get_logger
from core.ai_services import EmbeddingService

from modules.ai_assistant.logic.asset_reader import AssetReader
from modules.ai_assistant.logic.document_reader import DocumentReader
from modules.ai_assistant.logic.log_analyzer import LogAnalyzer
from modules.ai_assistant.logic.config_reader import ConfigReader
from modules.ai_assistant.logic.site_reader import SiteReader
from modules.ai_assistant.logic.enhanced_memory_manager import EnhancedMemoryManager, MemoryLevel

# 延迟获取 logger
def _get_logger():
    return get_logger(__name__)

logger = None

# v0.1 新增：意图解析、运行态上下文、本地/远程检索
# 可选导入，如果依赖未安装则跳过（优雅降级）
try:
    from modules.ai_assistant.logic.intent_parser import IntentEngine, IntentType
    from modules.ai_assistant.logic.runtime_context import RuntimeContextManager
    from modules.ai_assistant.logic.local_retriever import LocalDocIndex
    from modules.ai_assistant.logic.remote_retriever import RemoteRetriever
    V01_AVAILABLE = True
except ImportError as e:
    # logger 此时是 None，不能调用（模块级代码）
    print(f"[WARNING] v0.1 功能不可用（缺少依赖）：{e}", flush=True)
    IntentEngine = None
    IntentType = None
    RuntimeContextManager = None
    LocalDocIndex = None
    RemoteRetriever = None
    V01_AVAILABLE = False


class ContextManager:
    """智能上下文管理器（基于 Mem0 设计的增强版）
    
    核心能力：
    - 多级记忆管理（用户/会话/上下文）
    - 智能上下文融合
    - 去重和优化
    - 从日志学习
    """
    
    def __init__(self, asset_manager_logic=None, config_tool_logic=None, site_recommendations_logic=None, runtime_context=None, user_id: str = "default", debug: bool = False, max_context_tokens: int = 4000):
        """初始化上下文管理器
        
        Args:
            asset_manager_logic: asset_manager 模块的逻辑层实例
            config_tool_logic: config_tool 模块的逻辑层实例
            site_recommendations_logic: site_recommendations 模块的逻辑层实例
            runtime_context: 运行态上下文管理器（可选，会自动创建）
            user_id: 用户ID（用于记忆持久化）
            debug: 是否开启 debug 模式（输出完整上下文快照到日志）
            max_context_tokens: 上下文最大 token 数（默认 4000，约2万字符）
        """
        # 首先初始化 logger（其他方法需要使用）
        self.logger = _get_logger()
        
        self.asset_reader = AssetReader(asset_manager_logic)
        self.document_reader = DocumentReader()
        self.log_analyzer = LogAnalyzer()
        self.config_reader = ConfigReader(config_tool_logic)
        self.site_reader = SiteReader(site_recommendations_logic)
        
        # 创建统一的 EmbeddingService（单例模式）
        self.embedding_service = EmbeddingService()
        
        # 初始化 ChromaDB 客户端（用于向量存储）
        # 注意：避免调用 collection.count()，会导致崩溃
        self.db_client = self._init_chromadb_client()
        
        # 增强型记忆管理器（基于 Mem0 设计，支持向量检索）
        self.memory = EnhancedMemoryManager(
            user_id=user_id,
            embedding_service=self.embedding_service,
            db_client=self.db_client
        )
        
        # v0.1 新增：意图引擎（延迟创建，避免与后台预加载冲突）
        self._intent_engine = None
        self._intent_engine_type = "bge-small" if V01_AVAILABLE and IntentEngine else None
        
        # v0.1 新增：运行态上下文管理器
        self.runtime_context = runtime_context or (RuntimeContextManager() if V01_AVAILABLE and RuntimeContextManager else None)
        
        # v0.1 新增：本地文档索引（使用统一的嵌入服务）
        self.local_index = LocalDocIndex(embedding_service=self.embedding_service) if V01_AVAILABLE and LocalDocIndex else None
        
        # v0.1 新增：远程检索器（延迟加载）
        self.remote_retriever = RemoteRetriever() if V01_AVAILABLE and RemoteRetriever else None
        
        # 上下文缓存（避免重复计算）
        self._context_cache = {}
        self._cache_ttl = 60  # 缓存有效期（秒）
        
        # Token 控制
        self.max_context_tokens = max_context_tokens
        
        # Debug 模式
        self.debug = debug
        
        self.logger.info(f"智能上下文管理器初始化完成（用户: {user_id}，统一嵌入服务: ✓，向量检索: ✓）")
    
    def _init_chromadb_client(self):
        """初始化 ChromaDB 客户端"""
        try:
            import chromadb
            from chromadb.config import Settings
            from core.utils.path_utils import PathUtils
            
            # 获取数据库路径
            path_utils = PathUtils()
            db_path = path_utils.get_user_data_dir() / "chroma_db"
            db_path.mkdir(parents=True, exist_ok=True)
            
            # 创建持久化客户端
            client = chromadb.PersistentClient(
                path=str(db_path),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            self.logger.info(f"ChromaDB 客户端初始化成功（路径: {db_path}）")
            return client
            
        except Exception as e:
            self.logger.error(f"初始化 ChromaDB 客户端失败: {e}", exc_info=True)
            return None
    
    @property
    def intent_engine(self):
        """延迟创建意图引擎（首次访问时创建，确保后台预加载已完成）"""
        if self._intent_engine is None and self._intent_engine_type and V01_AVAILABLE and IntentEngine:
            self._intent_engine = IntentEngine(model_type=self._intent_engine_type)
            self.logger.info("意图引擎延迟创建完成")
        return self._intent_engine
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """分析用户查询，判断需要什么类型的上下文
        
        v0.1 更新：使用 IntentEngine 进行语义意图解析
        
        Args:
            query: 用户查询
            
        Returns:
            Dict: 分析结果，包含 needs_assets/docs/logs/configs, intent, confidence
        """
        try:
            # v0.1: 如果意图引擎可用，使用语义解析
            if self.intent_engine:
                intent_result = self.intent_engine.parse(query)
                
                intent = intent_result['intent']
                entities = intent_result['entities']
                confidence = intent_result['confidence']
                
                # 根据意图类型映射到需要的上下文
                result = {
                    'needs_assets': intent in [IntentType.ASSET_QUERY, IntentType.ASSET_DETAIL],
                    'needs_docs': intent == IntentType.DOC_SEARCH,
                    'needs_logs': intent in [IntentType.LOG_ANALYZE, IntentType.LOG_SEARCH],
                    'needs_configs': intent in [IntentType.CONFIG_QUERY, IntentType.CONFIG_COMPARE],
                    'needs_sites': intent == IntentType.SITE_RECOMMENDATION,
                    'keywords': entities,
                    'intent': str(intent),
                    'confidence': confidence
                }
                
                return result
            else:
                # v0.1 不可用，使用规则匹配
                return self._fallback_analyze(query)
            
        except Exception as e:
            self.logger.error(f"意图解析失败: {e}", exc_info=True)
            # 降级到规则匹配
            return self._fallback_analyze(query)
    
    def _fallback_analyze(self, query: str) -> Dict[str, Any]:
        """规则匹配分析（fallback）"""
        query_lower = query.lower()
        
        # 站点推荐关键词
        site_keywords = ['网站', '站点', '推荐', '资源网站', '论坛', '学习网站', 
                         'site', 'website', 'resource', 'forum', '哪里下载', 
                         '哪里学', 'fab', 'marketplace', '商城', '资产商店']
        
        needs_sites = any(keyword in query_lower for keyword in site_keywords)
        
        return {
            'needs_assets': False,
            'needs_docs': False,
            'needs_logs': False,
            'needs_configs': False,
            'needs_sites': needs_sites,
            'keywords': [],
            'intent': 'site_recommendation' if needs_sites else 'chitchat',
            'confidence': 0.5 if needs_sites else 0.0
        }
    
    def build_context(self, query: str, include_system_prompt: bool = False) -> str:
        """构建智能融合的上下文信息（基于 Mem0 设计）
        
        自动融合：
        1. 系统提示词（默认不包含，由外部单独发送）
        2. 用户画像（从记忆提取）
        3. 相关历史记忆（智能检索）
        4. 运行时状态（UE 工具箱状态）
        5. 特定领域上下文（资产/配置/日志/文档）
        
        Args:
            query: 用户查询
            include_system_prompt: 是否包含系统提示词（默认False，由外部管理）
            
        Returns:
            str: 优化后的上下文信息
        """
        context_sections = {}  # 使用字典避免重复
        
        # 调试：显示当前记忆系统状态
        if hasattr(self.memory, 'user_memories') and hasattr(self.memory, 'session_memories') and hasattr(self.memory, 'context_buffer'):
            self.logger.info(f"[记忆系统状态] 用户级:{len(self.memory.user_memories)}, 会话级:{len(self.memory.session_memories)}, 上下文缓冲:{len(self.memory.context_buffer)}")
        
        # ===== 第一层：查询意图分析（提前分析，优化加载策略）=====
        analysis = self.analyze_query(query)
        self.logger.info(f"查询意图分析: {analysis}")
        
        # 判断是否为简单问候/闲聊
        is_chitchat = analysis.get('intent') == 'chitchat' or analysis.get('intent') == str(IntentType.CHITCHAT) if V01_AVAILABLE and IntentType else False
        
        # 闲聊模式：返回基本角色说明+相关记忆（仅在需要时）
        if is_chitchat:
            self.logger.info("检测到闲聊模式，使用极简上下文")
            
            # Token 优化：彻底精简闲聊模式的上下文
            # 智能检索相关记忆（仅在明确询问记忆时）
            is_asking_memory = any(keyword in query.lower() for keyword in ['记得', '还记得', '记不记得', '忘了', '说过'])
            
            if is_asking_memory:
                # 用户明确询问记忆，检索并返回
                relevant_memories = self.memory.get_relevant_memories(query, limit=2, min_importance=0.1)
                
                if relevant_memories:
                    # Token优化：只返回记忆，不加额外描述
                    return "[相关记忆]\n" + "\n".join(f"- {m}" for m in relevant_memories[:2])
                else:
                    return ""  # 没找到就返回空，让AI自然回答
            else:
                # 普通闲聊，完全不添加上下文（Token优化：0 token）
                # 让AI依赖系统提示词和对话历史自然回答
                self.logger.info("普通闲聊，跳过所有上下文（Token优化）")
                return ""
        
        # ===== 第二层：系统级上下文（仅在显式要求时添加）=====
        if include_system_prompt:
            context_sections['system_prompt'] = self._build_system_prompt(is_chitchat=False)
        
        # ===== 第三层：用户身份设定（始终包含，确保AI记住角色）=====
        user_identity = self.memory.get_user_identity()
        if user_identity:
            context_sections['user_identity'] = f"[你的角色身份]\n{user_identity}\n⚠️ 请始终保持这个角色身份！"
            self.logger.info(f"已添加用户身份设定: {user_identity[:50]}...")
        
        # ===== 第四层：用户画像（习惯和偏好，排除身份）=====
        # Token优化：用户画像缩短到300字符
        user_profile = self.memory.get_user_profile()
        if user_profile:
            context_sections['user_profile'] = user_profile[:300] if len(user_profile) > 300 else user_profile
            self.logger.info("已添加用户画像")
        
        # ===== 第五层：智能记忆检索 =====
        # Token优化：从 limit=5 降到 limit=3，提高阈值从 0.2 到 0.3
        relevant_memories = self.memory.get_relevant_memories(query, limit=3, min_importance=0.3)
        
        # 调试：输出记忆检索详情
        self.logger.info(f"记忆检索结果: 找到 {len(relevant_memories)} 条记忆")
        if relevant_memories:
            for i, mem in enumerate(relevant_memories[:5], 1):
                self.logger.info(f"  记忆 {i}: {mem[:100]}...")
        else:
            self.logger.warning("未找到相关记忆！")
        
        if relevant_memories:
            # Token优化：每条记忆限制150字符，最多3条
            truncated_memories = [m[:150] + "..." if len(m) > 150 else m for m in relevant_memories[:3]]
            context_sections['relevant_memories'] = "[相关记忆]\n" + "\n".join(f"- {m}" for m in truncated_memories)
            self.logger.info(f"已添加 {len(truncated_memories)} 条记忆（已精简）")
        
        # ===== 第六层：最近对话摘要（如果有压缩摘要就包含）=====
        if hasattr(self.memory, 'compressed_summary') and self.memory.compressed_summary:
            context_sections['recent_context'] = self.memory.compressed_summary
            self.logger.info("已添加对话历史摘要")
        
        # ===== 第七层：运行时状态（仅在需要资产/配置/日志时添加）=====
        # Token优化：只在需要时才添加运行时状态，且更激进截断
        if analysis.get('needs_assets') or analysis.get('needs_configs') or analysis.get('needs_logs'):
            if self.runtime_context:
                runtime_snapshot = self.runtime_context.get_formatted_snapshot()
                if runtime_snapshot:
                    # Token优化：从 800 降到 400 字符
                    context_sections['runtime_status'] = runtime_snapshot[:400] if len(runtime_snapshot) > 400 else runtime_snapshot
                    self.logger.info("已添加运行态快照（精简版）")
        
        # ===== 第八层：检索证据（本地优先，远程 fallback）=====
        # Token优化：仅在需要文档时检索（资产查询用领域上下文）
        if analysis.get('needs_docs'):
            retrieval_evidence = self._build_retrieval_evidence(query)
            if retrieval_evidence:
                # Token优化：从 1500 降到 800 字符
                context_sections['retrieval_evidence'] = retrieval_evidence[:800] if len(retrieval_evidence) > 800 else retrieval_evidence
                self.logger.info("已添加检索证据（精简版）")
        
        # ===== 第九层：领域特定上下文 =====
        domain_contexts = self._build_domain_contexts(query, analysis)
        if domain_contexts:
            context_sections.update(domain_contexts)
        
        # ===== 第十层：智能回退 =====
        # Token优化：取消自动 fallback，只在必要时才添加系统概览
        # 让AI依赖系统提示词中的基础信息，减少冗余
        self.logger.info("跳过 fallback（Token优化）")
        
        # ===== 上下文优化和去重 =====
        optimized_context = self._optimize_context(context_sections, query)
        
        # v0.1 新增：Debug 模式输出
        if self.debug:
            self.logger.info("="*60)
            self.logger.info("[DEBUG] 完整上下文快照:")
            self.logger.info(f"查询: {query}")
            self.logger.info(f"意图: {analysis}")
            self.logger.info(f"上下文段数: {len(context_sections)}")
            for key, value in context_sections.items():
                self.logger.info(f"  - {key}: {len(value)} 字符")
            self.logger.info(f"优化后长度: {len(optimized_context)} 字符")
            self.logger.info("="*60)
        
        return optimized_context
    
    def _build_asset_context(self, query: str) -> str:
        """构建资产相关上下文
        
        Args:
            query: 用户查询
            
        Returns:
            str: 资产上下文
        """
        try:
            query_lower = query.lower()
            
            # 检查是否在询问详细信息/路径
            detail_keywords = ['路径', '在哪', '详细', '详情', '具体', '包含', '文件', 
                              'path', 'detail', 'where', 'location', '里面有', '都有什么']
            is_detail_query = any(keyword in query_lower for keyword in detail_keywords)
            
            # 提取可能的资产名称或关键词
            keywords = self._extract_keywords(query)
            
            context_parts = []
            
            # 如果有明确的搜索关键词
            if keywords:
                for keyword in keywords[:2]:  # 最多搜索 2 个关键词
                    # 如果是详细信息查询，直接获取资产详情
                    if is_detail_query:
                        detail_result = self.asset_reader.get_asset_details(keyword)
                        if "[ERROR]" not in detail_result and "未找到" not in detail_result:
                            context_parts.append(detail_result)
                        else:
                            # 如果没找到，尝试搜索
                            search_result = self.asset_reader.search_assets(keyword)
                            if "找到" in search_result:
                                context_parts.append(search_result)
                                context_parts.append("\n提示：如需查看详细路径和文件列表，请告诉我具体的资产名称。")
                    else:
                        # 常规搜索
                        search_result = self.asset_reader.search_assets(keyword)
                        if "找到" in search_result:
                            context_parts.append(search_result)
            
            # 如果没有找到特定资产，提供资产概览
            if not context_parts or "未找到" in "\n".join(context_parts):
                overview = self.asset_reader.get_all_assets_summary()
                context_parts.insert(0, overview)
            
            return "\n\n".join(context_parts)
        
        except Exception as e:
            self.logger.error(f"构建资产上下文失败: {e}")
            return ""
    
    def _build_document_context(self, query: str) -> str:
        """构建文档相关上下文
        
        Args:
            query: 用户查询
            
        Returns:
            str: 文档上下文
        """
        try:
            context_parts = []
            
            # 如果询问如何使用，提供 README
            if any(keyword in query.lower() for keyword in ['如何', 'how', '怎么', '使用']):
                readme = self.document_reader.get_readme_summary()
                context_parts.append(readme)
            else:
                # 搜索相关文档
                keywords = self._extract_keywords(query)
                for keyword in keywords[:1]:  # 只搜索主关键词
                    search_result = self.document_reader.search_in_documents(keyword)
                    if "找到" in search_result:
                        context_parts.append(search_result)
            
            # 如果没有找到，提供文档列表
            if not context_parts:
                doc_list = self.document_reader.get_available_documents()
                context_parts.append(doc_list)
            
            return "\n\n".join(context_parts)
        
        except Exception as e:
            self.logger.error(f"构建文档上下文失败: {e}")
            return ""
    
    def _build_log_context(self, query: str) -> str:
        """构建日志相关上下文
        
        Args:
            query: 用户查询
            
        Returns:
            str: 日志上下文
        """
        try:
            context_parts = []
            
            # 如果明确提到错误，分析错误
            if any(keyword in query.lower() for keyword in ['错误', 'error', '出错', '失败']):
                error_analysis = self.log_analyzer.analyze_errors()
                context_parts.append(error_analysis)
            else:
                # 提供日志摘要
                log_summary = self.log_analyzer.get_log_summary()
                context_parts.append(log_summary)
            
            # 如果有特定关键词，搜索日志
            keywords = self._extract_keywords(query)
            for keyword in keywords[:1]:
                if keyword not in ['错误', 'error', 'log', '日志']:
                    search_result = self.log_analyzer.search_in_logs(keyword)
                    if "找到" in search_result:
                        context_parts.append(search_result)
            
            return "\n\n".join(context_parts)
        
        except Exception as e:
            self.logger.error(f"构建日志上下文失败: {e}")
            return ""
    
    def _build_config_context(self, query: str) -> str:
        """构建配置相关上下文
        
        Args:
            query: 用户查询
            
        Returns:
            str: 配置上下文
        """
        try:
            context_parts = []
            query_lower = query.lower()
            
            # 检查是否在询问详细信息/路径
            detail_keywords = ['路径', '在哪', '详细', '详情', '具体', '包含', '文件', 
                              'path', 'detail', 'where', 'location', '里面有', '都有什么', 
                              'ini', '配置文件']
            is_detail_query = any(keyword in query_lower for keyword in detail_keywords)
            
            # 提取关键词
            keywords = self._extract_keywords(query)
            
            # 如果有明确的搜索关键词
            if keywords:
                for keyword in keywords[:2]:  # 最多搜索 2 个关键词
                    # 如果是详细信息查询，直接获取配置详情
                    if is_detail_query:
                        detail_result = self.config_reader.get_config_details(keyword)
                        if "[ERROR]" not in detail_result and "未找到" not in detail_result:
                            context_parts.append(detail_result)
                        else:
                            # 如果没找到，尝试搜索
                            search_result = self.config_reader.search_configs(keyword)
                            if "找到" in search_result:
                                context_parts.append(search_result)
                                context_parts.append("\n提示：如需查看详细路径和配置文件列表，请告诉我具体的配置名称。")
                    else:
                        # 常规搜索
                        search_result = self.config_reader.search_configs(keyword)
                        if "找到" in search_result:
                            context_parts.append(search_result)
            
            # 如果没有找到特定配置，提供配置概览
            if not context_parts or "未找到" in "\n".join(context_parts):
                overview = self.config_reader.get_all_configs_summary()
                context_parts.insert(0, overview)
            
            return "\n\n".join(context_parts)
        
        except Exception as e:
            self.logger.error(f"构建配置上下文失败: {e}")
            return ""
    
    def _build_site_context(self, query: str) -> str:
        """构建站点推荐相关上下文
        
        Args:
            query: 用户查询
            
        Returns:
            str: 站点推荐上下文
        """
        try:
            query_lower = query.lower()
            
            # 检测用户的意图
            # 1. 询问特定分类的站点
            category_keywords = {
                '资源': '资源网站',
                '论坛': '论坛',
                '学习': '学习',
                '工具': '工具',
                'resource': '资源网站',
                'forum': '论坛',
                'learn': '学习',
                'tool': '工具'
            }
            
            for keyword, category in category_keywords.items():
                if keyword in query_lower:
                    result = self.site_reader.get_sites_by_category(category)
                    if result and "未找到" not in result:
                        return f"[站点推荐]\n{result}"
            
            # 2. 搜索特定站点
            search_keywords = ['网站', '站点', '推荐', '哪里', '哪个', 'site', 'website', 'where']
            if any(keyword in query_lower for keyword in search_keywords):
                # 提取搜索关键词（排除常见词）
                excluded_words = ['推荐', '网站', '站点', '哪里', '哪个', '有', '没有', '吗', '的', '在']
                words = [w for w in query.split() if w not in excluded_words and len(w) > 1]
                
                if words:
                    # 使用第一个关键词搜索
                    search_result = self.site_reader.search_sites(words[0])
                    if search_result and "未找到" not in search_result:
                        return f"[站点搜索结果]\n{search_result}"
            
            # 3. 默认返回全部站点摘要
            return f"[站点推荐]\n{self.site_reader.get_all_sites_summary(max_count=50)}"
        
        except Exception as e:
            self.logger.error(f"构建站点上下文失败: {e}", exc_info=True)
            return ""
    
    def _build_system_prompt(self, is_chitchat: bool = False) -> str:
        """构建系统提示词
        
        Args:
            is_chitchat: 是否为闲聊模式
            
        Returns:
            str: 系统提示词
        """
        if is_chitchat:
            # 闲聊模式：简洁版提示词
            return """[系统角色]
你是虚幻引擎工具箱的 AI 助手。请自然、友好地回答用户的问候和闲聊。"""
        else:
            # 工作模式：完整版提示词
            return """[系统角色]
你是虚幻引擎工具箱的智能助手，专注于帮助用户管理 UE 项目资产、配置和日志。
你拥有记忆能力，能记住之前的对话内容，并结合用户习惯提供个性化建议。"""
    
    def _build_domain_contexts(self, query: str, analysis: Dict) -> Dict[str, str]:
        """构建领域特定上下文
        
        Args:
            query: 用户查询
            analysis: 查询分析结果
            
        Returns:
            Dict[str, str]: 领域上下文字典
        """
        contexts = {}
        
        if analysis['needs_assets']:
            asset_context = self._build_asset_context(query)
            if asset_context:
                # 智能限制：检测是否是"列出所有"的查询
                query_lower = query.lower()
                is_list_all_query = any(keyword in query_lower for keyword in [
                    '所有资产', '全部资产', '列出资产', '有哪些资产', '资产列表', 
                    'list all', 'show all', 'all assets'
                ])
                
                if is_list_all_query:
                    # 用户要求列出所有资产，不截断！
                    contexts['domain_assets'] = asset_context
                    self.logger.info(f"检测到列表查询，不限制资产上下文长度（{len(asset_context)} 字符）")
                else:
                    # 其他查询，适度限制
                    contexts['domain_assets'] = asset_context[:2000] if len(asset_context) > 2000 else asset_context
                    self.logger.info(f"常规资产查询，限制到 2000 字符")
        
        if analysis['needs_docs']:
            doc_context = self._build_document_context(query)
            if doc_context:
                # Token优化：文档上下文限制到 500 字符
                contexts['domain_docs'] = doc_context[:500] if len(doc_context) > 500 else doc_context
        
        if analysis['needs_logs']:
            log_context = self._build_log_context(query)
            if log_context:
                # Token优化：日志上下文限制到 600 字符
                contexts['domain_logs'] = log_context[:600] if len(log_context) > 600 else log_context
        
        if analysis['needs_configs']:
            config_context = self._build_config_context(query)
            if config_context:
                # Token优化：配置上下文限制到 600 字符
                contexts['domain_configs'] = config_context[:600] if len(config_context) > 600 else config_context
        
        if analysis.get('needs_sites', False):
            site_context = self._build_site_context(query)
            if site_context:
                # Token优化：站点上下文限制到 400 字符
                contexts['domain_sites'] = site_context[:400] if len(site_context) > 400 else site_context
        
        return contexts
    
    def _build_fallback_context(self, query: str) -> str:
        """构建智能回退上下文
        
        Args:
            query: 用户查询
            
        Returns:
            str: 回退上下文
        """
        fallback_parts = []
        
        # 添加系统概览
        fallback_parts.append(self._build_system_overview())
        
        # 如果提到问题，自动加载错误日志
        problem_keywords = ['问题', '错误', '不工作', '没反应', '失败', '崩溃', 
                           'problem', 'error', 'not working', 'fail', 'crash']
        if any(keyword in query.lower() for keyword in problem_keywords):
            log_context = self.log_analyzer.analyze_errors()
            if log_context:
                fallback_parts.append("[自动检测] 最近的错误日志:\n" + log_context)
        
        return "\n\n".join(fallback_parts) if fallback_parts else ""
    
    def _optimize_context(self, context_sections: Dict[str, str], query: str) -> str:
        """优化和去重上下文（避免冗余）
        
        Args:
            context_sections: 上下文各部分的字典
            query: 用户查询
            
        Returns:
            str: 优化后的上下文
        """
        # 按优先级排序
        priority_order = [
            'system_prompt',
            'user_identity',      # 用户身份设定（最高优先级，确保AI始终记住角色）
            'user_profile',
            'relevant_memories',
            'recent_context',
            'runtime_status',
            'domain_assets',
            'domain_configs',
            'domain_logs',
            'domain_docs',
            'domain_sites',       # 站点推荐
            'retrieval_evidence',
            'fallback'
        ]
        
        # 构建最终上下文
        final_parts = []
        total_tokens = 0
        max_tokens = self.max_context_tokens  # 使用配置的最大 token 数
        
        for key in priority_order:
            if key in context_sections and context_sections[key]:
                content = context_sections[key]
                content_tokens = self._estimate_tokens(content)
                
                # 检查是否会超出 token 限制
                if total_tokens + content_tokens > max_tokens:
                    # 截断内容（粗略估算，按字符比例截取）
                    remaining_tokens = max_tokens - total_tokens
                    if remaining_tokens > 50:  # 至少保留50 tokens
                        ratio = remaining_tokens / content_tokens
                        truncate_length = int(len(content) * ratio)
                        content = content[:truncate_length] + "\n...(内容被截断)"
                        final_parts.append(content)
                        total_tokens += remaining_tokens
                    break
                
                final_parts.append(content)
                total_tokens += content_tokens
        
        # 格式化输出（Token优化：简化header/footer）
        if final_parts:
            # Token优化：完全移除 header，直接返回内容
            # 记录token统计到日志，不添加到输出
            self.logger.info(f"上下文 Token 统计: {total_tokens}/{max_tokens}")
            
            return "\n\n".join(final_parts)
        
        return ""
    
    def _estimate_tokens(self, text: str) -> int:
        """估算文本的 token 数（粗略估算）
        
        使用规则：中文约 1.5字符/token，英文约 4字符/token
        
        Args:
            text: 文本内容
            
        Returns:
            int: 估算的 token 数
        """
        if not text:
            return 0
        
        # 统计中文和英文字符
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        
        # 估算 tokens
        chinese_tokens = chinese_chars / 1.5  # 中文约1.5字符/token
        other_tokens = other_chars / 4  # 英文约4字符/token
        
        return int(chinese_tokens + other_tokens)
    
    def sync_from_log(self, auto_learn: bool = True):
        """从日志自动学习上下文（实现"学习"能力）
        
        分析最近的日志，提取有价值的信息保存到记忆中。
        
        Args:
            auto_learn: 是否自动学习（评估重要性）
        """
        self.logger.info("开始从日志学习...")
        
        try:
            # 1. 获取最近的错误日志
            errors = self.log_analyzer.analyze_errors()
            
            if errors and "错误" in errors:
                # 提取错误模式
                error_lines = [line for line in errors.split('\n') if 'ERROR' in line or '错误' in line]
                
                for error_line in error_lines[:5]:  # 最多学习5条错误
                    # 保存到用户级记忆（持久化）
                    self.memory.add_memory(
                        content=f"系统错误: {error_line}",
                        level=MemoryLevel.USER,
                        metadata={'type': 'error_log', 'source': 'auto_learn'},
                        auto_evaluate=auto_learn
                    )
                
                self.logger.info(f"从日志中学习了 {len(error_lines[:5])} 条错误信息")
            
            # 2. 获取警告信息
            warnings = self.log_analyzer.get_log_summary()
            
            if warnings and "WARNING" in warnings:
                # 保存警告模式到会话级记忆
                self.memory.add_memory(
                    content=f"系统警告模式已检测",
                    level=MemoryLevel.SESSION,
                    metadata={'type': 'warning_pattern', 'source': 'auto_learn'}
                )
            
            self.logger.info("日志学习完成")
            
        except Exception as e:
            self.logger.error(f"从日志学习失败: {e}")
    
    def _build_runtime_status(self) -> str:
        """构建运行时状态信息（轻量级摘要，不包含详细列表）
        
        Returns:
            str: 运行时状态
        """
        try:
            status_parts = ["[运行时状态]"]
            
            # 检查最近的日志
            recent_log = self.log_analyzer.get_log_summary()
            if recent_log and "[LOG]" in recent_log:
                status_parts.append(f"**最近日志**: 可用")
            
            # 检查资产库状态（仅统计数量，不获取详细列表）
            try:
                if self.asset_reader.asset_manager_logic:
                    assets = self.asset_reader.asset_manager_logic.get_all_assets()
                    if assets:
                        status_parts.append(f"**资产库**: {len(assets)} 个资产")
            except Exception as e:
                self.logger.debug(f"获取资产统计失败: {e}")
            
            # 检查配置状态（仅统计数量）
            try:
                if self.config_reader.config_tool_logic:
                    configs = self.config_reader.config_tool_logic.get_all_templates()
                    if configs:
                        status_parts.append(f"**配置模板**: {len(configs)} 个配置")
            except Exception as e:
                self.logger.debug(f"获取配置统计失败: {e}")
            
            if len(status_parts) > 1:
                return "\n".join(status_parts)
            
            return ""
        
        except Exception as e:
            self.logger.error(f"构建运行时状态失败: {e}")
            return ""
    
    def _build_system_overview(self) -> str:
        """构建系统概览
        
        Returns:
            str: 系统概览
        """
        try:
            # Token优化：大幅精简系统概览
            overview_parts = [
                "[系统能力]",
                "资产管理、配置查询、文档查阅、日志分析"
            ]
            
            return "\n".join(overview_parts)
        
        except Exception as e:
            self.logger.error(f"构建系统概览失败: {e}")
            return ""
    
    def _extract_keywords(self, query: str) -> List[str]:
        """从查询中提取关键词
        
        Args:
            query: 用户查询
            
        Returns:
            List[str]: 关键词列表
        """
        # 移除常见的停用词
        stop_words = {'的', '了', '是', '在', '有', '和', '吗', '呢', '啊', '吧', 
                     'the', 'a', 'an', 'is', 'are', 'what', 'how', 'where'}
        
        # 分词（简单实现）
        words = re.findall(r'\w+', query.lower())
        
        # 过滤停用词和短词
        keywords = [word for word in words if word not in stop_words and len(word) > 1]
        
        return keywords
    
    def _build_retrieval_evidence(self, query: str) -> str:
        """
        构建检索证据（本地优先，远程 fallback）
        
        v0.1 新增：集成本地文档检索和远程代码搜索
        
        Args:
            query: 用户查询
            
        Returns:
            str: 检索证据文本，附带来源标签
        """
        try:
            evidence_parts = []
            
            # 1. 优先本地文档检索
            try:
                if self.local_index:
                    self.logger.info("📖 [上下文构建] 调用本地文档向量检索...")
                    # Token优化：从 top_k=3 降到 top_k=2
                    local_results = self.local_index.search(query, top_k=2)
                else:
                    self.logger.warning("⚠️ [上下文构建] 本地文档索引未启用")
                    local_results = []
                
                if local_results:
                    evidence_parts.append("[文档]")
                    for i, result in enumerate(local_results, 1):
                        # Token优化：从 150 降到 120 字符
                        content = result['content'][:120]
                        metadata = result.get('metadata', {})
                        source = metadata.get('source', 'unknown')
                        
                        # Token优化：更简洁的格式
                        evidence_parts.append(f"{i}. {content}...")
                    
                    self.logger.info(f"✅ [上下文构建] 本地文档向量检索返回 {len(local_results)} 条结果")
            
            except Exception as e:
                self.logger.warning(f"本地检索失败: {e}")
            
            # 2. 如果本地无结果，尝试远程检索（GitHub）
            if not evidence_parts:
                try:
                    # 只在特定意图下启用远程搜索（避免过度调用 API）
                    analysis = self.analyze_query(query)
                    if self.remote_retriever and analysis.get('intent') in ['doc.search', 'asset.query']:
                        remote_results = self.remote_retriever.search(
                            query, 
                            source="github",
                            repo="EpicGames/UnrealEngine",  # 可配置
                            top_k=2
                        )
                    else:
                        remote_results = []
                    
                    if remote_results:
                        evidence_parts.append("[远程代码]")
                        for i, result in enumerate(remote_results, 1):
                            # Token优化：从 200 降到 100 字符，移除冗余信息
                            snippet = result.get('content_snippet', '')[:100]
                            path = result.get('path', '')
                            
                            evidence_parts.append(f"{i}. {snippet}... ({path})")
                        
                        self.logger.info(f"远程检索到 {len(remote_results)} 条结果")
                
                except Exception as e:
                    self.logger.warning(f"远程检索失败（可能未配置 token）: {e}")
            
            return "\n".join(evidence_parts) if evidence_parts else ""
        
        except Exception as e:
            self.logger.error(f"构建检索证据失败: {e}", exc_info=True)
            return ""
    
    def execute_command(self, command: str) -> Optional[str]:
        """执行特定命令
        
        Args:
            command: 命令字符串
            
        Returns:
            Optional[str]: 命令执行结果
        """
        command_lower = command.lower()
        
        # 资产相关命令
        if '资产' in command_lower or 'asset' in command_lower:
            if '列表' in command_lower or '所有' in command_lower or '有哪些' in command_lower:
                return self.asset_reader.get_all_assets_summary()
            elif '分类' in command_lower:
                return self.asset_reader.get_categories_list()
        
        # 文档相关命令
        if '文档' in command_lower or 'document' in command_lower:
            if '列表' in command_lower or '有哪些' in command_lower:
                return self.document_reader.get_available_documents()
        
        # 日志相关命令
        if '日志' in command_lower or 'log' in command_lower:
            if '错误' in command_lower or 'error' in command_lower:
                return self.log_analyzer.analyze_errors()
            elif '统计' in command_lower or '摘要' in command_lower:
                return self.log_analyzer.get_log_summary()
        
        return None




