# -*- coding: utf-8 -*-

"""
站点推荐模块主入口文件
"""

from PyQt6.QtWidgets import QWidget
from typing import Optional

from core.logger import get_logger
from modules.site_recommendations.logic.site_recommendations_logic import SiteRecommendationsLogic
from modules.site_recommendations.ui.site_recommendations_ui import SiteRecommendationsUI

logger = get_logger(__name__)


class SiteRecommendationsModule:
    """站点推荐模块主类"""
    
    def __init__(self, parent=None):
        """初始化模块
        
        Args:
            parent: 父组件（可选）
        """
        self.parent = parent
        self.ui: Optional[SiteRecommendationsUI] = None
        self.logic: Optional[SiteRecommendationsLogic] = None
        logger.info("SiteRecommendationsModule 初始化")
    
    def initialize(self, config_dir: str):
        """初始化模块
        
        Args:
            config_dir: 配置文件目录路径
        """
        logger.info(f"初始化站点推荐模块，配置目录: {config_dir}")
        try:
            self.logic = SiteRecommendationsLogic(config_dir)
            logger.info("站点推荐模块初始化完成")
        except Exception as e:
            logger.error(f"站点推荐模块初始化失败: {e}", exc_info=True)
            raise
    
    def get_widget(self) -> QWidget:
        """获取模块的UI组件
        
        Returns:
            QWidget: 模块的主UI组件
        """
        logger.info("获取站点推荐UI组件")
        
        if self.ui is None:
            logger.info("创建新的站点推荐UI实例")
            self.ui = SiteRecommendationsUI()
            
            if self.logic:
                self.ui.set_logic(self.logic)
            
            self._setup_connections()
            self._initialize_ui_data()
        else:
            logger.info("返回已存在的站点推荐UI实例")
        
        return self.ui
    
    def _setup_connections(self):
        """设置信号槽连接"""
        if not self.ui:
            return
        
        logger.info("站点推荐信号槽连接设置完成")
    
    def _initialize_ui_data(self):
        """初始化UI数据"""
        if not self.ui or not self.logic:
            return
        
        sites = self.logic.get_sites()
        self.ui.update_sites(sites)
        
        logger.info("站点推荐UI数据初始化完成")
    
    def cleanup(self):
        """清理资源"""
        logger.info("清理站点推荐模块资源")
        try:
            if self.logic:
                self.logic.save_config()
            
            if self.ui:
                self.ui = None
            
            logger.info("站点推荐模块资源清理完成")
        except Exception as e:
            logger.error(f"清理站点推荐模块资源时发生错误: {e}", exc_info=True)


