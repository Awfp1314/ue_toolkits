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
                self.theme_manager.set_custom_theme(imported_name)
                
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
            "主题已自动应用，请查看界面效果。",
            "满意吗？"
        ]
        
        return "\n".join(preview)
    
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

