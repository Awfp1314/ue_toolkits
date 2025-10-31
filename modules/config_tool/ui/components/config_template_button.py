# -*- coding: utf-8 -*-

"""
配置模板按钮组件
"""

from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from core.logger import get_logger
from core.utils.style_loader import StyleLoader

logger = get_logger(__name__)


class SearchProjectsThread(QThread):
    """后台搜索UE工程的线程"""
    
    # 搜索完成信号，发送运行中的工程和所有工程列表
    search_completed = pyqtSignal(list, list)  # (running_projects, all_projects)
    search_error = pyqtSignal(str)
    progress_updated = pyqtSignal(int, int, str)  # (current, total, message)
    
    def __init__(self):
        super().__init__()
        self.running_projects = []
        self.all_projects = []
    
    def run(self):
        """在后台线程执行搜索"""
        try:
            from core.utils.ue_process_utils import UEProcessUtils
            ue_utils = UEProcessUtils()
            
            # 1. 检测运行中的工程
            logger.info("开始检测运行中的工程...")
            self.progress_updated.emit(0, 100, "正在检测运行中的工程...")
            self.running_projects = ue_utils.detect_running_ue_projects()
            logger.info(f"检测到 {len(self.running_projects)} 个运行中的工程")
            
            # 2. 搜索所有工程
            logger.info("开始搜索所有工程...")
            self.progress_updated.emit(50, 100, "正在搜索所有工程...")
            self.all_projects = ue_utils.search_all_ue_projects()
            logger.info(f"搜索到 {len(self.all_projects)} 个工程")
            
            # 3. 搜索完成
            self.progress_updated.emit(100, 100, "搜索完成！")
            self.search_completed.emit(self.running_projects, self.all_projects)
            
        except Exception as e:
            logger.error(f"搜索工程时出错: {e}")
            self.search_error.emit(str(e))


class ConfigTemplateButton(QPushButton):
    """配置模板按钮类"""
    
    def __init__(self, template, parent=None):
        super().__init__(template.name, parent)
        self.template = template
        self.main_ui = parent  # 保存主UI引用
        self.search_thread = None  # 搜索线程
        
        # 使用CSS类设置样式
        StyleLoader.set_property_class(self, "config-template-button")
        # 设置固定尺寸
        self.setFixedSize(180, 45)  # 固定宽度和高度
        # 禁用焦点，避免Alt键显示虚线框
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        # 启用右键菜单
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    
    def apply_config_to_ue_project(self):
        """应用配置到UE工程"""
        try:
            if not self.main_ui:
                logger.error("无法获取主UI引用")
                return
            
            # 检查逻辑层
            if self.main_ui is None or not hasattr(self.main_ui, 'logic') or not self.main_ui.logic:
                logger.error("无法获取逻辑层引用")
                return
            
            # 创建进度条对话框
            try:
                from modules.asset_manager.ui.progress_dialog import ProgressDialog
            except ImportError:
                logger.warning("无法导入ProgressDialog，创建简单进度窗口")
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self.main_ui, "搜索工程", "正在搜索UE工程，请稍候...")
                self._do_search_blocking()
                return
            
            progress_dialog = ProgressDialog("正在搜索工程", self.main_ui)
            progress_dialog.set_indeterminate(True)  # 设置为不确定进度模式
            
            # 创建并启动搜索线程
            self.search_thread = SearchProjectsThread()
            self.search_thread.progress_updated.connect(
                lambda c, t, m: progress_dialog.update_progress(c, t, m)
            )
            self.search_thread.search_completed.connect(
                lambda r, a: self._on_search_completed(r, a, progress_dialog)
            )
            self.search_thread.search_error.connect(
                lambda e: self._on_search_error(e, progress_dialog)
            )
            
            # 显示进度对话框（模态）
            progress_dialog.show()
            
            # 启动搜索线程
            self.search_thread.start()
            
        except Exception as e:
            logger.error(f"应用配置时发生错误: {e}")
            if self.main_ui:
                self.main_ui.show_error_message(f"应用配置时发生错误: {str(e)}")
    
    def _do_search_blocking(self):
        """如果ProgressDialog不可用，进行阻塞式搜索（备选方案）"""
        try:
            from core.utils.ue_process_utils import UEProcessUtils
            ue_utils = UEProcessUtils()
            
            running_projects = ue_utils.detect_running_ue_projects()
            all_projects = ue_utils.search_all_ue_projects()
            
            self._on_search_completed(running_projects, all_projects, None)
        except Exception as e:
            logger.error(f"搜索工程出错: {e}")
            self._on_search_error(str(e), None)
    
    def _on_search_completed(self, running_projects, all_projects, progress_dialog):
        """搜索完成回调"""
        try:
            logger.info(f"搜索完成: {len(running_projects)} 个运行中，{len(all_projects)} 个所有工程")
            
            # 关闭进度对话框（立即关闭，不延迟）
            if progress_dialog:
                progress_dialog.close()
            
            # 修正运行中工程的名称
            for project in running_projects:
                if project.project_path and project.project_path.exists():
                    project.name = project.project_path.stem
            
            # 合并两个列表，去除重复
            merged_projects = running_projects.copy()
            running_paths = {p.project_path.resolve() for p in running_projects}
            for project in all_projects:
                if project.project_path.resolve() not in running_paths:
                    merged_projects.append(project)
            
            # 如果没有工程，显示提示
            if not merged_projects:
                self.main_ui.show_no_ue_project_message()
                return
            
            # 弹出工程选择窗口
            selected_project = self.main_ui.select_ue_project(merged_projects)
            if not selected_project:
                return
            
            # 检查用户选择的工程是否正在运行
            if self._is_project_running(selected_project):
                self.show_project_running_message()
                return
            
            # 显示确认对话框
            if not self.show_confirm_dialog(selected_project):
                return
            
            # 复制配置文件
            success = self.main_ui.logic.copy_config_files_from_template(self.template, selected_project.project_path)
            if success:
                self.main_ui.show_success_message("配置应用成功！")
            else:
                self.main_ui.show_error_message("配置应用失败！")
        except Exception as e:
            logger.error(f"搜索完成处理出错: {e}")
            if self.main_ui:
                self.main_ui.show_error_message(f"处理搜索结果时出错: {str(e)}")
    
    def _on_search_error(self, error_msg, progress_dialog):
        """搜索出错回调"""
        logger.error(f"工程搜索出错: {error_msg}")
        if progress_dialog:
            progress_dialog.finish_error(error_msg)
        else:
            if self.main_ui:
                self.main_ui.show_error_message(f"搜索工程时出错: {error_msg}")
    
    def _is_project_running(self, project):
        """检查工程是否正在运行"""
        try:
            # 如果PID > 0，说明是运行中的工程
            return project.pid > 0
        except Exception as e:
            logger.error(f"检查工程运行状态时发生错误: {e}")
            return False
    
    def show_project_running_message(self):
        """显示工程正在运行的警告信息"""
        try:
            from ..dialogs import ProjectRunningWarningDialog
            dialog = ProjectRunningWarningDialog(self.main_ui)
            dialog.exec()
        except Exception as e:
            logger.error(f"显示工程运行警告时发生错误: {e}")
            # 回退到标准消息框
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self.main_ui, "警告", "当前工程正在运行无法导入配置文件，请关闭保存工程后重试")
    
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

