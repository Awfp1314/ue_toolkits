# -*- coding: utf-8 -*-

"""
资产管理逻辑层
"""

import uuid
import shutil
import json
import subprocess
import threading
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

try:
    from pypinyin import lazy_pinyin, Style
except ImportError:
    # 如果pypinyin未安装，使用简单的拼音映射
    lazy_pinyin = None
    Style = None

from PyQt6.QtCore import QObject, pyqtSignal

from core.logger import get_logger
from core.config_manager import ConfigManager
from .asset_model import Asset, AssetType

logger = get_logger(__name__)


class AssetManagerLogic(QObject):
    """资产管理逻辑类
    
    Signals:
        asset_added: 资产添加完成信号 (Asset)
        asset_removed: 资产删除完成信号 (str: asset_id)
        assets_loaded: 资产列表加载完成信号 (List[Asset])
        preview_started: 预览启动信号 (str: asset_id)
        preview_finished: 预览完成信号
        error_occurred: 错误发生信号 (str: error_message)
        progress_updated: 进度更新信号 (int: current, int: total, str: message)
    """
    
    asset_added = pyqtSignal(object)  # Asset
    asset_removed = pyqtSignal(str)  # asset_id
    assets_loaded = pyqtSignal(list)  # List[Asset]
    preview_started = pyqtSignal(str)  # asset_id
    preview_finished = pyqtSignal()
    thumbnail_updated = pyqtSignal(str, str)  # asset_id, thumbnail_path
    error_occurred = pyqtSignal(str)  # error_message
    progress_updated = pyqtSignal(int, int, str)  # current, total, message
    
    def __init__(self, config_dir: Path):
        super().__init__()
        self.config_dir = Path(config_dir)
        self.config_manager = ConfigManager("asset_manager", 
                                           template_path=self.config_dir / "config_template.json")
        
        # 本地配置路径（在资产库目录下，只在需要时初始化）
        self.local_config_path = None
        
        # 本地缩略图目录（将在 _load_config 中设置）
        self.thumbnails_dir = None
        
        # 本地文档目录（将在 _load_config 中设置）
        self.documents_dir = None
        
        # 资产列表
        self.assets: List[Asset] = []
        
        # 分类列表
        self.categories: List[str] = ["默认分类"]
        
        self._load_config()
        
        logger.info("资产管理逻辑初始化完成")
    
    def _load_config(self) -> None:
        """加载配置"""
        config = self.config_manager.load_user_config()
        if not config:
            # 不自动创建全局配置，只有在需要时才创建本地配置
            config = {
                "_version": "2.0.0",
                "preview_project_path": "",
                "last_target_project_path": "",
                "asset_library_configs": {}
            }
        
        # 自动迁移旧配置格式到新格式
        config = self._migrate_config(config)
        
        # 获取当前资产库路径
        asset_library_path = config.get("asset_library_path", "")
        if not asset_library_path or not Path(asset_library_path).exists():
            logger.warning("资产库路径未设置或不存在，不加载任何资产")
            self.assets.clear()
            self.assets_loaded.emit(self.assets)
            return
        
        # 设置本地配置文件路径
        self.local_config_path = Path(asset_library_path) / ".asset_config" / "config.json"
        
        # 设置本地缩略图和文档目录
        asset_config_dir = Path(asset_library_path) / ".asset_config"
        self.thumbnails_dir = asset_config_dir / "thumbnails"
        # 只在第一次扫描资产时创建本地目录，不在这里提前创建
        self.documents_dir = asset_config_dir / "documents"
        # 同样延迟创建文档目录
        
        # 优先加载本地配置，如果不存在则从全局配置迁移
        local_config = self._load_local_config()
        if local_config:
            lib_config = local_config
        else:
            # 从新的多路径配置中获取该路径的配置（用于迁移）
            asset_library_configs = config.get("asset_library_configs", {})
            lib_config = asset_library_configs.get(asset_library_path, {})
            # 如果本地配置不存在但有全局配置，则将其保存为本地配置
            if lib_config:
                self._save_local_config(lib_config)
        
        # 从配置加载分类列表
        self.categories = lib_config.get("categories", config.get("categories", ["默认分类"]))
        if "默认分类" not in self.categories:
            self.categories.insert(0, "默认分类")
        
        # 从资产库扫描实际存在的资产（优先使用缓存的资产数据）
        cached_assets_data = lib_config.get("assets", config.get("assets", []))
        self._scan_asset_library(Path(asset_library_path), cached_assets_data)
    
    def _migrate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """迁移旧配置格式到新的多路径格式
        
        旧格式: 
        {
            "asset_library_path": "...",
            "categories": [...],
            "assets": [...]
        }
        
        新格式:
        {
            "_version": "2.0.0",
            "asset_library_configs": {
                "path": {
                    "categories": [...],
                    "assets": [...]
                }
            }
        }
        """
        version = config.get("_version", "1.0.0")
        
        # 如果已经是新版本格式，直接返回
        if version == "2.0.0":
            logger.debug("配置已是最新版本2.0.0")
            return config
        
        logger.info(f"检测到旧配置版本 {version}，开始迁移...")
        
        try:
            # 保存旧的资产库路径和资产数据
            old_asset_library_path = config.get("asset_library_path", "")
            old_categories = config.get("categories", ["默认分类"])
            old_assets = config.get("assets", [])
            
            # 创建新格式的配置
            new_config = {
                "_version": "2.0.0",
                "preview_project_path": config.get("preview_project_path", ""),
                "last_target_project_path": config.get("last_target_project_path", ""),
                "asset_library_configs": {}
            }
            
            # 迁移旧的单个预览工程路径到新的多工程格式
            old_preview_project = config.get("preview_project_path", "")
            if old_preview_project and Path(old_preview_project).exists():
                # 检查是否已有额外工程配置，如果没有则从旧配置迁移
                if not config.get("additional_preview_projects_with_names"):
                    new_config["additional_preview_projects_with_names"] = [
                        {
                            "path": old_preview_project,
                            "name": "默认工程"
                        }
                    ]
                    logger.info(f"已迁移旧的预览工程路径到新格式: {old_preview_project}")
            
            # 如果旧配置有资产库路径，将其数据迁移到新格式
            if old_asset_library_path:
                new_config["asset_library_configs"][old_asset_library_path] = {
                    "categories": old_categories,
                    "assets": old_assets
                }
                logger.info(f"已迁移旧配置: {old_asset_library_path}")
            
            # 保存迁移后的配置
            self.config_manager.save_user_config(new_config)
            logger.info("配置迁移完成")
            
            # 返回与旧格式兼容的视图（用于向后兼容）
            # 这样可以保证加载逻辑不需要太多改动
            if old_asset_library_path:
                new_config["asset_library_path"] = old_asset_library_path
                new_config["categories"] = old_categories
                new_config["assets"] = old_assets
            
            return new_config
            
        except Exception as e:
            logger.error(f"配置迁移失败: {e}", exc_info=True)
            # 迁移失败时返回原配置
            return config
    
    def _scan_asset_library(self, library_path: Path, cached_assets_data: List[Dict[str, Any]]) -> None:
        """扫描资产库，加载实际存在的资产
        
        Args:
            library_path: 资产库路径
            cached_assets_data: 缓存的资产数据（用于恢复元数据）
        """
        self.assets.clear()
        
        # 创建缓存字典，key为资产路径，value为资产数据
        cached_assets_dict = {}
        for asset_data in cached_assets_data:
            asset_path = asset_data.get("path")
            if asset_path:
                cached_assets_dict[asset_path] = asset_data
        
        logger.info(f"开始扫描资产库: {library_path}")
        
        # 遍历所有分类文件夹
        for category in self.categories:
            category_folder = library_path / category
            if not category_folder.exists():
                logger.warning(f"分类文件夹不存在: {category_folder}")
                continue
            
            # 扫描该分类下的所有文件和文件夹
            for item in category_folder.iterdir():
                if item.name.startswith('.'):
                    # 跳过隐藏文件/文件夹
                    continue
                
                try:
                    # 确定资产类型
                    if item.is_dir():
                        asset_type = AssetType.PACKAGE
                        file_extension = ""
                    else:
                        asset_type = AssetType.FILE
                        file_extension = item.suffix
                    
                    # 尝试从缓存中获取资产数据
                    item_path_str = str(item)
                    cached_data = cached_assets_dict.get(item_path_str)
                    
                    if cached_data:
                        # 使用缓存的数据恢复资产
                        # 获取缩略图路径，并验证其有效性
                        thumbnail_path = None
                        if cached_data.get("thumbnail_path"):
                            thumbnail_candidate = Path(cached_data["thumbnail_path"])
                            # 验证缩略图文件是否存在
                            if thumbnail_candidate.exists():
                                thumbnail_path = thumbnail_candidate
                                logger.debug(f"找到有效的缩略图: {cached_data['name']} -> {thumbnail_path}")
                            else:
                                logger.warning(f"缩略图文件不存在，将跳过: {thumbnail_candidate}")
                                # 尝试从标准缩略图目录查找
                                thumbnail_path = self._find_thumbnail_by_asset_id(cached_data.get("id"))
                                if thumbnail_path:
                                    logger.info(f"从缩略图目录恢复了缩略图: {cached_data['name']}")
                        
                        asset = Asset(
                            id=cached_data["id"],
                            name=cached_data["name"],
                            asset_type=AssetType(cached_data["asset_type"]),
                            path=item,
                            category=category,  # 使用当前分类文件夹作为分类
                            file_extension=cached_data.get("file_extension", file_extension),
                            thumbnail_path=thumbnail_path,
                            thumbnail_source=cached_data.get("thumbnail_source"),
                            size=cached_data.get("size", 0),
                            created_time=datetime.fromisoformat(cached_data.get("created_time", datetime.now().isoformat())),
                            description=cached_data.get("description", "")
                        )
                        logger.debug(f"从缓存恢复资产: {asset.name}")
                    else:
                        asset_id = str(uuid.uuid4())
                        asset_name = item.stem if item.is_file() else item.name
                        
                        asset = Asset(
                            id=asset_id,
                            name=asset_name,
                            asset_type=asset_type,
                            path=item,
                            category=category,
                            file_extension=file_extension,
                            thumbnail_path=None,
                            thumbnail_source=None,
                            size=self._get_size(item),
                            created_time=datetime.now(),
                            description=""
                        )
                        logger.info(f"发现新资产: {asset.name}")
                    
                    self.assets.append(asset)
                    
                except Exception as e:
                    logger.error(f"扫描资产失败 {item}: {e}", exc_info=True)
        
        logger.info(f"资产库扫描完成，共加载 {len(self.assets)} 个资产")
        
        # 迁移缩略图和文档到本地目录
        self._migrate_thumbnails_and_docs()
        
        self.assets_loaded.emit(self.assets)
        
        self._save_config()
    
    def _get_size(self, path: Path) -> int:
        """获取文件或文件夹的大小（字节）"""
        if path.is_file():
            return path.stat().st_size
        elif path.is_dir():
            total_size = 0
            try:
                for item in path.rglob('*'):
                    if item.is_file():
                        total_size += item.stat().st_size
            except Exception as e:
                logger.warning(f"计算文件夹大小失败 {path}: {e}")
            return total_size
        return 0
    
    def _find_thumbnail_by_asset_id(self, asset_id: str) -> Optional[Path]:
        """根据资产ID在缩略图目录中查找缩略图
        
        Args:
            asset_id: 资产ID
            
        Returns:
            如果找到缩略图返回Path对象，否则返回None
        """
        if not asset_id or not self.thumbnails_dir.exists():
            return None
        
        try:
            # 标准缩略图文件名格式为 {asset_id}.png
            thumbnail_path = self.thumbnails_dir / f"{asset_id}.png"
            if thumbnail_path.exists():
                logger.debug(f"找到了缩略图文件: {thumbnail_path}")
                return thumbnail_path
            
            logger.debug(f"缩略图不存在: {thumbnail_path}")
            return None
            
        except Exception as e:
            logger.warning(f"查找缩略图失败 (asset_id: {asset_id}): {e}")
            return None
    
    def _load_assets_from_config(self, assets_data: List[Dict[str, Any]]) -> None:
        """从配置数据加载资产列表"""
        self.assets.clear()
        
        for asset_data in assets_data:
            try:
                # 安全地解析创建时间
                created_time_str = asset_data.get("created_time")
                if created_time_str:
                    try:
                        created_time = datetime.fromisoformat(created_time_str)
                    except (ValueError, TypeError):
                        logger.warning(f"资产 {asset_data.get('name', 'unknown')} 的创建时间格式无效: {created_time_str}，使用当前时间")
                        created_time = datetime.now()
                else:
                    created_time = datetime.now()
                
                asset = Asset(
                    id=asset_data["id"],
                    name=asset_data["name"],
                    asset_type=AssetType(asset_data["asset_type"]),
                    path=Path(asset_data["path"]),
                    category=asset_data.get("category", "默认分类"),
                    file_extension=asset_data.get("file_extension", ""),
                    thumbnail_path=Path(asset_data["thumbnail_path"]) if asset_data.get("thumbnail_path") else None,
                    thumbnail_source=asset_data.get("thumbnail_source"),  # 新增：读取缩略图来源
                    size=asset_data.get("size", 0),
                    created_time=created_time,
                    description=asset_data.get("description", "")
                )
                
                if asset.path.exists():
                    self.assets.append(asset)
                else:
                    logger.warning(f"资产路径不存在，跳过: {asset.path}")
                    
            except Exception as e:
                logger.error(f"加载资产数据失败: {e}", exc_info=True)
        
        logger.info(f"已加载 {len(self.assets)} 个资产")
        self.assets_loaded.emit(self.assets)
    
    def _save_config(self) -> None:
        """保存配置"""
        # 获取当前资产库路径
        current_lib_path = self.get_asset_library_path()
        
        if current_lib_path:
            # 准备本地配置数据
            lib_config = {
                "categories": self.categories
            }
            
            # 保存资产数据
            assets_data = []
            for asset in self.assets:
                assets_data.append({
                    "id": asset.id,
                    "name": asset.name,
                    "asset_type": asset.asset_type.value,
                    "path": str(asset.path),
                    "category": asset.category,
                    "file_extension": asset.file_extension,
                    "thumbnail_path": str(asset.thumbnail_path) if asset.thumbnail_path else None,
                    "thumbnail_source": asset.thumbnail_source,
                    "size": asset.size,
                    "created_time": asset.created_time.isoformat(),
                    "description": asset.description
                })
            
            lib_config["assets"] = assets_data
            
            # 保存到本地配置文件
            self._save_local_config(lib_config)
            logger.debug(f"已保存 {len(self.assets)} 个资产的配置到本地: {self.local_config_path}")
            
            # 不保存全局配置文件，只保存本地配置
            # 预览工程等全局设置由 set_preview_project() 等方法单独处理
    
    def _migrate_thumbnails_and_docs(self) -> None:
        """迁移缩略图和文档到本地目录
        
        此方法现在只用于日志记录，实际目录创建发生在需要时：
        - 缩略图目录在生成缩略图时创建
        - 文档目录在创建资产文档时创建
        """
        logger.debug("本地缩略图和文档目录已准备好（实际创建将在需要时进行）")
    
    def _load_local_config(self) -> Optional[Dict[str, Any]]:
        """从本地配置文件加载资产库配置
        
        Returns:
            配置字典或None（如果文件不存在）
        """
        if not self.local_config_path or not self.local_config_path.exists():
            logger.debug(f"本地配置文件不存在: {self.local_config_path}")
            return None
        
        try:
            with open(self.local_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 检查版本并进行迁移
            version = config.get("_version", "1.0.0")
            if version != "2.0.0":
                logger.info(f"检测到本地配置版本 {version}，需要迁移到 2.0.0")
                config = self._migrate_local_config(config)
                # 迁移后保存新版本
                self._save_local_config(config)
            
            logger.info(f"成功加载本地配置: {self.local_config_path}")
            return config
        except Exception as e:
            logger.error(f"加载本地配置失败: {e}", exc_info=True)
            return None
    
    def _migrate_local_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """迁移本地配置文件到新版本
        
        Args:
            config: 旧版本配置
            
        Returns:
            新版本配置
        """
        version = config.get("_version", "1.0.0")
        logger.info(f"开始迁移本地配置，从版本 {version} 到 2.0.0")
        
        # 如果已经是新版本，直接返回
        if version == "2.0.0":
            return config
        
        # 为旧版本添加版本字段
        config["_version"] = "2.0.0"
        
        return config
    
    def _save_local_config(self, config: Dict[str, Any]) -> bool:
        """保存资产库配置到本地文件
        
        Args:
            config: 要保存的配置字典
            
        Returns:
            是否保存成功
        """
        if not self.local_config_path:
            logger.warning("本地配置路径未设置，无法保存本地配置")
            return False
        
        try:
            # 确保目录存在
            self.local_config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 确保版本字段存在
            if "_version" not in config:
                config["_version"] = "2.0.0"
            
            # 创建备份前先备份旧配置（如果存在），然后备份新配置
            try:
                backup_dir = self.local_config_path.parent / "backup"
                backup_dir.mkdir(parents=True, exist_ok=True)
                
                # 创建带时间戳的备份文件（备份的是即将保存的新配置）
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = backup_dir / f"config_{timestamp}.json"
                
                # 备份即将保存的完整配置内容
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                logger.debug(f"已创建本地配置备份: {backup_path}")
                
                # 清理旧备份，只保留最近 5 个
                backup_files = sorted(backup_dir.glob("config_*.json"), reverse=True)
                for old_backup in backup_files[5:]:
                    try:
                        old_backup.unlink()
                        logger.debug(f"已删除旧备份: {old_backup}")
                    except Exception as e:
                        logger.warning(f"删除旧备份失败: {e}")
            
            except Exception as e:
                logger.warning(f"创建备份失败: {e}")
            
            # 保存配置到本地文件
            with open(self.local_config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"成功保存本地配置: {self.local_config_path}")
            return True
        except Exception as e:
            logger.error(f"保存本地配置失败: {e}", exc_info=True)
            return False
    
    def add_asset(self, asset_path: Path, asset_type: AssetType, name: str = "", category: str = "默认分类", 
                  description: str = "", create_markdown: bool = False) -> Optional[Asset]:
        """添加资产（将资产移动到资产库）
        
        Args:
            asset_path: 资产源路径（文件夹或文件）
            asset_type: 资产类型
            name: 资产名称（可选，默认使用文件/文件夹名）
            category: 资产分类
            description: 资产描述
            create_markdown: 是否创建markdown文档
            
        Returns:
            添加成功返回Asset对象，失败返回None
        """
        try:
            if not asset_path.exists():
                error_msg = f"资产路径不存在: {asset_path}"
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                return None
            
            library_path = self.get_asset_library_path()
            if not library_path or not library_path.exists():
                error_msg = "资产库路径未设置或不存在，请先设置资产库路径"
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                return None
            
            # 确保分类文件夹存在
            category_folder = library_path / category
            if not category_folder.exists():
                category_folder.mkdir(parents=True, exist_ok=True)
            
            # 将资产移动到资产库
            target_path = category_folder / asset_path.name
            
            # 如果目标已存在，添加数字后缀
            if target_path.exists():
                base_name = asset_path.stem
                suffix = asset_path.suffix
                counter = 1
                while target_path.exists():
                    if asset_type == AssetType.PACKAGE:
                        target_path = category_folder / f"{base_name}_{counter}"
                    else:
                        target_path = category_folder / f"{base_name}_{counter}{suffix}"
                    counter += 1
            
            # 移动资产到资产库
            logger.info(f"开始移动资产: {asset_path} -> {target_path}")
            logger.info(f"资产类型: {asset_type}, 源路径存在: {asset_path.exists()}")
            
            # 使用进度回调进行实时进度报告
            def move_progress_callback(current, total, message):
                self.progress_updated.emit(current, total, message)
            
            # 根据资产类型选择相应的移动方法
            if asset_type == AssetType.PACKAGE:
                # 移动整个文件夹（保持原文件夹名称）
                self._safe_move_tree(asset_path, target_path, progress_callback=move_progress_callback)
            else:
                # 移动单个文件（保持原文件名）
                self._safe_move_file(asset_path, target_path, progress_callback=move_progress_callback)
            
            logger.info(f"资产已移动: {asset_path} -> {target_path}")
            
            # 生成唯一ID
            asset_id = str(uuid.uuid4())
            
            asset_name = name if name else target_path.name
            
            # 计算文件大小
            size = self._calculate_size(target_path)
            
            file_extension = ""
            if asset_type == AssetType.FILE:
                file_extension = target_path.suffix.lower()
            
            asset = Asset(
                id=asset_id,
                name=asset_name,
                asset_type=asset_type,
                path=target_path,  # 使用资产库中的路径
                category=category,
                file_extension=file_extension,
                size=size,
                description=description
            )
            
            # 添加到列表
            self.assets.append(asset)
            
            logger.info("开始保存配置...")
            self.progress_updated.emit(0, 1, "正在保存配置...")
            self._save_config()
            logger.info("配置保存完成")
            
            logger.info(f"添加资产成功: {asset_name} ({asset_type.value})")
            logger.info("发送 asset_added 信号...")
            self.asset_added.emit(asset)
            logger.info("asset_added 信号已发送")
            
            # 如果需要创建markdown文档
            if create_markdown:
                self.progress_updated.emit(0, 1, "正在创建文档...")
                self._create_asset_markdown(asset)
                self.progress_updated.emit(1, 1, "文档创建完成")
            
            self.progress_updated.emit(1, 1, "资产添加完成！")
            
            return asset
            
        except Exception as e:
            error_msg = f"添加资产失败: {e}"
            logger.error(error_msg, exc_info=True)
            self.error_occurred.emit(error_msg)
            return None
    
    def _create_asset_markdown(self, asset: Asset) -> None:
        """创建资产的文本文档并用记事本打开
        
        Args:
            asset: 资产对象
        """
        try:
            import subprocess
            from pathlib import Path
            
            # 使用本地文档目录（在资产库目录下）
            if not self.documents_dir:
                logger.error("本地文档目录未设置")
                return
            
            documents_dir = self.documents_dir
            documents_dir.mkdir(parents=True, exist_ok=True)
            
            # 文档文件名为 {asset_id}.txt
            doc_filename = f"{asset.id}.txt"
            doc_path = documents_dir / doc_filename
            
            # 创建文本内容
            text_content = f"""资产信息表
{'='*50}

资产名称: {asset.name}
资产ID: {asset.id}
资产类型: {asset.asset_type.value}
分类: {asset.category}
文件路径: {asset.path}
文件大小: {self._format_size(asset.size)}
创建时间: {asset.created_time.strftime('%Y-%m-%d %H:%M:%S')}

描述:
{asset.description or '暂无'}

{'='*50}

使用说明:
请在下方添加关于如何使用该资产的详细说明...


备注:
请在下方添加其他备注信息...

"""
            
            # 写入文档到固定位置
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            logger.info(f"已创建文本文档: {doc_path}")
            
            # 用记事本打开
            import sys
            if sys.platform == "win32":
                subprocess.Popen(['notepad', str(doc_path)])
                logger.info(f"已用记事本打开文档: {doc_path}")
            elif sys.platform == "darwin":
                subprocess.Popen(['open', '-a', 'TextEdit', str(doc_path)])
                logger.info(f"已用TextEdit打开文档: {doc_path}")
            else:
                subprocess.Popen(['gedit', str(doc_path)])
                logger.info(f"已用gedit打开文档: {doc_path}")
            
        except Exception as e:
            logger.warning(f"创建文本文档失败: {e}", exc_info=True)
    
    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"
    
    def remove_asset(self, asset_id: str, delete_physical: bool = False) -> bool:
        """删除资产
        
        Args:
            asset_id: 资产ID
            delete_physical: 是否删除物理文件/文件夹（默认False，仅从列表移除）
            
        Returns:
            删除成功返回True，失败返回False
        """
        try:
            asset = self.get_asset(asset_id)
            if not asset:
                error_msg = f"未找到资产: {asset_id}"
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                return False
            
            # 如果需要删除物理文件
            if delete_physical and asset.path and asset.path.exists():
                try:
                    if asset.path.is_dir():
                        shutil.rmtree(asset.path)
                        logger.info(f"已删除资产文件夹: {asset.path}")
                    else:
                        asset.path.unlink()
                        logger.info(f"已删除资产文件: {asset.path}")
                except Exception as e:
                    error_msg = f"删除物理文件失败: {e}"
                    logger.error(error_msg, exc_info=True)
                    self.error_occurred.emit(error_msg)
                    return False
            
            # 从列表中删除
            self.assets = [a for a in self.assets if a.id != asset_id]
            
            # 删除缩略图
            if asset.thumbnail_path and asset.thumbnail_path.exists():
                try:
                    asset.thumbnail_path.unlink()
                    logger.info(f"已删除缩略图: {asset.thumbnail_path}")
                except Exception as e:
                    logger.warning(f"删除缩略图失败: {e}")
            
            # 删除关联的文档
            if self.documents_dir:
                doc_path = self.documents_dir / f"{asset_id}.txt"
                if doc_path.exists():
                    try:
                        doc_path.unlink()
                        logger.info(f"已删除关联文档: {doc_path}")
                    except Exception as e:
                        logger.warning(f"删除关联文档失败: {e}")
            
            self._save_config()
            
            logger.info(f"删除资产成功: {asset.name} (物理删除: {delete_physical})")
            self.asset_removed.emit(asset_id)
            
            return True
            
        except Exception as e:
            error_msg = f"删除资产失败: {e}"
            logger.error(error_msg, exc_info=True)
            self.error_occurred.emit(error_msg)
            return False
    
    def get_asset(self, asset_id: str) -> Optional[Asset]:
        """获取指定资产"""
        for asset in self.assets:
            if asset.id == asset_id:
                return asset
        return None
    
    def get_all_assets(self, category: Optional[str] = None) -> List[Asset]:
        """获取所有资产
        
        Args:
            category: 可选，指定分类名称，如果提供则只返回该分类的资产
            
        Returns:
            资产列表
        """
        if category is None:
            return self.assets.copy()
        return [asset for asset in self.assets if asset.category == category]
    
    def get_all_categories(self) -> List[str]:
        """获取所有分类
        
        Returns:
            分类列表（从配置文件读取）
        """
        # 从配置文件读取分类
        if not self.categories:
            self.categories = ["默认分类"]
        
        # 确保默认分类在最前面
        if "默认分类" not in self.categories:
            self.categories.insert(0, "默认分类")
        
        return self.categories.copy()
    
    def add_category(self, category_name: str) -> bool:
        """添加新分类
        
        Args:
            category_name: 分类名称
            
        Returns:
            是否添加成功
        """
        if not category_name or category_name.strip() == "":
            return False
        
        category_name = category_name.strip()
        
        if category_name in self.categories:
            return False
        
        # 添加分类
        self.categories.append(category_name)
        
        # 在资产库创建对应文件夹
        library_path = self.get_asset_library_path()
        if library_path and library_path.exists():
            category_folder = library_path / category_name
            if not category_folder.exists():
                try:
                    category_folder.mkdir(parents=True, exist_ok=True)
                    logger.info(f"创建分类文件夹: {category_folder}")
                except Exception as e:
                    logger.error(f"创建分类文件夹失败: {e}", exc_info=True)
        
        self._save_config()
        
        logger.info(f"已添加新分类: {category_name}")
        return True
    
    def remove_category(self, category_name: str) -> bool:
        """删除分类
        
        Args:
            category_name: 分类名称
            
        Returns:
            是否删除成功
        """
        # 不能删除默认分类
        if category_name == "默认分类":
            logger.warning("不能删除默认分类")
            return False
        
        if category_name not in self.categories:
            return False
        
        assets_in_category = [a for a in self.assets if a.category == category_name]
        if assets_in_category:
            # 将这些资产物理移动到默认分类文件夹
            library_path = self.get_asset_library_path()
            if library_path and library_path.exists():
                for asset in assets_in_category:
                    self._move_asset_to_category(asset, "默认分类")
            else:
                # 如果没有资产库，只更新配置
                for asset in assets_in_category:
                    asset.category = "默认分类"
            logger.info(f"已将 {len(assets_in_category)} 个资产从 {category_name} 移至默认分类")
        
        # 删除分类
        self.categories.remove(category_name)
        
        # 删除资产库中对应的文件夹
        library_path = self.get_asset_library_path()
        if library_path and library_path.exists():
            category_folder = library_path / category_name
            if category_folder.exists():
                try:
                    # 确保文件夹为空后再删除
                    if not any(category_folder.iterdir()):
                        category_folder.rmdir()
                        logger.info(f"删除分类文件夹: {category_folder}")
                    else:
                        logger.warning(f"分类文件夹不为空，无法删除: {category_folder}")
                except Exception as e:
                    logger.error(f"删除分类文件夹失败: {e}", exc_info=True)
        
        self._save_config()
        
        logger.info(f"已删除分类: {category_name}")
        return True
    
    def get_all_asset_names(self) -> List[str]:
        """获取所有资产名称
        
        Returns:
            资产名称列表
        """
        return [asset.name for asset in self.assets]
    
    def _get_pinyin(self, text: str) -> str:
        """获取文本的拼音
        
        Args:
            text: 输入文本
            
        Returns:
            拼音字符串（小写，无空格）
        """
        if lazy_pinyin is None:
            # 如果没有pypinyin，返回原文本的小写形式
            return text.lower()
        
        try:
            pinyin_list = lazy_pinyin(text, style=Style.NORMAL)
            return ''.join(pinyin_list).lower()
        except Exception as e:
            logger.warning(f"拼音转换失败: {e}")
            return text.lower()
    
    def search_assets(self, search_text: str, category: Optional[str] = None) -> List[Asset]:
        """搜索资产（支持拼音模糊搜索）
        
        Args:
            search_text: 搜索文本（支持中文和拼音）
            category: 可选，指定分类名称
            
        Returns:
            匹配的资产列表
        """
        if not search_text or not search_text.strip():
            # 如果搜索文本为空，返回所有资产
            return self.get_all_assets(category)
        
        search_text = search_text.strip().lower()
        search_pinyin = self._get_pinyin(search_text)
        
        candidates = self.get_all_assets(category)
        matched_assets = []
        
        for asset in candidates:
            asset_name = asset.name.lower()
            asset_name_pinyin = self._get_pinyin(asset.name)
            
            asset_desc = asset.description.lower() if asset.description else ""
            asset_desc_pinyin = self._get_pinyin(asset.description) if asset.description else ""
            
            asset_category = asset.category.lower()
            asset_category_pinyin = self._get_pinyin(asset.category)
            
            # 模糊匹配：检查是否包含搜索文本
            if (search_text in asset_name or 
                search_pinyin in asset_name_pinyin or
                search_text in asset_desc or 
                search_pinyin in asset_desc_pinyin or
                search_text in asset_category or 
                search_pinyin in asset_category_pinyin):
                matched_assets.append(asset)
        
        logger.debug(f"搜索 '{search_text}' 找到 {len(matched_assets)} 个匹配的资产")
        return matched_assets
    
    def sort_assets(self, assets: List[Asset], sort_method: str) -> List[Asset]:
        """对资产列表进行排序
        
        Args:
            assets: 要排序的资产列表
            sort_method: 排序方式
                - "添加时间（最新）": 按创建时间降序
                - "添加时间（最旧）": 按创建时间升序
                - "名称（A-Z）": 按名称升序
                - "名称（Z-A）": 按名称降序
                - "分类（A-Z）": 按分类升序
                - "分类（Z-A）": 按分类降序
        
        Returns:
            排序后的资产列表
        """
        if not assets:
            return []
        
        try:
            if sort_method == "添加时间（最新）":
                # 按创建时间降序（最新的在前）
                # 使用安全的排序键，确保 created_time 不为 None
                sorted_assets = sorted(assets, key=lambda x: x.created_time if x.created_time else datetime.min, reverse=True)
            elif sort_method == "添加时间（最旧）":
                # 按创建时间升序（最旧的在前）
                # 使用安全的排序键，确保 created_time 不为 None
                sorted_assets = sorted(assets, key=lambda x: x.created_time if x.created_time else datetime.min, reverse=False)
            elif sort_method == "名称（A-Z）":
                # 按名称升序
                sorted_assets = sorted(assets, key=lambda x: x.name.lower())
            elif sort_method == "名称（Z-A）":
                # 按名称降序
                sorted_assets = sorted(assets, key=lambda x: x.name.lower(), reverse=True)
            elif sort_method == "分类（A-Z）":
                # 按分类升序，同分类内按名称排序
                sorted_assets = sorted(assets, key=lambda x: (x.category.lower(), x.name.lower()))
            elif sort_method == "分类（Z-A）":
                # 按分类降序，同分类内按名称排序
                sorted_assets = sorted(assets, key=lambda x: (x.category.lower(), x.name.lower()), reverse=True)
            else:
                # 默认按添加时间降序
                sorted_assets = sorted(assets, key=lambda x: x.created_time, reverse=True)
            
            logger.debug(f"资产已按 '{sort_method}' 排序，共 {len(sorted_assets)} 个")
            return sorted_assets
        except Exception as e:
            logger.error(f"排序资产时出错: {e}", exc_info=True)
            return assets  # 出错时返回原列表
    
    def update_asset_description(self, asset_id: str, description: str) -> bool:
        """更新资产描述
        
        Args:
            asset_id: 资产ID
            description: 新的描述文本
            
        Returns:
            bool: 更新是否成功
        """
        asset = self.get_asset(asset_id)
        if not asset:
            logger.warning(f"资产不存在，无法更新描述: {asset_id}")
            return False
        
        asset.description = description
        
        self._save_config()
        logger.info(f"资产描述已更新并保存: {asset.name}")
        return True
    
    def update_asset_info(self, asset_id: str, new_name: str = None, new_category: str = None) -> bool:
        """更新资产信息（名称和/或分类）
        
        Args:
            asset_id: 资产ID
            new_name: 新的资产名称（可选）
            new_category: 新的分类（可选）
            
        Returns:
            bool: 更新是否成功
        """
        asset = self.get_asset(asset_id)
        if not asset:
            logger.warning(f"资产不存在，无法更新信息: {asset_id}")
            return False
        
        old_name = asset.name
        old_category = asset.category
        
        if new_name is not None and new_name.strip():
            asset.name = new_name.strip()
        
        # 更新分类（如果分类改变，物理移动文件）
        if new_category is not None and new_category.strip() and new_category != old_category:
            new_category = new_category.strip()
            # 如果是新分类，添加到分类列表
            if new_category not in self.categories:
                self.add_category(new_category)
            
            # 物理移动资产到新分类文件夹
            if self._move_asset_to_category(asset, new_category):
                logger.info(f"资产已移动到新分类: {old_category} -> {new_category}")
            else:
                # 如果移动失败，仅更新配置
                asset.category = new_category
                logger.warning(f"资产物理移动失败，仅更新配置: {old_category} -> {new_category}")
        
        self._save_config()
        
        # 记录日志
        changes = []
        if new_name and new_name != old_name:
            changes.append(f"名称: {old_name} -> {new_name}")
        if new_category and new_category != old_category:
            changes.append(f"分类: {old_category} -> {new_category}")
        
        if changes:
            logger.info(f"资产信息已更新: {', '.join(changes)}")
        
        return True
    
    def _calculate_size(self, path: Path) -> int:
        """计算文件或文件夹大小（字节）"""
        if path.is_file():
            return path.stat().st_size
        elif path.is_dir():
            total_size = 0
            for item in path.rglob('*'):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                    except:
                        pass
            return total_size
        return 0
    
    def set_preview_project(self, project_path: Path) -> bool:
        """设置预览工程路径
        
        Args:
            project_path: 预览工程路径
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            config = self.config_manager.load_user_config() or {}
            config["preview_project_path"] = str(project_path)
            self.config_manager.save_user_config(config)
            
            logger.info(f"预览工程路径已设置: {project_path}")
            return True
            
        except Exception as e:
            logger.error(f"设置预览工程路径失败: {e}", exc_info=True)
            return False
    
    def get_asset_library_path(self) -> Optional[Path]:
        """获取资产库路径"""
        config = self.config_manager.load_user_config()
        # 从配置中获取资产库路径，优先使用旧的单一路径，然后是新的多路径配置
        asset_library_path = config.get("asset_library_path", "")
        if not asset_library_path:
            # 尝试从配置中获取第一个资产库路径
            for key in config.get("asset_library_configs", {}).keys():
                if Path(key).exists():
                    asset_library_path = key
                    break
        
        if asset_library_path:
            return Path(asset_library_path)
        return None
    
    def set_asset_library_path(self, library_path: Path) -> bool:
        """设置资产库路径
        
        Args:
            library_path: 资产库路径
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            if not library_path.exists():
                library_path.mkdir(parents=True, exist_ok=True)
            
            # 第一步：保存当前资产库路径的配置
            current_lib_path = self.get_asset_library_path()
            if current_lib_path:
                logger.info(f"保存当前资产库路径的配置: {current_lib_path}")
                # 这里会保存当前路径的分类和资产数据
                self._save_config()
            
            # 第二步：更新配置中的资产库路径
            config = self.config_manager.load_user_config() or {}
            
            # 确保新的配置结构
            if "_version" not in config:
                config["_version"] = "2.0.0"
            
            # 清除旧的 asset_library_configs 字段（不再使用）
            if "asset_library_configs" in config:
                del config["asset_library_configs"]
            
            config["asset_library_path"] = str(library_path)
            self.config_manager.save_user_config(config)
            
            # 第三步：从新路径加载配置
            logger.info(f"从新资产库路径加载配置: {library_path}")
            self._load_config()
            
            logger.info(f"资产库路径已切换至: {library_path}")
            return True
            
        except Exception as e:
            logger.error(f"设置资产库路径失败: {e}", exc_info=True)
            return False
    
    def get_additional_preview_projects(self) -> List[str]:
        """获取额外的预览工程路径列表
        
        Returns:
            额外预览工程路径列表（字符串）
        """
        try:
            config = self.config_manager.load_user_config() or {}
            additional_paths = config.get("additional_preview_projects", [])
            
            # 确保返回的是字符串列表
            if isinstance(additional_paths, list):
                return [str(p) for p in additional_paths]
            
            logger.debug(f"已加载 {len(additional_paths)} 个额外预览工程路径")
            return additional_paths
            
        except Exception as e:
            logger.error(f"获取额外预览工程路径失败: {e}", exc_info=True)
            return []
    
    def get_additional_preview_projects_with_names(self) -> List[Dict[str, str]]:
        """获取额外的预览工程路径和名称列表
        
        Returns:
            包含path和name的字典列表，格式: [{"path": "...", "name": "..."}, ...]
        """
        try:
            config = self.config_manager.load_user_config() or {}
            
            # 支持新旧格式的兼容性
            additional_projects = config.get("additional_preview_projects_with_names", [])
            if not additional_projects:
                # 尝试从旧格式迁移
                old_paths = config.get("additional_preview_projects", [])
                additional_projects = [
                    {"path": str(p), "name": f"工程 {i+1}"} 
                    for i, p in enumerate(old_paths)
                ]
            
            logger.debug(f"已加载 {len(additional_projects)} 个额外预览工程")
            return additional_projects
            
        except Exception as e:
            logger.error(f"获取额外预览工程路径失败: {e}", exc_info=True)
            return []
    
    def set_additional_preview_projects(self, project_paths: List[str]) -> bool:
        """设置额外的预览工程路径列表
        
        Args:
            project_paths: 预览工程路径列表
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            config = self.config_manager.load_user_config() or {}
            
            # 验证所有路径都存在
            for path_str in project_paths:
                path = Path(path_str)
                if not path.exists():
                    logger.warning(f"预览工程路径不存在，跳过: {path_str}")
                    project_paths = [p for p in project_paths if p != path_str]
            
            config["additional_preview_projects"] = project_paths
            self.config_manager.save_user_config(config)
            
            logger.info(f"已保存 {len(project_paths)} 个额外预览工程路径")
            return True
            
        except Exception as e:
            logger.error(f"保存额外预览工程路径失败: {e}", exc_info=True)
            return False
    
    def set_additional_preview_projects_with_names(self, projects: List[Dict[str, str]]) -> bool:
        """设置额外的预览工程路径和名称列表
        
        Args:
            projects: 包含path和name的字典列表，格式: [{"path": "...", "name": "..."}, ...]
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            config = self.config_manager.load_user_config() or {}
            
            # 验证所有路径都存在
            valid_projects = []
            for project in projects:
                path_str = project.get("path", "")
                name = project.get("name", "")
                if not path_str or not name:
                    continue
                
                path = Path(path_str)
                if not path.exists():
                    logger.warning(f"预览工程路径不存在，跳过: {path_str}")
                    continue
                
                valid_projects.append({"path": path_str, "name": name})
            
            config["additional_preview_projects_with_names"] = valid_projects
            self.config_manager.save_user_config(config)
            
            logger.info(f"已保存 {len(valid_projects)} 个额外预览工程")
            return True
            
        except Exception as e:
            logger.error(f"保存额外预览工程路径失败: {e}", exc_info=True)
            return False
    
    def _sync_category_folders(self):
        """同步分类文件夹到资产库"""
        library_path = self.get_asset_library_path()
        if not library_path:
            return
        
        try:
            # 为每个分类创建文件夹
            for category in self.categories:
                category_folder = library_path / category
                if not category_folder.exists():
                    category_folder.mkdir(parents=True, exist_ok=True)
                    logger.info(f"创建分类文件夹: {category_folder}")
            
            logger.info("分类文件夹同步完成")
            
        except Exception as e:
            logger.error(f"同步分类文件夹失败: {e}", exc_info=True)
    
    def _move_asset_to_category(self, asset: Asset, new_category: str) -> bool:
        """将资产物理移动到新分类文件夹
        
        Args:
            asset: 资产对象
            new_category: 新分类名称
            
        Returns:
            成功返回True，失败返回False
        """
        library_path = self.get_asset_library_path()
        if not library_path or not library_path.exists():
            logger.warning("资产库路径未设置，无法移动资产")
            return False
        
        try:
            old_category_folder = library_path / asset.category
            new_category_folder = library_path / new_category
            
            # 确保新分类文件夹存在
            if not new_category_folder.exists():
                new_category_folder.mkdir(parents=True, exist_ok=True)
            
            # 构建新路径
            old_path = asset.path
            new_path = new_category_folder / old_path.name
            
            # 移动资产文件/文件夹
            if old_path.exists():
                shutil.move(str(old_path), str(new_path))
                logger.info(f"移动资产: {old_path} -> {new_path}")
                
                asset.path = new_path
            
            asset.category = new_category
            
            return True
            
        except Exception as e:
            logger.error(f"移动资产失败: {e}", exc_info=True)
            return False
    
    def get_preview_project(self) -> Optional[Path]:
        """获取预览工程路径
        
        优先级：
        1. 额外工程列表中的第一个工程
        2. 配置中的旧单个预览工程
        
        Returns:
            预览工程路径，不存在返回None
        """
        try:
            # 优先从额外工程中获取第一个
            additional_projects = self.get_additional_preview_projects_with_names()
            if additional_projects:
                first_project_path = additional_projects[0].get("path", "")
                if first_project_path:
                    path = Path(first_project_path)
                    if path.exists():
                        return path
            
            # 回退到旧的单个预览工程配置
            config = self.config_manager.load_user_config()
            preview_path = config.get("preview_project_path", "")
            if preview_path:
                path = Path(preview_path)
                if path.exists():
                    return path
            
            return None
        except Exception as e:
            logger.error(f"获取预览工程路径失败: {e}", exc_info=True)
            return None
    
    def clean_preview_project(self) -> bool:
        """清理预览工程的Content文件夹
        
        Returns:
            成功返回True，失败返回False
        """
        try:
            preview_project = self.get_preview_project()
            if not preview_project or not preview_project.exists():
                error_msg = "预览工程未设置或不存在"
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                return False
            
            content_dir = preview_project / "Content"
            if content_dir.exists():
                logger.info(f"清空预览工程Content文件夹: {content_dir}")
                shutil.rmtree(content_dir)
                content_dir.mkdir(parents=True, exist_ok=True)
                logger.info("预览工程Content文件夹已清理")
                return True
            else:
                logger.info("Content文件夹不存在，无需清理")
                return True
                
        except Exception as e:
            error_msg = f"清理预览工程失败: {e}"
            logger.error(error_msg, exc_info=True)
            self.error_occurred.emit(error_msg)
            return False
    
    def preview_asset(self, asset_id: str, progress_callback=None, preview_project_path: Optional[Path] = None) -> bool:
        """预览资产
        
        Args:
            asset_id: 资产ID
            progress_callback: 进度回调函数 (current, total, message)
            preview_project_path: 指定的预览工程路径（如果不提供则使用默认）
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            asset = self.get_asset(asset_id)
            if not asset:
                error_msg = f"未找到资产: {asset_id}"
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                return False
            
            # 使用提供的工程路径，或者获取默认工程
            if preview_project_path is None:
                preview_project = self.get_preview_project()
            else:
                preview_project = preview_project_path
            
            if not preview_project or not preview_project.exists():
                error_msg = "预览工程未设置或不存在，请先设置预览工程"
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                return False
            
            # 在后台线程中执行预览
            thread = threading.Thread(
                target=self._do_preview_asset,
                args=(asset, preview_project, progress_callback),
                daemon=True
            )
            thread.start()
            
            self.preview_started.emit(asset_id)
            return True
            
        except Exception as e:
            error_msg = f"启动预览失败: {e}"
            logger.error(error_msg, exc_info=True)
            self.error_occurred.emit(error_msg)
            return False
    
    def _safe_copytree(self, src: Path, dst: Path, max_depth: int = 20, 
                       progress_callback=None) -> None:
        """安全地复制目录树，限制最大深度防止无限递归
        
        Args:
            src: 源目录
            dst: 目标目录
            max_depth: 最大递归深度（默认20层）
            progress_callback: 进度回调函数 (current, total, message)
        """
        # 计算总文件数（用于进度报告）
        total_files = 0
        copied_files = 0
        
        if progress_callback:
            logger.info("正在计算文件总数...")
            for item in src.rglob('*'):
                if item.is_file() and not item.is_symlink():
                    # 跳过隐藏文件和系统文件
                    if not item.name.startswith('.') and item.name not in ['__pycache__', 'Thumbs.db', 'desktop.ini']:
                        total_files += 1
            logger.info(f"共需复制 {total_files} 个文件")
            progress_callback(0, total_files, f"准备复制 {total_files} 个文件...")
        
        def _copy_recursive(src_dir: Path, dst_dir: Path, current_depth: int = 0):
            """递归复制，带深度限制"""
            nonlocal copied_files
            
            if current_depth >= max_depth:
                logger.warning(f"达到最大复制深度 {max_depth}，跳过: {src_dir}")
                return
            
            dst_dir.mkdir(parents=True, exist_ok=True)
            
            # 遍历源目录中的所有项
            try:
                items = list(src_dir.iterdir())
            except (PermissionError, OSError) as e:
                logger.warning(f"无法访问目录 {src_dir}: {e}")
                return
            
            for item in items:
                try:
                    # 跳过符号链接
                    if item.is_symlink():
                        logger.debug(f"跳过符号链接: {item}")
                        continue
                    
                    # 跳过隐藏文件和系统文件
                    if item.name.startswith('.') or item.name in ['__pycache__', 'Thumbs.db', 'desktop.ini']:
                        continue
                    
                    dst_item = dst_dir / item.name
                    
                    if item.is_file():
                        # 复制文件
                        shutil.copy2(str(item), str(dst_item))
                        copied_files += 1
                        
                        # 报告进度
                        if progress_callback and total_files > 0:
                            progress = int((copied_files / total_files) * 100)
                            rel_path = item.relative_to(src)
                            progress_callback(copied_files, total_files, f"正在复制: {rel_path}")
                    elif item.is_dir():
                        # 递归复制子目录
                        _copy_recursive(item, dst_item, current_depth + 1)
                        
                except (PermissionError, OSError) as e:
                    logger.warning(f"复制失败 {item}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"处理 {item} 时出错: {e}")
                    continue
        
        try:
            logger.info(f"开始安全复制: {src} -> {dst} (最大深度: {max_depth})")
            _copy_recursive(src, dst)
            if progress_callback:
                progress_callback(total_files, total_files, "复制完成！")
            logger.info(f"复制完成: {dst}")
        except Exception as e:
            raise Exception(f"复制目录失败: {src} -> {dst}: {e}")
    
    def _safe_move_tree(self, src: Path, dst: Path, max_depth: int = 20, 
                        progress_callback=None) -> None:
        """安全地移动目录树，限制最大深度防止无限递归，支持实时进度报告
        
        Args:
            src: 源目录
            dst: 目标目录
            max_depth: 最大递归深度（默认20层）
            progress_callback: 进度回调函数 (current, total, message)
        """
        # 计算总文件数（用于进度报告）
        total_files = 0
        moved_files = 0
        
        if progress_callback:
            logger.info("正在计算文件总数...")
            for item in src.rglob('*'):
                if item.is_file() and not item.is_symlink():
                    # 跳过隐藏文件和系统文件
                    if not item.name.startswith('.') and item.name not in ['__pycache__', 'Thumbs.db', 'desktop.ini']:
                        total_files += 1
            logger.info(f"共需移动 {total_files} 个文件")
            progress_callback(0, total_files, f"准备移动 {total_files} 个文件...")
        
        def _move_recursive(src_dir: Path, dst_dir: Path, current_depth: int = 0):
            """递归移动，带深度限制"""
            nonlocal moved_files
            
            if current_depth >= max_depth:
                logger.warning(f"达到最大移动深度 {max_depth}，跳过: {src_dir}")
                return
            
            dst_dir.mkdir(parents=True, exist_ok=True)
            
            # 遍历源目录中的所有项
            try:
                items = list(src_dir.iterdir())
            except (PermissionError, OSError) as e:
                logger.warning(f"无法访问目录 {src_dir}: {e}")
                return
            
            for item in items:
                try:
                    # 跳过符号链接
                    if item.is_symlink():
                        logger.debug(f"跳过符号链接: {item}")
                        continue
                    
                    # 跳过隐藏文件和系统文件
                    if item.name.startswith('.') or item.name in ['__pycache__', 'Thumbs.db', 'desktop.ini']:
                        continue
                    
                    dst_item = dst_dir / item.name
                    
                    if item.is_file():
                        # 移动文件
                        shutil.move(str(item), str(dst_item))
                        moved_files += 1
                        
                        # 报告进度
                        if progress_callback and total_files > 0:
                            progress = int((moved_files / total_files) * 100)
                            rel_path = item.relative_to(src)
                            progress_callback(moved_files, total_files, f"正在移动: {rel_path}")
                    elif item.is_dir():
                        # 递归移动子目录
                        _move_recursive(item, dst_item, current_depth + 1)
                        
                except (PermissionError, OSError) as e:
                    logger.warning(f"移动失败 {item}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"处理 {item} 时出错: {e}")
                    continue
        
        try:
            logger.info(f"开始安全移动: {src} -> {dst} (最大深度: {max_depth})")
            _move_recursive(src, dst)
            
            # 删除源目录树（包括所有子目录）
            if src.exists():
                try:
                    shutil.rmtree(src)
                    logger.info(f"已删除源目录树: {src}")
                except Exception as e:
                    logger.warning(f"删除源目录树失败（部分文件可能已移动）: {e}")
            
            if progress_callback:
                progress_callback(total_files, total_files, "移动完成！")
            logger.info(f"移动完成: {dst}")
        except Exception as e:
            raise Exception(f"移动目录失败: {src} -> {dst}: {e}")
    
    def _safe_move_file(self, src: Path, dst: Path, progress_callback=None) -> None:
        """安全地移动单个文件，支持实时进度报告
        
        Args:
            src: 源文件
            dst: 目标文件
            progress_callback: 进度回调函数 (current, total, message)
        """
        try:
            if not src.is_file():
                raise ValueError(f"源路径不是文件: {src}")
            
            file_size = src.stat().st_size
            
            if progress_callback:
                progress_callback(0, 1, f"准备移动文件: {src.name}")
            
            # 简单地移动文件（通常很快）
            shutil.move(str(src), str(dst))
            
            if progress_callback:
                progress_callback(1, 1, f"已移动: {src.name}")
            
            logger.info(f"文件已移动: {src} -> {dst}")
            
        except Exception as e:
            logger.error(f"移动文件失败: {src} -> {dst}: {e}")
            raise Exception(f"移动文件失败: {e}")
    
    def _do_preview_asset(self, asset: Asset, preview_project: Path, progress_callback=None) -> None:
        """执行资产预览（后台线程）"""
        try:
            # 清空预览工程的Content文件夹
            content_dir = preview_project / "Content"
            
            # 检查资产路径是否在预览工程内（防止循环复制）
            try:
                asset_path_resolved = asset.path.resolve()
                content_dir_resolved = content_dir.resolve()
                
                # 检查资产是否在预览工程的Content目录内
                if asset_path_resolved == content_dir_resolved or \
                   content_dir_resolved in asset_path_resolved.parents:
                    error_msg = "不能预览位于预览工程Content目录内的资产，这会导致循环复制！\n\n请选择预览工程外的资产。"
                    logger.error(error_msg)
                    self.error_occurred.emit(error_msg)
                    return
            except Exception as e:
                logger.warning(f"检查路径时出错: {e}")
            
            if progress_callback:
                progress_callback(0, 1, "正在清空预览工程Content文件夹...")
            
            if content_dir.exists():
                logger.info("清空预览工程Content文件夹...")
                shutil.rmtree(content_dir)
            content_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制资产到Content文件夹
            logger.info(f"复制资产到预览工程: {asset.name}")
            if asset.asset_type == AssetType.PACKAGE:
                # A型：复制整个文件夹（保持原文件夹名称）
                dest_dir = content_dir / asset.path.name
                # 使用安全复制函数，避免符号链接导致的循环引用
                self._safe_copytree(asset.path, dest_dir, progress_callback=progress_callback)
            else:
                # B型：复制单个文件（保持原文件名）
                if progress_callback:
                    progress_callback(0, 1, f"正在复制: {asset.path.name}")
                dest_file = content_dir / asset.path.name
                shutil.copy2(asset.path, dest_file)
                if progress_callback:
                    progress_callback(1, 1, "复制完成！")
            
            # 启动虚幻引擎（在新线程中监听，不阻塞当前线程）
            logger.info("启动虚幻引擎预览工程...")
            
            # 通知进度对话框复制已完成，即将启动引擎
            if progress_callback:
                progress_callback(1, 1, "复制完成，正在启动虚幻引擎...")
            
            def launch_and_monitor():
                """在独立线程中启动和监听虚幻引擎"""
                try:
                    process = self._launch_unreal_project(preview_project)
                    
                    # 如果成功获取进程，等待进程结束后自动清理
                    if process:
                        logger.info("监听虚幻引擎进程，等待关闭后自动清理...")
                        process.wait()  # 阻塞等待进程结束
                        logger.info("虚幻引擎已关闭，开始处理截图和清理预览工程...")
                        
                        try:
                            self.process_screenshot(asset.id, preview_project)
                        except Exception as e:
                            logger.error(f"处理截图时出错: {e}", exc_info=True)
                        
                        # 自动清理Content文件夹
                        if content_dir.exists():
                            shutil.rmtree(content_dir)
                            content_dir.mkdir(parents=True, exist_ok=True)
                            logger.info("预览工程Content文件夹已自动清理完成")
                    
                    self.preview_finished.emit()
                except Exception as e:
                    logger.error(f"启动或监听虚幻引擎时出错: {e}", exc_info=True)
                    self.error_occurred.emit(f"启动虚幻引擎失败: {e}")
            
            # 在新线程中启动和监听虚幻引擎，不阻塞当前线程
            monitor_thread = threading.Thread(target=launch_and_monitor, daemon=True)
            monitor_thread.start()
            
        except Exception as e:
            error_msg = f"预览资产失败: {e}"
            logger.error(error_msg, exc_info=True)
            self.error_occurred.emit(error_msg)
    
    def _launch_unreal_project(self, project_path: Path):
        """启动虚幻引擎工程
        
        Returns:
            进程对象（如果可获取），用于监听引擎关闭；否则返回None
        """
        # 查找.uproject文件
        uproject_files = list(project_path.glob("*.uproject"))
        if not uproject_files:
            raise FileNotFoundError(f"未找到.uproject文件: {project_path}")
        
        uproject_file = uproject_files[0]
        
        # 使用subprocess.Popen启动，以便获取进程对象
        import sys
        
        try:
            if sys.platform == "win32":
                # Windows: 使用cmd /c start 启动，并通过psutil查找进程
                # 直接使用subprocess.Popen打开.uproject文件
                process = subprocess.Popen(
                    [str(uproject_file)],
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                logger.info(f"已启动工程: {uproject_file.name} (PID: {process.pid})")
                
                # Windows的shell=True会立即返回，需要找到实际的UE进程
                # 等待一下让UE启动
                import time
                time.sleep(2)
                
                # 尝试通过进程名查找UE编辑器进程
                ue_process = self._find_ue_process()
                if ue_process:
                    logger.info(f"找到虚幻引擎进程: PID {ue_process.pid}")
                    return ue_process
                else:
                    logger.warning("未能找到虚幻引擎进程，无法自动清理")
                    return None
                    
            elif sys.platform == "darwin":
                # macOS
                process = subprocess.Popen(
                    ['open', '-W', str(uproject_file)],  # -W 等待应用关闭
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                logger.info(f"已启动工程: {uproject_file.name}")
                return process
            else:
                # Linux
                process = subprocess.Popen(
                    ['xdg-open', str(uproject_file)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                logger.info(f"已启动工程: {uproject_file.name}")
                return process
                
        except Exception as e:
            logger.error(f"启动工程时出错: {e}")
            raise
    
    def _find_ue_process(self):
        """查找虚幻引擎编辑器进程（Windows）"""
        try:
            import psutil
            
            # 虚幻引擎编辑器的常见进程名
            ue_process_names = [
                'UE4Editor.exe',
                'UE4Editor-Win64-Debug.exe',
                'UE4Editor-Win64-DebugGame.exe',
                'UnrealEditor.exe',
                'UnrealEditor-Win64-Debug.exe',
                'UnrealEditor-Win64-DebugGame.exe',
            ]
            
            # 遍历所有进程
            for proc in psutil.process_iter(['name', 'create_time']):
                try:
                    if proc.info['name'] in ue_process_names:
                        # 找到最近启动的UE进程
                        return proc
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return None
            
        except ImportError:
            logger.warning("psutil未安装，无法查找UE进程。自动清理功能将不可用。")
            return None
        except Exception as e:
            logger.error(f"查找UE进程时出错: {e}")
            return None
    
    def migrate_asset(self, asset_id: str, target_project: Path, progress_callback=None) -> bool:
        """将资产从预览工程迁移到目标工程
        
        Args:
            asset_id: 资产ID
            target_project: 目标工程路径
            progress_callback: 进度回调函数 (current, total, message)
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            asset = self.get_asset(asset_id)
            if not asset:
                error_msg = f"未找到资产: {asset_id}"
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                return False
            
            if not target_project.exists():
                error_msg = f"目标工程不存在: {target_project}"
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                return False
            
            target_content = target_project / "Content"
            if not target_content.exists():
                error_msg = f"目标工程Content文件夹不存在: {target_content}"
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                return False
            
            # 复制资产到目标工程
            logger.info(f"迁移资产到目标工程: {asset.name}")
            if asset.asset_type == AssetType.PACKAGE:
                # A型：复制整个文件夹（保持原文件夹名称）
                dest_dir = target_content / asset.path.name
                
                # 如果目标已存在，先删除
                if dest_dir.exists():
                    if progress_callback:
                        progress_callback(0, 1, "正在删除已有的同名文件夹...")
                    shutil.rmtree(dest_dir)
                
                # 使用安全复制并报告进度
                self._safe_copytree(asset.path, dest_dir, progress_callback=progress_callback)
            else:
                # B型：复制单个文件（保持原文件名）
                if progress_callback:
                    progress_callback(0, 1, f"正在复制: {asset.path.name}")
                dest_file = target_content / asset.path.name
                shutil.copy2(asset.path, dest_file)
                if progress_callback:
                    progress_callback(1, 1, "复制完成！")
            
            config = self.config_manager.load_user_config()
            config["last_target_project_path"] = str(target_project)
            self.config_manager.save_user_config(config)
            
            logger.info(f"资产迁移成功: {asset.name} -> {target_project}")
            return True
            
        except Exception as e:
            error_msg = f"迁移资产失败: {e}"
            logger.error(error_msg, exc_info=True)
            self.error_occurred.emit(error_msg)
            return False
    
    def process_screenshot(self, asset_id: str, preview_project: Path) -> None:
        """处理预览截图
        
        在虚幻引擎关闭后，查找并移动截图到缩略图目录
        
        Args:
            asset_id: 资产ID
            preview_project: 预览工程路径
        """
        try:
            asset = self.get_asset(asset_id)
            if not asset:
                logger.warning(f"未找到资产: {asset_id}")
                return
            
            has_thumbnail = asset.thumbnail_path and Path(asset.thumbnail_path).exists()
            
            # 查找截图文件（根据缩略图来源决定搜索策略）
            screenshot_path, source = self._find_screenshot(preview_project, asset.thumbnail_source)
            
            if not screenshot_path:
                if has_thumbnail:
                    logger.info(f"资产 {asset.name} 保留原缩略图，未找到新截图")
                else:
                    logger.info(f"未找到资产 {asset.name} 的截图")
                return
            
            # 目标缩略图路径
            thumbnail_filename = f"{asset.id}.png"
            thumbnail_path = self.thumbnails_dir / thumbnail_filename
            
            # 移动截图到缩略图目录
            try:
                # 如果已存在旧缩略图，先删除
                if thumbnail_path.exists():
                    thumbnail_path.unlink()
                    logger.debug(f"删除旧缩略图: {thumbnail_path}")
                
                # 移动新截图
                shutil.move(str(screenshot_path), str(thumbnail_path))
                logger.info(f"截图已移动: {screenshot_path} -> {thumbnail_path}")
                
                asset.thumbnail_path = thumbnail_path
                asset.thumbnail_source = source  # 记录缩略图来源
                self._save_config()
                
                # 发送信号通知UI更新
                self.thumbnail_updated.emit(asset_id, str(thumbnail_path))
                logger.info(f"资产 {asset.name} 的缩略图已更新，来源: {source}")
                
            except Exception as e:
                logger.error(f"移动截图文件时出错: {e}", exc_info=True)
                
        except Exception as e:
            logger.error(f"处理截图时出错: {e}", exc_info=True)
    
    def _find_screenshot(self, preview_project: Path, thumbnail_source: Optional[str] = None) -> tuple[Optional[Path], Optional[str]]:
        """查找截图文件
        
        查找策略：
        1. 优先在 {预览工程}/Saved/Screenshots/ 及其子文件夹下查找用户主动截图
        2. 如果已获取过 Saved/Screenshots/ 的图片，只有新图片才更新
        3. 如果找不到，在 {预览工程}/Saved/ 下查找自动保存的截图
        
        Args:
            preview_project: 预览工程路径
            thumbnail_source: 缩略图来源（screenshots 或 autosave，用于判断是否需要更新）
            
        Returns:
            元组 (截图文件路径, 来源)，如果未找到返回 (None, None)
            来源值为 "screenshots" 或 "autosave"
        """
        try:
            # 第一步：查找用户截图
            screenshots_dir = preview_project / "Saved" / "Screenshots"
            
            if screenshots_dir.exists():
                latest_screenshot = None
                latest_mtime = 0
                
                # 扫描 Screenshots 当前目录
                for file_path in screenshots_dir.glob("*.png"):
                    mtime = file_path.stat().st_mtime
                    if mtime > latest_mtime:
                        latest_mtime = mtime
                        latest_screenshot = file_path
                
                # 扫描所有子文件夹
                for subdir in screenshots_dir.iterdir():
                    if subdir.is_dir():
                        for file_path in subdir.glob("*.png"):
                            mtime = file_path.stat().st_mtime
                            if mtime > latest_mtime:
                                latest_mtime = mtime
                                latest_screenshot = file_path
                
                if latest_screenshot:
                    logger.info(f"找到用户截图: {latest_screenshot}")
                    return latest_screenshot, "screenshots"
            
            # 第二步：如果已获取过 Saved/Screenshots/ 的图片，不再查找自动保存图
            if thumbnail_source == "screenshots":
                logger.debug(f"已获取过用户截图，不再查找自动保存的截图")
                return None, None
            
            # 第三步：查找自动保存的截图
            saved_dir = preview_project / "Saved"
            
            if saved_dir.exists():
                latest_autosave = None
                latest_mtime = 0
                
                # 在 Saved 目录下查找所有 PNG 文件（包括 Saved 根目录和所有子目录）
                for file_path in saved_dir.rglob("*.png"):
                    # 跳过 Screenshots 子目录中的文件（已在第一步检查过）
                    if "Screenshots" in str(file_path):
                        continue
                    
                    mtime = file_path.stat().st_mtime
                    if mtime > latest_mtime:
                        latest_mtime = mtime
                        latest_autosave = file_path
                
                if latest_autosave:
                    logger.info(f"找到自动保存的截图: {latest_autosave}")
                    return latest_autosave, "autosave"
            
            logger.debug(f"未找到任何截图")
            return None, None
            
        except Exception as e:
            logger.error(f"查找截图时出错: {e}", exc_info=True)
            return None, None
    

