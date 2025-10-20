# -*- coding: utf-8 -*-

"""自定义复选框组件"""

from PyQt6.QtWidgets import QCheckBox, QStyle, QStyleOptionButton
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QPen, QColor

from core.utils.theme_manager import get_theme_manager


class CustomCheckBox(QCheckBox):
    """自定义复选框"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.theme_manager = get_theme_manager()
        self.setStyleSheet("""
            QCheckBox {
                spacing: 8px;
            }
        """)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        
        indicator_rect = self.style().subElementRect(
            QStyle.SubElement.SE_CheckBoxIndicator, opt, self
        )
        
        tm = self.theme_manager
        bg_color = QColor(tm.get_variable('bg_tertiary'))
        border_color = QColor(tm.get_variable('border'))
        accent_color = QColor(tm.get_variable('accent'))
        text_color = QColor(tm.get_variable('text_primary'))
        
        painter.fillRect(indicator_rect, bg_color)
        
        if self.isChecked():
            painter.setPen(QPen(border_color, 2))
            painter.drawRoundedRect(indicator_rect.adjusted(1, 1, -1, -1), 3, 3)
            
            painter.setPen(QPen(accent_color, 2.5, Qt.PenStyle.SolidLine, 
                               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            
            x = indicator_rect.x()
            y = indicator_rect.y()
            w = indicator_rect.width()
            h = indicator_rect.height()
            
            x1 = x + w * 0.20
            y1 = y + h * 0.50
            x2 = x + w * 0.42
            y2 = y + h * 0.72
            x3 = x + w * 0.80
            y3 = y + h * 0.28
            
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            painter.drawLine(int(x2), int(y2), int(x3), int(y3))
        else:
            painter.setPen(QPen(border_color, 2))
            painter.drawRoundedRect(indicator_rect.adjusted(1, 1, -1, -1), 3, 3)
        
        text_rect = self.style().subElementRect(
            QStyle.SubElement.SE_CheckBoxContents, opt, self
        )
        painter.setPen(text_color)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.text())
        
        painter.end()
