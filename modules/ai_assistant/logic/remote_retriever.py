# -*- coding: utf-8 -*-

"""
远程代码检索器
支持 GitHub / Gitee 等远程仓库的代码搜索
"""

import os
from typing import List, Dict, Any, Optional
from core.logger import get_logger

logger = get_logger(__name__)


class GitHubConnector:
    """
    GitHub 代码搜索连接器
    
    使用 PyGithub 进行代码搜索
    """
    
    def __init__(self, token: Optional[str] = None, config_manager=None):
        """
        初始化 GitHub 连接器
        
        Args:
            token: GitHub Token（可选，优先从环境变量读取）
            config_manager: 配置管理器（用于读取配置中的 token）
        """
        self.logger = logger
        
        # Token 读取优先级：传入参数 > 环境变量 > config_manager
        self.token = token or os.getenv('GITHUB_TOKEN')
        
        if not self.token and config_manager:
            try:
                self.token = config_manager.get_config('github_token')
            except Exception as e:
                self.logger.warning(f"无法从配置读取 GitHub token: {e}")
        
        # 延迟初始化 GitHub 客户端
        self._github = None
        
        if self.token:
            self.logger.info("GitHub 连接器初始化成功（已配置 token）")
        else:
            self.logger.warning("GitHub 连接器初始化（未配置 token，搜索受限）")
    
    def _init_github(self):
        """延迟初始化 GitHub 客户端"""
        if self._github is not None:
            return
        
        try:
            from github import Github
            
            if self.token:
                self._github = Github(self.token)
            else:
                # 未认证模式（API 限制更严格）
                self._github = Github()
            
            self.logger.debug("GitHub 客户端初始化成功")
            
        except Exception as e:
            self.logger.error(f"初始化 GitHub 客户端失败: {e}", exc_info=True)
            raise
    
    def code_search(
        self, 
        query: str, 
        repo: Optional[str] = None, 
        top_k: int = 5,
        language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索 GitHub 代码
        
        Args:
            query: 搜索关键词
            repo: 指定仓库（格式：owner/repo，如 "EpicGames/UnrealEngine"）
            top_k: 返回结果数量
            language: 限定编程语言（如 "Python", "C++"）
        
        Returns:
            List[Dict]: 搜索结果列表，每个结果包含 {'path', 'repo', 'url', 'content_snippet'}
        """
        try:
            self._init_github()
            
            # 构建搜索查询
            search_query = query
            
            if repo:
                search_query += f" repo:{repo}"
            
            if language:
                search_query += f" language:{language}"
            
            # 执行代码搜索
            code_results = self._github.search_code(query=search_query)
            
            # 格式化结果
            results = []
            
            for i, code_file in enumerate(code_results[:top_k]):
                try:
                    results.append({
                        'path': code_file.path,
                        'repo': code_file.repository.full_name,
                        'url': code_file.html_url,
                        'content_snippet': self._get_content_snippet(code_file),
                        'source': 'github'
                    })
                except Exception as e:
                    self.logger.warning(f"处理搜索结果失败: {e}")
                    continue
            
            self.logger.info(f"GitHub 搜索到 {len(results)} 个结果")
            return results
            
        except Exception as e:
            self.logger.error(f"GitHub 代码搜索失败: {e}", exc_info=True)
            return []
    
    def _get_content_snippet(self, code_file, max_lines: int = 10) -> str:
        """获取代码片段"""
        try:
            content = code_file.decoded_content.decode('utf-8')
            lines = content.split('\n')[:max_lines]
            return '\n'.join(lines) + ('\n...' if len(content.split('\n')) > max_lines else '')
        except Exception as e:
            self.logger.warning(f"获取代码片段失败: {e}")
            return "[无法获取内容]"
    
    def search_issues(self, query: str, repo: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        搜索 GitHub Issues
        
        Args:
            query: 搜索关键词
            repo: 指定仓库
            top_k: 返回结果数量
        
        Returns:
            List[Dict]: Issue 列表
        """
        try:
            self._init_github()
            
            search_query = query
            if repo:
                search_query += f" repo:{repo}"
            
            issues = self._github.search_issues(query=search_query)
            
            results = []
            for i, issue in enumerate(issues[:top_k]):
                try:
                    results.append({
                        'title': issue.title,
                        'url': issue.html_url,
                        'state': issue.state,
                        'body': issue.body[:500] if issue.body else "",  # 限制长度
                        'source': 'github_issue'
                    })
                except Exception as e:
                    self.logger.warning(f"处理 Issue 失败: {e}")
                    continue
            
            self.logger.info(f"搜索到 {len(results)} 个 Issues")
            return results
            
        except Exception as e:
            self.logger.error(f"搜索 GitHub Issues 失败: {e}", exc_info=True)
            return []


class GiteeConnector:
    """
    Gitee 代码搜索连接器（接口 stub）
    
    与 GitHubConnector 接口对齐，便于后续实现
    """
    
    def __init__(self, token: Optional[str] = None, config_manager=None):
        """
        初始化 Gitee 连接器
        
        Args:
            token: Gitee Token（优先从环境变量 GITEE_TOKEN 读取）
            config_manager: 配置管理器
        """
        self.logger = logger
        
        # Token 读取优先级：传入参数 > 环境变量 > config_manager
        self.token = token or os.getenv('GITEE_TOKEN')
        
        if not self.token and config_manager:
            try:
                self.token = config_manager.get_config('gitee_token')
            except Exception as e:
                self.logger.warning(f"无法从配置读取 Gitee token: {e}")
        
        self.logger.info("Gitee 连接器初始化（接口 stub，待实现）")
    
    def code_search(
        self, 
        query: str, 
        repo: Optional[str] = None, 
        top_k: int = 5,
        language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索 Gitee 代码（stub）
        
        Args:
            query: 搜索关键词
            repo: 指定仓库
            top_k: 返回结果数量
            language: 限定编程语言
        
        Returns:
            List[Dict]: 搜索结果列表（暂时返回空）
        """
        self.logger.warning("Gitee 代码搜索功能尚未实现")
        return []
    
    def search_issues(self, query: str, repo: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        搜索 Gitee Issues（stub）
        
        Args:
            query: 搜索关键词
            repo: 指定仓库
            top_k: 返回结果数量
        
        Returns:
            List[Dict]: Issue 列表（暂时返回空）
        """
        self.logger.warning("Gitee Issues 搜索功能尚未实现")
        return []


class RemoteRetriever:
    """
    远程检索统一接口
    
    封装多个远程连接器，提供统一的搜索接口
    """
    
    def __init__(self, config_manager=None):
        """
        初始化远程检索器
        
        Args:
            config_manager: 配置管理器
        """
        self.logger = logger
        self.config_manager = config_manager
        
        # 初始化连接器
        self.github = GitHubConnector(config_manager=config_manager)
        self.gitee = GiteeConnector(config_manager=config_manager)
        
        self.logger.info("远程检索器初始化完成")
    
    def search(
        self, 
        query: str, 
        source: str = "github", 
        top_k: int = 5,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        统一搜索接口
        
        Args:
            query: 搜索关键词
            source: 检索源（github / gitee）
            top_k: 返回结果数量
            **kwargs: 其他参数（repo, language 等）
        
        Returns:
            List[Dict]: 搜索结果列表
        """
        try:
            if source.lower() == "github":
                return self.github.code_search(query, top_k=top_k, **kwargs)
            elif source.lower() == "gitee":
                return self.gitee.code_search(query, top_k=top_k, **kwargs)
            else:
                self.logger.warning(f"未知的检索源: {source}")
                return []
        except Exception as e:
            self.logger.error(f"远程搜索失败: {e}", exc_info=True)
            return []

