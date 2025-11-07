# -*- coding: utf-8 -*-

"""
资产导入器（测试功能）
将资产导入到正在运行的虚幻引擎项目中
"""

import shutil
import psutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from core.logger import get_logger

logger = get_logger(__name__)


class AssetImporter:
    """资产导入器（测试版本）"""
    
    def __init__(self, asset_manager_logic=None):
        """初始化资产导入器
        
        Args:
            asset_manager_logic: asset_manager 模块的逻辑层实例
        """
        self.asset_manager_logic = asset_manager_logic
        self.logger = logger
    
    def _find_running_ue_project(self) -> Optional[Path]:
        """查找正在运行的UE项目
        
        Returns:
            Optional[Path]: 项目路径，如果未找到则返回None
        """
        try:
            # 查找UE编辑器进程
            ue_process_names = [
                'UnrealEditor.exe',
                'UE4Editor.exe', 
                'UE5Editor.exe',
                'UnrealEditor-Win64-Debug.exe',
                'UnrealEditor-Win64-DebugGame.exe'
            ]
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_name = proc.info['name']
                    if proc_name and any(ue_name.lower() in proc_name.lower() for ue_name in ue_process_names):
                        # 找到UE进程，尝试从命令行参数获取项目路径
                        cmdline = proc.info.get('cmdline')
                        if cmdline:
                            for arg in cmdline:
                                if arg and arg.endswith('.uproject'):
                                    project_file = Path(arg)
                                    if project_file.exists():
                                        project_dir = project_file.parent
                                        self.logger.info(f"找到正在运行的UE项目: {project_dir}")
                                        return project_dir
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            self.logger.warning("未找到正在运行的UE项目")
            return None
        
        except Exception as e:
            self.logger.error(f"查找UE项目失败: {e}", exc_info=True)
            return None
    
    def import_asset_to_ue(self, asset_name: str, target_project_path: str = None) -> Dict[str, Any]:
        """将资产导入到UE项目
        
        这是一个测试功能，简化实现：
        1. 自动检测正在运行的UE项目
        2. 查找资产
        3. 复制到UE项目的Content目录
        
        Args:
            asset_name: 资产名称
            target_project_path: 目标UE项目路径（可选，如果为None则自动检测）
            
        Returns:
            Dict: {
                'success': bool,
                'message': str,
                'asset_name': str,
                'source_path': str,
                'target_path': str
            }
        """
        try:
            if not self.asset_manager_logic:
                return {
                    'success': False,
                    'message': '⚠️ 资产管理器未连接',
                    'asset_name': asset_name
                }
            
            # 1. 查找资产
            assets = self.asset_manager_logic.get_all_assets()
            target_asset = None
            
            for asset in assets:
                if hasattr(asset, 'name') and asset.name.lower() == asset_name.lower():
                    target_asset = asset
                    break
            
            if not target_asset:
                available_assets = [a.name for a in assets if hasattr(a, 'name')]
                return {
                    'success': False,
                    'message': f'[错误] 未找到名为 "{asset_name}" 的资产\n\n可用资产: {", ".join(available_assets[:10])}',
                    'asset_name': asset_name
                }
            
            # 2. 获取资产路径
            if not hasattr(target_asset, 'path') or not target_asset.path:
                return {
                    'success': False,
                    'message': f'[错误] 资产 "{asset_name}" 没有有效路径',
                    'asset_name': asset_name
                }
            
            source_path = Path(target_asset.path)
            if not source_path.exists():
                return {
                    'success': False,
                    'message': f'[错误] 资产路径不存在: {source_path}',
                    'asset_name': asset_name,
                    'source_path': str(source_path)
                }
            
            # 3. 自动检测正在运行的UE项目（如果未指定路径）
            if not target_project_path:
                project_path = self._find_running_ue_project()
                if not project_path:
                    asset_info = self._get_asset_info(target_asset, source_path)
                    return {
                        'success': False,
                        'message': f'''[错误] 未检测到正在运行的虚幻引擎项目

已找到资产: {asset_name}
{asset_info}

请先执行以下操作:
1. 打开虚幻引擎编辑器
2. 打开你想要导入资产的项目
3. 保持编辑器运行，然后再次尝试导入

提示: 或者你也可以手动指定项目路径（不推荐）''',
                        'asset_name': asset_name,
                        'source_path': str(source_path),
                        'requires_running_ue': True
                    }
            else:
                project_path = Path(target_project_path)
            
            # 4. 验证目标项目路径
            content_path = project_path / "Content"
            
            if not project_path.exists():
                return {
                    'success': False,
                    'message': f'[错误] 目标项目路径不存在: {project_path}',
                    'asset_name': asset_name,
                    'target_path': str(project_path)
                }
            
            if not content_path.exists():
                # 尝试查找.uproject文件
                uproject_files = list(project_path.glob("*.uproject"))
                if uproject_files:
                    # 如果找到了.uproject文件，创建Content目录
                    content_path.mkdir(exist_ok=True)
                    self.logger.info(f"创建Content目录: {content_path}")
                else:
                    return {
                        'success': False,
                        'message': f'[错误] 目标路径不是有效的UE项目（未找到Content文件夹或.uproject文件）',
                        'asset_name': asset_name,
                        'target_path': str(project_path)
                    }
            
            # 5. 执行复制
            target_asset_path = content_path / source_path.name
            
            # 检查是否已存在
            if target_asset_path.exists():
                return {
                    'success': False,
                    'message': f'[警告] 目标位置已存在同名资产: {target_asset_path}\n\n请先在UE中删除或重命名现有资产',
                    'asset_name': asset_name,
                    'source_path': str(source_path),
                    'target_path': str(target_asset_path)
                }
            
            # 复制资产
            if source_path.is_dir():
                shutil.copytree(source_path, target_asset_path)
                self.logger.info(f"已复制资产文件夹: {source_path} -> {target_asset_path}")
            else:
                shutil.copy2(source_path, target_asset_path)
                self.logger.info(f"已复制资产文件: {source_path} -> {target_asset_path}")
            
            # 检查是否是自动检测的项目
            auto_detected = not target_project_path
            project_info = f"[目标项目]: {project_path.name} (自动检测)" if auto_detected else f"[目标项目]: {project_path.name}"
            
            return {
                'success': True,
                'message': f'''[成功] 资产导入成功!

[资产名称]: {asset_name}
{project_info}
[源路径]: {source_path}
[目标路径]: {target_asset_path}

下一步:
1. 在虚幻引擎编辑器中，右键点击Content Browser
2. 选择 "Refresh" 或按 Ctrl+R
3. 导入的资产将出现在Content根目录下

导入完成！''',
                'asset_name': asset_name,
                'source_path': str(source_path),
                'target_path': str(target_asset_path),
                'auto_detected': auto_detected
            }
        
        except PermissionError as e:
            self.logger.error(f"权限错误: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'[错误] 权限不足，无法复制资产\n\n错误: {str(e)}\n\n请确保:\n1. UE编辑器已关闭该资产\n2. 您有写入目标目录的权限',
                'asset_name': asset_name
            }
        
        except Exception as e:
            self.logger.error(f"导入资产失败: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'[错误] 导入资产时出错: {str(e)}',
                'asset_name': asset_name
            }
    
    def _get_asset_info(self, asset, source_path: Path) -> str:
        """获取资产信息的格式化字符串"""
        info_parts = []
        
        # 基本信息
        asset_type = asset.asset_type.value if hasattr(asset, 'asset_type') else '未知'
        category = asset.category if hasattr(asset, 'category') else '未分类'
        size = asset._format_size() if hasattr(asset, '_format_size') else '未知大小'
        
        info_parts.append(f"**类型**: {asset_type}")
        info_parts.append(f"**分类**: {category}")
        info_parts.append(f"**路径**: {source_path}")
        info_parts.append(f"**大小**: {size}")
        
        # 文件信息
        if source_path.is_dir():
            files = list(source_path.glob("**/*"))
            file_count = len([f for f in files if f.is_file()])
            info_parts.append(f"**文件数量**: {file_count} 个文件")
        else:
            info_parts.append(f"**文件类型**: 单个文件")
        
        return "\n".join(info_parts)
    
    def list_importable_assets(self) -> str:
        """列出所有可导入的资产
        
        Returns:
            str: 可导入资产列表的格式化字符串
        """
        if not self.asset_manager_logic:
            return "[警告] 资产管理器未连接"
        
        try:
            assets = self.asset_manager_logic.get_all_assets()
            
            if not assets:
                return "[提示] 当前资产库为空\n\n请先在资产管理器中添加资产"
            
            result = [f"[可导入的资产] (共 {len(assets)} 个)\n"]
            
            # 按分类组织
            categories = {}
            for asset in assets:
                category = asset.category if hasattr(asset, 'category') else '未分类'
                if category not in categories:
                    categories[category] = []
                categories[category].append(asset)
            
            for category, cat_assets in categories.items():
                result.append(f"\n{category} ({len(cat_assets)} 个):")
                for asset in cat_assets[:10]:  # 每个分类最多显示10个
                    name = asset.name if hasattr(asset, 'name') else '未命名'
                    asset_type = asset.asset_type.value if hasattr(asset, 'asset_type') else '未知'
                    result.append(f"  - {name} ({asset_type})")
                
                if len(cat_assets) > 10:
                    result.append(f"  ... 还有 {len(cat_assets) - 10} 个")
            
            result.append("\n[提示] 要导入资产，只需告诉我资产名称，系统会自动检测正在运行的UE项目")
            
            return "\n".join(result)
        
        except Exception as e:
            self.logger.error(f"列出资产失败: {e}", exc_info=True)
            return f"[错误] 获取资产列表时出错: {str(e)}"

