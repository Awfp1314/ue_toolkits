# -*- coding: utf-8 -*-

"""
配置读取器
从 config_tool 模块读取虚幻引擎配置信息，供 AI 助手使用
"""

from typing import Optional, List
from core.logger import get_logger

logger = get_logger(__name__)


class ConfigReader:
    """虚幻引擎配置读取器"""
    
    def __init__(self, config_tool_logic=None):
        """初始化配置读取器
        
        Args:
            config_tool_logic: config_tool 模块的逻辑层实例
        """
        self.config_tool_logic = config_tool_logic
        self.logger = logger
    
    def get_all_configs_summary(self) -> str:
        """获取所有配置模板的摘要信息
        
        Returns:
            str: 配置摘要的格式化字符串
        """
        if not self.config_tool_logic:
            return "[WARN] 配置工具未连接，无法读取配置信息。"
        
        try:
            templates = self.config_tool_logic.get_templates()
            
            if not templates:
                return "[CONFIG] 当前没有保存的 UE 配置模板。"
            
            # 生成摘要
            summary_parts = [
                f"[CONFIG] **虚幻引擎配置模板概览**（共 {len(templates)} 个配置）\n"
            ]
            
            for i, template in enumerate(templates, 1):
                name = template.name if hasattr(template, 'name') else '未命名'
                description = template.description if hasattr(template, 'description') else '无描述'
                last_modified = template.last_modified if hasattr(template, 'last_modified') else '未知'
                projects = template.projects if hasattr(template, 'projects') else 0
                
                summary_parts.append(f"\n**{i}. {name}**")
                summary_parts.append(f"  - 描述: {description}")
                summary_parts.append(f"  - 最后修改: {last_modified}")
                summary_parts.append(f"  - 应用项目数: {projects}")
                
                # 添加路径和文件数量信息
                if hasattr(template, 'path') and template.path:
                    from pathlib import Path
                    config_path = Path(template.path)
                    if config_path.exists() and config_path.is_dir():
                        config_files = list(config_path.glob("*.ini"))
                        summary_parts.append(f"  - 配置文件数: {len(config_files)} 个")
                        summary_parts.append(f"  - 路径: {config_path}")
            
            return "\n".join(summary_parts)
        
        except Exception as e:
            self.logger.error(f"读取配置摘要失败: {e}", exc_info=True)
            return f"[ERROR] 读取配置信息时出错: {str(e)}"
    
    def search_configs(self, keyword: str) -> str:
        """搜索配置模板
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            str: 搜索结果的格式化字符串
        """
        if not self.config_tool_logic:
            return "⚠️ 配置工具未连接。"
        
        try:
            templates = self.config_tool_logic.get_templates()
            keyword_lower = keyword.lower()
            
            # 搜索匹配的配置
            matched_configs = []
            for template in templates:
                name = template.name.lower() if hasattr(template, 'name') else ''
                description = template.description.lower() if hasattr(template, 'description') else ''
                
                if keyword_lower in name or keyword_lower in description:
                    matched_configs.append(template)
            
            if not matched_configs:
                return f"[SEARCH] 未找到包含 '{keyword}' 的配置模板。"
            
            # 格式化结果
            results = [f"[SEARCH] 找到 {len(matched_configs)} 个相关配置：\n"]
            
            for template in matched_configs:
                name = template.name if hasattr(template, 'name') else '未命名'
                description = template.description if hasattr(template, 'description') else '无描述'
                last_modified = template.last_modified if hasattr(template, 'last_modified') else '未知'
                
                results.append(f"\n**{name}**")
                results.append(f"  - 描述: {description}")
                results.append(f"  - 最后修改: {last_modified}")
            
            return "\n".join(results)
        
        except Exception as e:
            self.logger.error(f"搜索配置失败: {e}", exc_info=True)
            return f"[ERROR] 搜索配置时出错: {str(e)}"
    
    def get_config_details(self, config_name: str) -> str:
        """获取特定配置的详细信息
        
        Args:
            config_name: 配置名称
            
        Returns:
            str: 配置详情的格式化字符串
        """
        if not self.config_tool_logic:
            return "⚠️ 配置工具未连接。"
        
        try:
            templates = self.config_tool_logic.get_templates()
            
            # 查找配置
            target_config = None
            for template in templates:
                if hasattr(template, 'name') and template.name.lower() == config_name.lower():
                    target_config = template
                    break
            
            if not target_config:
                return f"[ERROR] 未找到名为 '{config_name}' 的配置模板。"
            
            # 格式化详情
            name = target_config.name if hasattr(target_config, 'name') else '未命名'
            description = target_config.description if hasattr(target_config, 'description') else '无描述'
            last_modified = target_config.last_modified if hasattr(target_config, 'last_modified') else '未知'
            projects = target_config.projects if hasattr(target_config, 'projects') else 0
            
            details = [
                f"[CONFIG] **{name}** 配置详情\n",
                f"**描述**: {description}",
                f"**最后修改**: {last_modified}",
                f"**应用项目数**: {projects}",
            ]
            
            # 如果有路径信息，显示路径和文件列表
            if hasattr(target_config, 'path') and target_config.path:
                from pathlib import Path
                config_path = Path(target_config.path)
                details.append(f"\n**配置路径**: {config_path}")
                
                # 列出路径下的所有配置文件
                if config_path.exists() and config_path.is_dir():
                    config_files = list(config_path.glob("*.ini"))
                    if config_files:
                        details.append(f"\n**包含的配置文件** ({len(config_files)} 个):")
                        for config_file in sorted(config_files):
                            file_size = config_file.stat().st_size
                            size_kb = file_size / 1024
                            details.append(f"  - {config_file.name} ({size_kb:.1f} KB)")
                    else:
                        details.append("\n**包含的配置文件**: 无 .ini 文件")
                else:
                    details.append(f"  (路径不存在或不是目录)")
            
            # 如果有配置数据字典，显示配置项
            if hasattr(target_config, 'data') and target_config.data:
                details.append(f"\n**配置数据项**: {len(target_config.data)} 个")
                
                # 显示部分配置键（不显示全部值，避免过长）
                config_keys = list(target_config.data.keys())[:10]
                if config_keys:
                    details.append("\n**主要配置键**:")
                    for key in config_keys:
                        details.append(f"  - {key}")
                    
                    if len(target_config.data) > 10:
                        details.append(f"  ... 还有 {len(target_config.data) - 10} 个配置键")
            
            return "\n".join(details)
        
        except Exception as e:
            self.logger.error(f"获取配置详情失败: {e}", exc_info=True)
            return f"[ERROR] 获取配置详情时出错: {str(e)}"
    
    def get_config_list(self) -> str:
        """获取所有配置名称列表
        
        Returns:
            str: 配置列表的格式化字符串
        """
        if not self.config_tool_logic:
            return "[WARN] 配置工具未连接。"
        
        try:
            templates = self.config_tool_logic.get_templates()
            
            if not templates:
                return "[CONFIG] 当前没有保存的配置模板。"
            
            result = ["[CONFIG] **UE 配置模板列表**:\n"]
            for i, template in enumerate(templates, 1):
                name = template.name if hasattr(template, 'name') else '未命名'
                description = template.description if hasattr(template, 'description') else ''
                
                if description:
                    result.append(f"{i}. **{name}** - {description}")
                else:
                    result.append(f"{i}. **{name}**")
            
            return "\n".join(result)
        
        except Exception as e:
            self.logger.error(f"获取配置列表失败: {e}", exc_info=True)
            return f"[ERROR] 获取配置列表时出错: {str(e)}"

