# -*- coding: utf-8 -*-

# 模块加载与注册（扫描 modules/）
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum

from core.logger import get_logger
from core.config.config_manager import ConfigManager
from core.utils.path_utils import PathUtils
from core.utils.thread_utils import get_thread_manager


class ModuleState(Enum):
    """模块状态枚举"""
    DISCOVERED = "discovered"      # 已发现
    LOADED = "loaded"              # 已加载
    INITIALIZED = "initialized"    # 已初始化
    UNLOADED = "unloaded"          # 已卸载
    ERROR = "error"                # 错误状态


@dataclass
class ModuleInfo:
    """模块信息数据类"""
    name: str
    version: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    display_name: str = ""  # 显示名称
    author: str = ""  # 作者
    icon: str = ""  # 图标路径
    entry_point: str = ""
    path: Path = Path()
    state: ModuleState = ModuleState.DISCOVERED
    instance: Optional[object] = None
    config_manager: Optional[ConfigManager] = None
    
    def __str__(self) -> str:
        return f"ModuleInfo(name='{self.name}', version='{self.version}', state={self.state.value})"


class ModuleManager:
    """模块化架构的核心管理器"""
    
    def __init__(self, modules_dir: Optional[Path] = None):
        """初始化模块管理器
        
        Args:
            modules_dir: 模块目录路径，默认为项目根目录下的 modules/ 目录
        """
        self.logger = get_logger("module_manager")
        self.path_utils = PathUtils()
        self.thread_manager = get_thread_manager()
        
        # 设置模块目录
        if modules_dir is None:
            # 默认使用项目根目录下的 modules/ 目录
            self.modules_dir = Path(__file__).parent.parent / "modules"
        else:
            self.modules_dir = modules_dir
            
        # 模块注册表
        self.modules: Dict[str, ModuleInfo] = {}
        self.load_order: List[str] = []  # 模块加载顺序
        
        self.logger.info(f"初始化模块管理器，模块目录: {self.modules_dir}")
    
    def discover_modules(self) -> Dict[str, ModuleInfo]:
        """自动扫描 modules/ 目录下的所有模块
        
        Returns:
            Dict[str, ModuleInfo]: 发现的模块信息字典
        """
        self.logger.info("开始扫描模块目录")
        
        if not self.modules_dir.exists():
            self.logger.warning(f"模块目录不存在: {self.modules_dir}")
            return {}
        
        # 清空之前的模块信息
        self.modules.clear()
        self.load_order.clear()
        
        # 遍历模块目录
        for module_path in self.modules_dir.iterdir():
            if module_path.is_dir():
                # 检查是否存在 manifest.json 文件
                manifest_path = module_path / "manifest.json"
                if manifest_path.exists():
                    try:
                        # 解析模块元信息
                        module_info = self._parse_manifest(manifest_path, module_path)
                        if module_info:
                            self.modules[module_info.name] = module_info
                            self.logger.info(f"发现模块: {module_info}")
                    except Exception as e:
                        self.logger.error(f"解析模块 {module_path.name} 的 manifest.json 失败: {e}")
                else:
                    self.logger.warning(f"模块目录 {module_path.name} 缺少 manifest.json 文件")
        
        self.logger.info(f"模块扫描完成，共发现 {len(self.modules)} 个模块")
        return self.modules
    
    def _parse_manifest(self, manifest_path: Path, module_path: Path) -> Optional[ModuleInfo]:
        """解析模块的 manifest.json 文件
        
        Args:
            manifest_path: manifest.json 文件路径
            module_path: 模块目录路径
            
        Returns:
            Optional[ModuleInfo]: 解析成功的模块信息，失败则返回 None
        """
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_data = json.load(f)
            
            # 跳过模板模块
            if manifest_data.get("_template", False):
                self.logger.info(f"跳过模板模块: {module_path.name}")
                return None
            
            module_name = manifest_data.get("name", module_path.name)
            module_info = ModuleInfo(
                name=module_name,
                version=manifest_data.get("version", "1.0.0"),
                description=manifest_data.get("description", ""),
                dependencies=manifest_data.get("dependencies", []),
                display_name=manifest_data.get("display_name", module_name),  # 如果没有则使用name
                author=manifest_data.get("author", ""),
                icon=manifest_data.get("icon", ""),
                entry_point=manifest_data.get("entry_point", ""),
                path=module_path,
                state=ModuleState.DISCOVERED
            )
            
            config_template_path = module_path / "config_template.json"
            if config_template_path.exists():
                module_info.config_manager = ConfigManager(module_info.name, config_template_path)
            
            return module_info
        except json.JSONDecodeError as e:
            self.logger.error(f"manifest.json 格式错误: {e}")
            return None
        except Exception as e:
            self.logger.error(f"解析 manifest.json 失败: {e}")
            return None
    
    def resolve_dependencies(self) -> List[str]:
        """解析模块间的依赖关系，确定加载顺序
        
        执行以下检查：
        1. 检查自依赖（模块依赖自身）
        2. 检查未知依赖（依赖不存在的模块）
        3. 检查循环依赖（深度优先搜索检测所有循环）
        4. 拓扑排序确定加载顺序
        
        Returns:
            List[str]: 按依赖关系排序的模块名称列表
            
        Raises:
            ValueError: 当存在依赖问题时抛出异常
        """
        self.logger.info("开始解析模块依赖关系")
        
        if not self.modules:
            self.logger.warning("没有发现任何模块")
            return []
        
        # 构建依赖图
        dependencies: Dict[str, Set[str]] = {}
        for module_name, module_info in self.modules.items():
            dependencies[module_name] = set(module_info.dependencies)
        
        self._check_self_dependencies(dependencies)
        
        all_module_names = set(self.modules.keys())
        unknown_deps_found = False
        for module_name, deps in dependencies.items():
            unknown_deps = deps - all_module_names
            if unknown_deps:
                unknown_deps_found = True
                self.logger.error(
                    f"❌ 模块 '{module_name}' 依赖于未知模块: {sorted(unknown_deps)}\n"
                    f"   可用的模块: {sorted(all_module_names)}"
                )
        
        if unknown_deps_found:
            raise ValueError(
                "检测到未知依赖。请确保所有依赖的模块都已正确安装并在modules目录中。"
            )
        
        self._detect_circular_dependencies(dependencies)
        
        sorted_modules = self._topological_sort(dependencies)
        
        self.load_order = sorted_modules
        self.logger.info(f"依赖解析完成，加载顺序: {sorted_modules}")
        return sorted_modules
    
    def _check_self_dependencies(self, dependencies: Dict[str, Set[str]]) -> None:
        """检查自依赖（模块依赖自身）
        
        自依赖是最简单的循环依赖形式：A → A
        
        Args:
            dependencies: 模块依赖关系图
            
        Raises:
            ValueError: 当发现自依赖时抛出异常
        """
        self_deps = []
        
        for module_name, deps in dependencies.items():
            if module_name in deps:
                self_deps.append(module_name)
                self.logger.error(
                    f"❌ 检测到自依赖: 模块 '{module_name}' 依赖于自身"
                )
        
        if self_deps:
            raise ValueError(
                f"检测到自依赖问题：{sorted(self_deps)}\n"
                f"模块不能依赖自身。请检查这些模块的manifest.json文件。"
            )
    
    def _detect_circular_dependencies(self, dependencies: Dict[str, Set[str]]) -> None:
        """使用深度优先搜索检测所有循环依赖
        
        此方法能检测：
        1. 简单循环：A → B → A
        2. 复杂循环：A → B → C → D → B
        3. 多个独立循环
        
        算法原理：
        - 使用三种状态标记节点：
          * WHITE (0): 未访问
          * GRAY (1): 正在访问（在当前DFS路径中）
          * BLACK (2): 已完成访问
        - 当访问到GRAY状态的节点时，表示发现循环
        
        Args:
            dependencies: 模块依赖关系图
            
        Raises:
            ValueError: 当发现循环依赖时抛出异常，包含所有循环路径
        """
        # 节点状态
        WHITE, GRAY, BLACK = 0, 1, 2
        color: Dict[str, int] = {module: WHITE for module in dependencies}
        
        # 记录所有发现的循环
        cycles_found: List[List[str]] = []
        
        def dfs(node: str, path: List[str]) -> None:
            """深度优先搜索
            
            Args:
                node: 当前节点
                path: 当前访问路径
            """
            # 标记当前节点为正在访问
            color[node] = GRAY
            path.append(node)
            
            # 遍历当前节点的所有依赖
            for neighbor in dependencies.get(node, set()):
                if color[neighbor] == GRAY:
                    # 发现循环：neighbor在当前路径中
                    # 找到循环的起点在路径中的位置
                    cycle_start_index = path.index(neighbor)
                    cycle = path[cycle_start_index:] + [neighbor]
                    cycles_found.append(cycle)
                    
                    self.logger.error(
                        f"❌ 检测到循环依赖: {' → '.join(cycle)}"
                    )
                elif color[neighbor] == WHITE:
                    # 继续深度优先搜索
                    dfs(neighbor, path.copy())
            
            # 标记当前节点为已完成
            color[node] = BLACK
        
        # 对每个未访问的节点执行DFS
        for module in dependencies:
            if color[module] == WHITE:
                dfs(module, [])
        
        # 如果发现循环，抛出异常
        if cycles_found:
            error_msg = "检测到循环依赖问题：\n\n"
            
            for i, cycle in enumerate(cycles_found, 1):
                error_msg += f"循环 {i}: {' → '.join(cycle)}\n"
            
            error_msg += "\n请修改模块的manifest.json文件，移除循环依赖。"
            
            raise ValueError(error_msg)
        
        self.logger.debug("未检测到循环依赖")
    
    def _topological_sort(self, dependencies: Dict[str, Set[str]]) -> List[str]:
        """拓扑排序算法，用于确定模块加载顺序
        
        使用Kahn算法进行拓扑排序：
        1. 计算所有节点的入度
        2. 将入度为0的节点加入队列
        3. 依次处理队列中的节点，并更新其他节点的入度
        4. 重复直到队列为空
        
        注意：循环依赖已在 _detect_circular_dependencies() 中检测，
        此方法专注于确定正确的加载顺序。
        
        Args:
            dependencies: 模块依赖关系图
            
        Returns:
            List[str]: 排序后的模块列表（依赖在前，被依赖在后）
            
        Raises:
            ValueError: 当排序失败时抛出异常（理论上不应该发生，因为循环已被检测）
        """
        # 入度表：记录每个模块依赖多少个其他模块
        # 注意：在依赖图中，如果A依赖B（A → B），那么A的入度应该+1
        in_degree: Dict[str, int] = {module: len(deps) for module, deps in dependencies.items()}
        
        # 将入度为0的节点（没有依赖的模块）加入队列
        queue: List[str] = [module for module, degree in in_degree.items() if degree == 0]
        result: List[str] = []
        
        self.logger.debug(f"初始无依赖模块: {queue}")
        
        while queue:
            # 取出一个入度为0的节点（不依赖任何模块）
            current = queue.pop(0)
            result.append(current)
            
            # 逻辑：current 已经加入结果，所有依赖 current 的模块的入度应该减1
            for module, deps in dependencies.items():
                if current in deps:
                    in_degree[module] -= 1
                    # 如果某个节点的入度变为0，说明它的所有依赖都已处理
                    if in_degree[module] == 0:
                        queue.append(module)
        
        # 理论上不应该失败，因为循环依赖已被检测
        if len(result) != len(dependencies):
            remaining = set(dependencies.keys()) - set(result)
            self.logger.error(
                f"❌ 拓扑排序失败：未能排序所有模块\n"
                f"   已排序: {result}\n"
                f"   剩余: {remaining}"
            )
            raise ValueError(
                f"拓扑排序失败，这不应该发生（循环依赖应该已被检测）。\n"
                f"剩余模块: {remaining}"
            )
        
        return result
    
    def load_modules(self) -> bool:
        """按依赖顺序加载所有模块（同步版本，保持向后兼容）
        
        Returns:
            bool: 所有模块是否加载成功
        """
        self.logger.info("开始加载模块（同步模式）")
        
        try:
            # 首先发现所有模块
            self.discover_modules()
            
            # 解析依赖关系
            self.resolve_dependencies()
            
            # 按顺序加载模块
            success = True
            for module_name in self.load_order:
                if module_name in self.modules:
                    module_info = self.modules[module_name]
                    if not self._load_module(module_info):
                        success = False
                        self.logger.error(f"模块 {module_name} 加载失败")
            
            if success:
                self.logger.info("所有模块加载完成")
            else:
                self.logger.warning("部分模块加载失败")
                
            return success
        except Exception as e:
            self.logger.error(f"加载模块时发生错误: {e}")
            return False
    
    def load_modules_async(
        self, 
        on_complete: Optional[Callable[[bool], None]] = None,
        on_progress: Optional[Callable[[int, str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ):
        """异步加载所有模块（推荐使用）
        
        Args:
            on_complete: 完成回调 (success: bool) -> None
            on_progress: 进度回调 (percent: int, message: str) -> None
            on_error: 错误回调 (error_message: str) -> None
            
        Example:
            def on_done(success):
                if success:
                    print("模块加载成功")
            
            def on_progress(percent, msg):
                print(f"{percent}% - {msg}")
            
            manager.load_modules_async(
                on_complete=on_done,
                on_progress=on_progress
            )
        """
        self.logger.info("开始异步加载模块")
        
        def load_task():
            try:
                if on_progress:
                    on_progress(10, "正在扫描模块目录...")
                self.discover_modules()
                
                # 解析依赖
                if on_progress:
                    on_progress(30, "正在解析模块依赖...")
                self.resolve_dependencies()
                
                total = len(self.load_order)
                success = True
                
                for i, module_name in enumerate(self.load_order):
                    if on_progress:
                        percent = 30 + int((i / total) * 60)
                        on_progress(percent, f"正在加载模块: {module_name}")
                    
                    if module_name in self.modules:
                        module_info = self.modules[module_name]
                        if not self._load_module(module_info):
                            success = False
                            self.logger.error(f"模块 {module_name} 加载失败")
                
                if on_progress:
                    on_progress(100, "模块加载完成")
                
                return success
            except Exception as e:
                error_msg = f"加载模块时发生错误: {e}"
                self.logger.error(error_msg)
                if on_error:
                    on_error(error_msg)
                return False
        
        self.thread_manager.run_in_thread(
            load_task,
            on_result=on_complete,
            on_error=on_error,
            on_progress=on_progress
        )
    
    def _load_module(self, module_info: ModuleInfo) -> bool:
        """加载单个模块
        
        Args:
            module_info: 模块信息
            
        Returns:
            bool: 模块是否加载成功
        """
        try:
            self.logger.info(f"正在加载模块: {module_info.name}")
            
            for dep_name in module_info.dependencies:
                if dep_name in self.modules:
                    dep_module = self.modules[dep_name]
                    if dep_module.state != ModuleState.LOADED and dep_module.state != ModuleState.INITIALIZED:
                        self.logger.error(f"模块 {module_info.name} 的依赖 {dep_name} 尚未加载")
                        module_info.state = ModuleState.ERROR
                        return False
            
            # 实际加载模块
            if module_info.entry_point:
                try:
                    # 解析 entry_point 格式: "module_name:ClassName"
                    module_name, class_name = module_info.entry_point.split(":")
                    
                    # 构建完整的模块路径
                    if module_name == "__main__":
                        full_module_path = f"modules.{module_info.name}"
                        import_module_name = f"modules.{module_info.name}"
                    else:
                        full_module_path = f"modules.{module_info.name}.{module_name}"
                        import_module_name = full_module_path
                    
                    self.logger.info(f"尝试导入模块: {import_module_name}")
                    
                    # 动态导入模块
                    module = __import__(import_module_name, fromlist=[class_name])
                    
                    cls = getattr(module, class_name)
                    
                    module_info.instance = cls()
                    module_info.state = ModuleState.LOADED
                    self.logger.info(f"模块 {module_info.name} 加载成功")
                    return True
                except Exception as e:
                    self.logger.error(f"导入模块 {module_info.name} 失败: {e}")
                    module_info.state = ModuleState.ERROR
                    return False
            else:
                # 如果没有指定 entry_point，使用默认方式
                module_info.state = ModuleState.LOADED
                self.logger.info(f"模块 {module_info.name} 加载成功")
                return True
        except Exception as e:
            self.logger.error(f"加载模块 {module_info.name} 失败: {e}")
            module_info.state = ModuleState.ERROR
            return False
    
    def initialize_modules(self) -> bool:
        """初始化已加载的模块（同步版本，保持向后兼容）
        
        Returns:
            bool: 所有模块是否初始化成功
        """
        self.logger.info("开始初始化模块（同步模式）")
        
        success = True
        for module_name in self.load_order:
            if module_name in self.modules:
                module_info = self.modules[module_name]
                if module_info.state == ModuleState.LOADED:
                    if not self._initialize_module(module_info):
                        success = False
                        self.logger.error(f"模块 {module_name} 初始化失败")
        
        if success:
            self.logger.info("所有模块初始化完成")
        else:
            self.logger.warning("部分模块初始化失败")
            
        return success
    
    def initialize_modules_async(
        self,
        on_complete: Optional[Callable[[bool], None]] = None,
        on_progress: Optional[Callable[[int, str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ):
        """异步初始化模块（推荐使用）
        
        Args:
            on_complete: 完成回调
            on_progress: 进度回调
            on_error: 错误回调
        """
        self.logger.info("开始异步初始化模块")
        
        def init_task():
            try:
                total = len(self.load_order)
                success = True
                
                for i, module_name in enumerate(self.load_order):
                    if on_progress:
                        percent = int((i / total) * 100)
                        on_progress(percent, f"正在初始化模块: {module_name}")
                    
                    if module_name in self.modules:
                        module_info = self.modules[module_name]
                        if module_info.state == ModuleState.LOADED:
                            if not self._initialize_module(module_info):
                                success = False
                                self.logger.error(f"模块 {module_name} 初始化失败")
                
                if on_progress:
                    on_progress(100, "模块初始化完成")
                
                return success
            except Exception as e:
                error_msg = f"初始化模块时发生错误: {e}"
                self.logger.error(error_msg)
                if on_error:
                    on_error(error_msg)
                return False
        
        self.thread_manager.run_in_thread(
            init_task,
            on_result=on_complete,
            on_error=on_error,
            on_progress=on_progress
        )
    
    def _initialize_module(self, module_info: ModuleInfo) -> bool:
        """初始化单个模块
        
        Args:
            module_info: 模块信息
            
        Returns:
            bool: 模块是否初始化成功
        """
        try:
            self.logger.info(f"正在初始化模块: {module_info.name}")
            
            # 如果模块有实例且有initialize方法，则调用它
            if module_info.instance:
                initialize_method = getattr(module_info.instance, 'initialize', None)
                if initialize_method:
                    config_dir = self.path_utils.get_user_config_dir() / module_info.name
                    initialize_method(str(config_dir))
            
            module_info.state = ModuleState.INITIALIZED
            self.logger.info(f"模块 {module_info.name} 初始化成功")
            return True
        except Exception as e:
            self.logger.error(f"初始化模块 {module_info.name} 失败: {e}")
            module_info.state = ModuleState.ERROR
            return False
    
    def unload_module(self, module_name: str) -> bool:
        """卸载指定模块
        
        Args:
            module_name: 模块名称
            
        Returns:
            bool: 模块是否卸载成功
        """
        if module_name not in self.modules:
            self.logger.warning(f"模块 {module_name} 不存在")
            return False
        
        module_info = self.modules[module_name]
        
        try:
            self.logger.info(f"正在卸载模块: {module_name}")
            
            # 模拟模块卸载过程
            # 在实际应用中，这里会清理模块资源
            module_info.state = ModuleState.UNLOADED
            module_info.instance = None
            
            self.logger.info(f"模块 {module_name} 卸载成功")
            return True
        except Exception as e:
            self.logger.error(f"卸载模块 {module_name} 失败: {e}")
            module_info.state = ModuleState.ERROR
            return False
    
    def get_module(self, module_name: str) -> Optional[ModuleInfo]:
        """根据名称获取模块信息
        
        Args:
            module_name: 模块名称
            
        Returns:
            Optional[ModuleInfo]: 模块信息，如果不存在则返回 None
        """
        return self.modules.get(module_name)
    
    def get_modules_by_state(self, state: ModuleState) -> List[ModuleInfo]:
        """根据状态获取模块列表
        
        Args:
            state: 模块状态
            
        Returns:
            List[ModuleInfo]: 符合状态的模块列表
        """
        return [module for module in self.modules.values() if module.state == state]
    
    def get_all_modules(self) -> Dict[str, ModuleInfo]:
        """获取所有模块信息
        
        Returns:
            Dict[str, ModuleInfo]: 所有模块信息
        """
        return self.modules.copy()