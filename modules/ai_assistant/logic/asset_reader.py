# -*- coding: utf-8 -*-

"""
资产读取器
从 asset_manager 模块读取资产信息，供 AI 助手使用
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from core.logger import get_logger

logger = get_logger(__name__)


class AssetReader:
    """资产信息读取器"""
    
    def __init__(self, asset_manager_logic=None):
        """初始化资产读取器
        
        Args:
            asset_manager_logic: asset_manager 模块的逻辑层实例
        """
        self.asset_manager_logic = asset_manager_logic
        self.logger = logger
    
    def get_all_assets_summary(self) -> str:
        """获取所有资产的摘要信息
        
        Returns:
            str: 资产摘要的格式化字符串
        """
        if not self.asset_manager_logic:
            return "[WARN] 资产管理器未连接，无法读取资产信息。"
        
        try:
            assets = self.asset_manager_logic.get_all_assets()
            
            if not assets:
                return "[ASSET] 当前资产库为空，尚未添加任何资产。"
            
            # 按分类统计
            categories = {}
            for asset in assets:
                # Asset 对象有 category 属性
                category = asset.category if hasattr(asset, 'category') else '未分类'
                if category not in categories:
                    categories[category] = []
                categories[category].append(asset)
            
            # 生成摘要
            summary_parts = [
                f"[ASSET] **资产库概览**（共 {len(assets)} 个资产）\n"
            ]
            
            for category, cat_assets in categories.items():
                summary_parts.append(f"\n**{category}** ({len(cat_assets)} 个):")
                for asset in cat_assets[:5]:  # 每个分类最多显示 5 个
                    # 从 Asset 对象获取属性
                    name = asset.name if hasattr(asset, 'name') else '未命名'
                    asset_type = asset.asset_type.value if hasattr(asset, 'asset_type') else '未知类型'
                    summary_parts.append(f"  - {name} ({asset_type})")
                
                if len(cat_assets) > 5:
                    summary_parts.append(f"  ... 还有 {len(cat_assets) - 5} 个资产")
            
            return "\n".join(summary_parts)
        
        except Exception as e:
            self.logger.error(f"读取资产摘要失败: {e}", exc_info=True)
            return f"[ERROR] 读取资产信息时出错: {str(e)}"
    
    def search_assets(self, keyword: str) -> str:
        """搜索资产
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            str: 搜索结果的格式化字符串
        """
        if not self.asset_manager_logic:
            return "⚠️ 资产管理器未连接。"
        
        try:
            assets = self.asset_manager_logic.get_all_assets()
            keyword_lower = keyword.lower()
            
            # 搜索匹配的资产
            matched_assets = []
            for asset in assets:
                # 从 Asset 对象获取属性
                name = asset.name.lower() if hasattr(asset, 'name') else ''
                description = asset.description.lower() if hasattr(asset, 'description') else ''
                
                if keyword_lower in name or keyword_lower in description:
                    matched_assets.append(asset)
            
            if not matched_assets:
                return f"[SEARCH] 未找到包含 '{keyword}' 的资产。"
            
            # 格式化结果
            results = [f"[SEARCH] 找到 {len(matched_assets)} 个相关资产：\n"]
            
            for asset in matched_assets[:10]:  # 最多显示 10 个
                name = asset.name if hasattr(asset, 'name') else '未命名'
                category = asset.category if hasattr(asset, 'category') else '未分类'
                asset_type = asset.asset_type.value if hasattr(asset, 'asset_type') else '未知'
                description = asset.description if hasattr(asset, 'description') else '无描述'
                path = str(asset.path) if hasattr(asset, 'path') else '未知路径'
                
                results.append(f"\n**{name}**")
                results.append(f"  - 分类: {category}")
                results.append(f"  - 类型: {asset_type}")
                results.append(f"  - 描述: {description}")
                results.append(f"  - 路径: {path}")
            
            if len(matched_assets) > 10:
                results.append(f"\n... 还有 {len(matched_assets) - 10} 个匹配结果")
            
            return "\n".join(results)
        
        except Exception as e:
            self.logger.error(f"搜索资产失败: {e}", exc_info=True)
            return f"[ERROR] 搜索资产时出错: {str(e)}"
    
    def get_asset_details(self, asset_name: str) -> str:
        """获取特定资产的详细信息
        
        Args:
            asset_name: 资产名称
            
        Returns:
            str: 资产详情的格式化字符串
        """
        if not self.asset_manager_logic:
            return "⚠️ 资产管理器未连接。"
        
        try:
            assets = self.asset_manager_logic.get_all_assets()
            
            # 查找资产
            target_asset = None
            for asset in assets:
                if hasattr(asset, 'name') and asset.name.lower() == asset_name.lower():
                    target_asset = asset
                    break
            
            if not target_asset:
                return f"[ERROR] 未找到名为 '{asset_name}' 的资产。"
            
            # 格式化详情
            name = target_asset.name if hasattr(target_asset, 'name') else '未命名'
            category = target_asset.category if hasattr(target_asset, 'category') else '未分类'
            asset_type = target_asset.asset_type.value if hasattr(target_asset, 'asset_type') else '未知'
            description = target_asset.description if hasattr(target_asset, 'description') else '无描述'
            path = str(target_asset.path) if hasattr(target_asset, 'path') else '未知'
            size = target_asset._format_size() if hasattr(target_asset, '_format_size') else '未知大小'
            
            details = [
                f"[ASSET] **{name}** 详细信息\n",
                f"**分类**: {category}",
                f"**类型**: {asset_type}",
                f"**描述**: {description}",
                f"**路径**: {path}",
                f"**大小**: {size}",
            ]
            
            # 如果是目录资产，列出包含的文件
            if hasattr(target_asset, 'path') and target_asset.path:
                from pathlib import Path
                asset_path = Path(target_asset.path)
                
                if asset_path.exists():
                    if asset_path.is_dir():
                        # 列出目录下的文件
                        files = list(asset_path.glob("*"))
                        files = [f for f in files if f.is_file()]  # 只要文件，不要子目录
                        
                        if files:
                            details.append(f"\n**包含的文件** ({len(files)} 个):")
                            for file in sorted(files)[:20]:  # 最多显示20个文件
                                file_size = file.stat().st_size
                                if file_size < 1024:
                                    size_str = f"{file_size} B"
                                elif file_size < 1024 * 1024:
                                    size_str = f"{file_size / 1024:.1f} KB"
                                else:
                                    size_str = f"{file_size / (1024 * 1024):.1f} MB"
                                details.append(f"  - {file.name} ({size_str})")
                            
                            if len(files) > 20:
                                details.append(f"  ... 还有 {len(files) - 20} 个文件")
                    else:
                        # 单个文件
                        details.append(f"\n**文件名**: {asset_path.name}")
                        details.append(f"**所在目录**: {asset_path.parent}")
            
            # 添加缩略图信息
            if hasattr(target_asset, 'thumbnail_path') and target_asset.thumbnail_path:
                details.append(f"\n**缩略图**: 已设置")
                details.append(f"**缩略图路径**: {target_asset.thumbnail_path}")
            
            return "\n".join(details)
        
        except Exception as e:
            self.logger.error(f"获取资产详情失败: {e}", exc_info=True)
            return f"[ERROR] 获取资产详情时出错: {str(e)}"
    
    def get_categories_list(self) -> str:
        """获取所有资产分类
        
        Returns:
            str: 分类列表的格式化字符串
        """
        if not self.asset_manager_logic:
            return "[WARN] 资产管理器未连接。"
        
        try:
            # 尝试获取分类
            if hasattr(self.asset_manager_logic, 'get_all_categories'):
                categories = self.asset_manager_logic.get_all_categories()
            else:
                # 从资产中提取分类
                assets = self.asset_manager_logic.get_all_assets()
                categories = list(set(asset.category if hasattr(asset, 'category') else '未分类' for asset in assets))
            
            if not categories:
                return "📂 当前没有资产分类。"
            
            result = ["📂 **资产分类列表**:\n"]
            for i, category in enumerate(categories, 1):
                result.append(f"{i}. {category}")
            
            return "\n".join(result)
        
        except Exception as e:
            self.logger.error(f"获取分类列表失败: {e}", exc_info=True)
            return f"[ERROR] 获取分类列表时出错: {str(e)}"



