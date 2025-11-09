# -*- coding: utf-8 -*-

"""
API 调用追踪器

追踪所有 API 调用，检测和防止重复调用
"""

import time
import hashlib
import traceback
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class APICallRecord:
    """API 调用记录"""
    timestamp: float
    session_id: str
    messages_hash: str  # 消息列表的哈希值
    call_type: str  # 'non_streaming' | 'streaming' | 'retry'
    message_count: int
    has_tools: bool
    stack_trace: str  # 调用堆栈（用于调试）


class APICallTracker:
    """
    API 调用追踪器
    
    职责：
    1. 记录所有 API 调用
    2. 检测重复调用
    3. 生成调试报告
    """
    
    def __init__(self, duplicate_threshold: float = 1.0):
        """
        初始化追踪器
        
        Args:
            duplicate_threshold: 重复调用检测阈值（秒），在此时间内的相同调用视为重复
        """
        self.call_history: List[APICallRecord] = []
        self.current_session_id: Optional[str] = None
        self.duplicate_threshold = duplicate_threshold
        self._session_counter = 0
    
    def start_session(self) -> str:
        """
        开始新的对话会话
        
        Returns:
            str: 会话 ID
        """
        self._session_counter += 1
        self.current_session_id = f"session_{self._session_counter}_{int(time.time())}"
        print(f"[APICallTracker] 开始新会话: {self.current_session_id}")
        return self.current_session_id
    
    def record_call(self, messages: List[Dict], call_type: str, has_tools: bool = False):
        """
        记录一次 API 调用
        
        Args:
            messages: 消息列表
            call_type: 调用类型 ('non_streaming' | 'streaming' | 'retry')
            has_tools: 是否包含工具定义
        """
        if not self.current_session_id:
            self.start_session()
        
        # 计算消息哈希值
        messages_hash = self._hash_messages(messages)
        
        # 获取调用堆栈
        stack_trace = ''.join(traceback.format_stack()[-5:-1])  # 最近5层调用
        
        # 创建记录
        record = APICallRecord(
            timestamp=time.time(),
            session_id=self.current_session_id,
            messages_hash=messages_hash,
            call_type=call_type,
            message_count=len(messages),
            has_tools=has_tools,
            stack_trace=stack_trace
        )
        
        self.call_history.append(record)
        
        print(f"[APICallTracker] 记录 API 调用: {call_type}, 消息数: {len(messages)}, 哈希: {messages_hash[:8]}...")
    
    def check_duplicate(self, messages: List[Dict], call_type: str) -> bool:
        """
        检查是否为重复调用
        
        Args:
            messages: 消息列表
            call_type: 调用类型
            
        Returns:
            bool: True 如果检测到重复调用
        """
        if not self.current_session_id:
            return False
        
        messages_hash = self._hash_messages(messages)
        current_time = time.time()
        
        # 检查最近的调用记录
        for record in reversed(self.call_history[-10:]):  # 只检查最近10次调用
            # 只检查当前会话的调用
            if record.session_id != self.current_session_id:
                continue
            
            # 检查时间间隔
            time_diff = current_time - record.timestamp
            if time_diff > self.duplicate_threshold:
                continue
            
            # 检查消息哈希是否相同
            if record.messages_hash == messages_hash and record.call_type == call_type:
                print(f"\n{'='*80}")
                print(f"[APICallTracker] ⚠️ 检测到重复 API 调用！")
                print(f"[APICallTracker] 调用类型: {call_type}")
                print(f"[APICallTracker] 时间间隔: {time_diff:.2f}秒")
                print(f"[APICallTracker] 消息哈希: {messages_hash[:16]}...")
                print(f"[APICallTracker] 原始调用时间: {datetime.fromtimestamp(record.timestamp).strftime('%H:%M:%S')}")
                print(f"[APICallTracker] 当前调用时间: {datetime.fromtimestamp(current_time).strftime('%H:%M:%S')}")
                print(f"{'='*80}\n")
                
                # 记录到日志文件
                self._log_duplicate(record, messages_hash, time_diff)
                
                return True
        
        return False
    
    def get_session_calls(self, session_id: Optional[str] = None) -> List[APICallRecord]:
        """
        获取指定会话的所有调用记录
        
        Args:
            session_id: 会话 ID，None 表示当前会话
            
        Returns:
            List[APICallRecord]: 调用记录列表
        """
        target_session = session_id or self.current_session_id
        if not target_session:
            return []
        
        return [record for record in self.call_history if record.session_id == target_session]
    
    def get_session_summary(self, session_id: Optional[str] = None) -> Dict:
        """
        获取会话统计摘要
        
        Args:
            session_id: 会话 ID，None 表示当前会话
            
        Returns:
            Dict: 统计信息
        """
        calls = self.get_session_calls(session_id)
        
        if not calls:
            return {
                'total_calls': 0,
                'non_streaming_calls': 0,
                'streaming_calls': 0,
                'retry_calls': 0,
                'duration': 0
            }
        
        return {
            'total_calls': len(calls),
            'non_streaming_calls': sum(1 for c in calls if c.call_type == 'non_streaming'),
            'streaming_calls': sum(1 for c in calls if c.call_type == 'streaming'),
            'retry_calls': sum(1 for c in calls if c.call_type == 'retry'),
            'duration': calls[-1].timestamp - calls[0].timestamp if len(calls) > 1 else 0
        }
    
    def _hash_messages(self, messages: List[Dict]) -> str:
        """
        计算消息列表的哈希值
        
        Args:
            messages: 消息列表
            
        Returns:
            str: SHA256 哈希值
        """
        # 只使用 role 和 content 计算哈希，忽略其他字段
        simplified = []
        for msg in messages:
            role = msg.get('role', '')
            content = msg.get('content', '')
            
            # 处理多模态内容
            if isinstance(content, list):
                content = str([item.get('text', '') for item in content if item.get('type') == 'text'])
            
            simplified.append(f"{role}:{content}")
        
        message_str = '|'.join(simplified)
        return hashlib.sha256(message_str.encode('utf-8')).hexdigest()
    
    def _log_duplicate(self, original_record: APICallRecord, messages_hash: str, time_diff: float):
        """
        记录重复调用到日志文件
        
        Args:
            original_record: 原始调用记录
            messages_hash: 消息哈希
            time_diff: 时间间隔
        """
        try:
            import os
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            log_file = os.path.join(log_dir, "duplicate_api_calls.log")
            
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"会话 ID: {original_record.session_id}\n")
                f.write(f"调用类型: {original_record.call_type}\n")
                f.write(f"消息哈希: {messages_hash}\n")
                f.write(f"时间间隔: {time_diff:.2f}秒\n")
                f.write(f"原始调用时间: {datetime.fromtimestamp(original_record.timestamp).strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"原始调用堆栈:\n{original_record.stack_trace}\n")
                f.write(f"当前调用堆栈:\n{''.join(traceback.format_stack()[-5:-1])}\n")
                f.write(f"{'='*80}\n")
        
        except Exception as e:
            print(f"[APICallTracker] 写入日志文件失败: {e}")
    
    def clear_session(self):
        """清空当前会话的记录"""
        if self.current_session_id:
            self.call_history = [
                record for record in self.call_history 
                if record.session_id != self.current_session_id
            ]
            print(f"[APICallTracker] 已清空会话: {self.current_session_id}")
            self.current_session_id = None
