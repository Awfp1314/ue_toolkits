"""
查询改写模块（7.0-P7）
检测并处理模糊指代，提升查询明确性
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class RewriteResult:
    """改写结果"""
    original_query: str          # 原始查询
    rewritten_query: str         # 改写后的查询
    confidence: float            # 置信度（0-1）
    strategy: str                # 策略：'rewrite', 'clarify', 'skip'
    context_used: List[str]      # 使用的上下文
    
    def __str__(self):
        return f"RewriteResult(strategy={self.strategy}, confidence={self.confidence:.2f})"


class AmbiguityClassifier:
    """歧义检测器"""
    
    # 指代词权重
    DEICTIC_WORDS = {
        '那个': 0.3, '这个': 0.3, '那': 0.2, '这': 0.2,
        '刚才': 0.3, '上面': 0.2, '前面': 0.2, '之前': 0.2,
        '它': 0.2, '他': 0.15, '她': 0.15
    }
    
    # 省略主语的动词（以动词开头）
    VERB_STARTERS = ['怎么', '如何', '能不能', '可以', '为什么', '是不是']
    
    # 上下文依赖词
    CONTEXT_DEPENDENT = {'怎么办': 0.1, '为什么': 0.1, '呢': 0.05, '吗': 0.05}
    
    @classmethod
    def calculate_ambiguity_score(cls, query: str) -> float:
        """
        计算歧义评分
        
        Args:
            query: 查询文本
        
        Returns:
            歧义分数（0-1，越高越模糊）
        """
        score = 0.0
        
        # 1. 指代词检测
        for word, weight in cls.DEICTIC_WORDS.items():
            if word in query:
                score += weight
        
        # 2. 省略主语检测（以动词开头）
        for verb in cls.VERB_STARTERS:
            if query.startswith(verb):
                score += 0.2
                break
        
        # 3. 上下文依赖词检测
        for word, weight in cls.CONTEXT_DEPENDENT.items():
            if word in query:
                score += weight
        
        # 归一化到[0, 1]
        return min(score, 1.0)


class ContextExtractor:
    """上下文提取器"""
    
    @staticmethod
    def extract_entities(conversation_history: List[Dict], max_turns: int = 3) -> List[str]:
        """
        从历史对话中提取实体（名词、概念）
        
        Args:
            conversation_history: 对话历史
            max_turns: 最多提取几轮对话
        
        Returns:
            实体列表（按相关性排序）
        """
        entities = []
        
        # 只取最近的几轮对话
        recent_history = conversation_history[-max_turns * 2:] if len(conversation_history) > max_turns * 2 else conversation_history
        
        # 简单的名词提取（基于规则）
        noun_patterns = [
            r'(蓝图|节点|函数|变量|组件|资产|材质|模型|动画)',  # UE相关
            r'(文件|目录|配置|代码|脚本)',                    # 通用技术
            r'(问题|错误|BUG|功能|需求)',                     # 开发相关
        ]
        
        for msg in reversed(recent_history):  # 从最近的开始
            if msg.get('role') in ['user', 'assistant']:
                content = msg.get('content', '')
                if isinstance(content, str):
                    # 提取匹配的名词
                    for pattern in noun_patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if match not in entities:
                                entities.append(match)
        
        return entities[:5]  # 最多返回5个实体
    
    @staticmethod
    def get_last_topic(conversation_history: List[Dict]) -> Optional[str]:
        """
        获取上一轮对话的主题
        
        Args:
            conversation_history: 对话历史
        
        Returns:
            主题描述或None
        """
        if len(conversation_history) < 2:
            return None
        
        # 获取最后一轮用户消息
        for msg in reversed(conversation_history):
            if msg.get('role') == 'user':
                content = msg.get('content', '')
                if isinstance(content, str) and len(content) > 0:
                    # 返回前30个字符作为主题
                    return content[:30]
        
        return None


class QueryRewriter:
    """查询改写器"""
    
    # 歧义阈值
    THRESHOLD_HIGH = 0.7   # 高置信度：自动改写
    THRESHOLD_MID = 0.5    # 中置信度：生成澄清提示
    
    def __init__(self):
        self.classifier = AmbiguityClassifier()
        self.extractor = ContextExtractor()
    
    def rewrite_if_needed(
        self, 
        query: str, 
        conversation_history: List[Dict]
    ) -> RewriteResult:
        """
        根据需要改写查询
        
        Args:
            query: 原始查询
            conversation_history: 对话历史
        
        Returns:
            改写结果
        """
        # 1. 计算歧义分数
        ambiguity_score = self.classifier.calculate_ambiguity_score(query)
        
        print(f"[DEBUG] [7.0-P7] 歧义评分: {ambiguity_score:.2f} (查询: '{query}')")
        
        # 2. 根据分数决定策略
        if ambiguity_score < self.THRESHOLD_MID:
            # 低歧义：跳过改写
            return RewriteResult(
                original_query=query,
                rewritten_query=query,
                confidence=1.0 - ambiguity_score,
                strategy='skip',
                context_used=[]
            )
        
        # 3. 提取上下文
        entities = self.extractor.extract_entities(conversation_history)
        last_topic = self.extractor.get_last_topic(conversation_history)
        
        if ambiguity_score >= self.THRESHOLD_HIGH and entities:
            # 高歧义 + 有上下文：尝试改写
            rewritten = self._perform_rewrite(query, entities, last_topic)
            return RewriteResult(
                original_query=query,
                rewritten_query=rewritten,
                confidence=0.8,  # 保守估计
                strategy='rewrite',
                context_used=entities
            )
        else:
            # 中歧义：生成澄清提示（不改写原query）
            clarification = self._generate_clarification(query, entities, last_topic)
            return RewriteResult(
                original_query=query,
                rewritten_query=clarification,  # 实际上是澄清提示
                confidence=0.6,
                strategy='clarify',
                context_used=entities
            )
    
    def _perform_rewrite(
        self, 
        query: str, 
        entities: List[str], 
        last_topic: Optional[str]
    ) -> str:
        """
        执行改写
        
        Args:
            query: 原始查询
            entities: 提取的实体
            last_topic: 上一轮主题
        
        Returns:
            改写后的查询
        """
        rewritten = query
        
        # 替换指代词
        if '那个' in query or '这个' in query:
            if entities:
                # 用第一个实体替换
                ref = entities[0]
                rewritten = query.replace('那个', f'那个<ref>{ref}</ref>')
                rewritten = rewritten.replace('这个', f'这个<ref>{ref}</ref>')
        
        elif ('它' in query or '他' in query or '她' in query) and last_topic:
            # 用上一轮主题补充
            rewritten = f"{query}（指：{last_topic}）"
        
        return rewritten
    
    def _generate_clarification(
        self, 
        query: str, 
        entities: List[str], 
        last_topic: Optional[str]
    ) -> str:
        """
        生成澄清提示（实际返回原query，但会在系统消息中提示AI确认）
        
        Args:
            query: 原始查询
            entities: 提取的实体
            last_topic: 上一轮主题
        
        Returns:
            澄清提示文本
        """
        # 这个方法返回的内容会作为system消息插入
        hints = []
        if entities:
            hints.append(f"可能指代: {', '.join(entities)}")
        if last_topic:
            hints.append(f"上文提到: {last_topic}")
        
        if hints:
            return f"[澄清提示] 用户可能指代以下内容：{'; '.join(hints)}。请向用户确认。"
        else:
            return "[澄清提示] 用户查询较模糊，请引导用户明确需求。"

