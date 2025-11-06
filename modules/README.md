# Modules 功能模块

本目录包含 UE Toolkit 的所有功能模块，每个模块都是独立的、可插拔的功能单元。

## 📁 模块结构

```
modules/
├── _template/                # 模块模板（用于快速创建新模块）
├── ai_assistant/             # AI 助手模块
├── asset_manager/            # 资产管理模块
├── config_tool/              # 配置工具模块
└── site_recommendations/     # 站点推荐模块
```

## 🎯 功能模块

### 1. AI Assistant (AI 助手)

**路径**: `modules/ai_assistant/`

**功能描述**:
- 🤖 全能型 AI 助手，支持编程、UE 开发和工具箱管理
- 💬 智能对话系统，支持多轮对话和上下文理解
- 🧠 多级记忆系统（用户、会话、上下文）
- 🔍 基于 FAISS 的语义检索
- 🛠️ Function Calling（函数调用）能力
- 📝 Markdown 渲染和代码高亮

**技术栈**:
- LLM: Ollama / API (OpenAI-compatible)
- 向量检索: FAISS
- 嵌入模型: BAAI/bge-small-zh-v1.5
- UI: PyQt6 + Markdown + Pygments

**关键文件**:
- `ai_assistant.py` - 模块入口
- `logic/` - 核心逻辑
  - `api_client.py` / `ollama_llm_client.py` - LLM 客户端
  - `context_manager.py` - 上下文管理器
  - `enhanced_memory_manager.py` - 记忆管理器
  - `function_calling_coordinator.py` - 函数调用协调器
  - `tools_registry.py` - 工具注册表
- `ui/` - 用户界面
  - `chat_window.py` - 聊天窗口
  - `chat_composer.py` - 输入框（ChatGPT 风格）
  - `markdown_message.py` - 消息渲染

**详细文档**: 查看 `ai_assistant/README.md`（如果存在）

---

### 2. Asset Manager (资产管理器)

**路径**: `modules/asset_manager/`

**功能描述**:
- 📦 浏览和管理 UE 项目资产
- 🔍 资产搜索和过滤
- 📊 资产统计和分析
- 🖼️ 资产预览（缩略图）
- 📁 资产分类和标签管理

**技术栈**:
- UE 资产解析: UE4/UE5 兼容
- UI: PyQt6 + QTreeView + QTableView

**关键文件**:
- `asset_manager.py` - 模块入口
- `logic/asset_manager_logic.py` - 核心逻辑
- `ui/` - 用户界面组件

---

### 3. Config Tool (配置工具)

**路径**: `modules/config_tool/`

**功能描述**:
- ⚙️ 管理 UE 项目配置文件
- 📝 配置模板管理（如 DefaultEngine.ini）
- 🔄 配置导入/导出
- 🎯 配置参数快速调整
- 📋 配置历史记录

**技术栈**:
- INI 文件解析和编辑
- UI: PyQt6 + 自定义编辑器

**关键文件**:
- `__main__.py` - 模块入口
- `logic/config_tool_logic.py` - 核心逻辑
- `ui/` - 用户界面组件

---

### 4. Site Recommendations (站点推荐)

**路径**: `modules/site_recommendations/`

**功能描述**:
- 🌐 UE 相关网站推荐列表
- 🔖 网站分类和标签
- ⭐ 收藏和快速访问
- 🔍 网站搜索和过滤

**技术栈**:
- UI: PyQt6 + QListView

**关键文件**:
- `__main__.py` - 模块入口
- `logic/site_recommendations_logic.py` - 核心逻辑
- `ui/` - 用户界面组件

---

## 🏗️ 模块开发规范

### 标准模块结构

每个模块应遵循以下目录结构：

```
module_name/
├── __init__.py               # 模块包初始化
├── __main__.py 或 module_name.py  # 模块入口
├── manifest.json             # 模块清单
├── config_template.json      # 配置模板（可选）
├── config_schema.py          # 配置 Schema（可选）
├── logic/                    # 业务逻辑层
│   ├── __init__.py
│   └── module_logic.py       # 核心逻辑
├── ui/                       # 用户界面层
│   ├── __init__.py
│   └── ...                   # UI 组件
├── resources/                # 资源文件（可选）
│   ├── themes/               # 主题样式
│   ├── icons/                # 图标
│   └── ...
└── README.md                 # 模块说明（建议）
```

### 模块清单 (manifest.json)

```json
{
    "name": "module_name",
    "display_name": "模块显示名称",
    "version": "1.0.0",
    "author": "作者",
    "description": "模块描述",
    "icon": "icon_name",
    "entry_point": "module_name.py",
    "dependencies": [],
    "config_template": "config_template.json"
}
```

### 模块生命周期

1. **初始化** (`__init__`)
   - 加载配置
   - 初始化逻辑层
   - 创建 UI（懒加载）

2. **激活** (`activate`)
   - 显示 UI
   - 启动后台任务

3. **停用** (`deactivate`)
   - 清理资源
   - 保存状态

4. **销毁** (`cleanup`)
   - 释放所有资源
   - 关闭连接

### 模块通信

模块间通信使用以下方式：

1. **直接调用** - 通过 `ModuleManager` 获取其他模块实例
2. **信号槽** - 使用 PyQt6 信号机制
3. **事件系统** - 使用全局事件总线（如果实现）

## 🚀 创建新模块

### 方法1: 使用模块模板

```bash
# 复制模板
cp -r modules/_template modules/new_module

# 修改清单文件
# 编辑 modules/new_module/manifest.json

# 实现逻辑和 UI
# 编辑 modules/new_module/logic/module_logic.py
# 编辑 modules/new_module/ui/...
```

### 方法2: 手动创建

1. 创建模块目录和文件
2. 实现 `ModuleInterface` 接口
3. 添加 `manifest.json`
4. 实现逻辑层和 UI 层
5. 注册模块到 `ModuleManager`

## 📝 开发最佳实践

### 1. 分层架构

- **UI 层**: 只负责界面显示和用户交互
- **Logic 层**: 处理业务逻辑和数据
- **分离关注点**: UI 和逻辑解耦

### 2. 配置管理

- 使用 `ConfigManager` 管理模块配置
- 提供合理的默认配置
- 支持配置验证和升级

### 3. 错误处理

- 捕获并处理所有异常
- 提供友好的错误提示
- 记录错误日志

### 4. 性能优化

- UI 懒加载
- 异步操作（耗时任务）
- 资源及时释放

### 5. 代码规范

- 遵循 PEP 8 代码风格
- 添加完整的文档字符串
- 编写单元测试（建议）

## 🔧 调试模块

### 启用调试模式

```python
# 在模块入口添加
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 查看模块日志

```python
from core.logger import get_logger
logger = get_logger(__name__)

logger.debug("调试信息")
logger.info("普通信息")
logger.warning("警告信息")
logger.error("错误信息")
```

## ⚠️ 注意事项

- **模块命名**: 使用小写字母和下划线
- **版本管理**: 遵循语义化版本规范
- **向后兼容**: 升级时保持 API 稳定
- **资源清理**: 确保模块销毁时释放所有资源
- **线程安全**: 注意多线程访问共享资源

## 🔗 相关文档

- [模块开发指南](../docs/module_development.md)
- [API 文档](../docs/api.md)
- [配置系统说明](../docs/configuration.md)

