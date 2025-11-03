# -*- coding: utf-8 -*-

"""
主窗口核心逻辑
"""

from typing import Optional, Dict, Any, List, Set
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget, QSystemTrayIcon
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QRegion, QPainterPath, QPainter, QColor, QBrush
from PyQt6.QtGui import QMouseEvent

from core.module_interface import IModuleProvider
from core.logger import get_logger
from core.utils.theme_manager import get_theme_manager
from core.config.config_manager import ConfigManager

from .main_window_components import CustomTitleBar
from .main_window_handlers import NavigationHandler, ModuleLoader
from .system_tray_manager import SystemTrayManager
from .dialogs.close_confirmation_dialog import CloseConfirmationDialog

logger = get_logger(__name__)


class UEMainWindow(QMainWindow):
    """虚幻引擎工具箱主窗口"""
    
    def __init__(self, module_provider: Optional[IModuleProvider] = None):
        """初始化主窗口
        
        Args:
            module_provider: 模块提供者，用于获取模块
        """
        super().__init__()
        self.module_provider = module_provider
        self.module_ui_map: Dict[str, QWidget] = {}  # 存储模块UI的映射
        self.loaded_modules: Set[str] = set()  # 追踪已加载的模块，防止重复加载
        self.content_stack: Optional[QStackedWidget] = None  # QStackedWidget用于页面切换
        self.nav_buttons: List[Dict[str, Any]] = []  # 导航按钮列表
        self.tool_title_label: Optional[QLabel] = None  # 工具标题标签
        self._is_closing = False  # 标记是否正在关闭
        self._quit_on_close = False  # 标记是否退出应用
        
        # 初始化UI配置管理器
        self.ui_config_manager = ConfigManager("app")
        self._close_action_preference = None  # 用户记住的关闭行为偏好
        self._load_close_action_preference()
        
        self.navigation_handler = NavigationHandler(self)
        
        # 初始化系统托盘
        self.tray_manager = SystemTrayManager(self)
        self._init_system_tray()
        
        self.init_ui()
    
    def _init_system_tray(self):
        """初始化系统托盘"""
        try:
            # 获取图标路径
            icon_path = Path(__file__).parent.parent / "resources" / "tubiao.ico"
            self.tray_manager.initialize(icon_path)
            
            # 连接信号
            self.tray_manager.show_window_requested.connect(self._on_tray_show_window)
            self.tray_manager.quit_requested.connect(self._on_tray_quit)
            
        except Exception as e:
            logger.error(f"初始化系统托盘失败: {e}", exc_info=True)
    
    def _on_tray_show_window(self):
        """托盘图标点击 - 显示窗口"""
        self.show()
        self.activateWindow()
        self.raise_()
        logger.info("从系统托盘恢复主窗口")
        
    def _on_tray_quit(self):
        """托盘菜单 - 退出应用"""
        logger.info("托盘菜单退出：设置退出标志并关闭窗口")
        self._quit_on_close = True
        self._is_closing = True
        self.close()
        
        # 确保应用程序退出
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()
        logger.info("已调用 QApplication.quit()")
    
    def init_ui(self) -> None:
        """初始化用户界面"""
        self.setWindowTitle("UE Toolkit - 虚幻引擎工具箱")
        self.setGeometry(100, 100, 1300, 800)  # 增加宽度以容纳4个资产卡片和滚动条
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)  # 无边框窗口
        
        # 从 QSS 文件加载样式
        self.load_stylesheet()
        
        self.title_bar = CustomTitleBar(self)
        self.setMenuWidget(self.title_bar)
        
        self.create_central_widget()
        
        # 居中显示窗口
        self.center_window()
    
    def load_stylesheet(self) -> None:
        """加载样式表（使用 ThemeManager）"""
        try:
            theme_manager = get_theme_manager()
            theme_manager.apply_to_widget(self)
            logger.info("成功应用主题到主窗口")
        except Exception as e:
            logger.error(f"应用主题时出错: {e}", exc_info=True)
    
    def load_module_ui_lazy(self, module_name: str) -> bool:
        """懒加载模块 UI（首次访问时才创建）
        
        Args:
            module_name: 模块名称
            
        Returns:
            bool: 加载是否成功
        """
        if module_name in self.loaded_modules:
            logger.debug(f"模块 {module_name} UI已加载")
            return True
        
        # 确保content_stack已经创建
        if self.content_stack is None:
            logger.error("content_stack尚未创建，无法加载模块UI")
            return False
        
        if not self.module_provider:
            logger.error("模块提供者未初始化")
            return False
        
        try:
            module = self.module_provider.get_module(module_name)
            if not module:
                logger.error(f"找不到模块: {module_name}")
                return False
            
            logger.info(f"懒加载模块 {module_name} 的UI...")
            widget = module.get_widget()
            
            if not widget:
                logger.error(f"模块 {module_name} 的 get_widget 返回了 None")
                return False
            
            # 设置父对象为content_stack，确保Qt自动内存管理
            widget.setParent(self.content_stack)
            
            # 将模块UI添加到映射中
            self.module_ui_map[module_name] = widget
            
            # 添加到堆栈中
            self.content_stack.addWidget(widget)
            
            # 标记为已加载
            self.loaded_modules.add(module_name)
            
            # 🎯 建立模块之间的连接
            self._connect_modules(module_name, module)
            
            logger.info(f"成功懒加载模块 {module_name} UI")
            return True
            
        except Exception as e:
            logger.error(f"懒加载模块 {module_name} UI时出错: {e}", exc_info=True)
            return False
    
    def _connect_modules(self, module_name: str, module):
        """建立模块之间的连接
        
        Args:
            module_name: 模块名称
            module: 模块实例
        """
        try:
            # 如果是 AI 助手模块，连接 asset_manager
            if module_name == "ai_assistant":
                logger.info("建立 AI 助手与 asset_manager 的连接")
                
                # 获取 asset_manager 模块
                asset_manager_module = self.module_provider.get_module("asset_manager")
                if asset_manager_module:
                    # 获取 asset_manager 的逻辑层
                    # asset_manager_module 是 IModule 接口，实际是 ModuleAdapter
                    if hasattr(asset_manager_module, 'instance'):
                        asset_manager_instance = asset_manager_module.instance
                        if hasattr(asset_manager_instance, 'logic'):
                            asset_manager_logic = asset_manager_instance.logic
                            
                            # 设置到 AI 助手模块
                            # module 是 IModule 接口，实际是 ModuleAdapter
                            if hasattr(module, 'instance'):
                                ai_assistant_instance = module.instance
                                if hasattr(ai_assistant_instance, 'set_asset_manager_logic'):
                                    ai_assistant_instance.set_asset_manager_logic(asset_manager_logic)
                                    logger.info("✓ AI 助手已连接到 asset_manager")
                                else:
                                    logger.warning("AI 助手模块没有 set_asset_manager_logic 方法")
                            else:
                                logger.warning("AI 助手模块没有 instance 属性")
                        else:
                            logger.warning("asset_manager 模块没有 logic 属性")
                    else:
                        logger.warning("asset_manager 模块没有 instance 属性")
                else:
                    logger.warning("未找到 asset_manager 模块，AI 助手将无法访问资产数据")
        
        except Exception as e:
            logger.error(f"建立模块连接时出错: {e}", exc_info=True)
    
    def center_window(self) -> None:
        """将窗口居中显示"""
        screen = self.screen()
        if screen:
            screen_geometry = screen.availableGeometry()
            screen_center = screen_geometry.center()
            
            # 计算窗口应该的位置
            window_geometry = self.frameGeometry()
            window_geometry.moveCenter(screen_center)
            
            # 移动窗口到计算出的位置
            self.move(window_geometry.topLeft())
    
    def create_central_widget(self) -> None:
        """创建中央部件
        
        注意：必须先创建右侧内容区域（包括 content_stack），
        然后再创建左侧面板，这样在创建工具按钮时 content_stack 已存在
        """
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 使用水平布局分割左右区域
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        central_widget.setLayout(main_layout)
        
        # 先创建右侧内容区域（不添加到布局）
        # 这样 content_stack 会被创建，但还不会显示
        right_frame = self.create_right_content_widget()
        
        # 创建左侧面板（此时 content_stack 已经创建完成）
        self.create_left_panel(main_layout)
        
        # 最后将右侧内容添加到布局
        main_layout.addWidget(right_frame)
    
    def create_left_panel(self, parent_layout: QHBoxLayout) -> None:
        """创建左侧面板
        
        Args:
            parent_layout: 父布局
        """
        left_frame = QFrame()
        left_frame.setObjectName("leftPanel")  # 设置对象名称以便样式表识别
        left_frame.setFixedWidth(150)  # 设置固定宽度
        
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_frame.setLayout(left_layout)
        
        # 添加顶部间距
        left_layout.addSpacing(70)
        
        self.create_tool_buttons(left_layout)
        
        # 添加弹性空间
        left_layout.addStretch()
        
        # 添加设置按钮
        settings_button = QPushButton("⚙ 设置")
        settings_button.setProperty("class", "toolButton")
        settings_button.setFixedHeight(40)
        settings_button.setCheckable(True)
        settings_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # 禁用焦点，避免Alt键显示虚线框
        settings_button.clicked.connect(lambda: self.on_settings_clicked())
        left_layout.addWidget(settings_button)
        
        self.settings_button = settings_button
        
        # 添加作者信息
        author_label = QLabel("作者：HUTAO")
        author_label.setObjectName("authorLabel")  # 设置对象名称以便样式表识别
        author_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(author_label)
        
        parent_layout.addWidget(left_frame)
    
    def create_tool_buttons(self, parent_layout: QVBoxLayout) -> None:
        """创建工具按钮（动态从模块提供者获取）
        
        Args:
            parent_layout: 父布局
        """
        if not self.module_provider:
            logger.warning("模块提供者未初始化，无法创建工具按钮")
            return
        
        # 从模块提供者动态获取模块列表
        try:
            modules = self.module_provider.get_all_modules()
            
            for i, (module_name, module) in enumerate(modules.items()):
                metadata = module.get_metadata()
                
                button = QPushButton(metadata.display_name)
                button.setProperty("class", "toolButton")  # 设置CSS类
                button.setFixedHeight(40)
                button.setCheckable(True)
                button.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # 禁用焦点，避免Alt键显示虚线框
                
                # 默认选中第一个按钮
                if i == 0:
                    button.setChecked(True)
                
                # 连接点击事件（使用模块名称作为ID）
                button.clicked.connect(
                    lambda checked, mod_name=module_name: self.on_tool_button_clicked(mod_name)
                )
                
                # 添加到布局
                parent_layout.addWidget(button)
                
                # 添加到导航按钮列表
                self.nav_buttons.append({
                    "button": button, 
                    "id": module_name,
                    "display_name": metadata.display_name
                })
            
            # 将按钮列表同步到导航处理器
            self.navigation_handler.nav_buttons = self.nav_buttons
            
            logger.info(f"成功创建 {len(modules)} 个工具按钮")
            
            # 设置初始标题为第一个模块的名称
            if self.nav_buttons and len(self.nav_buttons) > 0:
                first_module_name = self.nav_buttons[0].get("display_name", "工具箱")
                if self.tool_title_label:
                    self.tool_title_label.setText(first_module_name)
                    logger.debug(f"设置初始标题: {first_module_name}")
                
                # 自动加载第一个模块的内容
                first_module_id = self.nav_buttons[0].get("id")
                if first_module_id:
                    logger.info(f"自动加载第一个模块: {first_module_id}")
                    # 使用QTimer延迟加载，确保窗口完全初始化后再加载
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(100, lambda: self.on_tool_button_clicked(first_module_id))
            
        except Exception as e:
            logger.error(f"创建工具按钮时发生错误: {e}", exc_info=True)
    
    def create_right_content_widget(self) -> QFrame:
        """创建右侧内容区域组件
        
        Returns:
            QFrame: 右侧内容框架
        """
        right_frame = QFrame()
        right_frame.setObjectName("rightFrame")  # 设置对象名称以便样式表识别
        
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_frame.setLayout(right_layout)
        
        self.create_tool_title_area(right_layout)
        
        self.create_content_display_area(right_layout)
        
        return right_frame
    
    def create_tool_title_area(self, parent_layout: QVBoxLayout) -> None:
        """创建工具名称显示区域
        
        Args:
            parent_layout: 父布局
        """
        self.tool_title_label = QLabel("")
        self.tool_title_label.setObjectName("toolTitle")  # 设置对象名称以便样式表识别
        parent_layout.addWidget(self.tool_title_label)
    
    def create_content_display_area(self, parent_layout: QVBoxLayout) -> None:
        """创建内容显示区域
        
        Args:
            parent_layout: 父布局
        """
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")  # 设置对象名称以便样式表识别
        
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_frame.setLayout(content_layout)
        
        self.content_stack = QStackedWidget()
        
        # 添加到内容布局
        content_layout.addWidget(self.content_stack)
        
        parent_layout.addWidget(content_frame)
        
        # 注意：使用懒加载机制，不在启动时加载所有模块UI
        # 模块UI将在首次访问时才创建（通过 load_module_ui_lazy 方法）
        logger.info("内容显示区域创建完成，使用懒加载机制")
    
    def on_tool_button_clicked(self, tool_id: str) -> None:
        """工具按钮点击事件（委托给NavigationHandler）
        
        Args:
            tool_id: 工具ID
        """
        self.navigation_handler.on_tool_button_clicked(tool_id)
    
    def on_settings_clicked(self) -> None:
        """设置按钮点击事件"""
        # 取消所有工具按钮的选中状态
        for btn_info in self.nav_buttons:
            btn_info["button"].setChecked(False)
        
        # 确保设置按钮被选中
        if hasattr(self, 'settings_button'):
            self.settings_button.setChecked(True)
        
        if self.tool_title_label:
            self.tool_title_label.setText("设置")
        
        self.show_settings()
        logger.info("切换到设置界面")
    
    def show_settings(self) -> None:
        """显示设置界面"""
        logger.info("=== 开始显示设置界面 ===")
        
        if not hasattr(self, 'settings_widget'):
            from .settings_widget import SettingsWidget
            self.settings_widget = SettingsWidget()
            if self.content_stack is not None:
                self.content_stack.addWidget(self.settings_widget)
            logger.info("✓ 创建设置界面")
        else:
            logger.info("✓ 设置界面已存在")
        
        # 每次显示时都尝试设置/更新资产管理器逻辑层引用（确保即使延迟加载也能获取）
        try:
            logger.info(f"检查 module_provider: {self.module_provider is not None}")
            logger.info(f"检查 settings_widget: {hasattr(self, 'settings_widget')}")
            
            if self.module_provider and hasattr(self, 'settings_widget'):
                asset_manager = self.module_provider.get_module("asset_manager")
                logger.info(f"获取到 asset_manager 模: {asset_manager is not None}")
                
                if asset_manager:
                    # 使用类型检查安全地访问 instance 属性
                    # asset_manager 是 IModule 接口类型，但实际可能是 ModuleAdapter
                    # ModuleAdapter 有 instance 属性，但接口中未声明
                    if hasattr(asset_manager, 'instance'):
                        module_instance = getattr(asset_manager, 'instance', None)
                        logger.info(f"module_instance 存在: {module_instance is not None}")
                        
                        if module_instance and hasattr(module_instance, 'logic'):
                            logic_instance = getattr(module_instance, 'logic', None)
                            logger.info(f"成功获取 logic 对象: {logic_instance}")
                            if logic_instance:
                                self.settings_widget.set_asset_manager_logic(logic_instance)
                                logger.info("✓ 已成功设置资产管理器逻辑层引用")
                            else:
                                logger.warning("✗ logic 对象为 None")
                        else:
                            logger.warning("✗ module_instance 没有 logic 属性或为 None")
                    else:
                        logger.warning("✗ asset_manager 没有 instance 属性")
                else:
                    logger.warning("✗ 未能获取 asset_manager 模块")
            else:
                logger.warning("✗ module_provider 或 settings_widget 不可用")
                
        except Exception as e:
            logger.error(f"✗ 设置资产管理器逻辑层引用失败: {e}", exc_info=True)
        
        # 切换到设置界面
        if self.content_stack is not None and hasattr(self, 'settings_widget'):
            self.content_stack.setCurrentWidget(self.settings_widget)
        logger.info("=== 设置界面显示完成 ===")
    
    def toggle_maximize(self) -> None:
        """切换最大化状态"""
        if self.isMaximized():
            self.showNormal()
            self.title_bar.maximize_button.setText("□")
        else:
            self.showMaximized()
            self.title_bar.maximize_button.setText("❐")

    def show(self) -> None:
        """重写show方法"""
        super().show()
        self.raise_()
        self.activateWindow()
    
    def cleanup_module_uis(self) -> None:
        """清理所有模块UI资源
        
        此方法会正确清理所有已加载的模块UI，释放内存。
        在窗口关闭或需要重新加载模块时调用。
        """
        if not self.content_stack:
            logger.debug("content_stack不存在，无需清理")
            return
        
        logger.info(f"开始清理模块UI，共 {len(self.loaded_modules)} 个模块")
        
        cleaned_count = 0
        error_count = 0
        
        # 遍历所有已加载的模块
        for module_name in list(self.loaded_modules):  # 使用list()创建副本，避免迭代时修改集合
            try:
                widget = self.module_ui_map.get(module_name)
                
                if widget:
                    # 从堆栈中移除
                    self.content_stack.removeWidget(widget)
                    
                    # 调用deleteLater()标记为待删除，Qt会在合适时机自动清理
                    widget.deleteLater()
                    
                    logger.debug(f"成功清理模块 {module_name} UI")
                    cleaned_count += 1
                else:
                    logger.warning(f"模块 {module_name} 在映射中不存在")
                    
            except Exception as e:
                logger.error(f"清理模块 {module_name} UI时出错: {e}", exc_info=True)
                error_count += 1
                continue
        
        # 清空映射和已加载集合
        self.module_ui_map.clear()
        self.loaded_modules.clear()
        
        logger.info(f"模块UI清理完成 - 成功: {cleaned_count} 个，失败: {error_count} 个")
    
    def _load_close_action_preference(self):
        """从配置文件加载关闭行为偏好"""
        try:
            config = self.ui_config_manager.load_user_config()
            self._close_action_preference = config.get("close_action_preference")
            if self._close_action_preference:
                logger.info(f"已加载用户关闭行为偏好: {self._close_action_preference}")
        except Exception as e:
            logger.error(f"加载关闭行为偏好失败: {e}", exc_info=True)
            self._close_action_preference = None
    
    def _save_close_action_preference(self, action: int):
        """保存关闭行为偏好到配置文件
        
        Args:
            action: CloseConfirmationDialog.RESULT_CLOSE 或 RESULT_MINIMIZE
        """
        try:
            config = self.ui_config_manager.load_user_config()
            
            # 如果配置是空的或者没有版本号，初始化版本号
            if not config or '_version' not in config:
                config['_version'] = "1.0.0"
            
            if action == CloseConfirmationDialog.RESULT_CLOSE:
                config["close_action_preference"] = "close"
            elif action == CloseConfirmationDialog.RESULT_MINIMIZE:
                config["close_action_preference"] = "minimize"
            
            # 保存配置
            success = self.ui_config_manager.save_user_config(config)
            
            if success:
                self._close_action_preference = config["close_action_preference"]
                logger.info(f"已保存用户关闭行为偏好: {self._close_action_preference}")
            else:
                logger.error("保存用户关闭行为偏好失败")
        except Exception as e:
            logger.error(f"保存关闭行为偏好失败: {e}", exc_info=True)
    
    def _sync_close_behavior_to_settings(self, preference: str):
        """同步关闭行为到设置界面的单选按钮
        
        Args:
            preference: "close" 或 "minimize"
        """
        try:
            # 检查设置界面是否已创建
            if not hasattr(self, 'settings_widget') or self.settings_widget is None:
                logger.debug("设置界面尚未创建，跳过同步")
                return
            
            # 更新设置界面的单选按钮状态
            if preference == "close":
                self.settings_widget.close_directly_radio.setChecked(True)
                logger.info("已同步设置界面单选按钮: 直接关闭")
            elif preference == "minimize":
                self.settings_widget.minimize_to_tray_radio.setChecked(True)
                logger.info("已同步设置界面单选按钮: 最小化到托盘")
                
        except Exception as e:
            logger.error(f"同步关闭行为到设置界面失败: {e}", exc_info=True)
    
    def show_close_confirmation(self):
        """显示关闭确认对话框"""
        if self._is_closing:
            return
        
        # 检查是否已经记住了用户选择
        if self._close_action_preference == "close":
            # 直接关闭
            logger.info("根据用户偏好直接关闭程序（不显示对话框）")
            self._quit_on_close = True
            self._is_closing = True
            self.close()
            return
        elif self._close_action_preference == "minimize":
            # 直接最小化到托盘
            logger.info("根据用户偏好最小化到托盘（不显示对话框）")
            self.hide()
            self.tray_manager.show_message(
                "UE Toolkit",
                "程序已最小化到系统托盘，点击托盘图标可恢复窗口",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            return
            
        # 显示确认对话框
        result, remember_choice = CloseConfirmationDialog.ask_close_action(self)
        
        if result == CloseConfirmationDialog.RESULT_CLOSE:
            # 直接关闭
            logger.info("用户选择直接关闭程序")
            if remember_choice:
                # 用户勾选了"记住我的选择"，保存偏好
                self._save_close_action_preference(result)
                logger.info("已保存用户关闭行为偏好: 直接关闭")
                # 同步更新设置界面的单选按钮
                self._sync_close_behavior_to_settings("close")
            self._quit_on_close = True
            self._is_closing = True
            self.close()
            
        elif result == CloseConfirmationDialog.RESULT_MINIMIZE:
            # 最小化到托盘
            logger.info("用户选择最小化到托盘")
            if remember_choice:
                # 用户勾选了"记住我的选择"，保存偏好
                self._save_close_action_preference(result)
                logger.info("已保存用户关闭行为偏好: 最小化到托盘")
                # 同步更新设置界面的单选按钮
                self._sync_close_behavior_to_settings("minimize")
            self.hide()
            # 显示托盘提示
            self.tray_manager.show_message(
                "UE Toolkit",
                "程序已最小化到系统托盘，点击托盘图标可恢复窗口",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
        else:
            # 取消
            logger.info("用户取消关闭操作")
    
    def closeEvent(self, a0) -> None:
        """窗口关闭事件处理
        
        重写此方法以在窗口关闭时自动清理资源。
        
        Args:
            a0: 关闭事件对象
        """
        # 如果不是通过确认对话框触发的关闭，显示确认对话框
        if not self._is_closing and not self._quit_on_close:
            a0.ignore()
            self.show_close_confirmation()
            return
            
        logger.info("主窗口正在关闭，清理资源...")
        
        try:
            # 清理系统托盘
            if hasattr(self, 'tray_manager'):
                self.tray_manager.cleanup()
            
            self.cleanup_module_uis()
            
            # 调用父类的closeEvent
            super().closeEvent(a0)
            
            logger.info("主窗口资源清理完成")
            
        except Exception as e:
            logger.error(f"关闭窗口时发生错误: {e}", exc_info=True)
            # 即使出错也要接受关闭事件
            if a0 is not None:
                a0.accept()
    
