# -*- coding: utf-8 -*-

"""
JSON 报告生成器

生成机器可读的 JSON 格式报告。
"""

import json
from datetime import datetime
from pathlib import Path
from .base import BaseReporter
from ..models import CleanupResult, Issue


class JSONReporter(BaseReporter):
    """JSON 报告生成器"""
    
    def generate(self, result: CleanupResult, output_path: str) -> None:
        """生成 JSON 报告"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 构建报告数据
        report_data = {
            'metadata': self._generate_metadata(result),
            'statistics': self._generate_statistics(result),
            'issues': self._generate_issues(result)
        }
        
        # 写入 JSON 文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
    
    def _generate_metadata(self, result: CleanupResult) -> dict:
        """生成元数据"""
        return {
            'generated_at': datetime.now().isoformat(),
            'analysis_duration': result.analysis_duration,
            'tool_version': '1.0.0'
        }
    
    def _generate_statistics(self, result: CleanupResult) -> dict:
        """生成统计信息"""
        stats = {
            'total_files_scanned': result.total_files_scanned,
            'total_issues_found': result.total_issues_found,
            'estimated_lines_to_remove': result.estimated_lines_to_remove,
            'by_category': {},
            'by_severity': {}
        }
        
        # 按类别统计
        for category, issues in result.issues_by_category.items():
            stats['by_category'][category] = {
                'count': len(issues),
                'percentage': round(len(issues) / result.total_issues_found * 100, 2) if result.total_issues_found > 0 else 0
            }
        
        # 按严重程度统计
        for severity, issues in result.issues_by_severity.items():
            stats['by_severity'][severity] = {
                'count': len(issues),
                'percentage': round(len(issues) / result.total_issues_found * 100, 2) if result.total_issues_found > 0 else 0
            }
        
        return stats
    
    def _generate_issues(self, result: CleanupResult) -> list:
        """生成问题列表"""
        issues_list = []
        
        # 收集所有问题
        all_issues = []
        for issues in result.issues_by_category.values():
            all_issues.extend(issues)
        
        # 按严重程度和文件路径排序
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        all_issues.sort(key=lambda x: (severity_order.get(x.severity, 3), str(x.file_path), x.line_number))
        
        # 转换为字典格式
        for issue in all_issues:
            issue_dict = {
                'category': issue.category,
                'severity': issue.severity,
                'file_path': str(issue.file_path),
                'line_number': issue.line_number,
                'description': issue.description,
                'suggestion': issue.suggestion
            }
            
            # 可选字段
            if issue.code_snippet:
                issue_dict['code_snippet'] = issue.code_snippet
            
            if issue.impact_analysis:
                issue_dict['impact_analysis'] = issue.impact_analysis
            
            issues_list.append(issue_dict)
        
        return issues_list

