# -*- coding: utf-8 -*-

"""
进度条对话框
用于显示资产复制的进度
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, pyqtSlot
from PyQt6.QtGui import QFont

from core.logger import get_logger
from core.utils.theme_manager import ThemeManager

logger = get_logger(__name__)


class ProgressDialog(QDialog):
    """进度条对话框（无标题栏，现代化设计）"""
    
    # 取消信号
    cancelled = pyqtSignal()
    
    # 进度更新信号（内部使用，用于线程安全的UI更新）
    _progress_signal = pyqtSignal(int, int, str)
    
    def __init__(self, title: str = "处理中", parent=None):
        """
        Args:
            title: 对话框标题
            parent: 父窗口
        """
        super().__init__(parent)
        self.title = title
        self._is_cancelled = False
        self._is_finished = False  # 添加完成标志，防止重复关闭
        self.theme_manager = ThemeManager()
        self.init_ui()
        
        # 连接内部信号到槽函数
        self._progress_signal.connect(self._on_progress_update)
    
    def _build_main_container_style(self) -> str:
        """构建主容器样式"""
        tm = self.theme_manager
        return f"""
            QWidget#mainContainer {{
                background-color: {tm.get_variable('bg_secondary')};
                border: 1px solid {tm.get_variable('border')};
                border-radius: 8px;
            }}
        """
    
    def _build_title_style(self) -> str:
        """构建标题样式"""
        tm = self.theme_manager
        return f"""
            QLabel {{
                color: {tm.get_variable('text_primary')};
                font-size: 16px;
                font-weight: bold;
            }}
        """
    
    def _build_progress_bar_style(self) -> str:
        """构建进度条样式"""
        tm = self.theme_manager
        accent = tm.get_variable('accent')
        accent_hover = tm.get_variable('accent_hover')
        return f"""
            QProgressBar {{
                border: 1px solid {tm.get_variable('border')};
                border-radius: 4px;
                background-color: {tm.get_variable('bg_tertiary')};
                text-align: center;
                color: {tm.get_variable('text_primary')};
                font-size: 12px;
                height: 25px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {accent},
                    stop:1 {accent_hover}
                );
                border-radius: 3px;
            }}
        """
    
    def _build_status_label_style(self) -> str:
        """构建状态标签样式"""
        tm = self.theme_manager
        return f"""
            QLabel {{
                color: {tm.get_variable('text_secondary')};
                font-size: 12px;
                padding: 5px;
            }}
        """
    
    def init_ui(self):
        """初始化UI"""
        self.setModal(True)
        self.setFixedSize(500, 180)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        main_container = QWidget()
        main_container.setObjectName("mainContainer")
        main_container.setStyleSheet(self._build_main_container_style())
        
        container_layout = QVBoxLayout(main_container)
        container_layout.setContentsMargins(25, 25, 25, 25)
        container_layout.setSpacing(15)
        
        title_label = QLabel(self.title)
        title_label.setStyleSheet(self._build_title_style())
        container_layout.addWidget(title_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setStyleSheet(self._build_progress_bar_style())
        container_layout.addWidget(self.progress_bar)
        
        # 状态信息标签
        self.status_label = QLabel("准备中...")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(self._build_status_label_style())
        container_layout.addWidget(self.status_label)
        
        # 设置主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(main_container)
    
    def set_progress(self, value: int):
        """设置进度值（0-100）
        
        Args:
            value: 进度值
        """
        self.progress_bar.setValue(value)
    
    def set_status(self, text: str):
        """设置状态文本
        
        Args:
            text: 状态文本
        """
        self.status_label.setText(text)
        logger.debug(f"进度状态: {text}")
    
    def set_indeterminate(self, indeterminate: bool = True):
        """设置为不确定进度模式
        
        Args:
            indeterminate: 是否为不确定模式
        """
        if indeterminate:
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(0)
        else:
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(100)
    
    def finish_success(self, delay_ms: int = 500):
        """完成并自动关闭
        
        Args:
            delay_ms: 延迟关闭的毫秒数
        """
        if self._is_finished:
            logger.debug("[进度对话框] 已经处于完成状态，忽略重复调用")
            return
        
        self._is_finished = True
        self.progress_bar.setValue(100)
        self.status_label.setText("完成！")
        
        # 使用主题变量设置成功状态样式
        tm = self.theme_manager
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {tm.get_variable('success')};
                font-size: 12px;
                font-weight: bold;
                padding: 5px;
            }}
        """)
        logger.info(f"[进度对话框] 设置完成状态，{delay_ms}ms后关闭")
        # 延迟关闭（使用hide+deleteLater确保对话框真正消失）
        QTimer.singleShot(delay_ms, self._do_close)
    
    def _do_close(self):
        """真正关闭对话框"""
        logger.info("[进度对话框] 开始关闭对话框")
        # 对于模态对话框（exec()），必须调用accept()或reject()来正确关闭
        self.accept()
        logger.info("[进度对话框] 对话框已关闭")
    
    def finish_error(self, error_msg: str):
        """显示错误并保持打开
        
        Args:
            error_msg: 错误信息
        """
        self.status_label.setText(f"错误：{error_msg}")
        
        # 使用主题变量设置错误状态样式
        tm = self.theme_manager
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {tm.get_variable('error')};
                font-size: 12px;
                font-weight: bold;
                padding: 5px;
            }}
        """)
    
    def is_cancelled(self) -> bool:
        """检查是否已取消
        
        Returns:
            是否已取消
        """
        return self._is_cancelled
    
    @pyqtSlot(int, int, str)
    def _on_progress_update(self, current: int, total: int, message: str):
        """处理进度更新（槽函数，在主线程运行）
        
        Args:
            current: 当前进度
            total: 总数
            message: 状态消息
        """
        logger.debug(f"[进度对话框] 收到进度更新: {current}/{total} - {message}")
        
        if total > 0:
            progress = int((current / total) * 100)
            self.set_progress(progress)
        elif "完成" in message or "已移动" in message:
            # 如果total为0（空文件夹）但操作已完成，也设置为100%
            self.set_progress(100)
        
        self.set_status(message)
        
        # 当操作完成后，自动关闭对话框
        # 检测完成条件：进度达到100%或包含完成相关关键词
        if (current == total and total > 0) or ("完成！" in message or "启动虚幻引擎" in message):
            logger.info(f"[进度对话框] 检测到完成条件（{current}/{total}），准备关闭对话框")
            self.finish_success(800)
    
    def update_progress(self, current: int, total: int, message: str):
        """更新进度（可从任何线程调用）
        
        Args:
            current: 当前进度
            total: 总数
            message: 状态消息
        """
        # 发射信号，确保UI更新在主线程执行
        self._progress_signal.emit(current, total, message)
    
    def closeEvent(self, event):
        """关闭事件"""
        if not self._is_cancelled and self.progress_bar.value() < 100:
            self._is_cancelled = True
            self.cancelled.emit()
        super().closeEvent(event)

