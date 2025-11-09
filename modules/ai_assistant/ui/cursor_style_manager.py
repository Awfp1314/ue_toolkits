# -*- coding: utf-8 -*-

"""
光标样式管理器

统一管理所有 UI 元素的光标样式
"""

from PyQt6.QtCore import Qt


class CursorStyleManager:
    """
    光标样式管理器
    
    职责：
    1. 统一设置所有组件的光标样式
    2. 确保光标样式符合用户预期
    """
    
    @staticmethod
    def apply_styles(chat_window):
        """
        应用光标样式到所有组件
        
        Args:
            chat_window: ChatWindow 实例
        """
        try:
            # 发送按钮：手型光标
            if hasattr(chat_window, 'input_area') and hasattr(chat_window.input_area, 'btn_send'):
                chat_window.input_area.btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
                print("[CursorStyleManager] 发送按钮：手型光标")
            
            # 加号按钮：手型光标
            if hasattr(chat_window, 'input_area') and hasattr(chat_window.input_area, 'btn_plus'):
                chat_window.input_area.btn_plus.setCursor(Qt.CursorShape.PointingHandCursor)
                print("[CursorStyleManager] 加号按钮：手型光标")
            
            # 输入框：文本选择光标
            if hasattr(chat_window, 'input_field'):
                chat_window.input_field.setCursor(Qt.CursorShape.IBeamCursor)
                print("[CursorStyleManager] 输入框：文本选择光标")
            
            # 聊天气泡文本：文本选择光标
            # 注意：这需要在创建气泡时单独设置
            
            # 滚动区域：默认箭头光标
            if hasattr(chat_window, 'scroll_area'):
                chat_window.scroll_area.setCursor(Qt.CursorShape.ArrowCursor)
                print("[CursorStyleManager] 滚动区域：默认箭头光标")
            
            print("[CursorStyleManager] 光标样式应用完成")
            
        except Exception as e:
            print(f"[CursorStyleManager] 应用光标样式失败: {e}")
    
    @staticmethod
    def set_bubble_cursor(bubble):
        """
        为聊天气泡设置光标样式
        
        Args:
            bubble: 聊天气泡组件
        """
        try:
            bubble.setCursor(Qt.CursorShape.IBeamCursor)
        except Exception as e:
            print(f"[CursorStyleManager] 设置气泡光标失败: {e}")
