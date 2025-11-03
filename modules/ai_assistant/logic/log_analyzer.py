# -*- coding: utf-8 -*-

"""
日志分析器
读取和分析日志文件，帮助用户诊断问题
"""

import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from core.logger import get_logger
from core.utils.path_utils import PathUtils

logger = get_logger(__name__)


class LogAnalyzer:
    """日志文件分析器"""
    
    def __init__(self):
        """初始化日志分析器"""
        self.path_utils = PathUtils()
        self.logger = logger
        
        # 获取日志目录
        self.log_dir = self.path_utils.get_user_logs_dir()
        self.logger.info(f"日志分析器初始化，日志目录: {self.log_dir}")
    
    def get_recent_logs(self, hours: int = 24) -> str:
        """获取最近的日志文件列表
        
        Args:
            hours: 时间范围（小时）
            
        Returns:
            str: 日志文件列表
        """
        try:
            if not self.log_dir.exists():
                return "⚠️ 日志目录不存在。"
            
            log_files = []
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            for log_file in self.log_dir.glob('*.log'):
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if mtime > cutoff_time:
                    log_files.append({
                        'name': log_file.name,
                        'path': log_file,
                        'mtime': mtime,
                        'size': log_file.stat().st_size
                    })
            
            if not log_files:
                return f"📋 最近 {hours} 小时内没有新的日志文件。"
            
            # 按修改时间排序
            log_files.sort(key=lambda x: x['mtime'], reverse=True)
            
            # 格式化输出
            result = [f"📋 **最近 {hours} 小时的日志文件**:\n"]
            for log in log_files:
                size_kb = log['size'] / 1024
                time_str = log['mtime'].strftime('%Y-%m-%d %H:%M:%S')
                result.append(f"  - **{log['name']}** ({size_kb:.1f} KB, {time_str})")
            
            return "\n".join(result)
        
        except Exception as e:
            self.logger.error(f"获取日志列表失败: {e}", exc_info=True)
            return f"❌ 获取日志列表时出错: {str(e)}"
    
    def analyze_errors(self, max_lines: int = 100) -> str:
        """分析最新日志文件中的错误
        
        Args:
            max_lines: 分析的最大行数（从文件末尾开始）
            
        Returns:
            str: 错误分析结果
        """
        try:
            if not self.log_dir.exists():
                return "⚠️ 日志目录不存在。"
            
            # 获取最新的日志文件
            log_files = list(self.log_dir.glob('*.log'))
            if not log_files:
                return "📋 没有找到日志文件。"
            
            latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
            
            # 读取日志文件
            with open(latest_log, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 从末尾开始分析
            recent_lines = lines[-max_lines:] if len(lines) > max_lines else lines
            
            # 查找错误和警告
            errors = []
            warnings = []
            
            for line in recent_lines:
                line_lower = line.lower()
                if 'error' in line_lower or '错误' in line_lower:
                    errors.append(line.strip())
                elif 'warning' in line_lower or '警告' in line_lower:
                    warnings.append(line.strip())
            
            # 格式化输出
            if not errors and not warnings:
                return f"✅ 最近的日志中没有发现错误或警告。\n日志文件: {latest_log.name}"
            
            result = [f"📋 **日志分析结果** ({latest_log.name})\n"]
            
            if errors:
                result.append(f"❌ **发现 {len(errors)} 个错误**:")
                for error in errors[:10]:  # 最多显示 10 个
                    result.append(f"  {error}")
                if len(errors) > 10:
                    result.append(f"  ... 还有 {len(errors) - 10} 个错误")
            
            if warnings:
                result.append(f"\n⚠️ **发现 {len(warnings)} 个警告**:")
                for warning in warnings[:5]:  # 最多显示 5 个
                    result.append(f"  {warning}")
                if len(warnings) > 5:
                    result.append(f"  ... 还有 {len(warnings) - 5} 个警告")
            
            return "\n".join(result)
        
        except Exception as e:
            self.logger.error(f"分析日志失败: {e}", exc_info=True)
            return f"❌ 分析日志时出错: {str(e)}"
    
    def search_in_logs(self, keyword: str, max_results: int = 20) -> str:
        """在日志中搜索关键词
        
        Args:
            keyword: 搜索关键词
            max_results: 最大结果数
            
        Returns:
            str: 搜索结果
        """
        try:
            if not self.log_dir.exists():
                return "⚠️ 日志目录不存在。"
            
            # 获取最新的日志文件
            log_files = sorted(
                self.log_dir.glob('*.log'),
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )
            
            if not log_files:
                return "📋 没有找到日志文件。"
            
            # 只搜索最新的日志文件
            latest_log = log_files[0]
            keyword_lower = keyword.lower()
            
            # 读取并搜索
            with open(latest_log, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            matched_lines = [
                line.strip() for line in lines
                if keyword_lower in line.lower()
            ]
            
            if not matched_lines:
                return f"🔍 在最新日志中未找到 '{keyword}'。"
            
            # 格式化输出
            result = [
                f"🔍 在日志 **{latest_log.name}** 中找到 {len(matched_lines)} 条匹配记录:\n"
            ]
            
            for line in matched_lines[:max_results]:
                result.append(f"  {line}")
            
            if len(matched_lines) > max_results:
                result.append(f"\n  ... 还有 {len(matched_lines) - max_results} 条记录")
            
            return "\n".join(result)
        
        except Exception as e:
            self.logger.error(f"搜索日志失败: {e}", exc_info=True)
            return f"❌ 搜索日志时出错: {str(e)}"
    
    def get_log_summary(self) -> str:
        """获取日志摘要统计
        
        Returns:
            str: 日志统计信息
        """
        try:
            if not self.log_dir.exists():
                return "⚠️ 日志目录不存在。"
            
            log_files = list(self.log_dir.glob('*.log'))
            if not log_files:
                return "📋 没有找到日志文件。"
            
            # 获取最新日志
            latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
            
            # 读取最新日志
            with open(latest_log, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 统计
            total_lines = len(lines)
            recent_lines = lines[-500:] if len(lines) > 500 else lines
            
            info_count = sum(1 for line in recent_lines if 'INFO' in line)
            warning_count = sum(1 for line in recent_lines if 'WARNING' in line or '警告' in line)
            error_count = sum(1 for line in recent_lines if 'ERROR' in line or '错误' in line)
            
            # 格式化输出
            result = [
                f"📊 **日志统计信息** ({latest_log.name})\n",
                f"总行数: {total_lines}",
                f"最近500行统计:",
                f"  ℹ️ INFO: {info_count}",
                f"  ⚠️ WARNING: {warning_count}",
                f"  ❌ ERROR: {error_count}",
            ]
            
            if error_count > 0:
                result.append(f"\n💡 提示: 发现 {error_count} 个错误，建议使用 '分析错误' 查看详情。")
            
            return "\n".join(result)
        
        except Exception as e:
            self.logger.error(f"获取日志摘要失败: {e}", exc_info=True)
            return f"❌ 获取日志摘要时出错: {str(e)}"



