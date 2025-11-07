# -*- coding: utf-8 -*-

"""
主题生成器（测试功能）
AI可以根据用户需求生成自定义主题
"""

import json
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from core.logger import get_logger
from core.utils.theme_manager import get_theme_manager

logger = get_logger(__name__)


class ThemeGenerator:
    """主题生成器（测试版本）"""
    
    def __init__(self):
        """初始化主题生成器"""
        self.theme_manager = get_theme_manager()
        self.logger = logger
        self.temp_theme_path: Optional[Path] = None
        self.last_generated_theme_name: Optional[str] = None
    
    def generate_and_apply_theme(self, theme_name: str, theme_description: str, color_variables: Dict[str, str]) -> Dict[str, Any]:
        """生成并立即应用主题
        
        Args:
            theme_name: 主题名称
            theme_description: 主题描述（用于向用户说明）
            color_variables: 颜色变量字典，格式如：
                {
                    "bg_primary": "#1a1a2e",
                    "text_primary": "#ffffff",
                    ...
                }
        
        Returns:
            Dict: {
                'success': bool,
                'message': str,
                'theme_name': str,
                'preview_message': str  # 用于向用户展示的预览信息
            }
        """
        try:
            # 验证必需的变量
            required_vars = [
                'bg_primary', 'bg_secondary', 'text_primary', 'text_secondary',
                'accent', 'border'
            ]
            
            missing_vars = [var for var in required_vars if var not in color_variables]
            if missing_vars:
                return {
                    'success': False,
                    'message': f'[错误] 缺少必需的颜色变量: {", ".join(missing_vars)}',
                    'theme_name': theme_name
                }
            
            # 自动补全缺失的字段（使用基于主色的智能推导）
            color_variables = self._complete_theme_variables(color_variables)
            
            # 创建临时主题文件
            temp_dir = Path(tempfile.gettempdir())
            self.temp_theme_path = temp_dir / f"ue_toolkit_temp_theme_{theme_name}.json"
            
            theme_data = {
                "name": theme_name,
                "variables": color_variables
            }
            
            # 保存到临时文件
            with open(self.temp_theme_path, 'w', encoding='utf-8') as f:
                json.dump(theme_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"生成临时主题文件: {self.temp_theme_path}")
            
            # 导入并应用主题
            try:
                imported_name = self.theme_manager.import_theme(self.temp_theme_path)
                self.last_generated_theme_name = imported_name
                
                # 立即切换到新主题
                self.theme_manager.set_custom_theme_by_name(imported_name)
                
                # 完整刷新应用程序主题（带完整异常保护）
                self._apply_theme_to_all_windows()
                
                # 生成预览信息
                preview_info = self._generate_preview_message(theme_name, theme_description, color_variables)
                
                return {
                    'success': True,
                    'message': f'[成功] 主题 "{theme_name}" 已生成并应用！',
                    'theme_name': imported_name,
                    'preview_message': preview_info,
                    'awaiting_feedback': True
                }
            
            except Exception as e:
                self.logger.error(f"导入或应用主题失败: {e}", exc_info=True)
                return {
                    'success': False,
                    'message': f'[错误] 应用主题失败: {str(e)}',
                    'theme_name': theme_name
                }
        
        except Exception as e:
            self.logger.error(f"生成主题失败: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'[错误] 生成主题时出错: {str(e)}',
                'theme_name': theme_name
            }
    
    def confirm_theme(self) -> Dict[str, Any]:
        """用户确认保留当前生成的主题
        
        Returns:
            Dict: {
                'success': bool,
                'message': str
            }
        """
        try:
            if not self.last_generated_theme_name:
                return {
                    'success': False,
                    'message': '[提示] 当前没有待确认的主题'
                }
            
            theme_name = self.last_generated_theme_name
            
            # 清理临时文件
            if self.temp_theme_path and self.temp_theme_path.exists():
                self.temp_theme_path.unlink()
                self.logger.info(f"已清理临时主题文件: {self.temp_theme_path}")
            
            # 重置状态
            self.temp_theme_path = None
            self.last_generated_theme_name = None
            
            return {
                'success': True,
                'message': f'[成功] 主题 "{theme_name}" 已保留并应用！\n\n你可以随时在设置中切换回其他主题。'
            }
        
        except Exception as e:
            self.logger.error(f"确认主题失败: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'[错误] 确认主题时出错: {str(e)}'
            }
    
    def reject_theme(self) -> Dict[str, Any]:
        """用户拒绝当前生成的主题，删除并恢复默认主题
        
        Returns:
            Dict: {
                'success': bool,
                'message': str
            }
        """
        try:
            if not self.last_generated_theme_name:
                return {
                    'success': False,
                    'message': '[提示] 当前没有待删除的主题'
                }
            
            theme_name = self.last_generated_theme_name
            
            # 切换回深色主题
            from core.utils.theme_manager import Theme
            self.theme_manager.set_theme(Theme.DARK)
            self.logger.info("已切换回深色主题")
            
            # 完整刷新应用程序主题
            self._apply_theme_to_all_windows()
            
            # 删除生成的主题
            self.theme_manager.delete_custom_theme(theme_name)
            self.logger.info(f"已删除主题: {theme_name}")
            
            # 清理临时文件
            if self.temp_theme_path and self.temp_theme_path.exists():
                self.temp_theme_path.unlink()
                self.logger.info(f"已清理临时主题文件: {self.temp_theme_path}")
            
            # 重置状态
            self.temp_theme_path = None
            self.last_generated_theme_name = None
            
            return {
                'success': True,
                'message': f'[成功] 已删除主题 "{theme_name}" 并恢复为深色主题。\n\n如需调整，请告诉我你想要什么样的配色！'
            }
        
        except Exception as e:
            self.logger.error(f"删除主题失败: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'[错误] 删除主题时出错: {str(e)}'
            }
    
    def _complete_theme_variables(self, variables: Dict[str, str]) -> Dict[str, str]:
        """自动补全缺失的主题变量
        
        基于提供的基础颜色智能推导其他颜色
        """
        completed = variables.copy()
        
        # 定义所有必需的变量及其默认推导逻辑
        bg_primary = variables.get('bg_primary', '#2b2b2b')
        bg_secondary = variables.get('bg_secondary', '#1e1e1e')
        text_primary = variables.get('text_primary', '#ffffff')
        text_secondary = variables.get('text_secondary', '#b0b0b0')
        accent = variables.get('accent', '#4CAF50')
        border = variables.get('border', '#3d3d3d')
        
        # 背景色系列
        if 'bg_tertiary' not in completed:
            completed['bg_tertiary'] = self._adjust_brightness(bg_primary, 1.15)
        if 'bg_hover' not in completed:
            completed['bg_hover'] = self._adjust_brightness(bg_primary, 1.3)
        if 'bg_pressed' not in completed:
            completed['bg_pressed'] = self._adjust_brightness(bg_secondary, 1.2)
        if 'bg_primary_alpha' not in completed:
            rgb = self._hex_to_rgb(bg_primary)
            completed['bg_primary_alpha'] = f'rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.9)'
        if 'bg_secondary_alpha' not in completed:
            rgb = self._hex_to_rgb(bg_secondary)
            completed['bg_secondary_alpha'] = f'rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.85)'
        
        # 文本色系列
        if 'text_tertiary' not in completed:
            completed['text_tertiary'] = self._adjust_brightness(text_secondary, 0.8)
        if 'text_disabled' not in completed:
            completed['text_disabled'] = self._adjust_brightness(text_secondary, 0.6)
        
        # 强调色系列
        if 'accent_hover' not in completed:
            completed['accent_hover'] = self._adjust_brightness(accent, 1.2)
        if 'accent_pressed' not in completed:
            completed['accent_pressed'] = self._adjust_brightness(accent, 0.8)
        if 'accent_alpha' not in completed:
            rgb = self._hex_to_rgb(accent)
            completed['accent_alpha'] = f'rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.8)'
        
        # 边框色系列
        if 'border_hover' not in completed:
            completed['border_hover'] = accent
        if 'border_focus' not in completed:
            completed['border_focus'] = completed.get('accent_hover', accent)
        
        # 状态色（使用通用默认值）
        if 'success' not in completed:
            completed['success'] = '#66BB6A'
        if 'warning' not in completed:
            completed['warning'] = '#FFB74D'
        if 'error' not in completed:
            completed['error'] = '#EF5350'
        if 'info' not in completed:
            completed['info'] = '#42A5F5'
        if 'danger' not in completed:
            completed['danger'] = completed.get('error', '#EF5350')
        if 'danger_hover' not in completed:
            completed['danger_hover'] = self._adjust_brightness(completed['danger'], 1.1)
        
        # 按钮色系列
        if 'button_bg' not in completed:
            completed['button_bg'] = completed.get('bg_tertiary', bg_primary)
        if 'button_text' not in completed:
            completed['button_text'] = text_primary
        if 'button_hover' not in completed:
            completed['button_hover'] = completed.get('bg_hover', bg_primary)
        if 'button_pressed' not in completed:
            completed['button_pressed'] = completed.get('bg_pressed', bg_secondary)
        
        # 滚动条色系列
        if 'scrollbar_track' not in completed:
            completed['scrollbar_track'] = self._adjust_brightness(bg_secondary, 0.8)
        if 'scrollbar_handle' not in completed:
            completed['scrollbar_handle'] = self._adjust_brightness(bg_primary, 1.5)
        if 'scrollbar_handle_hover' not in completed:
            completed['scrollbar_handle_hover'] = self._adjust_brightness(completed['scrollbar_handle'], 1.2)
        if 'scrollbar_handle_pressed' not in completed:
            completed['scrollbar_handle_pressed'] = self._adjust_brightness(completed['scrollbar_handle'], 1.4)
        
        return completed
    
    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """将十六进制颜色转换为RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _rgb_to_hex(self, r: int, g: int, b: int) -> str:
        """将RGB颜色转换为十六进制"""
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def _adjust_brightness(self, hex_color: str, factor: float) -> str:
        """调整颜色亮度
        
        Args:
            hex_color: 十六进制颜色
            factor: 亮度因子（>1变亮，<1变暗）
        """
        r, g, b = self._hex_to_rgb(hex_color)
        
        # 调整亮度
        r = max(0, min(255, int(r * factor)))
        g = max(0, min(255, int(g * factor)))
        b = max(0, min(255, int(b * factor)))
        
        return self._rgb_to_hex(r, g, b)
    
    def _generate_preview_message(self, theme_name: str, description: str, variables: Dict[str, str]) -> str:
        """生成主题预览信息"""
        preview = [
            f"主题预览: {theme_name}",
            f"说明: {description}",
            "",
            "主要配色:",
            f"  - 主背景: {variables.get('bg_primary', '未设置')}",
            f"  - 次级背景: {variables.get('bg_secondary', '未设置')}",
            f"  - 主文本: {variables.get('text_primary', '未设置')}",
            f"  - 次级文本: {variables.get('text_secondary', '未设置')}",
            f"  - 强调色: {variables.get('accent', '未设置')}",
            f"  - 边框: {variables.get('border', '未设置')}",
            "",
            "主题已自动应用！",
            "",
            "提示: 如果聊天界面文字颜色未更新，请切换到其他功能（如资产管理器）再切回来，即可看到完整效果。",
            "",
            "满意吗？"
        ]
        
        return "\n".join(preview)
    
    def _apply_theme_to_all_windows(self):
        """应用主题到所有窗口（极简安全版本）
        
        只应用全局样式，避免在对话过程中刷新模块导致崩溃
        """
        try:
            # 1. 应用到整个QApplication（全局样式）
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if not app:
                self.logger.warning("无法获取QApplication实例")
                return
            
            self.theme_manager.apply_to_application(app)
            self.logger.info("✅ 主题已应用到全局样式")
            
            # 2. 找到主窗口并刷新设置界面的下拉框
            main_window = None
            try:
                for widget in app.topLevelWidgets():
                    if widget.__class__.__name__ == 'MainWindow' or \
                       hasattr(widget, 'module_provider'):
                        main_window = widget
                        break
            except Exception as e:
                self.logger.warning(f"查找主窗口时出错: {e}")
            
            if main_window:
                # 刷新设置界面的主题下拉框
                try:
                    if hasattr(main_window, 'settings_widget') and main_window.settings_widget:
                        if hasattr(main_window.settings_widget, '_refresh_custom_themes_combo'):
                            main_window.settings_widget._refresh_custom_themes_combo()
                            self.logger.info("✅ 已刷新设置界面的主题下拉框")
                except Exception as e:
                    self.logger.warning(f"刷新主题下拉框失败: {e}")
            
            # 3. 强制刷新主窗口样式（如果找到了）
            if main_window:
                try:
                    # 对主窗口重新应用主题
                    self.theme_manager.apply_to_widget(main_window)
                    main_window.update()
                    self.logger.info("✅ 已刷新主窗口样式")
                except Exception as e:
                    self.logger.warning(f"刷新主窗口样式失败: {e}")
            
            # 4. 提示用户可能需要切换界面才能看到完整效果
            self.logger.info("💡 提示：切换到其他界面再切回来可查看完整主题效果")
            
        except Exception as e:
            self.logger.error(f"应用主题失败: {e}", exc_info=True)
            # 即使出错也不要让程序崩溃
    
    def list_available_themes(self) -> str:
        """列出所有可用的主题（内置+自定义）"""
        try:
            from core.utils.theme_manager import Theme
            
            builtin_themes = ["深色主题 (dark)", "浅色主题 (light)"]
            custom_themes = self.theme_manager.get_custom_theme_names()
            
            result = ["可用主题列表:\n", "内置主题:"]
            for theme in builtin_themes:
                result.append(f"  - {theme}")
            
            if custom_themes:
                result.append("\n自定义主题:")
                for theme in custom_themes:
                    result.append(f"  - {theme}")
            else:
                result.append("\n暂无自定义主题")
            
            return "\n".join(result)
        
        except Exception as e:
            self.logger.error(f"列出主题失败: {e}", exc_info=True)
            return f"[错误] 获取主题列表时出错: {str(e)}"

