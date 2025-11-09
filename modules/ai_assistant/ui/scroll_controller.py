# -*- coding: utf-8 -*-

"""
滚动控制器

管理聊天区域的滚动行为，实现防抖动和用户手动滚动检测
"""

import time
from PyQt6.QtWidgets import QScrollArea
from PyQt6.QtCore import QTimer


class ScrollController:
    """
    滚动控制器
    
    职责：
    1. 管理自动滚动到底部
    2. 检测用户手动滚动
    3. 实现防抖动机制
    4. 自动恢复滚动
    """
    
    def __init__(self, scroll_area: QScrollArea, debounce_ms: int = 100):
        """
        初始化滚动控制器
        
        Args:
            scroll_area: QScrollArea 实例
            debounce_ms: 防抖动延迟（毫秒）
        """
        self.scroll_area = scroll_area
        self.auto_scroll_enabled = True
        self.user_scrolling = False
        self.last_scroll_time = 0
        self.debounce_ms = debounce_ms
        
        # 防抖动定时器
        self.scroll_debounce_timer = QTimer()
        self.scroll_debounce_timer.timeout.connect(self._do_scroll)
        self.scroll_debounce_timer.setSingleShot(True)
        
        # 自动恢复定时器
        self.resume_timer = QTimer()
        self.resume_timer.timeout.connect(self._resume_auto_scroll)
        self.resume_timer.setSingleShot(True)
    
    def request_scroll_to_bottom(self):
        """
        请求滚动到底部（防抖动）
        
        如果用户正在手动滚动或自动滚动被禁用，则忽略请求
        """
        if not self.auto_scroll_enabled or self.user_scrolling:
            return
        
        # 防抖动：在指定时间内只执行一次
        self.scroll_debounce_timer.start(self.debounce_ms)
    
    def on_user_scroll(self, value):
        """
        用户手动滚动事件
        
        Args:
            value: 滚动条当前值
        """
        scrollbar = self.scroll_area.verticalScrollBar()
        max_value = scrollbar.maximum()
        
        # 如果用户向上滚动（距离底部超过 50px），禁用自动滚动
        if value < max_value - 50:
            if self.auto_scroll_enabled:
                print("[ScrollController] 用户向上滚动，禁用自动滚动")
            self.auto_scroll_enabled = False
            self.user_scrolling = True
        else:
            # 用户滚动到底部，恢复自动滚动
            if not self.auto_scroll_enabled:
                print("[ScrollController] 用户滚动到底部，恢复自动滚动")
            self.auto_scroll_enabled = True
            self.user_scrolling = False
    
    def on_slider_pressed(self):
        """滚动条被按下"""
        self.user_scrolling = True
        print("[ScrollController] 用户按下滚动条")
    
    def on_slider_released(self):
        """滚动条被释放"""
        self.user_scrolling = False
        print("[ScrollController] 用户释放滚动条")
        
        # 2 秒后恢复自动滚动
        self.resume_timer.start(2000)
    
    def _resume_auto_scroll(self):
        """恢复自动滚动（如果用户在底部附近）"""
        scrollbar = self.scroll_area.verticalScrollBar()
        max_value = scrollbar.maximum()
        current_value = scrollbar.value()
        
        # 如果用户在底部附近（距离底部小于 50px），恢复自动滚动
        if current_value >= max_value - 50:
            print("[ScrollController] 自动恢复滚动")
            self.auto_scroll_enabled = True
    
    def _do_scroll(self):
        """执行滚动（防抖动后）"""
        if self.auto_scroll_enabled and not self.user_scrolling:
            scrollbar = self.scroll_area.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            self.last_scroll_time = time.time()
    
    def force_scroll_to_bottom(self):
        """强制滚动到底部（忽略所有限制）"""
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        self.last_scroll_time = time.time()
    
    def enable_auto_scroll(self):
        """启用自动滚动"""
        self.auto_scroll_enabled = True
        print("[ScrollController] 自动滚动已启用")
    
    def disable_auto_scroll(self):
        """禁用自动滚动"""
        self.auto_scroll_enabled = False
        print("[ScrollController] 自动滚动已禁用")
