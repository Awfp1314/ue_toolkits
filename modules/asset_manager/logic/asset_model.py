# -*- coding: utf-8 -*-

"""
资产数据模型
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional
from datetime import datetime


class AssetType(Enum):
    """资产类型枚举"""
    PACKAGE = "package"  # A型：资源包（文件夹）
    FILE = "file"        # B型：原始文件


@dataclass
class Asset:
    """资产数据类
    
    Attributes:
        id: 资产唯一标识符
        name: 资产名称
        asset_type: 资产类型（PACKAGE或FILE）
        path: 资产路径
        category: 资产分类
        file_extension: 文件扩展名（仅FILE类型）
        thumbnail_path: 缩略图路径
        thumbnail_source: 缩略图来源（"screenshots" 或 "saved" 或 None）
        size: 文件大小（字节）
        created_time: 创建时间
        description: 资产描述
    """
    id: str
    name: str
    asset_type: AssetType
    path: Path
    category: str = "默认分类"
    file_extension: str = ""
    thumbnail_path: Optional[Path] = None
    thumbnail_source: Optional[str] = None  # 新增：缩略图来源（"screenshots" 或 "saved"）
    size: int = 0
    created_time: datetime = field(default_factory=datetime.now)
    description: str = ""
    
    def get_display_info(self) -> str:
        """获取显示信息"""
        if self.asset_type == AssetType.PACKAGE:
            return f"资源包 · {self._format_size()}"
        else:
            return f"{self.file_extension.upper()} 文件 · {self._format_size()}"
    
    def _format_size(self) -> str:
        """格式化文件大小"""
        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024 * 1024:
            return f"{self.size / 1024:.1f} KB"
        elif self.size < 1024 * 1024 * 1024:
            return f"{self.size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.size / (1024 * 1024 * 1024):.2f} GB"

