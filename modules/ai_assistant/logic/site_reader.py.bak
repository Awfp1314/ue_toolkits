# -*- coding: utf-8 -*-

"""
站点推荐读取器
读取站点推荐数据，供 AI 助手使用
"""

from typing import Optional
from core.logger import get_logger


logger = get_logger(__name__)


class SiteReader:
    """站点推荐读取器"""
    
    def __init__(self, site_recommendations_logic=None):
        """初始化站点读取器
        
        Args:
            site_recommendations_logic: SiteRecommendationsLogic 实例
        """
        self.site_logic = site_recommendations_logic
        self.logger = logger
        
        if self.site_logic:
            self.logger.info("站点读取器初始化成功（已连接到站点推荐模块）")
        else:
            self.logger.warning("站点读取器初始化：站点推荐逻辑未连接")
    
    def get_all_sites_summary(self, max_count: int = 100) -> str:
        """获取所有站点的摘要信息
        
        Args:
            max_count: 最大返回站点数
            
        Returns:
            str: 站点摘要（Markdown 格式）
        """
        try:
            if not self.site_logic:
                return "❌ 站点推荐模块未连接"
            
            sites = self.site_logic.get_sites()
            
            if not sites:
                return "📭 暂无站点推荐"
            
            # 按分类组织
            categories = {}
            for site in sites[:max_count]:
                category = site.get('category', '其他')
                if category not in categories:
                    categories[category] = []
                categories[category].append(site)
            
            # 格式化输出
            result = ["🌐 **站点推荐列表**\n"]
            
            category_order = ["资源网站", "工具", "论坛", "学习"]
            
            for category in category_order:
                if category in categories:
                    result.append(f"\n### {category}")
                    for site in categories[category]:
                        name = site.get('name', '未知')
                        url = site.get('url', '')
                        description = site.get('description', '')
                        result.append(f"- **[{name}]({url})**: {description}")
            
            # 添加其他未分类的站点
            for category, category_sites in categories.items():
                if category not in category_order:
                    result.append(f"\n### {category}")
                    for site in category_sites:
                        name = site.get('name', '未知')
                        url = site.get('url', '')
                        description = site.get('description', '')
                        result.append(f"- **[{name}]({url})**: {description}")
            
            result.append(f"\n\n📊 共 {len(sites)} 个站点")
            
            return "\n".join(result)
        
        except Exception as e:
            self.logger.error(f"获取站点摘要失败: {e}", exc_info=True)
            return f"❌ 获取站点信息时出错: {str(e)}"
    
    def search_sites(self, keyword: str, max_count: int = 20) -> str:
        """搜索站点
        
        Args:
            keyword: 搜索关键词
            max_count: 最大返回数量
            
        Returns:
            str: 搜索结果（Markdown 格式）
        """
        try:
            if not self.site_logic:
                return "❌ 站点推荐模块未连接"
            
            sites = self.site_logic.get_sites()
            
            if not sites:
                return "📭 暂无站点推荐"
            
            # 搜索匹配的站点
            keyword_lower = keyword.lower()
            matched_sites = []
            
            for site in sites:
                name = site.get('name', '').lower()
                description = site.get('description', '').lower()
                category = site.get('category', '').lower()
                url = site.get('url', '').lower()
                
                if (keyword_lower in name or 
                    keyword_lower in description or 
                    keyword_lower in category or
                    keyword_lower in url):
                    matched_sites.append(site)
            
            if not matched_sites:
                return f"🔍 未找到包含 '{keyword}' 的站点"
            
            # 限制返回数量
            matched_sites = matched_sites[:max_count]
            
            # 格式化输出
            result = [f"🔍 **搜索结果**（关键词: {keyword}）\n"]
            
            for site in matched_sites:
                name = site.get('name', '未知')
                url = site.get('url', '')
                description = site.get('description', '')
                category = site.get('category', '其他')
                result.append(f"- **[{name}]({url})** ({category}): {description}")
                result.append("")
            
            result.append(f"📊 找到 {len(matched_sites)} 个相关站点")
            
            return "\n".join(result)
        
        except Exception as e:
            self.logger.error(f"搜索站点失败: {e}", exc_info=True)
            return f"❌ 搜索站点时出错: {str(e)}"
    
    def get_sites_by_category(self, category: str) -> str:
        """获取指定分类的站点
        
        Args:
            category: 分类名称（资源网站、工具、论坛、学习）
            
        Returns:
            str: 站点列表（Markdown 格式）
        """
        try:
            if not self.site_logic:
                return "❌ 站点推荐模块未连接"
            
            sites = self.site_logic.get_sites()
            
            if not sites:
                return "📭 暂无站点推荐"
            
            # 过滤指定分类的站点
            category_sites = [
                site for site in sites 
                if site.get('category', '').lower() == category.lower()
            ]
            
            if not category_sites:
                return f"🔍 未找到 '{category}' 分类的站点"
            
            # 格式化输出
            result = [f"🌐 **{category}站点**\n"]
            
            for site in category_sites:
                name = site.get('name', '未知')
                url = site.get('url', '')
                description = site.get('description', '')
                result.append(f"- **[{name}]({url})**: {description}")
            
            result.append(f"\n📊 共 {len(category_sites)} 个站点")
            
            return "\n".join(result)
        
        except Exception as e:
            self.logger.error(f"获取分类站点失败: {e}", exc_info=True)
            return f"❌ 获取分类站点时出错: {str(e)}"
    
    def get_site_detail(self, site_name: str) -> str:
        """获取指定站点的详细信息
        
        Args:
            site_name: 站点名称
            
        Returns:
            str: 站点详细信息（Markdown 格式）
        """
        try:
            if not self.site_logic:
                return "❌ 站点推荐模块未连接"
            
            sites = self.site_logic.get_sites()
            
            if not sites:
                return "📭 暂无站点推荐"
            
            # 查找站点
            for site in sites:
                if site.get('name', '').lower() == site_name.lower():
                    name = site.get('name', '未知')
                    url = site.get('url', '')
                    description = site.get('description', '')
                    category = site.get('category', '其他')
                    
                    result = [
                        f"🌐 **[{name}]({url})**\n",
                        f"**分类**: {category}",
                        f"**描述**: {description}",
                        f"**链接**: [{url}]({url})",
                    ]
                    
                    return "\n".join(result)
            
            return f"🔍 未找到名为 '{site_name}' 的站点"
        
        except Exception as e:
            self.logger.error(f"获取站点详情失败: {e}", exc_info=True)
            return f"❌ 获取站点详情时出错: {str(e)}"

