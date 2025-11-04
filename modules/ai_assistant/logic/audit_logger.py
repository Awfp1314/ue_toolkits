# -*- coding: utf-8 -*-

"""
审计日志记录器
记录所有工具调用和用户确认操作
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from core.logger import get_logger

logger = get_logger(__name__)


class AuditLogger:
    """
    审计日志记录器
    
    v0.3: 记录工具调用的审计信息
    - 工具名称
    - 参数
    - 预览结果
    - 确认人
    - 时间戳
    - 执行结果
    """
    
    def __init__(self, log_path: Optional[Path] = None):
        """
        初始化审计日志记录器
        
        Args:
            log_path: 审计日志文件路径（由 PathUtils.get_user_logs_dir() 提供）
        """
        self.logger = logger
        
        # 审计日志路径
        if log_path is None:
            try:
                from core.utils.path_utils import PathUtils
                path_utils = PathUtils()
                self.log_path = path_utils.get_user_logs_dir() / "tool_audit.log"
            except Exception as e:
                self.logger.warning(f"无法获取日志目录，使用默认路径: {e}")
                self.log_path = Path.home() / ".ue_toolkit" / "logs" / "tool_audit.log"
        else:
            self.log_path = log_path
        
        # 确保目录存在
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.error(f"创建审计日志目录失败: {e}")
        
        self.logger.info(f"审计日志记录器初始化完成（路径: {self.log_path}）")
    
    def log_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        preview: str,
        user_confirmed: bool,
        result: Optional[Dict[str, Any]] = None,
        user_name: str = "default_user"
    ):
        """
        记录工具调用
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            preview: 预览结果
            user_confirmed: 用户是否确认
            result: 执行结果（如果已执行）
            user_name: 确认人标识
        """
        try:
            # 构建审计记录
            audit_record = {
                "timestamp": datetime.now().isoformat(),
                "tool_name": tool_name,
                "arguments": arguments,
                "preview_summary": preview[:500] if preview else "",  # 限制长度
                "user_confirmed": user_confirmed,
                "user_name": user_name,
                "result": result if result else None,
                "success": result.get('success', None) if result else None
            }
            
            # 写入审计日志（追加模式）
            with open(self.log_path, 'a', encoding='utf-8') as f:
                # 每条记录一行 JSON
                f.write(json.dumps(audit_record, ensure_ascii=False) + '\n')
            
            self.logger.info(f"审计记录已写入：{tool_name} (确认: {user_confirmed})")
        
        except Exception as e:
            self.logger.error(f"写入审计日志失败: {e}", exc_info=True)
    
    def get_recent_audits(self, limit: int = 10) -> list:
        """
        获取最近的审计记录
        
        Args:
            limit: 返回记录数量
            
        Returns:
            list: 审计记录列表
        """
        try:
            if not self.log_path.exists():
                return []
            
            records = []
            
            with open(self.log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 读取最后 N 行
            for line in lines[-limit:]:
                try:
                    record = json.loads(line.strip())
                    records.append(record)
                except json.JSONDecodeError:
                    continue
            
            return records
        
        except Exception as e:
            self.logger.error(f"读取审计日志失败: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取审计统计
        
        Returns:
            Dict: 统计信息 {total_calls, confirmed_calls, rejected_calls}
        """
        try:
            if not self.log_path.exists():
                return {
                    "total_calls": 0,
                    "confirmed_calls": 0,
                    "rejected_calls": 0
                }
            
            with open(self.log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            total = 0
            confirmed = 0
            rejected = 0
            
            for line in lines:
                try:
                    record = json.loads(line.strip())
                    total += 1
                    
                    if record.get('user_confirmed'):
                        confirmed += 1
                    else:
                        rejected += 1
                
                except json.JSONDecodeError:
                    continue
            
            return {
                "total_calls": total,
                "confirmed_calls": confirmed,
                "rejected_calls": rejected,
                "log_path": str(self.log_path)
            }
        
        except Exception as e:
            self.logger.error(f"获取审计统计失败: {e}")
            return {
                "total_calls": 0,
                "confirmed_calls": 0,
                "rejected_calls": 0
            }

