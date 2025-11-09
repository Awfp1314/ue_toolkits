# -*- coding: utf-8 -*-

"""
启动加载界面 - 显示程序启动进度

⚡ 优化方案B：使用 QTimer 异步更新进度，避免事件循环冲突
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QPixmap
from core.logger import get_logger
from typing import Tuple
from queue import Queue
from pathlib import Path

logger = get_logger(__name__)


class SplashScreen(QWidget):
    """启动加载界面

    ⚡ 优化：使用消息队列和定时器异步更新进度，避免事件循环冲突
    """

    def __init__(self, parent=None):
        """初始化启动界面"""
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool  # 添加 Tool 标志，避免任务栏显示
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)  # 关闭时自动删除

        # 设置固定大小
        self.setFixedSize(500, 300)

        # ⚡ 优化：使用消息队列存储待更新的进度信息
        self._progress_queue = Queue()

        # ⚡ 优化：使用定时器定期检查队列并更新UI
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._process_progress_queue)
        self._update_timer.start(50)  # 每50ms检查一次队列

        # ⚡ 新增：平滑进度条动画
        self._current_progress = 0  # 当前显示的进度
        self._target_progress = 0   # 目标进度
        self._smooth_timer = QTimer(self)
        self._smooth_timer.timeout.connect(self._smooth_progress_update)
        self._smooth_timer.start(16)  # 约60fps

        # 初始化UI
        self._init_ui()

        # 居中显示
        self._center_on_screen()

        logger.info("启动加载界面已创建")
    
    def _init_ui(self):
        """初始化UI"""
        # 主容器
        container = QWidget(self)
        container.setObjectName("SplashContainer")
        container.setStyleSheet("""
            #SplashContainer {
                background-color: #1e1e1e;
                border: 2px solid #3d3d3d;
                border-radius: 12px;
            }
            #SplashTitle {
                color: #ffffff;
                font-size: 24px;
                font-weight: bold;
                background-color: transparent;
            }
            #SplashIcon {
                background-color: transparent;
            }
            #SplashMessage {
                color: #b0b0b0;
                font-size: 14px;
                background-color: transparent;
            }
            QProgressBar {
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                background-color: #2d2d2d;
                height: 8px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4a9eff;
                border-radius: 3px;
            }
        """)
        
        # 布局
        layout = QVBoxLayout(container)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 图标
        self.icon_label = QLabel()
        self.icon_label.setObjectName("SplashIcon")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 加载图标文件
        icon_path = Path(__file__).parent.parent / "resources" / "tubiao.ico"
        if icon_path.exists():
            pixmap = QPixmap(str(icon_path))
            # 缩放图标到合适大小（保持宽高比）
            scaled_pixmap = pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.icon_label.setPixmap(scaled_pixmap)
        else:
            # 如果图标文件不存在，使用emoji作为后备
            self.icon_label.setText("🎮")
            self.icon_label.setStyleSheet("font-size: 48px;")
            logger.warning(f"图标文件不存在: {icon_path}")

        layout.addWidget(self.icon_label)
        
        # 标题
        self.title_label = QLabel("虚幻引擎工具箱")
        self.title_label.setObjectName("SplashTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        
        # 加载消息
        self.message_label = QLabel("正在初始化...")
        self.message_label.setObjectName("SplashMessage")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.message_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 设置容器布局
        container_layout = QVBoxLayout(self)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(container)
    
    def _center_on_screen(self):
        """将窗口居中显示"""
        screen = self.screen()
        if screen:
            screen_geometry = screen.availableGeometry()
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            self.move(x, y)
    
    def _process_progress_queue(self):
        """处理进度队列（在定时器中调用）

        ⚡ 优化：从队列中取出进度信息并更新UI，避免阻塞主线程
        """
        try:
            # 一次性处理队列中的所有消息（取最新的）
            latest_progress = None
            while not self._progress_queue.empty():
                latest_progress = self._progress_queue.get_nowait()

            # 如果有新的进度信息，更新目标进度（不直接更新UI，由平滑动画处理）
            if latest_progress is not None:
                percent, message = latest_progress
                self._target_progress = percent
                self.message_label.setText(message)
                logger.debug(f"启动进度: {percent}% - {message}")
        except Exception as e:
            logger.error(f"处理进度队列时出错: {e}")

    def _smooth_progress_update(self):
        """平滑更新进度条（由定时器调用，约60fps）

        ⚡ 优化：使用缓动动画让进度条平滑过渡
        """
        try:
            if self._current_progress < self._target_progress:
                # 计算增量（使用缓动函数：越接近目标越慢）
                diff = self._target_progress - self._current_progress
                step = max(0.5, diff * 0.1)  # 至少移动0.5%，最多移动10%的差距

                self._current_progress = min(self._current_progress + step, self._target_progress)
                self.progress_bar.setValue(int(self._current_progress))
            elif self._current_progress > self._target_progress:
                # 如果目标进度倒退（不应该发生，但做个保护）
                self._current_progress = self._target_progress
                self.progress_bar.setValue(int(self._current_progress))
        except Exception as e:
            logger.error(f"平滑更新进度条时出错: {e}")

    def update_progress(self, percent: int, message: str):
        """更新加载进度（线程安全）

        ⚡ 优化：将进度信息放入队列，由定时器异步更新UI

        Args:
            percent: 进度百分比 (0-100)
            message: 加载消息
        """
        try:
            # 将进度信息放入队列
            self._progress_queue.put((percent, message))
        except Exception as e:
            logger.error(f"更新进度时出错: {e}")
    
    def finish(self):
        """完成加载，关闭启动界面

        ⚡ 优化：停止定时器，清理资源
        """
        try:
            logger.info("启动加载完成，关闭启动界面")
            # 停止所有定时器
            if hasattr(self, '_update_timer') and self._update_timer.isActive():
                self._update_timer.stop()
            if hasattr(self, '_smooth_timer') and self._smooth_timer.isActive():
                self._smooth_timer.stop()
            # 关闭窗口
            if self.isVisible():
                self.close()
        except RuntimeError:
            # 窗口已被删除，忽略错误
            pass

