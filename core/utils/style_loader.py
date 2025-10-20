# -*- coding: utf-8 -*-

"""
样式加载器 - 负责加载和管理QSS样式文件

这个模块提供了一个集中式的样式管理系统，用于：
1. 从QSS文件加载样式
2. 缓存已加载的样式
3. 为控件应用样式类
4. 提供样式热重载功能（开发模式）

使用示例:
    style_loader = StyleLoader()
    button_style = style_loader.load_stylesheet("components/buttons.qss")
    button.setStyleSheet(button_style)
    
    # 使用CSS类
    StyleLoader.set_property_class(button, "primary-button")
    
    style_loader.apply_component_style(button, "buttons", use_cache=True)
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Set
from PyQt6.QtWidgets import QWidget

# 使用标准logging避免循环导入
logger = logging.getLogger(__name__)


class StyleLoader:
    """
    样式加载器类
    
    使用单例模式确保全局只有一个样式加载器实例。
    提供样式文件加载、缓存管理和样式应用功能。
    """
    
    _instance: Optional['StyleLoader'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'StyleLoader':
        """单例模式 - 确保只有一个实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化样式加载器"""
        # 避免重复初始化
        if StyleLoader._initialized:
            return
        
        # 样式缓存字典 {文件路径: 样式内容}
        self._styles_cache: Dict[str, str] = {}
        
        # 已加载的样式文件集合
        self._loaded_files: Set[str] = set()
        
        # QSS文件根目录
        self._qss_root = Path(__file__).parent.parent.parent / "resources" / "qss"
        
        # 默认内联样式（用于回退）
        self._default_styles: Dict[str, str] = {
            'button_primary': """
                QPushButton {
                    background-color: rgba(0, 122, 204, 0.8);
                    color: white;
                    border: none;
                    padding: 4px 8px;
                    border-radius: 2px;
                }
                QPushButton:hover {
                    background-color: rgba(0, 144, 224, 0.9);
                }
            """,
            'button_secondary': """
                QPushButton {
                    background-color: rgba(68, 68, 68, 0.8);
                    color: white;
                    border: none;
                    padding: 4px 8px;
                    border-radius: 2px;
                }
                QPushButton:hover {
                    background-color: rgba(85, 85, 85, 0.9);
                }
            """,
            'scrollbar': """
                QScrollBar:vertical {
                    background: rgba(43, 43, 43, 0.8);
                    width: 15px;
                    border-radius: 4px;
                }
                QScrollBar::handle:vertical {
                    background: rgba(68, 68, 68, 0.8);
                    border-radius: 4px;
                }
                QScrollBar::handle:vertical:hover {
                    background: rgba(85, 85, 85, 0.9);
                }
            """,
        }
        
        StyleLoader._initialized = True
        logger.info(f"样式加载器初始化完成，QSS根目录: {self._qss_root}")
    
    def load_stylesheet(self, style_file: str, use_cache: bool = True) -> str:
        """
        从QSS文件加载样式表
        
        Args:
            style_file: QSS文件路径（相对于resources/qss/目录）
                       例如: "components/buttons.qss" 或 "sidebar.qss"
            use_cache: 是否使用缓存（默认True）
        
        Returns:
            str: QSS样式内容，如果加载失败返回空字符串
        
        Examples:
            >>> loader = StyleLoader()
            >>> style = loader.load_stylesheet("components/buttons.qss")
            >>> widget.setStyleSheet(style)
        """
        try:
            if use_cache and style_file in self._styles_cache:
                logger.debug(f"从缓存加载样式: {style_file}")
                return self._styles_cache[style_file]
            
            # 构建完整文件路径
            full_path = self._qss_root / style_file
            
            if not full_path.exists():
                logger.warning(f"QSS文件不存在: {full_path}")
                return ""
            
            # 读取文件内容
            with open(full_path, 'r', encoding='utf-8') as f:
                style_content = f.read()
            
            # 缓存样式
            if use_cache:
                self._styles_cache[style_file] = style_content
                self._loaded_files.add(style_file)
            
            logger.info(f"成功加载样式文件: {style_file}")
            return style_content
            
        except Exception as e:
            logger.error(f"加载样式文件失败: {style_file}, 错误: {e}", exc_info=True)
            return ""
    
    def apply_component_style(
        self, 
        widget: QWidget, 
        component_name: str, 
        use_cache: bool = True,
        fallback_to_default: bool = True
    ) -> bool:
        """
        为组件应用样式
        
        Args:
            widget: 要应用样式的控件
            component_name: 组件名称（不含.qss后缀），例如 "buttons", "scrollbars"
            use_cache: 是否使用缓存
            fallback_to_default: 加载失败时是否回退到默认样式
        
        Returns:
            bool: 是否成功应用样式
        
        Examples:
            >>> loader = StyleLoader()
            >>> loader.apply_component_style(button, "buttons")
        """
        try:
            # 尝试从QSS文件加载
            style = self.load_stylesheet(f"components/{component_name}.qss", use_cache)
            
            if style:
                widget.setStyleSheet(style)
                logger.debug(f"成功为 {widget.objectName() or '控件'} 应用 {component_name} 样式")
                return True
            
            # 如果加载失败且允许回退
            if fallback_to_default:
                default_key = component_name.replace('s', '_').replace('-', '_')  # buttons -> button_
                default_style = self._default_styles.get(default_key, '')
                
                if default_style:
                    widget.setStyleSheet(default_style)
                    logger.warning(f"QSS加载失败，为 {widget.objectName() or '控件'} 使用默认 {component_name} 样式")
                    return True
                else:
                    logger.error(f"无法为 {widget.objectName() or '控件'} 应用 {component_name} 样式：文件不存在且无默认样式")
            
            return False
            
        except Exception as e:
            logger.error(f"应用组件样式失败: {component_name}, 错误: {e}", exc_info=True)
            return False
    
    @staticmethod
    def set_property_class(widget: QWidget, class_name: str) -> None:
        """
        为控件设置CSS类属性
        
        这个方法用于实现CSS类选择器功能。设置后可以在QSS中使用属性选择器：
        [class="primary-button"] { ... }
        
        Args:
            widget: 要设置属性的控件
            class_name: CSS类名
        
        Examples:
            >>> StyleLoader.set_property_class(button, "primary-button")
            >>> # 在QSS中: QPushButton[class="primary-button"] { ... }
        """
        try:
            widget.setProperty("class", class_name)
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            logger.debug(f"为控件 {widget.objectName() or '未命名'} 设置CSS类: {class_name}")
        except Exception as e:
            logger.error(f"设置CSS类失败: {class_name}, 错误: {e}")
    
    @staticmethod
    def set_property_state(widget: QWidget, state: str) -> None:
        """
        为控件设置状态属性
        
        用于动态样式切换，例如错误状态、禁用状态等。
        可以在QSS中使用: [state="error"] { ... }
        
        Args:
            widget: 要设置属性的控件
            state: 状态名称（例如: "normal", "error", "warning", "disabled"）
        
        Examples:
            >>> StyleLoader.set_property_state(button, "error")
            >>> # 在QSS中: QPushButton[state="error"] { ... }
        """
        try:
            widget.setProperty("state", state)
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            logger.debug(f"为控件 {widget.objectName() or '未命名'} 设置状态: {state}")
        except Exception as e:
            logger.error(f"设置状态失败: {state}, 错误: {e}")
    
    def reload_stylesheet(self, style_file: str) -> str:
        """
        重新加载样式文件（忽略缓存）
        
        主要用于开发调试，可以在不重启程序的情况下看到样式变化。
        
        Args:
            style_file: QSS文件路径
        
        Returns:
            str: 重新加载的样式内容
        """
        # 清除缓存
        if style_file in self._styles_cache:
            del self._styles_cache[style_file]
        
        logger.info(f"重新加载样式文件: {style_file}")
        return self.load_stylesheet(style_file, use_cache=False)
    
    def reload_all_styles(self) -> int:
        """
        重新加载所有已加载的样式文件
        
        用于开发模式下的样式热重载。
        
        Returns:
            int: 成功重新加载的样式文件数量
        """
        logger.info("开始重新加载所有样式文件")
        reload_count = 0
        
        # 复制文件列表以避免迭代时修改
        files_to_reload = list(self._loaded_files)
        
        # 清空缓存
        self._styles_cache.clear()
        
        # 重新加载所有文件
        for style_file in files_to_reload:
            style = self.load_stylesheet(style_file, use_cache=True)
            if style:
                reload_count += 1
        
        logger.info(f"重新加载完成，成功加载 {reload_count}/{len(files_to_reload)} 个样式文件")
        return reload_count
    
    def clear_cache(self) -> None:
        """清空样式缓存"""
        self._styles_cache.clear()
        self._loaded_files.clear()
        logger.info("样式缓存已清空")
    
    def get_loaded_files(self) -> Set[str]:
        """获取已加载的样式文件列表"""
        return self._loaded_files.copy()
    
    def get_qss_root(self) -> Path:
        """获取QSS文件根目录"""
        return self._qss_root
    
    @staticmethod
    def safe_load_style(component_name: str, default_style: str = "") -> str:
        """
        安全地加载样式（静态方法）
        
        提供一个简单的接口用于加载样式，失败时返回默认样式。
        
        Args:
            component_name: 组件名称
            default_style: 默认样式（加载失败时使用）
        
        Returns:
            str: 加载的样式或默认样式
        """
        try:
            loader = StyleLoader()
            style = loader.load_stylesheet(f"components/{component_name}.qss")
            return style if style else default_style
        except Exception as e:
            logger.warning(f"安全加载样式失败: {component_name}, 使用默认样式, 错误: {e}")
            return default_style


# 提供一个全局实例（可选使用）
_global_style_loader: Optional[StyleLoader] = None


def get_style_loader() -> StyleLoader:
    """
    获取全局样式加载器实例
    
    Returns:
        StyleLoader: 全局样式加载器实例
    """
    global _global_style_loader
    if _global_style_loader is None:
        _global_style_loader = StyleLoader()
    return _global_style_loader


# 便捷函数
def load_qss(style_file: str) -> str:
    """
    便捷函数：加载QSS文件
    
    Args:
        style_file: QSS文件路径
    
    Returns:
        str: QSS样式内容
    """
    return get_style_loader().load_stylesheet(style_file)


def apply_style(widget: QWidget, component_name: str) -> bool:
    """
    便捷函数：为控件应用样式
    
    Args:
        widget: 控件
        component_name: 组件名称
    
    Returns:
        bool: 是否成功
    """
    return get_style_loader().apply_component_style(widget, component_name)


def set_class(widget: QWidget, class_name: str) -> None:
    """
    便捷函数：设置CSS类
    
    Args:
        widget: 控件
        class_name: 类名
    """
    StyleLoader.set_property_class(widget, class_name)


def set_state(widget: QWidget, state: str) -> None:
    """
    便捷函数：设置状态
    
    Args:
        widget: 控件
        state: 状态名
    """
    StyleLoader.set_property_state(widget, state)

