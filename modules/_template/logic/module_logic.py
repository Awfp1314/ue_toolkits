# -*- coding: utf-8 -*-

"""
模块业务逻辑层
负责处理数据和业务逻辑，不包含UI代码
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# 使用统一的日志系统
from core.logger import get_logger

logger = get_logger(__name__)


class ModuleLogic:
    """模块业务逻辑类
    
    负责：
    1. 数据管理（加载、保存、更新）
    2. 业务逻辑处理
    3. 与外部系统交互
    """
    
    def __init__(self, config_dir: str):
        """初始化业务逻辑
        
        Args:
            config_dir: 配置文件目录路径
        """
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "module_config.json")
        self.config: Dict[str, Any] = {}
        
        logger.info(f"初始化模块逻辑，配置目录: {config_dir}")
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info("配置文件加载成功")
            else:
                logger.info("配置文件不存在，使用默认配置")
                self._create_default_config()
        except Exception as e:
            logger.error(f"加载配置文件时出错: {e}", exc_info=True)
            self._create_default_config()
    
    def _create_default_config(self):
        """创建默认配置"""
        self.config = {
            "version": "1.0.0",
            "settings": {},
            "data": []
        }
        self.save_config()
    
    def save_config(self):
        """保存配置文件"""
        try:
            # 确保目录存在
            os.makedirs(self.config_dir, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            logger.info("配置文件保存成功")
        except Exception as e:
            logger.error(f"保存配置文件时出错: {e}", exc_info=True)
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        return self.config.get(key, default)
    
    def set_config_value(self, key: str, value: Any):
        """设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        self.config[key] = value
        logger.info(f"配置已更新: {key} = {value}")
    
    # 在这里添加更多业务逻辑方法
    # 例如：
    # def process_data(self, data: Any) -> Any:
    #     """处理数据"""
    #     pass
    # def validate_input(self, input_data: Any) -> bool:
    #     """验证输入"""
    #     pass


