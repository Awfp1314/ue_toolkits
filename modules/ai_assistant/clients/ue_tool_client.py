# -*- coding: utf-8 -*-

"""
UE工具客户端
用于与虚幻引擎编辑器的Python Socket服务器进行RPC通信
"""

import socket
import json
import struct
import threading
from typing import Dict, Any, Optional
from core.logger import get_logger

logger = get_logger(__name__)


class UEToolClient:
    """
    虚幻引擎工具RPC客户端
    
    功能：
    - 与UE编辑器的Python Socket服务器通信
    - 支持自动重连
    - 使用MCP-Style JSON格式
    - 解决TCP粘包问题（4字节长度前缀）
    - 线程安全
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 9998):
        """
        初始化UE工具客户端
        
        Args:
            host: UE Python服务器地址
            port: UE Python服务器端口
        """
        self.host = host
        self.port = port
        self._socket: Optional[socket.socket] = None
        self._lock = threading.Lock()  # 线程安全锁
        self._connected = False
        
        logger.info(f"UEToolClient 初始化完成 (目标: {host}:{port})")
    
    def _connect(self) -> bool:
        """
        建立与UE服务器的连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            # 如果已有连接，先关闭
            if self._socket:
                try:
                    self._socket.close()
                except Exception:
                    pass
                self._socket = None
            
            # 创建新的Socket连接
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(5.0)  # 连接超时5秒
            
            self._socket.connect((self.host, self.port))
            self._connected = True
            
            logger.info(f"[UE-RPC] 成功连接到 {self.host}:{self.port}")
            return True
            
        except socket.timeout:
            logger.warning(f"[UE-RPC] 连接超时: {self.host}:{self.port}")
            self._connected = False
            return False
        except ConnectionRefusedError:
            logger.warning(f"[UE-RPC] 连接被拒绝: {self.host}:{self.port} (UE服务器可能未启动)")
            self._connected = False
            return False
        except Exception as e:
            logger.error(f"[UE-RPC] 连接失败: {e}", exc_info=True)
            self._connected = False
            return False
    
    def _send_and_receive(self, data: dict, timeout: int = 10) -> Optional[dict]:
        """
        发送数据并接收响应（解决TCP粘包问题）
        
        协议格式：
        [4字节长度前缀 (Network Byte Order)] + [JSON数据]
        
        Args:
            data: 要发送的数据字典
            timeout: 接收超时时间（秒）
            
        Returns:
            dict: 接收到的响应字典，失败返回None
        """
        try:
            if not self._socket:
                logger.error("[UE-RPC] Socket未初始化")
                return None
            
            # 1. 序列化为JSON
            json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            data_length = len(json_data)
            
            # 2. 添加4字节长度前缀（Network Byte Order）
            length_prefix = struct.pack('!I', data_length)
            
            # 3. 发送数据
            self._socket.sendall(length_prefix + json_data)
            logger.debug(f"[UE-RPC] 已发送 {data_length} 字节数据")
            
            # 4. 设置接收超时
            self._socket.settimeout(timeout)
            
            # 5. 接收4字节长度前缀
            length_data = self._recv_exact(4)
            if not length_data:
                logger.error("[UE-RPC] 接收长度前缀失败")
                return None
            
            expected_length = struct.unpack('!I', length_data)[0]
            logger.debug(f"[UE-RPC] 预期接收 {expected_length} 字节")
            
            # 6. 接收完整的JSON数据
            json_data_received = self._recv_exact(expected_length)
            if not json_data_received:
                logger.error("[UE-RPC] 接收数据失败")
                return None
            
            # 7. 反序列化JSON
            response = json.loads(json_data_received.decode('utf-8'))
            logger.debug(f"[UE-RPC] 成功接收响应")
            
            return response
            
        except socket.timeout:
            logger.error(f"[UE-RPC] 接收超时 ({timeout}秒)")
            return None
        except Exception as e:
            logger.error(f"[UE-RPC] 发送/接收数据失败: {e}", exc_info=True)
            return None
    
    def _recv_exact(self, n: int) -> Optional[bytes]:
        """
        精确接收n字节数据（解决TCP粘包）
        
        Args:
            n: 要接收的字节数
            
        Returns:
            bytes: 接收到的数据，失败返回None
        """
        data = b''
        while len(data) < n:
            try:
                chunk = self._socket.recv(n - len(data))
                if not chunk:
                    # 连接已关闭
                    logger.warning("[UE-RPC] 连接已被远程关闭")
                    return None
                data += chunk
            except Exception as e:
                logger.error(f"[UE-RPC] 接收数据块失败: {e}")
                return None
        return data
    
    def execute_tool_rpc(self, tool_name: str, **kwargs) -> dict:
        """
        执行UE工具的RPC调用（供ToolRegistry使用）
        
        Args:
            tool_name: 工具名称 (如 "get_current_blueprint_summary")
            **kwargs: 工具参数
            
        Returns:
            dict: MCP-Style JSON响应
                成功: {"status": "success", "data": {...}}
                失败: {"status": "error", "message": "..."}
        """
        # 线程安全：同一时间只允许一个RPC调用
        with self._lock:
            try:
                # 1. 检查连接状态，如果未连接则尝试连接
                if not self._connected or not self._socket:
                    logger.info("[UE-RPC] 尝试连接到UE服务器...")
                    if not self._connect():
                        return {
                            "status": "error",
                            "message": f"无法连接到UE编辑器 ({self.host}:{self.port})。请确保UE编辑器已启动并运行Python Socket服务器。"
                        }
                
                # 2. 构建MCP-Style请求
                request = {
                    "action": tool_name,
                    "parameters": kwargs
                }
                
                logger.info(f"[UE-RPC] 执行工具: {tool_name}")
                logger.debug(f"[UE-RPC] 请求参数: {kwargs}")
                
                # 3. 发送请求并接收响应
                response = self._send_and_receive(request, timeout=30)
                
                if response is None:
                    # 通信失败，标记为未连接并返回错误
                    self._connected = False
                    return {
                        "status": "error",
                        "message": f"与UE编辑器通信失败。工具: {tool_name}"
                    }
                
                # 4. 返回响应
                logger.info(f"[UE-RPC] 工具执行完成: {tool_name}")
                return response
                
            except Exception as e:
                logger.error(f"[UE-RPC] RPC调用异常: {e}", exc_info=True)
                self._connected = False
                return {
                    "status": "error",
                    "message": f"RPC调用异常: {str(e)}"
                }
    
    def close(self):
        """关闭连接"""
        with self._lock:
            if self._socket:
                try:
                    self._socket.close()
                    logger.info("[UE-RPC] 连接已关闭")
                except Exception as e:
                    logger.warning(f"[UE-RPC] 关闭连接时出错: {e}")
                finally:
                    self._socket = None
                    self._connected = False
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected and self._socket is not None
    
    def test_connection(self) -> bool:
        """测试连接是否正常
        
        Returns:
            bool: 连接是否正常
        """
        try:
            # 尝试发送一个ping请求
            result = self.execute_tool_rpc("ping")
            return result.get("status") == "success"
        except Exception:
            return False

