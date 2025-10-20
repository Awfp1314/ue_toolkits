# -*- coding: utf-8 -*-

"""
配置处理器 - 处理配置的添加、删除等操作
"""

import sys
import os
import subprocess
import threading
from pathlib import Path
from typing import List
from PyQt6.QtWidgets import QFileDialog, QDialog, QMessageBox, QMenu, QApplication
from PyQt6.QtCore import Qt, QProcess, QTimer, QEvent, QObject, QRunnable, QThreadPool
from PyQt6.QtGui import QAction, QCursor

from core.logger import get_logger
from core.utils.theme_manager import get_theme_manager
from core.utils.ue_process_utils import UEProcessUtils

logger = get_logger(__name__)


def _open_folder_async(folder_path: Path):
    """在独立线程中异步打开文件夹（最小化阻塞）
    
    使用轻量级线程 + 系统原生调用，确保最快响应速度。
    """
    try:
        folder_str = str(folder_path)
        
        if sys.platform == "win32":
            # Windows: 使用 os.startfile（最快，原生API）
            os.startfile(folder_str)
        elif sys.platform == "darwin":
            # macOS: 使用 open 命令
            subprocess.Popen(['open', folder_str], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
        else:
            # Linux: 使用 xdg-open
            subprocess.Popen(['xdg-open', folder_str],
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
        
        logger.info(f"成功打开文件夹: {folder_str}")
        
    except Exception as e:
        logger.error(f"打开文件夹时出错: {e}", exc_info=True)


class MenuEventFilter(QObject):
    """菜单事件过滤器 - 监听全局事件实现自动关闭"""
    
    def __init__(self, menu: QMenu):
        super().__init__()
        self.menu = menu
        self.mouse_was_inside = True  # 标记鼠标是否曾在菜单内
        
        # 安装到应用程序级别，捕获所有事件
        QApplication.instance().installEventFilter(self)
        
        # 启动定时器，持续检测鼠标位置
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self._check_mouse_position)
        self.check_timer.start(50)  # 每50ms检查一次鼠标位置
        
    def eventFilter(self, obj, event):
        """全局事件过滤器 - 监控鼠标按下和窗口失活"""
        if not self.menu or not self.menu.isVisible():
            return False
        
        # 监控鼠标按下事件
        if event.type() == QEvent.Type.MouseButtonPress:
            click_pos = QCursor.pos()
            menu_rect = self.menu.rect()
            menu_global_pos = self.menu.mapToGlobal(menu_rect.topLeft())
            menu_global_rect = menu_rect.translated(menu_global_pos)
            
            # 如果点击在菜单外，关闭菜单
            if not menu_global_rect.contains(click_pos):
                self._close_menu()
                return False
        
        # 监控窗口失去激活状态
        elif event.type() == QEvent.Type.WindowDeactivate:
            if obj == self.menu:
                self._close_menu()
        
        return False
    
    def _check_mouse_position(self):
        """定时检查鼠标位置，如果离开菜单则关闭"""
        if not self.menu or not self.menu.isVisible():
            self.check_timer.stop()
            return
        
        cursor_pos = QCursor.pos()
        menu_rect = self.menu.rect()
        menu_global_pos = self.menu.mapToGlobal(menu_rect.topLeft())
        menu_global_rect = menu_rect.translated(menu_global_pos)
        
        mouse_inside = menu_global_rect.contains(cursor_pos)
        
        # 如果鼠标曾经在菜单内，现在离开了，则关闭菜单
        if self.mouse_was_inside and not mouse_inside:
            self._close_menu()
        
        if mouse_inside:
            self.mouse_was_inside = True
    
    def _close_menu(self):
        """关闭菜单"""
        if self.menu and self.menu.isVisible():
            # 停止定时器
            if hasattr(self, 'check_timer'):
                self.check_timer.stop()
            
            # 先从应用程序移除事件过滤器
            QApplication.instance().removeEventFilter(self)
            
            self.menu.hide()
            self.menu.deleteLater()
            self.menu = None


class ConfigHandler:
    """配置事件处理器"""
    
    def __init__(self, ui):
        """初始化配置处理器
        
        Args:
            ui: ConfigToolUI实例
        """
        self.ui = ui
    
    def on_add_config_clicked(self):
        """添加配置按钮点击事件"""
        logger.info("添加配置按钮被点击")
        
        try:
            # 1. 搜索所有UE工程
            logger.info("搜索所有UE工程")
            ue_utils = UEProcessUtils()
            ue_projects = ue_utils.search_all_ue_projects()
            
            # 2. 如果没有工程，则显示提示消息
            if not ue_projects:
                self.show_no_ue_project_message()
                return
            
            # 3. 直接弹出所有搜索到工程的弹窗供用户选择
            selected_project = self.select_ue_project(ue_projects)
            if not selected_project:
                return
            
            # 4. 打开文件选择对话框
            config_dir = selected_project.project_path.parent / "Saved/Config/Windows"
            files = self.select_config_files(config_dir)
            if not files:
                return
            
            # 5. 弹出名称设置弹窗
            config_name = self.show_name_dialog()
            if not config_name:
                return
            
            # 6. 复制文件到目标目录
            if self.ui.logic:
                success = self.ui.logic.add_config_template(config_name, files)
                if success:
                    self.ui.refresh_config_list()  # 刷新配置列表
                else:
                    self.show_error_message("添加配置失败")
            else:
                self.show_error_message("逻辑层未初始化")
        except Exception as e:
            logger.error(f"添加配置时发生错误: {e}")
            self.show_error_message(f"添加配置时发生错误: {str(e)}")
    
    def detect_running_ue_projects(self):
        """检测运行的UE工程"""
        if not hasattr(self.ui, 'logic') or not self.ui.logic:
            logger.error("无法获取逻辑层引用")
            try:
                # 如果没有逻辑层引用，使用旧方法
                ue_utils = UEProcessUtils()
                projects = ue_utils.detect_running_ue_projects()
                
                # 如果没有检测到运行的工程，则搜索所有UE工程
                if not projects:
                    logger.info("未检测到运行的UE工程，开始搜索所有UE工程")
                    projects = ue_utils.search_all_ue_projects()
                
                return projects
            except Exception as e:
                logger.error(f"检测UE工程时发生错误: {e}")
                return []
        
        # 调用逻辑层方法
        return self.ui.logic.detect_running_ue_projects()
    
    def select_ue_project(self, ue_projects):
        """选择UE工程"""
        if not ue_projects:
            return None
        elif len(ue_projects) == 1:
            return ue_projects[0]
        else:
            from ..dialogs import UEProjectSelectorDialog
            dialog = UEProjectSelectorDialog(ue_projects, self.ui)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                return dialog.get_selected_project()
            return None
    
    def select_config_files(self, config_dir: Path) -> List[Path]:
        """选择配置文件，只选择.ini文件"""
        # 确保目录存在
        if not config_dir.exists():
            config_dir = Path.home()  # 如果目录不存在，使用用户主目录
        
        # 打开文件选择对话框
        file_dialog = QFileDialog(self.ui)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setDirectory(str(config_dir))
        file_dialog.setNameFilter("配置文件 (*.ini)")
        
        # 确保对话框是模态的
        file_dialog.setModal(True)
        
        # 显式设置窗口标志，确保正确的行为
        file_dialog.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        
        result = file_dialog.exec()
        if result == QFileDialog.DialogCode.Accepted:
            selected_files = file_dialog.selectedFiles()
            # 过滤只选择.ini文件
            ini_files = [Path(f) for f in selected_files if Path(f).suffix.lower() == '.ini']
            # 记录跳过的非.ini文件
            non_ini_files = [f for f in selected_files if Path(f).suffix.lower() != '.ini']
            if non_ini_files:
                logger.info(f"跳过 {len(non_ini_files)} 个非.ini文件: {non_ini_files}")
            return ini_files
        return []
    
    def show_name_dialog(self):
        """显示名称设置弹窗"""
        from ..dialogs import NameInputDialog
        dialog = NameInputDialog(self.ui)
        
        existing_names = [template.name for template in self.ui.config_templates]
        dialog.set_existing_names(existing_names)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_config_name()
        return ""
    
    def show_no_ue_project_message(self):
        """显示没有找到UE工程的消息"""
        QMessageBox.information(self.ui, "提示", "未检测到正在运行的UE工程，请先启动UE编辑器。")
    
    def show_error_message(self, message: str):
        """显示错误消息"""
        QMessageBox.critical(self.ui, "错误", message)
    
    def show_config_context_menu(self, pos, button, template):
        """显示配置按钮的右键菜单
        
        修复说明（全局事件监听 + 定时检测版本）：
        1. 使用popup()非阻塞方法，不阻塞事件循环
        2. 安装全局MenuEventFilter事件过滤器，监控：
           - 全局鼠标按下事件（MouseButtonPress）→ 点击菜单外立即关闭
           - 定时检测鼠标位置（每50ms）→ 鼠标离开菜单立即关闭
           - 窗口失去激活（WindowDeactivate）→ 立即关闭
        3. 设置Popup窗口类型，配合全局过滤器
        4. 菜单会在以下情况自动关闭：
           - 鼠标点击菜单外部（立即响应）
           - 鼠标移开菜单（立即响应，50ms检测间隔）
           - 菜单失去焦点
           - 按Esc键
        """
        # 创建菜单，父对象设置为button以确保正确的坐标映射和生命周期管理
        context_menu = QMenu(button)
        
        # 设置菜单属性，确保自动隐藏行为
        context_menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)  # 关闭时自动删除
        context_menu.setWindowFlags(
            Qt.WindowType.Popup |  # 弹出窗口类型，失去焦点自动关闭
            Qt.WindowType.FramelessWindowHint |  # 无边框
            Qt.WindowType.NoDropShadowWindowHint  # 使用自定义阴影
        )
        
        # 设置主题样式
        tm = get_theme_manager()
        context_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {tm.get_variable('bg_secondary')};
                color: {tm.get_variable('text_primary')};
                border: 1px solid {tm.get_variable('border')};
                border-radius: 4px;
                padding: 5px;
            }}
            QMenu::item {{
                padding: 5px 20px;
                background-color: transparent;
            }}
            QMenu::item:selected {{
                background-color: {tm.get_variable('bg_hover')};
                border-radius: 2px;
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {tm.get_variable('border')};
                margin: 5px 0px;
            }}
        """)
        
        open_folder_action = QAction("打开配置所在文件夹", context_menu)
        open_folder_action.triggered.connect(lambda: self.open_config_folder(template))
        context_menu.addAction(open_folder_action)
        
        delete_config_action = QAction("删除配置", context_menu)
        delete_config_action.triggered.connect(lambda: self.delete_config(template, button))
        context_menu.addAction(delete_config_action)
        
        # ⭐关键改进：创建全局事件过滤器
        # 过滤器会：
        # 1. 监控全局鼠标点击事件，点击菜单外立即关闭
        # 2. 定时检测鼠标位置（每50ms），鼠标离开立即关闭
        event_filter = MenuEventFilter(context_menu)
        
        context_menu._event_filter = event_filter
        
        # 连接aboutToHide信号，确保清理资源
        def cleanup_menu():
            if hasattr(context_menu, '_event_filter'):
                # 停止定时器
                if hasattr(context_menu._event_filter, 'check_timer'):
                    context_menu._event_filter.check_timer.stop()
                # 确保从应用程序移除全局事件过滤器
                try:
                    QApplication.instance().removeEventFilter(context_menu._event_filter)
                except:
                    pass
            context_menu.deleteLater()
        
        context_menu.aboutToHide.connect(cleanup_menu)
        
        # 使用popup()非阻塞显示菜单
        # 配合全局事件过滤器和定时检测，实现完善的自动关闭
        context_menu.popup(button.mapToGlobal(pos))
    
    def open_config_folder(self, template):
        """打开配置所在文件夹（完全异步，零延迟）
        
        使用守护线程 + 原生系统调用实现最快响应：
        1. 立即验证路径有效性（<1ms）
        2. 创建并启动守护线程（<5ms）
        3. 主线程立即返回，完全不阻塞UI
        4. 后台线程执行系统调用
        
        关键优化：
        - Windows: 使用 os.startfile（原生API，最快）
        - 守护线程：主进程退出时自动清理
        - 不等待线程完成：火力全开模式
        """
        try:
            # 快速验证路径（主线程，<1ms）
            if not template.path or not template.path.exists():
                QMessageBox.warning(self.ui, "警告", "配置文件路径不存在")
                return
            
            folder_path = template.path.parent
            
            thread = threading.Thread(
                target=_open_folder_async,
                args=(folder_path,),
                daemon=True  # 守护线程，主进程退出时自动清理
            )
            thread.start()  # 立即启动，不等待
            
            logger.debug(f"已启动打开文件夹线程: {folder_path}")
            
        except Exception as e:
            logger.error(f"启动打开文件夹线程时出错: {e}")
            QMessageBox.critical(self.ui, "错误", f"打开配置文件夹时出错: {str(e)}")
    
    def delete_config(self, template, button):
        """删除配置"""
        try:
            # 调用逻辑层删除方法，确保同步到配置文件
            if self.ui.logic:
                self.ui.logic.remove_template(template)
            
            self.ui.update_config_buttons()
        except Exception as e:
            logger.error(f"删除配置时出错: {e}")
            QMessageBox.critical(self.ui, "错误", f"删除配置时出错: {str(e)}")

