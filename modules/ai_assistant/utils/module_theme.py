# -*- coding: utf-8 -*-

"""
模块主题适配器
为不同模块提供主题值覆盖机制

使用场景：
- 某些模块需要独立的颜色体系（如 asset_manager）
- 可选地覆盖全局主题变量，不影响其他模块

注意：本系统仅提供骨架，暂未在 asset_manager 中接入
"""

import logging
import json
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def get_theme_value(
    module: str,
    key: str,
    *,
    fallback: str,
    theme_manager=None
) -> str:
    """
    获取模块特定的主题值
    
    查找顺序：
    1. resources/themes/module_overrides/{module}.json  # 模块覆盖值
    2. theme_manager.get_variable(key)                  # 全局主题变量
    3. fallback                                         # 回退值
    
    Args:
        module: 模块名称（如 "asset_manager", "config_tool"）
        key: 主题变量名（如 "bg_secondary", "border_hover"）
        fallback: 回退值（获取失败时使用）
        theme_manager: 主题管理器实例（可选）
        
    Returns:
        str: 主题值（颜色代码或其他CSS值）
        
    Examples:
        >>> from core.utils.theme_manager import get_theme_manager
        >>> tm = get_theme_manager()
        >>> 
        >>> # 获取asset_manager的背景色（优先使用模块覆盖值）
        >>> bg_color = get_theme_value(
        ...     "asset_manager",
        ...     "bg_secondary",
        ...     fallback="#1e1e1e",
        ...     theme_manager=tm
        ... )
        >>> # 如果存在 module_overrides/asset_manager.json
        >>> # 且包含 {"bg_secondary": "#1a1a1a"}
        >>> # 则返回 "#1a1a1a"
        >>> # 否则返回 theme_manager 的值或 fallback
    """
    try:
        # 1. 尝试从模块覆盖文件加载
        override_value = _load_module_override(module, key)
        if override_value is not None:
            logger.debug(f"[ModuleTheme] {module}.{key} = {override_value} (来自模块覆盖)")
            return override_value
        
        # 2. 尝试从 theme_manager 获取
        if theme_manager and hasattr(theme_manager, 'get_variable'):
            try:
                global_value = theme_manager.get_variable(key)
                if global_value:
                    logger.debug(f"[ModuleTheme] {module}.{key} = {global_value} (来自全局主题)")
                    return global_value
            except Exception as e:
                logger.warning(f"[ModuleTheme] 从 theme_manager 获取 {key} 失败: {e}")
        
        # 3. 使用回退值
        logger.debug(f"[ModuleTheme] {module}.{key} = {fallback} (使用回退值)")
        return fallback
        
    except Exception as e:
        logger.error(f"[ModuleTheme] 获取主题值失败 ({module}.{key}): {e}", exc_info=True)
        return fallback


def _load_module_override(module: str, key: str) -> Optional[str]:
    """
    从模块覆盖文件加载值
    
    文件路径: resources/themes/module_overrides/{module}.json
    
    Args:
        module: 模块名称
        key: 变量名
        
    Returns:
        Optional[str]: 覆盖值，如果不存在返回 None
    """
    try:
        # 获取项目根目录
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent.parent
        
        # 覆盖文件路径
        override_file = project_root / "resources" / "themes" / "module_overrides" / f"{module}.json"
        
        if not override_file.exists():
            logger.debug(f"[ModuleTheme] 模块覆盖文件不存在: {override_file}")
            return None
        
        # 读取JSON文件
        with open(override_file, 'r', encoding='utf-8') as f:
            overrides = json.load(f)
        
        # 返回指定key的值
        if key in overrides:
            return overrides[key]
        
        logger.debug(f"[ModuleTheme] 模块覆盖文件中无 {key} 定义")
        return None
        
    except json.JSONDecodeError as e:
        logger.error(f"[ModuleTheme] 模块覆盖文件JSON格式错误 ({module}.json): {e}")
        return None
    except Exception as e:
        logger.error(f"[ModuleTheme] 加载模块覆盖失败 ({module}.{key}): {e}")
        return None


def create_module_override_template(module: str) -> bool:
    """
    为指定模块创建覆盖模板文件
    
    Args:
        module: 模块名称
        
    Returns:
        bool: 是否成功创建
        
    Examples:
        >>> # 为 asset_manager 创建模板
        >>> create_module_override_template("asset_manager")
        ✅ 模块覆盖模板已创建: resources/themes/module_overrides/asset_manager.json
    """
    try:
        # 获取项目根目录
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent.parent
        
        # 创建目录
        override_dir = project_root / "resources" / "themes" / "module_overrides"
        override_dir.mkdir(parents=True, exist_ok=True)
        
        # 覆盖文件路径
        override_file = override_dir / f"{module}.json"
        
        if override_file.exists():
            logger.warning(f"[ModuleTheme] 模块覆盖文件已存在: {override_file}")
            return False
        
        # 创建模板内容
        template = {
            "_comment": f"模块 {module} 的主题覆盖值",
            "_usage": "在此定义模块特定的颜色值，覆盖全局主题",
            "_example_bg_secondary": "#1e1e1e",
            "_example_border_hover": "#505050"
        }
        
        # 写入文件
        with open(override_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 模块覆盖模板已创建: {override_file}")
        return True
        
    except Exception as e:
        logger.error(f"[ModuleTheme] 创建模块覆盖模板失败 ({module}): {e}", exc_info=True)
        return False


# 便捷函数：直接获取颜色值（最常用）
def get_color(
    module: str,
    color_key: str,
    fallback: str,
    theme_manager=None
) -> str:
    """
    便捷函数：获取颜色值
    
    与 get_theme_value 功能相同，仅为了语义更清晰
    
    Args:
        module: 模块名称
        color_key: 颜色变量名
        fallback: 回退颜色值
        theme_manager: 主题管理器
        
    Returns:
        str: 颜色值
    """
    return get_theme_value(module, color_key, fallback=fallback, theme_manager=theme_manager)


# 导出
__all__ = [
    'get_theme_value',
    'get_color',
    'create_module_override_template',
]

