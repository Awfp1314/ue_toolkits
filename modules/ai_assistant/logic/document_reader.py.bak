# -*- coding: utf-8 -*-

"""
文档读取器
读取项目文档和说明文件，供 AI 助手使用
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
from core.logger import get_logger

logger = get_logger(__name__)


class DocumentReader:
    """项目文档读取器"""
    
    def __init__(self, project_root: Optional[Path] = None):
        """初始化文档读取器
        
        Args:
            project_root: 项目根目录路径
        """
        if project_root is None:
            # 获取项目根目录（假设当前文件在 modules/ai_assistant/logic/）
            self.project_root = Path(__file__).parent.parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.logger = logger
        self.logger.info(f"文档读取器初始化，项目根目录: {self.project_root}")
    
    def get_available_documents(self) -> str:
        """获取可用的文档列表
        
        Returns:
            str: 文档列表的格式化字符串
        """
        try:
            docs = []
            
            # 搜索常见的文档文件
            doc_patterns = ['*.md', 'README*', 'CHANGELOG*', '*.txt']
            
            for pattern in doc_patterns:
                for doc_file in self.project_root.glob(pattern):
                    if doc_file.is_file():
                        docs.append({
                            'name': doc_file.name,
                            'path': doc_file,
                            'size': doc_file.stat().st_size
                        })
            
            # 同时搜索 modules 目录下的文档
            modules_dir = self.project_root / 'modules'
            if modules_dir.exists():
                for module_dir in modules_dir.iterdir():
                    if module_dir.is_dir():
                        for doc_file in module_dir.glob('*.md'):
                            docs.append({
                                'name': f"{module_dir.name}/{doc_file.name}",
                                'path': doc_file,
                                'size': doc_file.stat().st_size
                            })
            
            if not docs:
                return "📄 未找到项目文档文件。"
            
            # 格式化输出
            result = ["📄 **可用文档列表**:\n"]
            for i, doc in enumerate(docs, 1):
                size_kb = doc['size'] / 1024
                result.append(f"{i}. **{doc['name']}** ({size_kb:.1f} KB)")
            
            return "\n".join(result)
        
        except Exception as e:
            self.logger.error(f"获取文档列表失败: {e}", exc_info=True)
            return f"❌ 获取文档列表时出错: {str(e)}"
    
    def read_document(self, doc_name: str, max_lines: int = 200) -> str:
        """读取指定文档的内容
        
        Args:
            doc_name: 文档名称
            max_lines: 最大读取行数
            
        Returns:
            str: 文档内容
        """
        try:
            # 尝试直接匹配
            doc_path = self.project_root / doc_name
            
            if not doc_path.exists():
                # 尝试在 modules 目录中查找
                for module_dir in (self.project_root / 'modules').glob('*'):
                    potential_path = module_dir / doc_name
                    if potential_path.exists():
                        doc_path = potential_path
                        break
            
            if not doc_path.exists():
                return f"❌ 未找到文档: {doc_name}"
            
            # 读取文档内容
            with open(doc_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 限制行数
            if len(lines) > max_lines:
                content = ''.join(lines[:max_lines])
                content += f"\n\n... (文档过长，已截取前 {max_lines} 行)"
            else:
                content = ''.join(lines)
            
            return f"📄 **{doc_name}**\n\n{content}"
        
        except Exception as e:
            self.logger.error(f"读取文档失败: {e}", exc_info=True)
            return f"❌ 读取文档 '{doc_name}' 时出错: {str(e)}"
    
    def search_in_documents(self, keyword: str) -> str:
        """在文档中搜索关键词
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            str: 搜索结果
        """
        try:
            results = []
            keyword_lower = keyword.lower()
            
            # 搜索所有 Markdown 文件
            for doc_file in self.project_root.glob('*.md'):
                try:
                    with open(doc_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if keyword_lower in content.lower():
                        # 提取包含关键词的行
                        lines = content.split('\n')
                        matched_lines = [
                            line for line in lines 
                            if keyword_lower in line.lower()
                        ]
                        
                        results.append({
                            'file': doc_file.name,
                            'matches': matched_lines[:3]  # 最多显示 3 行
                        })
                except Exception as e:
                    self.logger.warning(f"搜索文档 {doc_file} 时出错: {e}")
                    continue
            
            if not results:
                return f"🔍 在文档中未找到 '{keyword}'。"
            
            # 格式化输出
            output = [f"🔍 在 {len(results)} 个文档中找到 '{keyword}':\n"]
            
            for result in results[:5]:  # 最多显示 5 个文档
                output.append(f"\n**{result['file']}**:")
                for line in result['matches']:
                    output.append(f"  {line.strip()}")
            
            return "\n".join(output)
        
        except Exception as e:
            self.logger.error(f"搜索文档失败: {e}", exc_info=True)
            return f"❌ 搜索文档时出错: {str(e)}"
    
    def get_readme_summary(self) -> str:
        """获取 README 文档的摘要
        
        Returns:
            str: README 摘要
        """
        try:
            readme_files = ['README.md', 'readme.md', 'Readme.md']
            
            for readme_name in readme_files:
                readme_path = self.project_root / readme_name
                if readme_path.exists():
                    return self.read_document(readme_name, max_lines=50)
            
            return "📄 未找到 README 文档。"
        
        except Exception as e:
            self.logger.error(f"获取 README 失败: {e}", exc_info=True)
            return f"❌ 获取 README 时出错: {str(e)}"





