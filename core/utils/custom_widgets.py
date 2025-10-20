# -*- coding: utf-8 -*-

"""自定义UI组件"""

from PyQt6.QtWidgets import QLineEdit, QTextEdit, QPlainTextEdit
from PyQt6.QtCore import Qt


class NoContextMenuLineEdit(QLineEdit):
    """无右键菜单的单行编辑框"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)


class NoContextMenuTextEdit(QTextEdit):
    """无右键菜单的多行文本编辑框"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)


class NoContextMenuPlainTextEdit(QPlainTextEdit):
    """无右键菜单的纯文本编辑框"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
