# -*- coding: utf-8 -*-

"""
虚幻引擎工具箱主入口
"""

import sys
import os
from pathlib import Path

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
    app.setApplicationVersion("1.0.1")
    
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
                
                # ========== 加载 StyleLoader 组件样式 ==========
                try:
                    from core.utils.style_loader import StyleLoader
                    
                    logger.info("正在加载全局 QSS 组件样式...")
                    style_loader = StyleLoader()
                    
                    # 加载所有组件 QSS（自动替换变量）
                    component_qss = style_loader.load_all_components(replace_vars=True)
                    
                    if component_qss:
                        # 获取当前应用样式（ThemeManager 设置的）
                        current_qss = app.styleSheet()
                        
                        # 叠加组件样式
                        merged_qss = current_qss + "\n\n/* ===== StyleLoader 组件样式 ===== */\n" + component_qss
                        app.setStyleSheet(merged_qss)
                        
                        logger.info(f"[OK] 全局 QSS 组件样式已加载，字符数: {len(component_qss)}")
                        print(f"[StyleLoader] [OK] Loaded {len(component_qss)} characters of component styles")
                    else:
                        logger.warning("[WARN] 未加载到任何组件样式")
                        print("[StyleLoader] [WARN] No component styles loaded")
                    
                except Exception as e:
                    logger.error(f"[ERROR] 加载全局 QSS 组件样式失败: {e}", exc_info=True)
                    print(f"[StyleLoader] [ERROR] Failed to load: {e}")
                
                # 创建模块提供者
                from core.module_interface import ModuleProviderAdapter
                module_provider = ModuleProviderAdapter(app_manager.module_manager)
                
                # 建立模块间的连接（AI助手、资产管理器、配置工具）
                try:
                    logger.info("========== 开始建立模块间连接 ==========")
                    print("[DEBUG] ========== 开始建立模块间连接 ==========")
                    
                    asset_manager_module = app_manager.module_manager.get_module("asset_manager")
                    config_tool_module = app_manager.module_manager.get_module("config_tool")
                    ai_assistant_module = app_manager.module_manager.get_module("ai_assistant")
                    
                    print(f"[DEBUG] asset_manager 模块: {asset_manager_module}")
                    print(f"[DEBUG] config_tool 模块: {config_tool_module}")
                    print(f"[DEBUG] ai_assistant 模块: {ai_assistant_module}")
                    
                    if ai_assistant_module:
                        print(f"[DEBUG] ai_assistant 实例: {ai_assistant_module.instance}")
                        
                        # 连接 asset_manager
                        if asset_manager_module:
                            print(f"[DEBUG] asset_manager 实例: {asset_manager_module.instance}")
                            
                            # 获取 asset_manager 的逻辑层实例
                            if hasattr(asset_manager_module.instance, 'logic'):
                                asset_logic = asset_manager_module.instance.logic
                                print(f"[DEBUG] [OK] 通过 .logic 属性获取到 asset_manager 逻辑层: {asset_logic}")
                                logger.info("获取到 asset_manager 逻辑层")
                            elif hasattr(asset_manager_module.instance, 'get_logic'):
                                asset_logic = asset_manager_module.instance.get_logic()
                                print(f"[DEBUG] [OK] 通过 get_logic() 获取到 asset_manager 逻辑层: {asset_logic}")
                                logger.info("通过 get_logic 获取到 asset_manager 逻辑层")
                            else:
                                asset_logic = None
                                print("[DEBUG] [ERROR] 无法获取 asset_manager 逻辑层")
                                logger.warning("无法获取 asset_manager 逻辑层")
                            
                            # 将 asset_manager 逻辑层传递给 AI助手
                            if asset_logic and hasattr(ai_assistant_module.instance, 'set_asset_manager_logic'):
                                print(f"[DEBUG] 正在调用 ai_assistant.set_asset_manager_logic({asset_logic})...")
                                ai_assistant_module.instance.set_asset_manager_logic(asset_logic)
                                print("[DEBUG] [OK] 已将 asset_manager 逻辑层连接到 AI助手")
                                logger.info("已将 asset_manager 逻辑层连接到 AI助手")
                            else:
                                if not asset_logic:
                                    print("[DEBUG] [ERROR] asset_logic 为 None，无法连接")
                                if not hasattr(ai_assistant_module.instance, 'set_asset_manager_logic'):
                                    print("[DEBUG] [ERROR] AI助手模块缺少 set_asset_manager_logic 方法")
                                    logger.warning("AI助手模块缺少 set_asset_manager_logic 方法")
                        else:
                            print("[DEBUG] [WARN] asset_manager 模块未加载")
                            logger.info("asset_manager 模块未加载，跳过连接")
                        
                        # 连接 config_tool
                        if config_tool_module:
                            print(f"[DEBUG] config_tool 实例: {config_tool_module.instance}")
                            
                            # 获取 config_tool 的逻辑层实例
                            if hasattr(config_tool_module.instance, 'logic'):
                                config_logic = config_tool_module.instance.logic
                                print(f"[DEBUG] [OK] 通过 .logic 属性获取到 config_tool 逻辑层: {config_logic}")
                                logger.info("获取到 config_tool 逻辑层")
                            elif hasattr(config_tool_module.instance, 'get_logic'):
                                config_logic = config_tool_module.instance.get_logic()
                                print(f"[DEBUG] [OK] 通过 get_logic() 获取到 config_tool 逻辑层: {config_logic}")
                                logger.info("通过 get_logic 获取到 config_tool 逻辑层")
                            else:
                                config_logic = None
                                print("[DEBUG] [ERROR] 无法获取 config_tool 逻辑层")
                                logger.warning("无法获取 config_tool 逻辑层")
                            
                            # 将 config_tool 逻辑层传递给 AI助手
                            if config_logic and hasattr(ai_assistant_module.instance, 'set_config_tool_logic'):
                                print(f"[DEBUG] 正在调用 ai_assistant.set_config_tool_logic({config_logic})...")
                                ai_assistant_module.instance.set_config_tool_logic(config_logic)
                                print("[DEBUG] [OK] 已将 config_tool 逻辑层连接到 AI助手")
                                logger.info("已将 config_tool 逻辑层连接到 AI助手")
                            else:
                                if not config_logic:
                                    print("[DEBUG] [ERROR] config_logic 为 None，无法连接")
                                if not hasattr(ai_assistant_module.instance, 'set_config_tool_logic'):
                                    print("[DEBUG] [ERROR] AI助手模块缺少 set_config_tool_logic 方法")
                                    logger.warning("AI助手模块缺少 set_config_tool_logic 方法")
                        else:
                            print("[DEBUG] [WARN] config_tool 模块未加载")
                            logger.info("config_tool 模块未加载，跳过连接")
                        
                        # 连接 site_recommendations
                        site_recommendations_module = module_provider.get_module("site_recommendations")
                        if site_recommendations_module:
                            print(f"[DEBUG] site_recommendations 实例: {site_recommendations_module.instance}")
                            
                            # 获取 site_recommendations 的逻辑层实例
                            if hasattr(site_recommendations_module.instance, 'logic'):
                                site_logic = site_recommendations_module.instance.logic
                                print(f"[DEBUG] [OK] 通过 .logic 属性获取到 site_recommendations 逻辑层: {site_logic}")
                                logger.info("获取到 site_recommendations 逻辑层")
                            elif hasattr(site_recommendations_module.instance, 'get_logic'):
                                site_logic = site_recommendations_module.instance.get_logic()
                                print(f"[DEBUG] [OK] 通过 get_logic() 获取到 site_recommendations 逻辑层: {site_logic}")
                                logger.info("通过 get_logic 获取到 site_recommendations 逻辑层")
                            else:
                                site_logic = None
                                print("[DEBUG] [ERROR] 无法获取 site_recommendations 逻辑层")
                                logger.warning("无法获取 site_recommendations 逻辑层")
                            
                            # 将 site_recommendations 逻辑层传递给 AI助手
                            if site_logic and hasattr(ai_assistant_module.instance, 'site_recommendations_logic'):
                                print(f"[DEBUG] 正在设置 ai_assistant.site_recommendations_logic = {site_logic}")
                                ai_assistant_module.instance.site_recommendations_logic = site_logic
                                print("[DEBUG] [OK] 已将 site_recommendations 逻辑层连接到 AI助手")
                                logger.info("已将 site_recommendations 逻辑层连接到 AI助手")
                            else:
                                if not site_logic:
                                    print("[DEBUG] [ERROR] site_logic 为 None，无法连接")
                                if not hasattr(ai_assistant_module.instance, 'site_recommendations_logic'):
                                    print("[DEBUG] [ERROR] AI助手模块缺少 site_recommendations_logic 属性")
                                    logger.warning("AI助手模块缺少 site_recommendations_logic 属性")
                        else:
                            print("[DEBUG] [WARN] site_recommendations 模块未加载")
                            logger.info("site_recommendations 模块未加载，跳过连接")
                    else:
                        print("[DEBUG] [WARN] ai_assistant 模块未加载")
                        logger.info("ai_assistant 模块未加载，跳过连接")
                    
                    print("[DEBUG] ========== 模块连接流程结束 ==========")
                except Exception as e:
                    print(f"[DEBUG] [ERROR] 建立模块间连接时发生异常: {e}")
                    logger.error(f"建立模块间连接失败: {e}", exc_info=True)
                    import traceback
                    traceback.print_exc()
                
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