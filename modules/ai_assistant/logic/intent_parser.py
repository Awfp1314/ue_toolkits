# -*- coding: utf-8 -*-

"""
语义意图解析器
支持多模型（嵌入模型 / 规则匹配）的可替换架构
"""

import re
from typing import Dict, Any, List, Optional
from enum import Enum
from core.logger import get_logger

logger = get_logger(__name__)

# 全局模型缓存（多个 IntentEngine 实例共享同一个模型，避免重复加载）
_CACHED_EMBEDDER = None


class IntentType(str, Enum):
    """意图类型枚举"""
    ASSET_QUERY = "asset.query"           # 查询资产
    ASSET_DETAIL = "asset.detail"         # 资产详情
    CONFIG_QUERY = "config.query"         # 查询配置
    CONFIG_COMPARE = "config.compare"     # 配置对比
    LOG_ANALYZE = "log.analyze"           # 日志分析
    LOG_SEARCH = "log.search"             # 日志搜索
    DOC_SEARCH = "doc.search"             # 文档搜索
    SITE_RECOMMENDATION = "site.recommendation"  # 站点推荐
    CHITCHAT = "chitchat"                 # 闲聊


class ModelType(str, Enum):
    """模型类型枚举"""
    BGE_SMALL = "bge-small"               # BAAI/bge-small-zh-v1.5
    RULE_BASED = "rule-based"             # 规则匹配


class IntentEngine:
    """
    语义意图引擎
    
    特性：
    - 延迟加载：首次调用 parse() 时才加载模型
    - 可替换模型：支持嵌入模型和规则匹配
    - 自动降级：模型加载失败时自动切换到规则匹配
    """
    
    def __init__(self, model_type: str = "bge-small", model_path: Optional[str] = None):
        """
        初始化意图引擎
        
        Args:
            model_type: 模型类型（bge-small / rule-based）
            model_path: 模型路径（可选，默认自动下载）
        """
        self.model_type = model_type
        self.model_path = model_path
        
        # 延迟加载：模型在首次使用时才初始化
        self._model = None
        self._embedder = None
        self._model_loaded = False
        
        self.logger = logger
        self.logger.info(f"意图引擎初始化（模型类型: {model_type}，延迟加载模式）")
    
    def parse(self, query: str) -> Dict[str, Any]:
        """
        解析用户查询的意图
        
        Args:
            query: 用户查询文本
            
        Returns:
            Dict: {
                'intent': IntentType,      # 意图类型
                'entities': List[str],     # 提取的实体
                'confidence': float        # 置信度 0-1
            }
        """
        try:
            # 延迟加载模型
            if not self._model_loaded:
                self._load_model()
            
            # 根据模型类型选择解析方法
            if self.model_type == ModelType.BGE_SMALL and self._embedder is not None:
                return self._parse_with_embedding(query)
            else:
                return self._parse_with_rules(query)
                
        except Exception as e:
            self.logger.error(f"意图解析失败: {e}", exc_info=True)
            # 降级到规则匹配
            return self._parse_with_rules(query)
    
    def _load_model(self):
        """
        延迟加载模型（首次调用时执行）
        
        注意：此方法在首次 parse() 时才执行，避免影响 PyQt6 启动速度
        
        优化：使用全局缓存，多个 IntentEngine 实例共享同一个模型
        """
        # 检查全局缓存
        global _CACHED_EMBEDDER
        if _CACHED_EMBEDDER is not None:
            self.logger.info("使用已缓存的语义模型")
            self._embedder = _CACHED_EMBEDDER
            self._model_loaded = True
            return
        
        self._model_loaded = True
        
        if self.model_type == ModelType.RULE_BASED:
            self.logger.info("使用规则匹配模式，无需加载模型")
            return
        
        try:
            self.logger.info("开始加载 sentence-transformers 模型...")
            from sentence_transformers import SentenceTransformer
            
            # 使用 BAAI/bge-small-zh-v1.5（约 100MB，中文语义表现优秀）
            model_name = self.model_path or "BAAI/bge-small-zh-v1.5"
            self._embedder = SentenceTransformer(model_name)
            
            # 保存到全局缓存（供其他 IntentEngine 实例复用）
            _CACHED_EMBEDDER = self._embedder
            
            self.logger.info(f"模型加载成功: {model_name}（已缓存到全局）")
            
        except Exception as e:
            self.logger.warning(f"模型加载失败，将使用规则匹配作为 fallback: {e}")
            self._embedder = None
    
    def _parse_with_embedding(self, query: str) -> Dict[str, Any]:
        """
        使用嵌入模型进行意图分类
        
        Args:
            query: 用户查询
            
        Returns:
            Dict: 意图解析结果
        """
        try:
            # 预定义的意图模板
            intent_templates = {
                IntentType.ASSET_QUERY: [
                    "查找资产", "搜索资产", "有哪些资产", "资产列表",
                    "查询蓝图", "找材质", "查找模型", "搜索纹理"
                ],
                IntentType.ASSET_DETAIL: [
                    "资产详情", "资产路径", "资产在哪", "资产包含什么",
                    "查看资产详细信息", "资产文件列表"
                ],
                IntentType.CONFIG_QUERY: [
                    "有哪些配置", "查找配置", "搜索配置", "配置列表",
                    "引擎配置", "项目设置"
                ],
                IntentType.CONFIG_COMPARE: [
                    "配置对比", "配置差异", "比较配置", "配置区别"
                ],
                IntentType.LOG_ANALYZE: [
                    "分析日志", "日志错误", "查看错误", "为什么出错",
                    "日志问题", "错误分析"
                ],
                IntentType.LOG_SEARCH: [
                    "搜索日志", "查找日志", "日志里有什么", "日志内容"
                ],
                IntentType.DOC_SEARCH: [
                    "查看文档", "搜索文档", "怎么使用", "如何操作",
                    "使用说明", "帮助文档"
                ],
                IntentType.SITE_RECOMMENDATION: [
                    "推荐网站", "有什么网站", "站点推荐", "资源网站",
                    "哪里下载", "学习网站", "论坛推荐", "资产商城"
                ],
                IntentType.CHITCHAT: [
                    "你好", "谢谢", "再见", "你是谁", "聊天"
                ]
            }
            
            # 计算查询与各意图模板的相似度
            query_embedding = self._embedder.encode(query, convert_to_numpy=True)
            
            max_similarity = 0.0
            best_intent = IntentType.CHITCHAT
            
            for intent, templates in intent_templates.items():
                template_embeddings = self._embedder.encode(templates, convert_to_numpy=True)
                
                # 计算余弦相似度
                import numpy as np
                similarities = np.dot(template_embeddings, query_embedding) / (
                    np.linalg.norm(template_embeddings, axis=1) * np.linalg.norm(query_embedding)
                )
                
                avg_similarity = float(np.mean(similarities))
                
                if avg_similarity > max_similarity:
                    max_similarity = avg_similarity
                    best_intent = intent
            
            # 提取实体（简单关键词提取）
            entities = self._extract_entities(query)
            
            return {
                'intent': best_intent,
                'entities': entities,
                'confidence': max_similarity
            }
            
        except Exception as e:
            self.logger.error(f"嵌入模型解析失败: {e}", exc_info=True)
            # 降级到规则匹配
            return self._parse_with_rules(query)
    
    def _parse_with_rules(self, query: str) -> Dict[str, Any]:
        """
        使用规则匹配进行意图分类（fallback 方法）
        
        Args:
            query: 用户查询
            
        Returns:
            Dict: 意图解析结果
        """
        query_lower = query.lower()
        
        # 规则匹配表
        rules = [
            # (意图类型, 关键词列表, 优先级)
            (IntentType.ASSET_DETAIL, ['路径', '在哪', '详细', '详情', '具体', '包含', '文件', '里面有'], 2),
            (IntentType.ASSET_QUERY, ['资产', 'asset', '模型', 'model', '纹理', 'texture', '蓝图', 'blueprint', '材质', 'material', '搜索', '查找', '有哪些'], 1),
            (IntentType.CONFIG_COMPARE, ['配置对比', '配置差异', '比较配置', 'diff', 'compare'], 2),
            (IntentType.CONFIG_QUERY, ['配置', 'config', '设置', 'settings', '模板', 'template', 'ini'], 1),
            (IntentType.LOG_ANALYZE, ['错误', 'error', '警告', 'warning', '分析日志', '为什么', '出错', '失败', '崩溃'], 2),
            (IntentType.LOG_SEARCH, ['日志', 'log', '搜索日志', '查找日志'], 1),
            (IntentType.DOC_SEARCH, ['文档', 'document', '说明', 'readme', '教程', '如何', 'how', '怎么', '使用'], 1),
            (IntentType.SITE_RECOMMENDATION, ['网站', '站点', '推荐', 'site', 'website', '资源网站', '论坛', '学习网站', '哪里下载', '哪里学', 'fab', 'marketplace', '商城', '资产商店'], 2),
        ]
        
        # 按优先级匹配
        matched_intent = IntentType.CHITCHAT
        max_priority = 0
        match_count = 0
        
        for intent, keywords, priority in rules:
            count = sum(1 for keyword in keywords if keyword in query_lower)
            if count > 0 and priority >= max_priority:
                if priority > max_priority or count > match_count:
                    matched_intent = intent
                    max_priority = priority
                    match_count = count
        
        # 提取实体
        entities = self._extract_entities(query)
        
        # 计算置信度（基于匹配关键词数量）
        confidence = min(0.5 + (match_count * 0.15), 1.0) if match_count > 0 else 0.3
        
        return {
            'intent': matched_intent,
            'entities': entities,
            'confidence': confidence
        }
    
    def _extract_entities(self, query: str) -> List[str]:
        """
        提取查询中的实体（关键词）
        
        Args:
            query: 用户查询
            
        Returns:
            List[str]: 提取的实体列表
        """
        # 简单的实体提取：移除停用词后的关键词
        stop_words = {
            '的', '了', '是', '在', '有', '和', '吗', '呢', '啊', '吧', '我', '你', '他',
            'the', 'a', 'an', 'is', 'are', 'what', 'how', 'where', '查找', '搜索', '查看'
        }
        
        # 分词（简单按空格和标点分割）
        words = re.findall(r'\w+', query.lower())
        
        # 过滤停用词和短词
        entities = [word for word in words if word not in stop_words and len(word) > 1]
        
        return entities[:5]  # 最多返回5个实体

