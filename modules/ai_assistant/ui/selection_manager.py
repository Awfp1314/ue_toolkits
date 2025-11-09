# -*- coding: utf-8 -*-

"""
选中状态管理器

统一管理所有聊天气泡的文本选中状态
"""

from typing import List, Union
from PyQt6.QtWidgets import QTextBrowser, QLabel


class SelectionManager:
    """
    选中状态管理器
    
    职责：
    1. 追踪所有有选中文本的气泡
    2. 提供统一的清除选中状态接口
    3. 响应用户交互事件
    """
    
    def __init__(self, chat_window):
        """
        初始化选中状态管理器
        
        Args:
            chat_window: ChatWindow 实例
        """
        self.chat_window = chat_window
        self.selected_bubbles: List[Union[QTextBrowser, QLabel]] = []
    
    def register_bubble(self, bubble: Union[QTextBrowser, QLabel]):
        """
        注册一个聊天气泡
        
        Args:
            bubble: 聊天气泡组件（QTextBrowser 或 QLabel）
        """
        # 只有 QTextBrowser 有 selectionChanged 信号
        if isinstance(bubble, QTextBrowser) and hasattr(bubble, 'selectionChanged'):
            bubble.selectionChanged.connect(
                lambda: self._on_selection_changed(bubble)
            )
        # QLabel 不需要连接信号，因为它的选中状态由系统管理
    
    def clear_all_selections(self):
        """清除所有气泡的选中状态"""
        for bubble in self.selected_bubbles[:]:  # 使用副本遍历
            try:
                if isinstance(bubble, QTextBrowser):
                    # QTextBrowser：使用 textCursor 清除选中
                    cursor = bubble.textCursor()
                    cursor.clearSelection()
                    bubble.setTextCursor(cursor)
                elif isinstance(bubble, QLabel):
                    # QLabel：清除选中文本（如果有）
                    if bubble.hasSelectedText():
                        bubble.setSelection(0, 0)
            except Exception as e:
                print(f"[SelectionManager] 清除选中状态失败: {e}")
        
        self.selected_bubbles.clear()
        print(f"[SelectionManager] 已清除所有选中状态")
    
    def _on_selection_changed(self, bubble: QTextBrowser):
        """
        选中状态变化回调（仅用于 QTextBrowser）
        
        Args:
            bubble: 发生变化的气泡
        """
        try:
            if bubble.textCursor().hasSelection():
                # 有选中文本，添加到列表
                if bubble not in self.selected_bubbles:
                    self.selected_bubbles.append(bubble)
            else:
                # 无选中文本，从列表移除
                if bubble in self.selected_bubbles:
                    self.selected_bubbles.remove(bubble)
        except Exception as e:
            print(f"[SelectionManager] 处理选中状态变化失败: {e}")
