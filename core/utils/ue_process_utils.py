# -*- coding: utf-8 -*-

# UE进程检测工具
import psutil
import logging
import os
from pathlib import Path
from typing import List, Dict, Optional
import string
from core.logger import get_logger


class UEProcess:
    """UE进程信息类"""
    
    def __init__(self, pid: int, name: str, project_path: Path):
        self.pid = pid
        self.name = name
        self.project_path = project_path
    
    def __str__(self):
        return f"UEProcess(pid={self.pid}, name={self.name}, project_path={self.project_path})"


class UEProcessUtils:
    """UE进程检测工具类"""
    
    def __init__(self):
        self.logger = get_logger("ue_process_utils")
        self.ue_process_names = ["UE4Editor.exe", "UE5Editor.exe"]
    
    def detect_running_ue_projects(self) -> List[UEProcess]:
        """检测正在运行的UE工程
        
        Returns:
            List[UEProcess]: 正在运行的UE工程列表
        """
        self.logger.info("开始检测正在运行的UE工程")
        ue_processes = []
        
        try:
            # 遍历所有运行的进程
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] in self.ue_process_names:
                        # 提取工程路径
                        project_path = self._extract_project_path(proc.info['cmdline'])
                        if project_path:
                            ue_process = UEProcess(
                                proc.info['pid'],
                                proc.info['name'],
                                project_path
                            )
                            ue_processes.append(ue_process)
                            self.logger.info(f"发现UE进程: {ue_process}")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # 忽略无法访问的进程
                    pass
                except Exception as e:
                    self.logger.warning(f"处理进程 {proc.info.get('pid', 'unknown')} 时出错: {e}")
            
            self.logger.info(f"检测完成，共发现 {len(ue_processes)} 个UE工程")
            return ue_processes
        except Exception as e:
            self.logger.error(f"检测UE工程时发生错误: {e}")
            return []
    
    def _extract_project_path(self, cmdline: List[str]) -> Optional[Path]:
        """从命令行参数中提取工程路径
        
        Args:
            cmdline: 命令行参数列表
            
        Returns:
            Optional[Path]: 工程路径，如果无法提取则返回None
        """
        try:
            # 遍历命令行参数，查找工程文件路径
            for i, arg in enumerate(cmdline):
                if arg.endswith('.uproject'):
                    project_path = Path(arg)
                    if project_path.exists():
                        return project_path
                    # 如果是相对路径，尝试转换为绝对路径
                    elif project_path.is_absolute():
                        return project_path
            return None
        except Exception as e:
            self.logger.error(f"提取工程路径时发生错误: {e}")
            return None
    
    def search_all_ue_projects(self) -> List[UEProcess]:
        """快速搜索系统中的UE工程
        
        Returns:
            List[UEProcess]: 所有找到的UE工程列表
        """
        self.logger.info("开始快速搜索系统中的UE工程")
        
        try:
            # 使用优化的搜索算法
            projects = self._quick_search_ue_projects()
            self.logger.info(f"搜索完成，共发现 {len(projects)} 个UE工程")
            return projects
        except Exception as e:
            self.logger.error(f"搜索UE工程时发生错误: {e}")
            return []
    
    def _quick_search_ue_projects(self) -> List[UEProcess]:
        """快速搜索UE工程的核心算法"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        common_locations = self._get_common_project_locations()
        
        # 并行搜索这些位置
        ue_projects = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(self._search_location, loc) for loc in common_locations]
            for future in as_completed(futures):
                try:
                    results = future.result()
                    ue_projects.extend(results)
                except Exception as e:
                    self.logger.warning(f"搜索位置时发生错误: {e}")
                    continue
        
        filtered_results = self._apply_exclusion_rules(ue_projects)
        return filtered_results
    
    def _should_exclude_path(self, path: Path) -> bool:
        """检查路径是否应该被排除"""
        # 更精确的排除规则，避免误排除用户自定义路径
        exclude_patterns = [
            "Epic Games", 
            "Program Files", 
            "Windows", 
            "\\Engine\\",  # 引擎源码目录
            "\\Templates\\",  # 官方模板
            "\\Samples\\",  # 官方示例
            "\\FeaturePacks\\",  # 功能包
            "\\Marketplace\\",  # 市场内容
            "AppData",
            "$Recycle.Bin", 
            "Recycled", 
            "System Volume Information",
            "\\temp\\", 
            "\\tmp\\"
        ]
        path_str = str(path).replace("\\", "\\\\")  # 转义反斜杠
        path_lower = path_str.lower()
        return any(pattern.lower() in path_lower for pattern in exclude_patterns)
    
    def _get_common_project_locations(self) -> List[Path]:
        """获取常见项目位置"""
        locations = []
        
        # 用户目录
        user_home = Path.home()
        locations.extend([
            user_home / "Documents",
            user_home / "Desktop", 
            user_home / "Downloads",
            user_home / "Projects",
            user_home / "Work",
            user_home / "Dev"
        ])
        
        # 各磁盘的常见项目文件夹
        drives = [Path(f"{drive}:\\") for drive in string.ascii_uppercase 
                 if Path(f"{drive}:\\").exists()]
        
        for drive in drives:
            locations.extend([
                drive / "Projects",
                drive / "Work",
                drive / "Dev",
                drive / "Unreal Projects",
                drive / "UE_Projects",
                drive / "UnrealEngine"  # 添加UnrealEngine目录
            ])
        
        # 添加环境变量指定的路径
        ue_paths_env = ["UE_PROJECTS_PATH", "UNREAL_PROJECTS_PATH"]
        for env_var in ue_paths_env:
            env_path = Path(os.getenv(env_var, ""))
            if env_path.exists():
                locations.append(env_path)
        
        # 添加一些常见的自定义路径
        custom_paths = [
            Path("D:\\UnrealEngine"),  # 直接添加您的路径
            Path("C:\\UnrealEngine"),
            Path("E:\\UnrealEngine")
        ]
        for custom_path in custom_paths:
            if custom_path.exists():
                locations.append(custom_path)
        
        # 去除重复路径
        unique_locations = []
        seen_paths = set()
        for loc in locations:
            if loc.exists():
                path_str = str(loc)
                if path_str not in seen_paths:
                    unique_locations.append(loc)
                    seen_paths.add(path_str)
        
        return unique_locations
    
    def _search_location(self, location: Path) -> List[UEProcess]:
        """搜索指定位置的UE工程"""
        projects = []
        
        if not location.exists():
            return projects
        
        try:
            # 使用广度优先搜索，限制深度为4层
            from collections import deque
            queue = deque([(location, 0)])  # (路径, 深度)
            
            while queue:
                current_path, depth = queue.popleft()
                
                # 限制搜索深度
                if depth > 4:
                    continue
                
                try:
                    # 检查当前目录下的.uproject文件
                    if current_path.is_dir():
                        for item in current_path.iterdir():
                            if item.is_file() and item.suffix.lower() == '.uproject':
                                project_name = item.stem
                                virtual_process = UEProcess(
                                    pid=-1,  # 虚拟PID
                                    name=project_name,  # 使用项目名作为进程名
                                    project_path=item
                                )
                                projects.append(virtual_process)
                                self.logger.info(f"发现UE工程: {project_name} - {item}")
                            elif item.is_dir() and not self._should_exclude_path(item):
                                # 将子目录加入队列继续搜索
                                queue.append((item, depth + 1))
                except PermissionError:
                    # 忽略没有权限访问的目录
                    self.logger.warning(f"无权限访问目录: {current_path}")
                    continue
                except Exception as e:
                    self.logger.warning(f"搜索目录 {current_path} 时发生错误: {e}")
                    continue
        except Exception as e:
            self.logger.error(f"搜索位置 {location} 时发生错误: {e}")
        
        return projects
    
    def _apply_exclusion_rules(self, projects: List[UEProcess]) -> List[UEProcess]:
        """应用排除规则"""
        filtered_projects = []
        for project in projects:
            if not self._should_exclude_path(project.project_path):
                filtered_projects.append(project)
        return filtered_projects
    
    def is_project_running(self, project_path) -> bool:
        """检查指定的工程是否正在运行
        
        Args:
            project_path: 工程路径
            
        Returns:
            bool: 工程是否正在运行
        """
        from pathlib import Path
        project_path = Path(project_path) if not isinstance(project_path, Path) else project_path
        
        try:
            running_projects = self.detect_running_ue_projects()
            for running_project in running_projects:
                if running_project.project_path.resolve() == project_path.resolve():
                    return True
            return False
        except Exception as e:
            self.logger.error(f"检查工程运行状态时发生错误: {e}")
            return False