"""
工具状态显示组件
用于在 AI 调用工具时显示友好的工具名称

设计要求：
1. 将工具名称转换为用户友好的中文描述
2. 保持原有的所有动画效果（圆点旋转、文字渐变）
3. 支持动态更新显示文字
"""

from typing import Dict


class ToolStatusDisplay:
    """工具状态显示管理器
    
    职责：
    1. 维护工具名称映射表（英文 -> 中文）
    2. 提供友好的工具名称转换
    3. 生成工具调用状态文本
    """
    
    # 工具名称映射字典（英文 -> 中文）
    TOOL_NAME_MAP: Dict[str, str] = {
        # 只读工具
        "search_assets": "搜索资产",
        "query_asset_detail": "查询资产详情",
        "search_configs": "搜索配置",
        "diff_config": "对比配置",
        "search_logs": "搜索日志",
        "search_docs": "搜索文档",
        
        # 实验性工具
        "import_asset_to_ue": "导入资产",
        "list_importable_assets": "列出可导入资产",
        "generate_and_apply_theme": "生成主题",
        "confirm_theme": "确认主题",
        "reject_theme": "拒绝主题",
        "list_themes": "列出主题",
        
        # 受控工具
        "export_config_template": "导出配置模板",
        "batch_rename_preview": "批量重命名预览",
        
        # UE 蓝图工具（只读模式）
        "get_current_blueprint_summary": "读取蓝图",
        # 注意：apply_blueprint_changes 已弃用（只读模式）
    }
    
    @staticmethod
    def get_friendly_name(tool_name: str) -> str:
        """获取工具的友好名称（中文）
        
        Args:
            tool_name: 工具名称（英文，如 "search_assets"）
            
        Returns:
            str: 友好的中文名称（如 "搜索资产"），如果未找到则返回原名称
        """
        return ToolStatusDisplay.TOOL_NAME_MAP.get(tool_name, tool_name)
    
    @staticmethod
    def show_tool_calling(tool_name: str) -> str:
        """生成工具调用状态文本
        
        Args:
            tool_name: 工具名称（英文，如 "search_assets"）
            
        Returns:
            str: 工具调用状态文本（如 "调用搜索资产工具"）
        """
        friendly_name = ToolStatusDisplay.get_friendly_name(tool_name)
        return f"调用{friendly_name}工具"
    
    @staticmethod
    def show_thinking() -> str:
        """生成思考状态文本
        
        Returns:
            str: 思考状态文本（"正在思考"）
        """
        return "正在思考"


# 为了向后兼容，导出 TOOL_NAME_MAP
TOOL_NAME_MAP = ToolStatusDisplay.TOOL_NAME_MAP

