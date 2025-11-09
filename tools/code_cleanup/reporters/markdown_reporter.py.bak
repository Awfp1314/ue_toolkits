# -*- coding: utf-8 -*-

"""
Markdown 报告生成器
"""

from datetime import datetime
from pathlib import Path
from .base import BaseReporter
from ..models import CleanupResult, Issue


class MarkdownReporter(BaseReporter):
    """Markdown 报告生成器"""
    
    def generate(self, result: CleanupResult, output_path: str) -> None:
        """生成 Markdown 报告"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(self._generate_header(result))
            f.write(self._generate_statistics(result))
            f.write(self._generate_issues_by_category(result))
            f.write(self._generate_recommendations())
    
    def _generate_header(self, result: CleanupResult) -> str:
        """生成报告头部"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return f"""# 代码清理报告

生成时间: {now}
分析耗时: {result.analysis_duration:.2f} 秒

"""
    
    def _generate_statistics(self, result: CleanupResult) -> str:
        """生成统计摘要"""
        content = """## 统计摘要

"""
        content += f"- 扫描文件数: {result.total_files_scanned}\n"
        content += f"- 发现问题数: {result.total_issues_found}\n"
        content += f"- 预计可删除代码行数: {result.estimated_lines_to_remove}\n\n"
        
        # 按类别统计
        content += "### 按类别统计\n\n"
        content += "| 类别 | 数量 |\n"
        content += "| ---- | ---- |\n"
        
        for category, issues in result.issues_by_category.items():
            content += f"| {self._translate_category(category)} | {len(issues)} |\n"
        
        content += "\n"
        
        # 按严重程度统计
        content += "### 按严重程度统计\n\n"
        content += "| 严重程度 | 数量 |\n"
        content += "| -------- | ---- |\n"
        
        for severity, issues in result.issues_by_severity.items():
            content += f"| {self._translate_severity(severity)} | {len(issues)} |\n"
        
        content += "\n"
        
        return content
    
    def _generate_issues_by_category(self, result: CleanupResult) -> str:
        """生成按类别分组的问题列表"""
        content = "## 详细问题列表\n\n"
        
        for category, issues in result.issues_by_category.items():
            if not issues:
                continue
            
            content += f"### {self._translate_category(category)} ({len(issues)})\n\n"
            
            for i, issue in enumerate(issues[:10], 1):  # 每个类别最多显示 10 个
                content += f"#### {i}. {issue.description}\n\n"
                content += f"**文件**: `{issue.file_path}`\n"
                content += f"**行号**: {issue.line_number}\n"
                content += f"**严重程度**: {self._translate_severity(issue.severity)}\n\n"
                content += f"**建议**: {issue.suggestion}\n\n"
                
                if issue.code_snippet:
                    content += f"**代码片段**:\n```python\n{issue.code_snippet}\n```\n\n"
                
                content += "---\n\n"
            
            if len(issues) > 10:
                content += f"*还有 {len(issues) - 10} 个问题未显示...*\n\n"
        
        return content
    
    def _generate_recommendations(self) -> str:
        """生成建议操作"""
        return """## 建议操作

1. **优先处理高严重程度问题** - 这些问题可能影响代码质量
2. **审查废弃代码** - 确认是否可以安全删除
3. **清理未使用导入** - 可以自动清理
4. **人工审查公共 API 相关问题** - 避免破坏外部依赖

"""
    
    def _translate_category(self, category: str) -> str:
        """翻译类别名称"""
        translations = {
            'dead_code': '死代码',
            'deprecated': '废弃代码',
            'unused_import': '未使用导入',
            'unused_variable': '未使用变量',
            'unused_file': '未使用文件',
            'duplicate_code': '重复代码',
            'config': '配置问题'
        }
        return translations.get(category, category)
    
    def _translate_severity(self, severity: str) -> str:
        """翻译严重程度"""
        translations = {
            'high': '高',
            'medium': '中',
            'low': '低'
        }
        return translations.get(severity, severity)

