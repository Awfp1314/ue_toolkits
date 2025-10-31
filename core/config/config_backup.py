# -*- coding: utf-8 -*-

"""
配置备份管理器模块
负责配置文件的备份、恢复和清理
"""

import json
import shutil
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from core.logger import get_logger


class ConfigBackupManager:
    """配置备份管理器"""
    
    def __init__(self, module_name: str, user_config_path: Path, backup_dir: Path):
        """初始化备份管理器
        
        Args:
            module_name: 模块名称
            user_config_path: 用户配置文件路径
            backup_dir: 备份目录路径
        """
        self.module_name = module_name
        self.user_config_path = user_config_path
        self.backup_dir = backup_dir
        self.logger = get_logger(f"config_backup.{module_name}")
        
        # 限制备份文件数量
        self.max_backup_files = 10
        
        # 确保备份目录存在
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def backup_config(self, reason: str = "manual", config: Optional[Dict[str, Any]] = None) -> bool:
        """备份配置数据
        
        改进的备份策略：
        1. 备份新配置（即将保存的配置）
        2. 使用带时间戳和原因的文件名，确保唯一性
        3. 验证备份文件的有效性
        4. 自动清理旧备份
        
        Args:
            reason: 备份原因（用于文件命名）
                - manual: 手动备份
                - manual_save: 手动保存前备份
                - auto_upgrade: 自动升级前备份
                - recovery: 恢复前备份
                - scheduled: 定时备份
            config: 要备份的配置字典。如果为 None，则从现有文件读取
            
        Returns:
            bool: 备份是否成功
        """
        try:
            # 如果没有提供新配置，尝试从现有文件读取
            if config is None:
                if not self.user_config_path.exists():
                    self.logger.debug("配置文件不存在，无需备份")
                    return True
                try:
                    with open(self.user_config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                except Exception as e:
                    self.logger.error(f"读取现有配置文件失败: {e}")
                    return False
            
            if not config or not isinstance(config, dict):
                self.logger.error("配置数据无效")
                return False
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]  # 精确到毫秒的前3位
            safe_reason = reason.replace(" ", "_").replace("/", "_").replace("\\", "_")
            backup_filename = f"{self.module_name}_config_{timestamp}_{safe_reason}.json"
            backup_path = self.backup_dir / backup_filename
            
            # 备份新配置
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            if not self._verify_backup(backup_path):
                self.logger.error(f"备份文件验证失败: {backup_path}")
                # 删除无效的备份文件
                backup_path.unlink()
                return False
            
            self.logger.info(f"配置文件备份成功: {backup_path.name} (原因: {reason})")
            
            self._cleanup_old_backups()
            
            return True
            
        except Exception as e:
            self.logger.error(f"备份配置文件失败: {e}", exc_info=True)
            return False
    
    def _verify_backup(self, backup_path: Path) -> bool:
        """验证备份文件的有效性
        
        验证步骤：
        1. 文件存在性检查
        2. 文件大小检查（不能为空）
        3. JSON格式验证
        4. 配置结构验证
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            bool: 备份文件是否有效
        """
        try:
            if not backup_path.exists():
                self.logger.error(f"备份文件不存在: {backup_path}")
                return False
            
            file_size = backup_path.stat().st_size
            if file_size == 0:
                self.logger.error(f"备份文件为空: {backup_path}")
                return False
            
            if file_size < 10:  # 至少应该有 "{}" 这样的最小JSON
                self.logger.error(f"备份文件过小，可能损坏: {backup_path} ({file_size} bytes)")
                return False
            
            try:
                with open(backup_path, 'r', encoding='utf-8') as f:
                    backup_config = json.load(f)
            except json.JSONDecodeError as e:
                self.logger.error(f"备份文件JSON格式无效: {backup_path}, 错误: {e}")
                return False
            
            if not isinstance(backup_config, dict):
                self.logger.error(f"备份文件配置结构无效（不是字典类型）: {backup_path}")
                return False
            
            if not backup_config:
                self.logger.warning(f"备份文件配置为空字典: {backup_path}")
                # 空字典也算有效，只是警告
            
            # 可选：验证必需字段
            if '_version' not in backup_config:
                self.logger.warning(f"备份文件缺少版本号: {backup_path}")
                # 缺少版本号不算致命错误，只是警告
            
            self.logger.debug(f"备份文件验证通过: {backup_path.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"验证备份文件时发生异常: {backup_path}, 错误: {e}")
            return False
    
    def _cleanup_old_backups(self) -> None:
        """清理旧的备份文件，保留最新的N个
        
        清理策略：
        1. 按修改时间排序，保留最新的N个
        2. 删除超过限制的旧文件
        3. 记录清理统计信息
        """
        try:
            backup_files = list(self.backup_dir.glob(f"{self.module_name}_config_*.json"))
            
            if not backup_files:
                self.logger.debug("没有备份文件需要清理")
                return
            
            total_count = len(backup_files)
            self.logger.debug(f"当前备份文件总数: {total_count}")
            
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            files_to_delete = backup_files[self.max_backup_files:]
            
            if not files_to_delete:
                self.logger.debug(f"备份文件数量 ({total_count}) 未超过限制 ({self.max_backup_files})，无需清理")
                return
            
            deleted_count = 0
            failed_count = 0
            
            for old_file in files_to_delete:
                try:
                    file_size = old_file.stat().st_size
                    old_file.unlink()
                    deleted_count += 1
                    self.logger.info(f"删除旧备份文件: {old_file.name} ({file_size} bytes)")
                except Exception as e:
                    failed_count += 1
                    self.logger.error(f"删除备份文件失败: {old_file.name}, 错误: {e}")
            
            remaining_count = total_count - deleted_count
            self.logger.info(
                f"备份清理完成 - 总数: {total_count}, "
                f"删除: {deleted_count}, 失败: {failed_count}, 保留: {remaining_count}"
            )
            
        except Exception as e:
            self.logger.error(f"清理旧备份文件时发生异常: {e}", exc_info=True)
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有可用的备份文件
        
        Returns:
            List[Dict[str, Any]]: 备份文件信息列表，每个元素包含：
                - path: 备份文件路径
                - filename: 文件名
                - size: 文件大小（字节）
                - mtime: 修改时间（时间戳）
                - mtime_str: 修改时间（可读字符串）
                - reason: 备份原因（从文件名解析）
                - valid: 是否有效
        """
        backups = []
        
        try:
            backup_files = list(self.backup_dir.glob(f"{self.module_name}_config_*.json"))
            
            # 按修改时间排序（最新的在前）
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for backup_file in backup_files:
                try:
                    stat_info = backup_file.stat()
                    mtime = stat_info.st_mtime
                    mtime_dt = datetime.datetime.fromtimestamp(mtime)
                    
                    # 从文件名解析备份原因
                    # 格式: {module_name}_config_{timestamp}_{reason}.json
                    parts = backup_file.stem.split('_')
                    reason = parts[-1] if len(parts) >= 4 else "unknown"
                    
                    is_valid = self._verify_backup(backup_file)
                    
                    backup_info = {
                        'path': backup_file,
                        'filename': backup_file.name,
                        'size': stat_info.st_size,
                        'mtime': mtime,
                        'mtime_str': mtime_dt.strftime('%Y-%m-%d %H:%M:%S'),
                        'reason': reason,
                        'valid': is_valid
                    }
                    
                    backups.append(backup_info)
                    
                except Exception as e:
                    self.logger.warning(f"处理备份文件信息失败: {backup_file.name}, 错误: {e}")
                    continue
            
            self.logger.debug(f"找到 {len(backups)} 个备份文件")
            return backups
            
        except Exception as e:
            self.logger.error(f"列出备份文件时发生异常: {e}")
            return []
    
    def restore_from_backup(self, backup_index: int = 0) -> Optional[Dict[str, Any]]:
        """从备份恢复配置
        
        Args:
            backup_index: 备份索引（0表示最新的备份，1表示第二新的，以此类推）
            
        Returns:
            Optional[Dict[str, Any]]: 恢复的配置数据，失败则返回None
        """
        try:
            backups = self.list_backups()
            
            if not backups:
                self.logger.error("没有可用的备份文件")
                return None
            
            if backup_index < 0 or backup_index >= len(backups):
                self.logger.error(
                    f"备份索引超出范围: {backup_index}, "
                    f"可用范围: 0-{len(backups)-1}"
                )
                return None
            
            backup_info = backups[backup_index]
            backup_path = backup_info['path']
            
            self.logger.info(
                f"准备从备份恢复配置: {backup_info['filename']} "
                f"(时间: {backup_info['mtime_str']}, 原因: {backup_info['reason']})"
            )
            
            if not backup_info['valid']:
                self.logger.error(f"备份文件无效，无法恢复: {backup_info['filename']}")
                return None
            
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_config = json.load(f)
            
            self.logger.info(
                f"成功从备份加载配置: {backup_info['filename']} "
                f"(时间: {backup_info['mtime_str']})"
            )
            return backup_config
            
        except Exception as e:
            self.logger.error(f"从备份恢复配置时发生异常: {e}", exc_info=True)
            return None
    
    def get_backup_stats(self) -> Dict[str, Any]:
        """获取备份统计信息
        
        Returns:
            Dict[str, Any]: 备份统计信息，包含：
                - total_count: 备份文件总数
                - valid_count: 有效备份数
                - invalid_count: 无效备份数
                - total_size: 总大小（字节）
                - oldest_backup: 最旧备份信息
                - newest_backup: 最新备份信息
        """
        try:
            backups = self.list_backups()
            
            if not backups:
                return {
                    'total_count': 0,
                    'valid_count': 0,
                    'invalid_count': 0,
                    'total_size': 0,
                    'oldest_backup': None,
                    'newest_backup': None
                }
            
            valid_backups = [b for b in backups if b['valid']]
            invalid_backups = [b for b in backups if not b['valid']]
            total_size = sum(b['size'] for b in backups)
            
            stats = {
                'total_count': len(backups),
                'valid_count': len(valid_backups),
                'invalid_count': len(invalid_backups),
                'total_size': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'oldest_backup': backups[-1] if backups else None,
                'newest_backup': backups[0] if backups else None
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"获取备份统计信息时发生异常: {e}")
            return {
                'total_count': 0,
                'valid_count': 0,
                'invalid_count': 0,
                'total_size': 0,
                'oldest_backup': None,
                'newest_backup': None
            }

