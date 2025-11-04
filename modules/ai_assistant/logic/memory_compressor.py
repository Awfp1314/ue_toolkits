# -*- coding: utf-8 -*-

"""
对话历史压缩模块
使用轻量模型（如 gemini-2.5-flash）生成对话摘要，降低 token 消耗
"""

from typing import List, Dict, Any, Optional, Callable
from core.logger import get_logger

logger = get_logger(__name__)


class MemoryCompressor:
    """对话历史压缩器
    
    策略：
    - 当对话历史超过 max_history 条时，触发压缩
    - 保留最近 keep_recent 条原始消息
    - 将旧消息压缩为摘要（约 200 tokens）
    """
    
    def __init__(
        self, 
        api_client_factory: Optional[Callable] = None,
        max_history: int = 10,
        keep_recent: int = 5,
        compression_model: str = "gemini-2.5-flash"
    ):
        """初始化压缩器
        
        Args:
            api_client_factory: API 客户端工厂函数
            max_history: 触发压缩的历史消息数量阈值
            keep_recent: 压缩后保留的最近消息数量
            compression_model: 用于生成摘要的模型
        """
        self.api_client_factory = api_client_factory
        self.max_history = max_history
        self.keep_recent = keep_recent
        self.compression_model = compression_model
        self.logger = logger
        
        self.logger.info(
            f"对话压缩器初始化完成（阈值: {max_history}，保留: {keep_recent}，模型: {compression_model}）"
        )
    
    def should_compress(self, history_count: int) -> bool:
        """判断是否需要压缩
        
        Args:
            history_count: 当前历史消息数量
            
        Returns:
            bool: 是否需要压缩
        """
        return history_count > self.max_history
    
    def compress_history(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """压缩对话历史为摘要
        
        Args:
            messages: 需要压缩的消息列表 [{'role': 'user', 'content': '...'}, ...]
            
        Returns:
            str: 压缩后的摘要，格式为 "[记忆摘要]: ..."
        """
        if not messages:
            return None
        
        if not self.api_client_factory:
            self.logger.warning("API 客户端工厂未设置，无法压缩历史，返回简化摘要")
            return self._simple_summary(messages)
        
        try:
            self.logger.info(f"开始压缩 {len(messages)} 条历史消息...")
            
            # 构建压缩提示词
            compression_prompt = self._build_compression_prompt(messages)
            
            # 调用 API 生成摘要（非流式，同步获取结果）
            summary = self._call_compression_api(compression_prompt)
            
            if summary:
                self.logger.info(f"压缩完成，摘要长度: {len(summary)} 字符")
                return f"[记忆摘要]: {summary}"
            else:
                self.logger.warning("压缩失败，返回简化摘要")
                return self._simple_summary(messages)
        
        except Exception as e:
            self.logger.error(f"压缩历史时出错: {e}", exc_info=True)
            return self._simple_summary(messages)
    
    def _build_compression_prompt(self, messages: List[Dict[str, str]]) -> str:
        """构建压缩提示词
        
        Args:
            messages: 需要压缩的消息列表
            
        Returns:
            str: 压缩提示词
        """
        # 将消息格式化为文本
        conversation_text = []
        for msg in messages:
            role = "用户" if msg['role'] == 'user' else "助手"
            content = msg.get('content', '')
            
            # 处理多模态内容（如果有）
            if isinstance(content, list):
                # 提取文本内容
                text_parts = [item.get('text', '') for item in content if item.get('type') == 'text']
                content = ' '.join(text_parts)
            
            conversation_text.append(f"{role}: {content}")
        
        conversation = "\n".join(conversation_text)
        
        # 压缩提示词
        prompt = f"""请将以下对话历史压缩为简洁的摘要（约100字以内）。

要求：
1. 提取关键信息和用户意图
2. 保留重要的技术细节和决策
3. 忽略寒暄和重复内容
4. 使用第三人称描述

对话历史：
{conversation}

摘要："""
        
        return prompt
    
    def _call_compression_api(self, prompt: str) -> Optional[str]:
        """调用 API 生成压缩摘要（同步方式）
        
        Args:
            prompt: 压缩提示词
            
        Returns:
            str: 生成的摘要
        """
        try:
            from PyQt6.QtCore import QEventLoop
            
            # 构建消息
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            # 创建 API 客户端
            client = self.api_client_factory(messages, model=self.compression_model)
            
            # 用于收集流式响应
            summary_parts = []
            error_message = None
            
            def on_chunk(chunk):
                summary_parts.append(chunk)
            
            def on_error(error):
                nonlocal error_message
                error_message = error
                self.logger.error(f"压缩 API 调用失败: {error}")
            
            # 连接信号
            client.chunk_received.connect(on_chunk)
            client.error_occurred.connect(on_error)
            
            # 创建事件循环等待完成
            loop = QEventLoop()
            client.request_finished.connect(loop.quit)
            client.error_occurred.connect(loop.quit)
            
            # 启动请求
            client.start()
            
            # 等待完成（最多30秒）
            from PyQt6.QtCore import QTimer
            timeout_timer = QTimer()
            timeout_timer.setSingleShot(True)
            timeout_timer.timeout.connect(loop.quit)
            timeout_timer.start(30000)
            
            loop.exec()
            
            # 检查错误
            if error_message:
                return None
            
            # 返回摘要
            if summary_parts:
                return ''.join(summary_parts).strip()
            return None
        
        except Exception as e:
            self.logger.error(f"调用压缩 API 时出错: {e}", exc_info=True)
            return None
    
    def _simple_summary(self, messages: List[Dict[str, str]]) -> str:
        """生成简化摘要（不调用 API）
        
        Args:
            messages: 消息列表
            
        Returns:
            str: 简化摘要
        """
        user_count = sum(1 for m in messages if m['role'] == 'user')
        topics = []
        
        # 提取用户消息的关键词
        for msg in messages:
            if msg['role'] == 'user':
                content = msg.get('content', '')
                if isinstance(content, list):
                    content = ' '.join([item.get('text', '') for item in content if item.get('type') == 'text'])
                
                # 简单提取（取前30字符）
                if len(content) > 30:
                    topics.append(content[:30] + "...")
                elif content:
                    topics.append(content)
        
        # 限制主题数量
        if len(topics) > 3:
            topics = topics[:3] + [f"等 {len(topics) - 3} 个话题"]
        
        summary = f"用户在前面的对话中共提出 {user_count} 个问题"
        if topics:
            summary += f"，涉及：{', '.join(topics)}"
        
        return f"[记忆摘要]: {summary}"

