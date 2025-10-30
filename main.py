# -*- coding: utf-8 -*-

"""
虚幻引擎工具箱主入口
"""

import sys
import os
from pathlib import Path

# 首先启用路径追踪（用于调试）
try:
    import core.path_tracer
except:
    pass

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt, QStandardPaths
from PyQt6.QtGui import QIcon
from ui.ue_main_window import UEMainWindow
from core.app_manager import AppManager
from core.module_manager import ModuleManager
from core.logger import init_logging_system, get_logger
from core.single_instance import SingleInstanceManager
from core.utils.theme_manager import get_theme_manager, Theme
import json


init_logging_system()
logger = get_logger(__name__)


def set_windows_app_user_model_id():
    """设置 Windows AppUserModelID，确保任务栏图标正确显示"""
    try:
        import ctypes
        app_id = 'HUTAO.UEToolkit.1.0'  # 应用程序唯一标识符
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        logger.info(f"已设置 Windows AppUserModelID: {app_id}")
    except Exception as e:
        logger.warning(f"设置 Windows AppUserModelID 失败: {e}")


def main():
    """主函数"""
    logger.info("启动虚幻引擎工具箱")
    
    # 设置 Windows 任务栏图标
    if sys.platform == 'win32':
        set_windows_app_user_model_id()
    
    # 创建应用实例
    app = QApplication(sys.argv)
    app.setApplicationName("ue_toolkit")  # 统一使用无空格的名称
    app.setApplicationVersion("1.0.0")
    
    # 设置应用程序图标
    icon_path = project_root / "resources" / "tubiao.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
        logger.info(f"已设置应用图标: {icon_path}")
    else:
        logger.warning(f"图标文件不存在: {icon_path}")
    
    # 检查单实例
    single_instance = SingleInstanceManager("UEToolkit")
    
    if single_instance.is_running():
        logger.info("程序已经在运行，激活现有实例")
        return 0
    
    try:
        # 创建应用管理器
        app_manager = AppManager()
        
        # 设置应用程序
        logger.info("开始设置应用程序")
        if not app_manager.setup():
            logger.error("应用程序设置失败")
            QMessageBox.critical(None, "启动失败", "应用程序设置失败，请查看日志文件获取详细信息。")
            return 1
        
        logger.info("应用程序设置成功")
        
        # 存储主窗口引用（在回调中使用）
        main_window = None
        module_provider = None
        
        def on_startup_complete(success: bool):
            """异步启动完成回调"""
            nonlocal main_window, module_provider
            
            if not success:
                logger.error("应用程序启动失败")
                QMessageBox.critical(
                    None, 
                    "启动失败", 
                    "应用程序启动失败，请查看日志文件获取详细信息。"
                )
                app.quit()
                return
            
            try:
                logger.info("应用程序启动成功")
                
                # 加载保存的主题设置
                try:
                    app_data = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
                    config_path = Path(app_data) / "ue_toolkit" / "ui_settings.json"
                    if config_path.exists():
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        theme_name = config.get('theme', 'dark')
                        theme_manager = get_theme_manager()
                        
                        if theme_name == 'light':
                            theme_manager.set_theme(Theme.LIGHT)
                        elif theme_name == 'dark':
                            theme_manager.set_theme(Theme.DARK)
                        elif theme_name.startswith('custom:'):
                            # 新格式：custom:theme_name
                            custom_theme_name = theme_name.split(':', 1)[1]
                            try:
                                theme_manager.set_custom_theme_by_name(custom_theme_name)
                            except ValueError as e:
                                logger.warning(f"自定义主题 '{custom_theme_name}' 不存在，使用默认主题: {e}")
                                theme_manager.set_theme(Theme.DARK)
                        elif theme_name == 'custom':
                            # 兼容旧格式
                            theme_manager.set_theme(Theme.CUSTOM)
                        else:
                            theme_manager.set_theme(Theme.DARK)
                        
                        logger.info(f"已加载保存的主题: {theme_name}")
                except Exception as e:
                    logger.warning(f"加载主题设置失败，使用默认主题: {e}")
                
                # 创建模块提供者
                from core.module_interface import ModuleProviderAdapter
                module_provider = ModuleProviderAdapter(app_manager.module_manager)
                
                # 创建主窗口
                logger.info("创建主窗口")
                main_window = UEMainWindow(module_provider)
                main_window.show()
                
                # 启动单实例服务器
                single_instance.start_server(main_window)
                
                # 确保窗口显示在最前面
                main_window.raise_()
                main_window.activateWindow()
                
                logger.info("应用程序完全启动完成")
                
            except Exception as e:
                logger.error(f"创建主窗口时发生错误: {e}", exc_info=True)
                QMessageBox.critical(
                    None,
                    "启动失败",
                    f"创建主窗口失败: {str(e)}"
                )
                app.quit()
        
        def on_startup_progress(percent: int, message: str):
            """启动进度更新回调"""
            logger.info(f"启动进度: {percent}% - {message}")
            app.processEvents()
        
        def on_startup_error(error_message: str):
            """启动错误回调"""
            logger.error(f"启动过程出错: {error_message}")
            QMessageBox.critical(
                None,
                "启动错误",
                f"启动过程中发生错误:\n{error_message}"
            )
            app.quit()
        
        # 异步启动应用程序
        logger.info("开始异步启动应用程序")
        app_manager.start_async(
            on_complete=on_startup_complete,
            on_progress=on_startup_progress,
            on_error=on_startup_error
        )
        
        # 运行应用程序事件循环
        exit_code = app.exec()
        
        # 清理单实例资源
        single_instance.cleanup()
        
        logger.info(f"应用程序退出，退出码: {exit_code}")
        return exit_code
        
    except Exception as e:
        logger.error(f"启动应用程序时发生错误: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)