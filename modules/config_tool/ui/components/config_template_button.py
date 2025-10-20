# -*- coding: utf-8 -*-

"""
配置模板按钮组件
"""

from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, QTimer, QDateTime
from core.logger import get_logger
from core.utils.style_loader import StyleLoader

logger = get_logger(__name__)


class ConfigTemplateButton(QPushButton):
    """配置模板按钮类，支持双击事件"""
    
    def __init__(self, template, parent=None):
        super().__init__(template.name, parent)
        self.template = template
        self.main_ui = parent  # 保存主UI引用
        self.is_double_click = False
        self.last_click_time = 0
        self.click_timer = QTimer()
        self.click_timer.setSingleShot(True)
        self.click_timer.timeout.connect(self.handle_single_click)
        
        # 使用CSS类设置样式
        StyleLoader.set_property_class(self, "config-template-button")
        # 设置固定尺寸
        self.setFixedSize(180, 45)  # 固定宽度和高度
        # 禁用焦点，避免Alt键显示虚线框
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        # 启用右键菜单
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    
    def mousePressEvent(self, e):
        """重写鼠标按下事件，处理双击检测"""
        if e and e.button() == Qt.MouseButton.LeftButton:
            current_time = QDateTime.currentMSecsSinceEpoch()
            
            # 检查是否在双击时间范围内（500毫秒）
            if current_time - self.last_click_time < 500:
                # 双击事件
                self.is_double_click = True
                self.click_timer.stop()
                self.handle_double_click()
                if e:
                    e.accept()
                return
            else:
                # 单击事件
                self.is_double_click = False
                self.last_click_time = current_time
                self.click_timer.start(500)  # 500毫秒后触发单击
        
        super().mousePressEvent(e)
    
    def handle_single_click(self):
        """处理单击事件"""
        if not self.is_double_click:
            # 触发单击事件
            if self.main_ui:
                self.main_ui.on_config_button_clicked(self.template)
    
    def handle_double_click(self):
        """处理双击事件"""
        logger.info(f"配置按钮被双击: {self.template.name}")
        # 触发配置应用功能
        self.apply_config_to_ue_project()
    
    def apply_config_to_ue_project(self):
        """应用配置到UE工程"""
        try:
            if not self.main_ui:
                logger.error("无法获取主UI引用")
                return
            
            # 1. 检测运行的UE工程
            if not hasattr(self.main_ui, 'logic') or not self.main_ui.logic:
                logger.error("无法获取逻辑层引用")
                return
                
            ue_projects = self.main_ui.logic.detect_running_ue_projects()
            if not ue_projects:
                self.main_ui.show_no_ue_project_message()
                return
            
            # 2. 如果多个UE实例，让用户选择
            selected_project = self.main_ui.select_ue_project(ue_projects)
            if not selected_project:
                return
            
            # 3. 显示确认对话框
            if not self.show_confirm_dialog(selected_project):
                return
            
            # 4. 复制配置文件 - 使用逻辑层方法
            success = self.main_ui.logic.copy_config_files_from_template(self.template, selected_project.project_path)
            if success:
                self.main_ui.show_success_message("配置应用成功！")
            else:
                self.main_ui.show_error_message("配置应用失败！")
        except Exception as e:
            logger.error(f"应用配置时发生错误: {e}")
            if self.main_ui:
                self.main_ui.show_error_message(f"应用配置时发生错误: {str(e)}")
    
    def show_confirm_dialog(self, selected_project):
        """显示确认对话框"""
        try:
            if not self.main_ui:
                return False
            
            # 获取源配置文件列表，只获取.ini文件
            source_files = []
            if self.template.path and self.template.path.exists():
                source_files = list(self.template.path.glob("*.ini"))
            
            from ..dialogs import ConfigApplyConfirmDialog
            dialog = ConfigApplyConfirmDialog(
                self.template.name,
                selected_project.project_path,
                source_files,
                self.main_ui
            )
            
            from PyQt6.QtWidgets import QDialog
            return dialog.exec() == QDialog.DialogCode.Accepted
        except Exception as e:
            logger.error(f"显示确认对话框时发生错误: {e}")
            return False
    
    # 已移动到逻辑层，这里不再需要
    def copy_config_files(self, target_project):
        """复制配置文件到目标工程 - 已移动到逻辑层，此方法仅保留兼容性"""
        if not hasattr(self.main_ui, 'logic') or not self.main_ui.logic:
            logger.error("无法获取逻辑层引用")
            return False
            
        # 调用逻辑层方法
        return self.main_ui.logic.copy_config_files_from_template(self.template, target_project.project_path)

