# -*- coding: utf-8 -*-

"""
配置模板数据类
"""

from datetime import datetime
from typing import Optional
from pathlib import Path


class ConfigTemplate:
    """配置模板数据类"""
    
    def __init__(self, name: str, description: str = "", last_modified: Optional[str] = None, projects: int = 0, path: Optional[Path] = None):
        self.name = name
        self.description = description
        self.last_modified = last_modified or datetime.now().strftime("%Y-%m-%d %H:%M")
        self.projects = projects
        self.path = path  # 添加配置文件路径属性

