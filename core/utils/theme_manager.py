# -*- coding: utf-8 -*-

"""
主题管理器 - 统一管理应用程序的样式主题

提供：
1. 主题变量系统（类似CSS变量）
2. 主题切换功能（深色/浅色）
3. 统一的样式应用接口
4. 自定义主题支持
"""

from enum import Enum
from typing import Dict, Optional
from pathlib import Path
import json
from PyQt6.QtWidgets import QWidget, QApplication
from core.utils.style_loader import StyleLoader, get_style_loader
from core.logger import get_logger

logger = get_logger(__name__)


class Theme(Enum):
    """主题枚举"""
    DARK = "dark"
    LIGHT = "light"
    CUSTOM = "custom"


class ThemeManager:
    """主题管理器
    
    统一管理应用程序的样式和主题切换
    
    Example:

        theme_manager = ThemeManager()
        
        theme_manager.apply_to_widget(main_window)
        
        theme_manager.set_theme(Theme.LIGHT)
        theme_manager.apply_to_widget(main_window)
        
        bg_color = theme_manager.get_variable('bg_primary')
    """
    
    _instance: Optional['ThemeManager'] = None
    
    def __new__(cls) -> 'ThemeManager':
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化主题管理器"""
        # 避免重复初始化
        if hasattr(self, '_initialized'):
            return
        
        self.current_theme = Theme.DARK
        self.current_custom_theme_name = None  # 当前使用的自定义主题名称
        self.style_loader = get_style_loader()
        self._theme_variables: Dict[str, str] = {}
        self._custom_variables: Dict[str, str] = {}
        self._custom_themes: Dict[str, Dict[str, str]] = {}  # 存储所有导入的自定义主题
        
        self._load_custom_themes()
        
        self._load_theme_variables()
        
        self._initialized = True
        logger.info(f"主题管理器初始化完成，当前主题: {self.current_theme.value}")
    
    def _load_theme_variables(self):
        """加载当前主题的变量"""
        if self.current_theme == Theme.DARK:
            self._theme_variables = {
                'bg_primary': '#1e1e1e',
                'bg_secondary': '#2b2b2b',
                'bg_tertiary': '#353535',
                'bg_hover': '#3d3d3d',
                'bg_pressed': '#2a2a2a',
                
                'text_primary': '#ffffff',
                'text_secondary': '#cccccc',
                'text_tertiary': '#aaaaaa',
                'text_disabled': '#666666',
                
                'accent': '#4CAF50',
                'accent_hover': '#66BB6A',
                'accent_pressed': '#388E3C',
                
                'border': '#3d3d3d',
                'border_hover': '#4CAF50',
                'border_focus': '#66BB6A',
                
                # 状态色
                'success': '#4CAF50',
                'warning': '#FF9800',
                'error': '#F44336',
                'info': '#2196F3',
                
                # 透明度变体
                'bg_primary_alpha': 'rgba(30, 30, 30, 0.85)',
                'bg_secondary_alpha': 'rgba(43, 43, 43, 0.8)',
                'accent_alpha': 'rgba(76, 175, 80, 0.8)',
            }
        
        elif self.current_theme == Theme.LIGHT:
            self._theme_variables = {
                'bg_primary': '#ffffff',
                'bg_secondary': '#f5f5f5',
                'bg_tertiary': '#e0e0e0',
                'bg_hover': '#eeeeee',
                'bg_pressed': '#e0e0e0',
                
                'text_primary': '#212121',
                'text_secondary': '#616161',
                'text_tertiary': '#757575',
                'text_disabled': '#9e9e9e',
                
                'accent': '#4CAF50',
                'accent_hover': '#66BB6A',
                'accent_pressed': '#388E3C',
                
                'border': '#e0e0e0',
                'border_hover': '#4CAF50',
                'border_focus': '#66BB6A',
                
                # 状态色
                'success': '#4CAF50',
                'warning': '#FF9800',
                'error': '#F44336',
                'info': '#2196F3',
                
                # 透明度变体
                'bg_primary_alpha': 'rgba(255, 255, 255, 0.95)',
                'bg_secondary_alpha': 'rgba(245, 245, 245, 0.9)',
                'accent_alpha': 'rgba(76, 175, 80, 0.8)',
            }
        
        # 合并自定义变量
        self._theme_variables.update(self._custom_variables)
        
        logger.debug(f"加载主题变量完成，共 {len(self._theme_variables)} 个变量")
    
    def set_theme(self, theme: Theme):
        """设置当前主题
        
        Args:
            theme: 要切换到的主题
            
        Example:
            theme_manager.set_theme(Theme.LIGHT)
        """
        if theme != self.current_theme:
            old_theme = self.current_theme
            self.current_theme = theme
            
            # 如果切换到非自定义主题，清空自定义变量和主题名称
            if theme != Theme.CUSTOM:
                self._custom_variables.clear()
                self.current_custom_theme_name = None
            
            self._load_theme_variables()
            logger.info(f"切换主题: {old_theme.value} -> {theme.value}")
    
    def get_theme(self) -> Theme:
        """获取当前主题
        
        Returns:
            Theme: 当前主题
        """
        return self.current_theme
    
    def get_variable(self, name: str, default: str = '#000000') -> str:
        """获取主题变量值
        
        Args:
            name: 变量名
            default: 默认值
            
        Returns:
            str: 变量值
            
        Example:
            bg_color = theme_manager.get_variable('bg_primary')
        """
        value = self._theme_variables.get(name, default)
        if value == default and name not in self._theme_variables:
            logger.warning(f"主题变量 '{name}' 不存在，使用默认值: {default}")
        return value
    
    def set_custom_variable(self, name: str, value: str):
        """设置自定义主题变量
        
        Args:
            name: 变量名
            value: 变量值
            
        Example:
            theme_manager.set_custom_variable('my_color', '#FF5722')
        """
        self._custom_variables[name] = value
        self._theme_variables[name] = value
        logger.debug(f"设置自定义变量: {name} = {value}")
    
    def apply_to_widget(self,
                        widget: QWidget,
                        component: Optional[str] = None,
                        use_inline: bool = False):
        """为组件应用主题
        
        Args:
            widget: 要应用主题的组件
            component: 组件类型（如 "buttons", "scrollbars"）
            use_inline: 是否使用内联样式（而不是QSS文件）
            
        Example:
            theme_manager.apply_to_widget(main_window)
            
            theme_manager.apply_to_widget(button, component="buttons")
        """
        try:
            if use_inline:
                # 使用内联样式
                style = self._get_inline_style(component)
            else:
                # 从QSS文件加载
                if component:
                    qss_file = f"components/{component}.qss"
                else:
                    # 自定义主题使用 dark.qss 作为基础模板
                    if self.current_theme == Theme.CUSTOM:
                        qss_file = "themes/dark.qss"
                    else:
                        qss_file = f"themes/{self.current_theme.value}.qss"
                
                style = self.style_loader.load_stylesheet(qss_file)
                
                # 如果QSS文件不存在，回退到内联样式
                if not style:
                    logger.warning(f"QSS文件 {qss_file} 不存在，使用内联样式")
                    style = self._get_inline_style(component)
            
            # 替换主题变量
            style = self._replace_variables(style)
            
            widget.setStyleSheet(style)
            
            logger.debug(f"成功应用主题到 {widget.objectName() or widget.__class__.__name__}")
            
        except Exception as e:
            logger.error(f"应用主题失败: {e}", exc_info=True)
    
    def _replace_variables(self, style: str) -> str:
        """替换样式中的变量
        
        支持格式: ${variable_name}
        
        Args:
            style: 原始样式字符串
            
        Returns:
            str: 替换后的样式字符串
        """
        import re
        
        # 替换 ${variable_name} 格式的变量
        def replacer(match):
            var_name = match.group(1)
            return self.get_variable(var_name)
        
        return re.sub(r'\$\{(\w+)\}', replacer, style)
    
    def _get_inline_style(self, component: Optional[str] = None) -> str:
        """获取内联样式作为回退
        
        Args:
            component: 组件类型
            
        Returns:
            str: 内联样式字符串
        """
        if component == "buttons":
            return f"""
                QPushButton {{
                    background-color: {self.get_variable('bg_secondary')};
                    color: {self.get_variable('text_primary')};
                    border: 1px solid {self.get_variable('border')};
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background-color: {self.get_variable('bg_hover')};
                    border-color: {self.get_variable('accent')};
                }}
                QPushButton:pressed {{
                    background-color: {self.get_variable('bg_pressed')};
                }}
            """
        
        elif component == "scrollbars":
            return f"""
                QScrollBar:vertical {{
                    background: {self.get_variable('bg_secondary')};
                    width: 15px;
                    border-radius: 4px;
                }}
                QScrollBar::handle:vertical {{
                    background: {self.get_variable('bg_tertiary')};
                    border-radius: 4px;
                    min-height: 20px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background: {self.get_variable('bg_hover')};
                }}
            """
        
        # 默认全局样式
        return f"""
            QWidget {{
                background-color: {self.get_variable('bg_primary')};
                color: {self.get_variable('text_primary')};
            }}
        """
    
    def apply_to_application(self, app: QApplication):
        """为整个应用程序应用主题
        
        Args:
            app: QApplication 实例
            
        Example:
            app = QApplication(sys.argv)
            theme_manager.apply_to_application(app)
        """
        try:
            # 自定义主题使用 dark.qss 作为基础模板
            if self.current_theme == Theme.CUSTOM:
                qss_file = "themes/dark.qss"
            else:
                qss_file = f"themes/{self.current_theme.value}.qss"
            
            style = self.style_loader.load_stylesheet(qss_file)
            
            if not style:
                # 回退到基本样式
                style = self._get_inline_style()
            
            # 替换变量
            style = self._replace_variables(style)
            
            app.setStyleSheet(style)
            
            logger.info("成功应用主题到应用程序")
            
        except Exception as e:
            logger.error(f"应用应用程序主题失败: {e}", exc_info=True)
    
    def get_all_variables(self) -> Dict[str, str]:
        """获取所有主题变量
        
        Returns:
            Dict[str, str]: 变量字典
        """
        return self._theme_variables.copy()
    
    def get_custom_themes(self) -> Dict[str, Dict[str, str]]:
        """获取所有已导入的自定义主题
        
        Returns:
            Dict[str, Dict[str, str]]: 主题名称 -> 主题变量字典
        """
        return self._custom_themes.copy()
    
    def get_custom_theme_names(self) -> list:
        """获取所有自定义主题的名称列表
        
        Returns:
            list: 主题名称列表
        """
        return list(self._custom_themes.keys())
    
    def set_custom_theme_by_name(self, theme_name: str):
        """按名称切换到指定的自定义主题
        
        Args:
            theme_name: 自定义主题名称
            
        Raises:
            ValueError: 如果主题名称不存在
        """
        if theme_name not in self._custom_themes:
            raise ValueError(f"自定义主题 '{theme_name}' 不存在")
        
        # 设置为自定义主题模式
        self.current_theme = Theme.CUSTOM
        self.current_custom_theme_name = theme_name
        
        self._custom_variables = self._custom_themes[theme_name].copy()
        self._load_theme_variables()
        
        logger.info(f"已切换到自定义主题: {theme_name}")
    
    def _get_config_path(self) -> Path:
        """获取自定义主题配置文件路径
        
        Returns:
            Path: 配置文件路径
        """
        from PyQt6.QtCore import QStandardPaths
        
        # 使用 AppData/Roaming/ue_toolkit 作为配置目录
        app_data = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        config_dir = Path(app_data) / "ue_toolkit"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "custom_themes.json"
    
    def _save_custom_themes(self):
        """保存所有自定义主题到配置文件"""
        try:
            config_path = self._get_config_path()
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self._custom_themes, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"已保存 {len(self._custom_themes)} 个自定义主题到配置文件")
            
        except Exception as e:
            logger.error(f"保存自定义主题失败: {e}", exc_info=True)
    
    def _load_custom_themes(self):
        """从配置文件加载所有自定义主题"""
        try:
            config_path = self._get_config_path()
            
            if not config_path.exists():
                logger.debug("自定义主题配置文件不存在，跳过加载")
                return
            
            with open(config_path, 'r', encoding='utf-8') as f:
                self._custom_themes = json.load(f)
            
            logger.info(f"已加载 {len(self._custom_themes)} 个自定义主题")
            
        except Exception as e:
            logger.error(f"加载自定义主题失败: {e}", exc_info=True)
            self._custom_themes = {}
    
    def export_theme(self, output_path: Path):
        """导出当前主题到JSON文件
        
        Args:
            output_path: 输出文件路径
        """
        try:
            theme_data = {
                'name': self.current_theme.value,
                'variables': self._theme_variables
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(theme_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"主题导出成功: {output_path}")
            
        except Exception as e:
            logger.error(f"导出主题失败: {e}", exc_info=True)
    
    def import_theme(self, theme_path: Path) -> str:
        """从JSON文件导入主题并保存到自定义主题列表
        
        Args:
            theme_path: 主题文件路径
            
        Returns:
            str: 导入的主题名称
            
        Raises:
            ValueError: 如果主题文件格式不正确
        """
        try:
            with open(theme_path, 'r', encoding='utf-8') as f:
                theme_data = json.load(f)
            
            theme_name = theme_data.get('name')
            if not theme_name:
                raise ValueError("主题文件缺少'name'字段")
            
            variables = theme_data.get('variables', {})
            if not variables:
                raise ValueError("主题文件缺少'variables'字段")
            
            self._custom_themes[theme_name] = variables.copy()
            
            self._save_custom_themes()
            
            logger.info(f"主题导入成功: {theme_name} (来自 {theme_path})")
            
            return theme_name
            
        except Exception as e:
            logger.error(f"导入主题失败: {e}", exc_info=True)
            raise


# 全局实例
_global_theme_manager: Optional[ThemeManager] = None


def get_theme_manager() -> ThemeManager:
    """获取全局主题管理器实例
    
    Returns:
        ThemeManager: 全局主题管理器
    """
    global _global_theme_manager
    if _global_theme_manager is None:
        _global_theme_manager = ThemeManager()
    return _global_theme_manager

