# -*- coding: utf-8 -*-

"""
工具注册表
定义只读工具的接口和调度逻辑
"""

from typing import Dict, Any, List, Callable, Optional
from core.logger import get_logger

logger = get_logger(__name__)


class ToolDefinition:
    """工具定义"""
    
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        function: Callable,
        requires_confirmation: bool = False
    ):
        self.name = name
        self.description = description
        self.parameters = parameters  # JSON Schema 格式
        self.function = function
        self.requires_confirmation = requires_confirmation  # v0.2: 权限声明


class ToolsRegistry:
    """
    工具注册表
    
    v0.2: 注册和管理所有只读工具
    v0.3: 扩展支持受控写入工具
    """
    
    def __init__(self, asset_reader=None, config_reader=None, log_analyzer=None, document_reader=None, asset_importer=None):
        """
        初始化工具注册表
        
        Args:
            asset_reader: 资产读取器
            config_reader: 配置读取器
            log_analyzer: 日志分析器
            document_reader: 文档读取器
            asset_importer: 资产导入器（测试功能）
        """
        self.logger = logger
        self.asset_reader = asset_reader
        self.config_reader = config_reader
        self.log_analyzer = log_analyzer
        self.document_reader = document_reader
        self.asset_importer = asset_importer
        
        # 工具注册表
        self.tools: Dict[str, ToolDefinition] = {}
        
        # 注册所有只读工具
        self._register_readonly_tools()
        
        # 注册测试功能工具
        self._register_experimental_tools()
        
        self.logger.info(f"工具注册表初始化完成，共注册 {len(self.tools)} 个工具")
    
    def _register_readonly_tools(self):
        """注册所有只读工具"""
        
        # 1. 搜索资产
        self.register_tool(ToolDefinition(
            name="search_assets",
            description="搜索虚幻引擎资产（模型、蓝图、材质等）",
            parameters={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词，如资产名称或类型"
                    }
                },
                "required": ["keyword"]
            },
            function=self._tool_search_assets,
            requires_confirmation=False  # 只读，无需确认
        ))
        
        # 2. 查询资产详情
        self.register_tool(ToolDefinition(
            name="query_asset_detail",
            description="获取特定资产的详细信息（路径、文件列表、大小等）",
            parameters={
                "type": "object",
                "properties": {
                    "asset_name": {
                        "type": "string",
                        "description": "资产名称"
                    }
                },
                "required": ["asset_name"]
            },
            function=self._tool_query_asset_detail,
            requires_confirmation=False
        ))
        
        # 3. 搜索配置模板
        self.register_tool(ToolDefinition(
            name="search_configs",
            description="搜索UE项目配置模板",
            parameters={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词"
                    }
                },
                "required": ["keyword"]
            },
            function=self._tool_search_configs,
            requires_confirmation=False
        ))
        
        # 4. 对比配置
        self.register_tool(ToolDefinition(
            name="diff_config",
            description="对比两个配置模板的差异",
            parameters={
                "type": "object",
                "properties": {
                    "config1": {"type": "string", "description": "第一个配置名称"},
                    "config2": {"type": "string", "description": "第二个配置名称"}
                },
                "required": ["config1", "config2"]
            },
            function=self._tool_diff_config,
            requires_confirmation=False
        ))
        
        # 5. 搜索日志
        self.register_tool(ToolDefinition(
            name="search_logs",
            description="搜索日志文件中的特定内容",
            parameters={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词"
                    }
                },
                "required": ["keyword"]
            },
            function=self._tool_search_logs,
            requires_confirmation=False
        ))
        
        # 6. 搜索文档
        self.register_tool(ToolDefinition(
            name="search_docs",
            description="搜索项目文档和使用说明",
            parameters={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词"
                    }
                },
                "required": ["keyword"]
            },
            function=self._tool_search_docs,
            requires_confirmation=False
        ))
    
    def register_tool(self, tool: ToolDefinition):
        """注册工具"""
        self.tools[tool.name] = tool
        self.logger.debug(f"注册工具: {tool.name} (需要确认: {tool.requires_confirmation})")
    
    def openai_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        返回 OpenAI tools 描述格式
        
        兼容 ChatGPT Function Calling 规范：
        tools=[{type:'function', function:{name, description, parameters}}]
        
        Returns:
            List[Dict]: OpenAI tools 格式的工具列表
        """
        schemas = []
        
        for tool_name, tool_def in self.tools.items():
            schemas.append({
                "type": "function",
                "function": {
                    "name": tool_def.name,
                    "description": tool_def.description,
                    "parameters": tool_def.parameters
                }
            })
        
        return schemas
    
    def dispatch(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        调度工具执行
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            Dict: 工具执行结果 {success, result, error}
        """
        try:
            if tool_name not in self.tools:
                return {
                    "success": False,
                    "error": f"未知工具: {tool_name}"
                }
            
            tool = self.tools[tool_name]
            
            self.logger.info(f"执行工具: {tool_name}, 参数: {arguments}")
            
            # 调用工具函数
            result = tool.function(**arguments)
            
            return {
                "success": True,
                "result": result,
                "tool_name": tool_name,
                "requires_confirmation": tool.requires_confirmation
            }
        
        except Exception as e:
            self.logger.error(f"工具执行失败 {tool_name}: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name
            }
    
    # ========== 工具实现函数 ==========
    
    def _tool_search_assets(self, keyword: str) -> str:
        """搜索资产工具实现"""
        if self.asset_reader:
            return self.asset_reader.search_assets(keyword)
        return "[错误] 资产读取器未初始化"
    
    def _tool_query_asset_detail(self, asset_name: str) -> str:
        """查询资产详情工具实现"""
        if self.asset_reader:
            return self.asset_reader.get_asset_details(asset_name)
        return "[错误] 资产读取器未初始化"
    
    def _tool_search_configs(self, keyword: str) -> str:
        """搜索配置工具实现"""
        if self.config_reader:
            return self.config_reader.search_configs(keyword)
        return "[错误] 配置读取器未初始化"
    
    def _tool_diff_config(self, config1: str, config2: str) -> str:
        """配置对比工具实现（暂时返回占位符）"""
        # TODO: 实现配置对比逻辑
        return f"[配置对比] {config1} vs {config2}\n（功能待实现）"
    
    def _tool_search_logs(self, keyword: str) -> str:
        """搜索日志工具实现"""
        if self.log_analyzer:
            return self.log_analyzer.search_in_logs(keyword)
        return "[错误] 日志分析器未初始化"
    
    def _tool_search_docs(self, keyword: str) -> str:
        """搜索文档工具实现"""
        if self.document_reader:
            return self.document_reader.search_in_documents(keyword)
        return "[错误] 文档读取器未初始化"
    
    def _register_experimental_tools(self):
        """注册实验性功能工具（测试版）"""
        
        # 1. 导入资产到UE项目
        self.register_tool(ToolDefinition(
            name="import_asset_to_ue",
            description="将资产导入到正在运行的虚幻引擎项目（测试功能）",
            parameters={
                "type": "object",
                "properties": {
                    "asset_name": {
                        "type": "string",
                        "description": "要导入的资产名称"
                    },
                    "target_project_path": {
                        "type": "string",
                        "description": "目标UE项目路径（可选）"
                    }
                },
                "required": ["asset_name"]
            },
            function=self._tool_import_asset,
            requires_confirmation=False  # 测试功能，简化流程
        ))
        
        # 2. 列出可导入的资产
        self.register_tool(ToolDefinition(
            name="list_importable_assets",
            description="列出所有可以导入到UE项目的资产",
            parameters={
                "type": "object",
                "properties": {}
            },
            function=self._tool_list_importable_assets,
            requires_confirmation=False
        ))
    
    def _tool_import_asset(self, asset_name: str, target_project_path: str = None) -> str:
        """导入资产工具实现"""
        if self.asset_importer:
            result = self.asset_importer.import_asset_to_ue(asset_name, target_project_path)
            return result.get('message', '[错误] 导入失败')
        return "[错误] 资产导入器未初始化"
    
    def _tool_list_importable_assets(self) -> str:
        """列出可导入资产工具实现"""
        if self.asset_importer:
            return self.asset_importer.list_importable_assets()
        return "[错误] 资产导入器未初始化"
    
    def _register_controlled_tools(self):
        """
        v0.3 新增：注册受控写入工具
        
        所有受控工具标记 requires_confirmation=True
        """
        # 1. 导出配置模板
        self.register_tool(ToolDefinition(
            name="export_config_template",
            description="导出UE配置模板到指定路径（需要确认）",
            parameters={
                "type": "object",
                "properties": {
                    "template_name": {
                        "type": "string",
                        "description": "配置模板名称"
                    },
                    "export_path": {
                        "type": "string",
                        "description": "导出路径"
                    }
                },
                "required": ["template_name", "export_path"]
            },
            function=self._tool_export_config_template,
            requires_confirmation=True  # 需要确认
        ))
        
        # 2. 批量重命名预览
        self.register_tool(ToolDefinition(
            name="batch_rename_preview",
            description="批量重命名资产（需要确认）",
            parameters={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "匹配模式"
                    },
                    "replacement": {
                        "type": "string",
                        "description": "替换文本"
                    },
                    "asset_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "资产ID列表"
                    }
                },
                "required": ["pattern", "replacement", "asset_ids"]
            },
            function=self._tool_batch_rename_preview,
            requires_confirmation=True  # 需要确认
        ))
    
    def _tool_export_config_template(self, template_name: str, export_path: str) -> str:
        """导出配置模板工具实现（返回预览）"""
        if self.controlled_tools:
            result = self.controlled_tools.export_config_template(template_name, export_path)
            return result.get('preview', '[错误] 无预览')
        return "[错误] 受控工具集未初始化"
    
    def _tool_batch_rename_preview(self, pattern: str, replacement: str, asset_ids: list) -> str:
        """批量重命名工具实现（返回预览）"""
        if self.controlled_tools:
            result = self.controlled_tools.batch_rename_preview(pattern, replacement, asset_ids)
            return result.get('preview', '[错误] 无预览')
        return "[错误] 受控工具集未初始化"

