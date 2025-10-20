# -*- coding: utf-8 -*-

"""
单实例管理器
确保应用程序只运行一个实例
"""

import sys
from PyQt6.QtCore import QSharedMemory
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtWidgets import QMessageBox
from core.logger import get_logger

logger = get_logger(__name__)


class SingleInstanceManager:
    """单实例管理器"""
    
    def __init__(self, app_name="UEToolkit"):
        """
        初始化单实例管理器
        
        Args:
            app_name: 应用程序名称，用于生成唯一标识
        """
        self.app_name = app_name
        self.shared_memory_key = f"{app_name}_SingleInstance"
        self.server_name = f"{app_name}_LocalServer"
        
        self.shared_memory = None
        self.local_server = None
        self.main_window = None
    
    def is_running(self) -> bool:
        """
        检查应用程序是否已经在运行
        
        Returns:
            True: 已经有实例在运行
            False: 没有实例运行
        """
        # 尝试连接到现有的本地服务器
        socket = QLocalSocket()
        socket.connectToServer(self.server_name)
        
        if socket.waitForConnected(500):
            # 服务器存在，说明已经有实例在运行
            logger.info("检测到已有实例在运行")
            
            # 发送激活信号
            socket.write(b"activate")
            socket.waitForBytesWritten(1000)
            socket.disconnectFromServer()
            
            return True
        
        # 没有连接成功，说明是第一个实例
        return False
    
    def start_server(self, main_window):
        """
        启动本地服务器，监听来自其他实例的连接
        
        Args:
            main_window: 主窗口实例
        """
        self.main_window = main_window
        
        self.shared_memory = QSharedMemory(self.shared_memory_key)
        if not self.shared_memory.create(1):
            logger.warning(f"创建共享内存失败: {self.shared_memory.errorString()}")
        
        self.local_server = QLocalServer()
        
        # 移除之前可能存在的服务器
        QLocalServer.removeServer(self.server_name)
        
        # 监听新连接
        if self.local_server.listen(self.server_name):
            logger.info(f"本地服务器启动成功: {self.server_name}")
            self.local_server.newConnection.connect(self._on_new_connection)
        else:
            logger.error(f"本地服务器启动失败: {self.local_server.errorString()}")
    
    def _on_new_connection(self):
        """处理来自其他实例的连接"""
        socket = self.local_server.nextPendingConnection()
        
        if socket:
            socket.waitForReadyRead(1000)
            message = socket.readAll().data().decode('utf-8')
            
            logger.info(f"收到来自其他实例的消息: {message}")
            
            if message == "activate" and self.main_window:
                # 激活主窗口
                self._activate_window()
            
            socket.disconnectFromServer()
    
    def _activate_window(self):
        """激活主窗口"""
        if not self.main_window:
            return
        
        try:
            # 如果窗口最小化，先恢复
            if self.main_window.isMinimized():
                self.main_window.showNormal()
            
            self.main_window.show()
            
            # 激活窗口
            self.main_window.raise_()
            self.main_window.activateWindow()
            
            logger.info("主窗口已激活")
        
        except Exception as e:
            logger.error(f"激活窗口失败: {e}", exc_info=True)
    
    def cleanup(self):
        """清理资源"""
        if self.local_server:
            self.local_server.close()
            logger.info("本地服务器已关闭")
        
        if self.shared_memory and self.shared_memory.isAttached():
            self.shared_memory.detach()
            logger.info("共享内存已分离")

