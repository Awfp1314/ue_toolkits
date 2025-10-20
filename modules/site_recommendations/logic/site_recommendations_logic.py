# -*- coding: utf-8 -*-

"""
站点推荐业务逻辑层
"""

from typing import Any, Dict, List
from core.base_logic import BaseLogic
from core.utils.validators import InputValidator


class SiteRecommendationsLogic(BaseLogic):
    """站点推荐业务逻辑类（继承自 BaseLogic）"""
    
    def get_config_name(self) -> str:
        """获取配置文件名"""
        return "site_config"
    
    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "version": "1.0.0",
            "sites": [
                {
                    "name": "Fab虚幻引擎商城",
                    "url": "https://www.fab.com/zh-cn/",
                    "description": "Epic Games官方资产商城",
                    "category": "资源网站"
                },
                {
                    "name": "爱给网",
                    "url": "https://www.aigei.com",
                    "description": "综合素材资源站",
                    "category": "资源网站"
                },
                {
                    "name": "微妙网",
                    "url": "https://www.wmiao.com/",
                    "description": "CG动画资源",
                    "category": "资源网站"
                },
                {
                    "name": "CG模型网",
                    "url": "https://www.cgmodel.com/",
                    "description": "中文CG模型库",
                    "category": "资源网站"
                },
                {
                    "name": "人人CG",
                    "url": "https://www.rrcg.cn/",
                    "description": "中文CG综合资源站",
                    "category": "资源网站"
                },
                {
                    "name": "itch.io",
                    "url": "https://itch.io/games",
                    "description": "独立游戏发行与资源站（需要魔法）",
                    "category": "资源网站"
                },
                {
                    "name": "CGTrader",
                    "url": "https://www.cgtrader.com/",
                    "description": "国际3D模型市场（需要魔法）",
                    "category": "资源网站"
                },
                {
                    "name": "Artstation",
                    "url": "https://www.artstation.com/",
                    "description": "艺术家作品集平台（需要魔法）",
                    "category": "资源网站"
                },
                {
                    "name": "opengameart",
                    "url": "https://opengameart.org/",
                    "description": "免费开源游戏素材库",
                    "category": "资源网站"
                },
                {
                    "name": "CG3DA",
                    "url": "https://www.cg3da.com/",
                    "description": "CG资源库",
                    "category": "资源网站"
                },
                {
                    "name": "音效编辑工具",
                    "url": "https://vocalremover.org/zh/cutter",
                    "description": "免费音频格式转换与编辑",
                    "category": "工具"
                },
                {
                    "name": "Reddit - UnrealEngine",
                    "url": "https://www.reddit.com/r/unrealengine/",
                    "description": "Reddit虚幻引擎社区（需要魔法）",
                    "category": "论坛"
                },
                {
                    "name": "Discord",
                    "url": "https://discord.com/",
                    "description": "Discord社区平台（需要魔法）",
                    "category": "论坛"
                },
                {
                    "name": "Polycount",
                    "url": "https://polycount.com/",
                    "description": "游戏艺术家论坛",
                    "category": "论坛"
                },
                {
                    "name": "吾爱破解",
                    "url": "https://www.52pojie.cn/",
                    "description": "中文技术交流论坛",
                    "category": "论坛"
                },
                {
                    "name": "StackOverFlow",
                    "url": "https://stackoverflow.com/",
                    "description": "程序员问答社区",
                    "category": "论坛"
                },
                {
                    "name": "官方文档",
                    "url": "https://dev.epicgames.com/documentation/zh-cn/unreal-engine/unreal-engine-5-6-documentation",
                    "description": "虚幻引擎官方中文文档",
                    "category": "学习"
                },
                {
                    "name": "Udemy",
                    "url": "https://www.udemy.com/zh-cn/",
                    "description": "高质量在线课程平台",
                    "category": "学习"
                }
            ]
        }
    
    def get_sites(self) -> List[Dict[str, str]]:
        """获取所有站点
        
        Returns:
            List[Dict[str, str]]: 站点列表
        """
        return self.config.get("sites", [])
    
    def add_site(self, name: str, url: str, description: str, category: str) -> tuple[bool, str]:
        """添加新站点（带输入验证）
        
        Args:
            name: 站点名称
            url: 站点URL
            description: 站点描述
            category: 站点分类
            
        Returns:
            tuple[bool, str]: (是否成功, 错误消息)
        """
        if not name or not name.strip():
            return False, "站点名称不能为空"
        
        if len(name) > 100:
            return False, "站点名称过长（最多100字符）"
        
        valid, error = InputValidator.validate_url(
            url,
            allowed_schemes=['http', 'https'],
            require_netloc=True
        )
        if not valid:
            return False, f"URL验证失败: {error}"
        
        if len(description) > 500:
            return False, "站点描述过长（最多500字符）"
        
        if not category or not category.strip():
            return False, "站点分类不能为空"
        
        for existing_site in self.config.get("sites", []):
            if existing_site.get("url") == url:
                return False, f"URL已存在: {url}"
        
        # 添加站点
        site = {
            "name": name.strip(),
            "url": url.strip(),
            "description": description.strip(),
            "category": category.strip()
        }
        
        if "sites" not in self.config:
            self.config["sites"] = []
        
        self.config["sites"].append(site)
        self.save_config()
        self.logger.info(f"添加新站点: {name}")
        
        return True, ""
    
    def remove_site(self, index: int) -> tuple[bool, str]:
        """删除站点（带索引验证）
        
        Args:
            index: 站点索引
            
        Returns:
            tuple[bool, str]: (是否成功, 错误消息)
        """
        sites = self.config.get("sites", [])
        
        if not sites:
            return False, "站点列表为空"
        
        if not (0 <= index < len(sites)):
            return False, f"索引越界: {index}（有效范围: 0-{len(sites)-1}）"
        
        # 删除站点
        site_name = sites[index]["name"]
        del sites[index]
        self.save_config()
        self.logger.info(f"删除站点: {site_name}")
        
        return True, ""

