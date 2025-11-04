# -*- coding: utf-8 -*-

"""
动作引擎
实现 OpenAI Function/Tool Calling 两段式回路
"""

import time
import json
from typing import Dict, Any, List, Optional
from core.logger import get_logger

logger = get_logger(__name__)


class ActionEngine:
    """
    动作引擎
    
    v0.2: 实现两段式工具调用流程
    1. 第一次请求：带 tools 描述 → 接收 tool_calls
    2. 执行工具 → 形成 tool outputs
    3. 第二次请求：追加 tool outputs → 生成最终答复
    """
    
    def __init__(self, tools_registry, api_client_factory):
        """
        初始化动作引擎
        
        Args:
            tools_registry: ToolsRegistry 实例
            api_client_factory: API 客户端工厂函数
        """
        self.logger = logger
        self.tools_registry = tools_registry
        self.api_client_factory = api_client_factory
        
        # 调用记录
        self.call_history: List[Dict[str, Any]] = []
        
        self.logger.info("动作引擎初始化完成")
    
    def execute_with_tools(
        self,
        messages: List[Dict[str, Any]],
        on_chunk_received: Optional[Callable] = None,
        on_finished: Optional[Callable] = None,
        on_error: Optional[Callable] = None
    ) -> None:
        """
        使用工具增强的执行流程（两段式）
        
        Args:
            messages: 对话历史
            on_chunk_received: 接收数据块回调
            on_finished: 完成回调
            on_error: 错误回调
        """
        try:
            self.logger.info("开始两段式工具调用流程")
            
            # ===== 第一阶段：请求工具调用 =====
            
            # 获取 OpenAI tools schemas
            tools_schemas = self.tools_registry.openai_tool_schemas()
            
            if not tools_schemas:
                self.logger.warning("无可用工具，使用普通对话流程")
                self._execute_normal_flow(messages, on_chunk_received, on_finished, on_error)
                return
            
            # 创建第一次 API 请求（带 tools）
            first_request_messages = messages.copy()
            
            # 注意：这里需要同步调用 API 获取 tool_calls
            # 暂时使用简化实现：直接执行工具（后续可以真正调用 OpenAI API）
            
            # v0.2 简化实现：使用意图引擎决定调用哪个工具
            last_user_message = self._get_last_user_message(messages)
            
            if last_user_message:
                tool_calls_result = self._decide_tool_calls(last_user_message)
                
                if tool_calls_result:
                    # ===== 第二阶段：执行工具 =====
                    tool_outputs = self._execute_tools(tool_calls_result)
                    
                    # ===== 第三阶段：生成最终答复 =====
                    self._generate_final_response(
                        messages,
                        tool_outputs,
                        on_chunk_received,
                        on_finished,
                        on_error
                    )
                else:
                    # 无需调用工具，普通流程
                    self._execute_normal_flow(messages, on_chunk_received, on_finished, on_error)
            else:
                self._execute_normal_flow(messages, on_chunk_received, on_finished, on_error)
        
        except Exception as e:
            self.logger.error(f"工具调用流程失败: {e}", exc_info=True)
            if on_error:
                on_error(f"工具调用失败: {str(e)}")
    
    def _get_last_user_message(self, messages: List[Dict]) -> Optional[str]:
        """获取最后一条用户消息"""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                # 处理字符串或列表格式
                if isinstance(content, str):
                    return content
                elif isinstance(content, list):
                    # 多模态消息，提取文本
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            return item.get("text", "")
                return ""
        return None
    
    def _decide_tool_calls(self, query: str) -> Optional[List[Dict]]:
        """
        决定需要调用哪些工具（基于意图）
        
        v0.2 简化实现：基于意图引擎的结果选择工具
        真正的 OpenAI tool_calls 在后续版本实现
        
        Args:
            query: 用户查询
            
        Returns:
            List[Dict]: 工具调用列表，格式类似 OpenAI tool_calls
        """
        try:
            from modules.ai_assistant.logic.intent_parser import IntentEngine, IntentType
            
            engine = IntentEngine(model_type="rule-based")  # 快速决策用规则
            result = engine.parse(query)
            
            intent = result['intent']
            entities = result['entities']
            
            # 根据意图映射到工具
            if intent == IntentType.ASSET_QUERY and entities:
                return [{
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "search_assets",
                        "arguments": json.dumps({"keyword": entities[0]})
                    }
                }]
            
            elif intent == IntentType.ASSET_DETAIL and entities:
                return [{
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "query_asset_detail",
                        "arguments": json.dumps({"asset_name": entities[0]})
                    }
                }]
            
            elif intent == IntentType.CONFIG_QUERY and entities:
                return [{
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "search_configs",
                        "arguments": json.dumps({"keyword": entities[0]})
                    }
                }]
            
            elif intent == IntentType.LOG_SEARCH and entities:
                return [{
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "search_logs",
                        "arguments": json.dumps({"keyword": entities[0]})
                    }
                }]
            
            elif intent == IntentType.DOC_SEARCH and entities:
                return [{
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "search_docs",
                        "arguments": json.dumps({"keyword": entities[0]})
                    }
                }]
            
            return None
        
        except Exception as e:
            self.logger.error(f"决策工具调用失败: {e}")
            return None
    
    def _execute_tools(self, tool_calls: List[Dict]) -> List[Dict[str, Any]]:
        """
        执行工具调用
        
        Args:
            tool_calls: 工具调用列表
            
        Returns:
            List[Dict]: 工具输出列表
        """
        tool_outputs = []
        
        for tool_call in tool_calls:
            start_time = time.time()
            
            try:
                tool_name = tool_call["function"]["name"]
                arguments_str = tool_call["function"]["arguments"]
                arguments = json.loads(arguments_str)
                
                # v0.2: 安全检查 - 是否需要确认
                tool_def = self.tools_registry.tools.get(tool_name)
                if tool_def and tool_def.requires_confirmation:
                    # TODO v0.3: 触发确认对话框
                    self.logger.warning(f"工具 {tool_name} 需要确认，但确认机制未实现（v0.3）")
                
                # 调度执行
                result = self.tools_registry.dispatch(tool_name, arguments)
                
                elapsed = time.time() - start_time
                
                # 记录调用
                self.call_history.append({
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "result": result,
                    "elapsed_time": elapsed,
                    "timestamp": time.time()
                })
                
                # 格式化输出
                tool_outputs.append({
                    "tool_call_id": tool_call.get("id", "unknown"),
                    "role": "tool",
                    "name": tool_name,
                    "content": result.get("result", result.get("error", ""))
                })
                
                self.logger.info(f"工具 {tool_name} 执行完成，耗时: {elapsed:.2f}s")
            
            except Exception as e:
                self.logger.error(f"执行工具失败: {e}")
                tool_outputs.append({
                    "tool_call_id": tool_call.get("id", "unknown"),
                    "role": "tool",
                    "name": tool_call.get("function", {}).get("name", "unknown"),
                    "content": f"[错误] 工具执行失败: {str(e)}"
                })
        
        return tool_outputs
    
    def _generate_final_response(
        self,
        original_messages: List[Dict],
        tool_outputs: List[Dict],
        on_chunk_received,
        on_finished,
        on_error
    ):
        """
        生成包含工具结果的最终答复
        
        Args:
            original_messages: 原始对话历史
            tool_outputs: 工具输出
            on_chunk_received: 数据块回调
            on_finished: 完成回调
            on_error: 错误回调
        """
        try:
            # 将工具结果附加到上下文
            enhanced_messages = original_messages.copy()
            
            # 添加工具输出到消息历史
            for tool_output in tool_outputs:
                enhanced_messages.append({
                    "role": "tool",
                    "name": tool_output["name"],
                    "content": tool_output["content"]
                })
            
            # 添加提示让 AI 基于工具结果回答
            enhanced_messages.append({
                "role": "system",
                "content": "请基于上述工具查询结果回答用户问题，并在回答中标注信息来源。"
            })
            
            # 创建新的 API 请求
            api_client = self.api_client_factory(enhanced_messages)
            
            if on_chunk_received:
                api_client.chunk_received.connect(on_chunk_received)
            if on_finished:
                api_client.request_finished.connect(on_finished)
            if on_error:
                api_client.error_occurred.connect(on_error)
            
            api_client.start()
            
        except Exception as e:
            self.logger.error(f"生成最终答复失败: {e}")
            if on_error:
                on_error(f"生成答复失败: {str(e)}")
    
    def _execute_normal_flow(self, messages, on_chunk_received, on_finished, on_error):
        """执行普通对话流程（无工具调用）"""
        try:
            api_client = self.api_client_factory(messages)
            
            if on_chunk_received:
                api_client.chunk_received.connect(on_chunk_received)
            if on_finished:
                api_client.request_finished.connect(on_finished)
            if on_error:
                api_client.error_occurred.connect(on_error)
            
            api_client.start()
        
        except Exception as e:
            self.logger.error(f"普通流程执行失败: {e}")
            if on_error:
                on_error(str(e))
    
    def get_call_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取工具调用历史
        
        Args:
            limit: 返回的记录数量
            
        Returns:
            List[Dict]: 最近的工具调用记录
        """
        return self.call_history[-limit:] if self.call_history else []

