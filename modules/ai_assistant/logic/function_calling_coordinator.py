# -*- coding: utf-8 -*-

"""
Function Calling 协调器
实现真正的两段式 Function Calling：LLM → 工具执行 → LLM 最终回复
支持多轮工具调用和循环限制
"""

import json
import traceback
from typing import Dict, List, Callable, Optional, Any
from PyQt6.QtCore import QThread, pyqtSignal


def format_tool_result(result: Dict) -> str:
    """
    将工具执行结果格式化为 LLM 可理解的文本
    
    Args:
        result: 工具执行结果字典
        
    Returns:
        str: 格式化后的文本
    """
    if result.get('success'):
        tool_result = result.get('result', '')
        # 如果结果是字典或列表，转为 JSON
        if isinstance(tool_result, (dict, list)):
            tool_result = json.dumps(tool_result, ensure_ascii=False, indent=2)
        return f"工具执行成功。结果:\n{tool_result}"
    else:
        error_msg = result.get('error', '未知错误')
        return f"工具执行失败。错误: {error_msg}"


class FunctionCallingCoordinator(QThread):
    """
    Function Calling 协调器
    
    职责：
    1. 协调 LLM 和工具执行的多轮交互
    2. 检测 tool_calls 并执行工具
    3. 将工具结果返回 LLM 生成最终回复
    4. 提供 UI 回调支持
    """
    
    # 信号定义
    tool_start = pyqtSignal(str)  # 工具开始执行：tool_name
    tool_complete = pyqtSignal(str, dict)  # 工具完成：tool_name, result
    chunk_received = pyqtSignal(str)  # 文本块接收：chunk
    request_finished = pyqtSignal()  # 请求完成
    token_usage = pyqtSignal(dict)  # Token 使用量统计
    error_occurred = pyqtSignal(str)  # 错误发生：error_message
    
    def __init__(
        self,
        messages: List[Dict],
        tools_registry,
        llm_client,
        max_iterations: int = 5
    ):
        """
        初始化协调器
        
        Args:
            messages: 初始消息列表
            tools_registry: 工具注册表实例
            llm_client: LLM 客户端实例
            max_iterations: 最大迭代次数（防止无限循环）
        """
        super().__init__()
        self.messages = messages.copy()
        self.tools_registry = tools_registry
        self.llm_client = llm_client
        self.max_iterations = max_iterations
        self._should_stop = False
    
    def stop(self):
        """停止执行"""
        self._should_stop = True
    
    def run(self):
        """
        执行 Function Calling 流程
        
        流程：
        1. 调用 LLM（带 tools 参数）
        2. 检查响应是否包含 tool_calls
        3. 如果有，执行工具并将结果追加到消息
        4. 重复步骤 1-3，直到 LLM 返回最终文本或达到最大迭代次数
        """
        # 关键调试：追踪协调器启动
        import traceback
        call_stack = ''.join(traceback.format_stack())
        print(f"\n{'='*80}")
        print(f"[COORDINATOR] !!! FunctionCallingCoordinator.run() 被调用！")
        print(f"[COORDINATOR] 消息数量: {len(self.messages)}")
        tools_count = len(self.tools_registry.openai_tool_schemas()) if self.tools_registry else 0
        print(f"[COORDINATOR] 工具数量: {tools_count}")
        print(f"[COORDINATOR] 调用堆栈:\n{call_stack}")
        print(f"{'='*80}\n")
        
        try:
            iteration = 0
            
            while iteration < self.max_iterations and not self._should_stop:
                print(f"[DEBUG] [FunctionCalling] 第 {iteration + 1} 轮迭代开始")
                
                # 获取工具定义
                tools = self.tools_registry.openai_tool_schemas() if self.tools_registry else None
                
                # 调用 LLM（非流式，用于检测 tool_calls）
                response_data = self._call_llm_non_streaming(self.messages, tools)
                
                if self._should_stop:
                    break
                
                # 检查响应类型
                if response_data['type'] == 'tool_calls':
                    # LLM 决定调用工具
                    tool_calls = response_data['tool_calls']
                    print(f"[DEBUG] [FunctionCalling] LLM 请求调用 {len(tool_calls)} 个工具")
                    
                    # 构建 assistant 消息（包含 tool_calls）
                    assistant_message = {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": tool_calls
                    }
                    self.messages.append(assistant_message)
                    
                    # 执行每个工具
                    for tool_call in tool_calls:
                        if self._should_stop:
                            break
                        
                        tool_name = tool_call['function']['name']
                        tool_args_str = tool_call['function']['arguments']
                        tool_call_id = tool_call['id']
                        
                        print(f"[DEBUG] [FunctionCalling] 执行工具: {tool_name}")
                        print(f"[DEBUG] [FunctionCalling] 参数: {tool_args_str}")
                        
                        # 通知 UI 工具开始
                        self.tool_start.emit(tool_name)
                        
                        # 执行工具
                        result = self._execute_tool(tool_name, tool_args_str)
                        
                        # 通知 UI 工具完成
                        self.tool_complete.emit(tool_name, result)
                        
                        # 将工具结果追加到消息
                        tool_message = {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": format_tool_result(result)
                        }
                        self.messages.append(tool_message)
                        
                        print(f"[DEBUG] [FunctionCalling] 工具结果: {format_tool_result(result)[:200]}")
                    
                    # 继续下一轮迭代
                    iteration += 1
                    
                elif response_data['type'] == 'content':
                    # LLM 返回最终文本（第一次非流式调用已获取）
                    print(f"[DEBUG] [FunctionCalling] LLM 返回最终回复（无需工具调用）")
                    print(f"[DEBUG] [FunctionCalling] [OPTIMIZATION] 使用第一次调用的结果，避免重复API请求")
                    
                    # [OPTIMIZATION] 关键修复：直接使用第一次调用的content，避免第二次API调用
                    content = response_data.get('content', '')
                    usage = response_data.get('usage')  # 获取token使用统计
                    
                    if content:
                        # 模拟流式输出（逐字发送给UI，提供流畅体验）
                        import time
                        buffer = ""
                        for char in content:
                            buffer += char
                            # 每10个字符发送一次，模拟流式效果
                            if len(buffer) >= 10:
                                self.chunk_received.emit(buffer)
                                buffer = ""
                                time.sleep(0.01)  # 短暂延迟，模拟网络传输
                        
                        # 发送剩余内容
                        if buffer:
                            self.chunk_received.emit(buffer)
                    
                    # ⚡ 发送token使用统计（如果有）
                    if usage:
                        self.token_usage.emit(usage)
                    
                    # 完成
                    self.request_finished.emit()
                    break
                
                else:
                    # 未知响应类型
                    raise Exception(f"未知的响应类型: {response_data['type']}")
            
            if iteration >= self.max_iterations:
                # 超过最大迭代次数
                error_msg = f"工具调用次数过多（{self.max_iterations} 次），已终止"
                print(f"[WARNING] [FunctionCalling] {error_msg}")
                self.error_occurred.emit(error_msg)
        
        except Exception as e:
            error_msg = f"Function Calling 执行失败: {str(e)}"
            print(f"[ERROR] [FunctionCalling] {error_msg}")
            print(traceback.format_exc())
            self.error_occurred.emit(error_msg)
    
    def _call_llm_non_streaming(self, messages: List[Dict], tools: List[Dict]) -> Dict:
        """
        调用 LLM（非流式）用于检测 tool_calls
        
        Args:
            messages: 消息列表
            tools: 工具定义列表
            
        Returns:
            Dict: {
                'type': 'tool_calls' | 'content',
                'tool_calls': [...] | None,
                'content': str | None
            }
        """
        try:
            # 调用 LLM 客户端的非流式方法
            return self.llm_client.generate_response_non_streaming(messages, tools=tools)
        except AttributeError:
            # 如果 LLM 客户端不支持非流式方法，回退到流式并累积
            print("[WARNING] [FunctionCalling] LLM 客户端不支持非流式调用，使用流式回退")
            
            accumulated_content = ""
            accumulated_tool_calls = None
            
            for chunk in self.llm_client.generate_response(messages, stream=True, tools=tools):
                if isinstance(chunk, dict):
                    chunk_type = chunk.get('type')
                    
                    if chunk_type == 'tool_calls':
                        accumulated_tool_calls = chunk.get('tool_calls')
                    elif chunk_type == 'content':
                        accumulated_content += chunk.get('text', '')
                    elif chunk_type == 'token_usage':
                        # ⚡ 转发 token 使用量
                        self.token_usage.emit(chunk.get('usage', {}))
                else:
                    accumulated_content += str(chunk)
            
            if accumulated_tool_calls:
                return {'type': 'tool_calls', 'tool_calls': accumulated_tool_calls, 'content': None}
            else:
                return {'type': 'content', 'tool_calls': None, 'content': accumulated_content}
        except Exception as e:
            # 捕获模型不支持工具的错误
            error_msg = str(e)
            if 'does not support tools' in error_msg or 'tools' in error_msg.lower():
                print(f"[WARNING] [FunctionCalling] 当前模型不支持 Function Calling，降级为普通模式")
                # 返回空的 tool_calls，让协调器直接生成普通回复
                try:
                    # 不带 tools 参数重新调用
                    return self.llm_client.generate_response_non_streaming(messages, tools=None)
                except:
                    # 回退到流式
                    accumulated_content = ""
                    for chunk in self.llm_client.generate_response(messages, stream=True, tools=None):
                        if isinstance(chunk, dict):
                            chunk_type = chunk.get('type')
                            
                            if chunk_type == 'content':
                                accumulated_content += chunk.get('text', '')
                            elif chunk_type == 'token_usage':
                                # ⚡ 转发 token 使用量
                                self.token_usage.emit(chunk.get('usage', {}))
                        else:
                            accumulated_content += str(chunk)
                    return {'type': 'content', 'tool_calls': None, 'content': accumulated_content}
            else:
                # 其他错误，继续抛出
                raise
    
    def _stream_final_response(self, messages: List[Dict], tools: List[Dict]):
        """
        流式输出最终响应
        
        Args:
            messages: 消息列表
            tools: 工具定义列表
        """
        # 尝试传递 tools，如果失败则降级为无工具模式
        try:
            for chunk in self.llm_client.generate_response(messages, stream=True, tools=tools):
                if self._should_stop:
                    break
                
                # 只处理文本内容和token统计
                if isinstance(chunk, dict):
                    chunk_type = chunk.get('type')
                    
                    if chunk_type == 'content':
                        text = chunk.get('text', '')
                        if text:
                            self.chunk_received.emit(text)
                    elif chunk_type == 'token_usage':
                        # ⚡ 转发 token 使用量
                        self.token_usage.emit(chunk.get('usage', {}))
                else:
                    # 字符串类型（向后兼容）
                    self.chunk_received.emit(str(chunk))
        except Exception as e:
            error_msg = str(e)
            print(f"[DEBUG] [FunctionCalling] 捕获到异常: {error_msg}")
            # 如果是模型不支持工具的错误，尝试不带 tools 参数重新调用
            if 'does not support tools' in error_msg or 'tools' in error_msg.lower():
                print(f"\n{'='*80}")
                print(f"[RETRY_DETECTED] !!! 检测到重试逻辑被触发！")
                print(f"[RETRY_DETECTED] 原始错误: {error_msg}")
                print(f"[RETRY_DETECTED] 即将进行第二次API调用（无tools参数）")
                print(f"[RETRY_DETECTED] 消息数量: {len(messages)}")
                print(f"{'='*80}\n")
                for chunk in self.llm_client.generate_response(messages, stream=True, tools=None):
                    if self._should_stop:
                        break
                    
                    # 只处理文本内容和token统计
                    if isinstance(chunk, dict):
                        chunk_type = chunk.get('type')
                        
                        if chunk_type == 'content':
                            text = chunk.get('text', '')
                            if text:
                                self.chunk_received.emit(text)
                        elif chunk_type == 'token_usage':
                            # ⚡ 转发 token 使用量
                            self.token_usage.emit(chunk.get('usage', {}))
                    else:
                        # 字符串类型（向后兼容）
                        self.chunk_received.emit(str(chunk))
            else:
                # 其他错误，继续抛出
                raise
    
    def _execute_tool(self, tool_name: str, tool_args_str: str) -> Dict:
        """
        执行工具
        
        Args:
            tool_name: 工具名称
            tool_args_str: 工具参数（JSON 字符串）
            
        Returns:
            Dict: {
                'success': bool,
                'result': Any | None,
                'error': str | None
            }
        """
        try:
            # 解析参数
            tool_args = json.loads(tool_args_str)
            
            # 调用工具注册表
            result = self.tools_registry.dispatch(tool_name, tool_args)
            
            # 检查结果格式
            if isinstance(result, dict) and 'success' in result:
                return result
            else:
                # 兼容旧格式
                return {
                    'success': True,
                    'result': result,
                    'error': None
                }
        
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'result': None,
                'error': f"参数解析失败: {str(e)}"
            }
        
        except Exception as e:
            return {
                'success': False,
                'result': None,
                'error': f"工具执行异常: {str(e)}"
            }

