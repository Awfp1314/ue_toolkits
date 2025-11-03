# -*- coding: utf-8 -*-

"""
上下文管理器
协调资产、文档、日志、配置等各种数据源，为 AI 助手提供智能上下文
"""

import re
from typing import Optional, Dict, Any, List
from core.logger import get_logger

from modules.ai_assistant.logic.asset_reader import AssetReader
from modules.ai_assistant.logic.document_reader import DocumentReader
from modules.ai_assistant.logic.log_analyzer import LogAnalyzer
from modules.ai_assistant.logic.config_reader import ConfigReader
from modules.ai_assistant.logic.enhanced_memory_manager import EnhancedMemoryManager, MemoryLevel

logger = get_logger(__name__)


class ContextManager:
    """智能上下文管理器（基于 Mem0 设计的增强版）
    
    核心能力：
    - 多级记忆管理（用户/会话/上下文）
    - 智能上下文融合
    - 去重和优化
    - 从日志学习
    """
    
    def __init__(self, asset_manager_logic=None, config_tool_logic=None, user_id: str = "default"):
        """初始化上下文管理器
        
        Args:
            asset_manager_logic: asset_manager 模块的逻辑层实例
            config_tool_logic: config_tool 模块的逻辑层实例
            user_id: 用户ID（用于记忆持久化）
        """
        self.asset_reader = AssetReader(asset_manager_logic)
        self.document_reader = DocumentReader()
        self.log_analyzer = LogAnalyzer()
        self.config_reader = ConfigReader(config_tool_logic)
        
        # 增强型记忆管理器（基于 Mem0 设计）
        self.memory = EnhancedMemoryManager(user_id=user_id)
        
        # 上下文缓存（避免重复计算）
        self._context_cache = {}
        self._cache_ttl = 60  # 缓存有效期（秒）
        
        self.logger = logger
        self.logger.info(f"智能上下文管理器初始化完成（用户: {user_id}，支持记忆、理解、学习）")
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """分析用户查询，判断需要什么类型的上下文
        
        Args:
            query: 用户查询
            
        Returns:
            Dict: 分析结果
        """
        query_lower = query.lower()
        
        result = {
            'needs_assets': False,
            'needs_docs': False,
            'needs_logs': False,
            'needs_configs': False,
            'keywords': [],
            'intent': 'general'
        }
        
        # 资产相关关键词
        asset_keywords = [
            '资产', 'asset', '模型', 'model', '纹理', 'texture',
            '蓝图', 'blueprint', '材质', 'material', '动画', 'animation',
            '查找', '搜索', 'search', '有哪些', '列表'
        ]
        
        # 文档相关关键词
        doc_keywords = [
            '文档', 'document', '说明', 'readme', '教程', 'tutorial',
            '如何', 'how', '怎么', '使用', 'use', '帮助', 'help'
        ]
        
        # 日志/错误相关关键词
        log_keywords = [
            '错误', 'error', '警告', 'warning', '日志', 'log',
            '出错', '失败', 'failed', '问题', 'problem', '异常', 'exception',
            '崩溃', 'crash', '不工作', 'not working'
        ]
        
        # 配置相关关键词
        config_keywords = [
            '配置', 'config', 'configuration', '设置', 'settings',
            '模板', 'template', 'ini', '引擎配置', 'engine config',
            'defaultengine', 'defaultgame', 'defaultinput'
        ]
        
        # 检查是否需要各种上下文
        for keyword in asset_keywords:
            if keyword in query_lower:
                result['needs_assets'] = True
                result['keywords'].append(keyword)
                break
        
        for keyword in doc_keywords:
            if keyword in query_lower:
                result['needs_docs'] = True
                result['keywords'].append(keyword)
                break
        
        for keyword in log_keywords:
            if keyword in query_lower:
                result['needs_logs'] = True
                result['keywords'].append(keyword)
                break
        
        for keyword in config_keywords:
            if keyword in query_lower:
                result['needs_configs'] = True
                result['keywords'].append(keyword)
                break
        
        # 判断意图
        if result['needs_logs']:
            result['intent'] = 'troubleshooting'
        elif result['needs_assets']:
            result['intent'] = 'asset_query'
        elif result['needs_docs']:
            result['intent'] = 'documentation'
        elif result['needs_configs']:
            result['intent'] = 'configuration'
        
        return result
    
    def build_context(self, query: str, include_system_prompt: bool = True) -> str:
        """构建智能融合的上下文信息（基于 Mem0 设计）
        
        自动融合：
        1. 系统提示词
        2. 用户画像（从记忆提取）
        3. 相关历史记忆（智能检索）
        4. 运行时状态（UE 工具箱状态）
        5. 特定领域上下文（资产/配置/日志/文档）
        
        Args:
            query: 用户查询
            include_system_prompt: 是否包含系统提示词
            
        Returns:
            str: 优化后的上下文信息
        """
        context_sections = {}  # 使用字典避免重复
        
        # ===== 第一层：系统级上下文 =====
        if include_system_prompt:
            context_sections['system_prompt'] = self._build_system_prompt()
        
        # ===== 第二层：用户画像 =====
        user_profile = self.memory.get_user_profile()
        if user_profile:
            context_sections['user_profile'] = user_profile
            self.logger.info("已添加用户画像")
        
        # ===== 第三层：智能记忆检索 =====
        relevant_memories = self.memory.get_relevant_memories(query, limit=3, min_importance=0.4)
        if relevant_memories:
            context_sections['relevant_memories'] = "[相关历史记忆]\n" + "\n".join(f"- {m}" for m in relevant_memories)
            self.logger.info(f"已检索到 {len(relevant_memories)} 条相关记忆")
        
        # ===== 第四层：最近上下文 =====
        recent_context = self.memory.get_recent_context(limit=3)
        if recent_context:
            context_sections['recent_context'] = recent_context
            self.logger.info("已添加最近对话上下文")
        
        # ===== 第五层：运行时状态 =====
        runtime_status = self._build_runtime_status()
        if runtime_status:
            context_sections['runtime_status'] = runtime_status
            self.logger.info("已添加运行时状态")
        
        # ===== 第六层：领域特定上下文 =====
        analysis = self.analyze_query(query)
        self.logger.info(f"查询意图分析: {analysis}")
        
        domain_contexts = self._build_domain_contexts(query, analysis)
        if domain_contexts:
            context_sections.update(domain_contexts)
        
        # ===== 第七层：智能回退 =====
        if not any([analysis['needs_assets'], analysis['needs_docs'], 
                   analysis['needs_logs'], analysis['needs_configs']]):
            self.logger.info("触发智能回退策略")
            fallback = self._build_fallback_context(query)
            if fallback:
                context_sections['fallback'] = fallback
        
        # ===== 上下文优化和去重 =====
        optimized_context = self._optimize_context(context_sections, query)
        
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
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词
        
        Returns:
            str: 系统提示词
        """
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
                contexts['domain_assets'] = asset_context
        
        if analysis['needs_docs']:
            doc_context = self._build_document_context(query)
            if doc_context:
                contexts['domain_docs'] = doc_context
        
        if analysis['needs_logs']:
            log_context = self._build_log_context(query)
            if log_context:
                contexts['domain_logs'] = log_context
        
        if analysis['needs_configs']:
            config_context = self._build_config_context(query)
            if config_context:
                contexts['domain_configs'] = config_context
        
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
            'user_profile',
            'relevant_memories',
            'recent_context',
            'runtime_status',
            'domain_assets',
            'domain_configs',
            'domain_logs',
            'domain_docs',
            'fallback'
        ]
        
        # 构建最终上下文
        final_parts = []
        total_length = 0
        max_length = 8000  # 最大上下文长度（避免超出 token 限制）
        
        for key in priority_order:
            if key in context_sections and context_sections[key]:
                content = context_sections[key]
                content_length = len(content)
                
                # 检查是否会超出长度限制
                if total_length + content_length > max_length:
                    # 截断内容
                    remaining = max_length - total_length
                    if remaining > 100:  # 至少保留100字符
                        content = content[:remaining] + "\n...(内容被截断)"
                        final_parts.append(content)
                    break
                
                final_parts.append(content)
                total_length += content_length
        
        # 格式化输出
        if final_parts:
            header = "\n" + "="*60 + "\n"
            header += "[智能上下文系统] Powered by Mem0\n"
            header += "="*60 + "\n\n"
            
            footer = "\n" + "="*60 + "\n"
            footer += f"上下文长度: {total_length} 字符\n"
            footer += "="*60
            
            return header + "\n\n---\n\n".join(final_parts) + footer
        
        return ""
    
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
        """构建运行时状态信息
        
        Returns:
            str: 运行时状态
        """
        try:
            status_parts = ["[运行时状态]"]
            
            # 检查最近的日志
            recent_log = self.log_analyzer.get_log_summary()
            if recent_log and "[LOG]" in recent_log:
                status_parts.append(f"**最近日志**: 可用")
            
            # 检查资产库状态
            assets_summary = self.asset_reader.get_all_assets_summary()
            if "[ASSET]" in assets_summary:
                # 提取资产数量
                import re
                match = re.search(r'共 (\d+) 个资产', assets_summary)
                if match:
                    status_parts.append(f"**资产库**: {match.group(1)} 个资产")
            
            # 检查配置状态
            config_summary = self.config_reader.get_all_configs_summary()
            if "[CONFIG]" in config_summary:
                match = re.search(r'共 (\d+) 个配置', config_summary)
                if match:
                    status_parts.append(f"**配置模板**: {match.group(1)} 个配置")
            
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
            overview_parts = [
                "[SYSTEM] **UE 工具箱系统概览**\n",
                "我可以帮你：",
                "1. [ASSET] 查找和管理虚幻引擎资产",
                "2. [CONFIG] 查看和管理 UE 引擎配置模板",
                "3. [DOC] 查阅项目文档和使用说明",
                "4. [LOG] 分析日志文件和诊断错误",
                "5. [HELP] 回答虚幻引擎相关问题\n",
                "**可用命令**:",
                "- '有哪些资产' - 查看资产库",
                "- '有哪些配置' - 查看配置模板",
                "- '搜索 [关键词]' - 搜索资产或配置",
                "- '查看文档' - 查看可用文档",
                "- '分析错误' - 查看最近的错误日志",
                "- '查看日志' - 查看日志统计"
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




