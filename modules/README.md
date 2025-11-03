# 🧩 Modules - 功能模块系统

> 可插拔的功能模块，每个模块提供独立的功能

---

## 📋 目录

- [概述](#概述)
- [模块列表](#模块列表)
- [模块结构](#模块结构)
- [开发指南](#开发指南)
- [模块通信](#模块通信)

---

## 概述

Modules 是 UE Toolkit 的核心功能实现层，采用**模块化架构**设计：

### ✨ 核心特点

- ✅ **可插拔**：每个模块可独立开发、测试、部署
- ✅ **标准化**：统一的接口和配置格式
- ✅ **分层清晰**：logic（业务逻辑）/ ui（用户界面）分离
- ✅ **自动发现**：新模块无需修改核心代码

### 📦 模块架构

```
每个模块包含:
├── manifest.json          # 模块元信息
├── __init__.py            # 模块入口
├── __main__.py            # 主类定义
├── logic/                 # 业务逻辑层
│   └── *_logic.py
└── ui/                    # 用户界面层
    └── *_ui.py
```

---

## 模块列表

### 当前模块（4个）

| 模块 | 名称 | 说明 | 状态 |
|------|------|------|------|
| 🤖 **ai_assistant** | AI 助手 | 智能对话助手，支持上下文感知和记忆管理 | ✅ 活跃 |
| 📦 **asset_manager** | 资产管理器 | UE 资产的导入、分类、管理 | ✅ 活跃 |
| ⚙️ **config_tool** | 配置工具 | UE 项目配置的模板化管理 | ✅ 活跃 |
| 🌐 **site_recommendations** | 网站推荐 | 快速访问常用 UE 相关网站 | ✅ 活跃 |
| 📝 **_template** | 模块模板 | 开发新模块的参考模板 | 📚 参考 |

---

## 模块详解

### 🤖 AI Assistant - AI 助手

**目录**: `ai_assistant/`

#### 功能概述
- 智能对话
- 上下文感知（自动读取资产、配置、日志）
- 多级记忆管理（用户级/会话级/上下文级）
- 从日志自动学习

#### 核心技术
- **ContextManager**: 7层智能上下文融合
- **EnhancedMemoryManager**: 基于 Mem0 的记忆管理
- **API Client**: OpenAI 兼容接口

#### 详细文档
📖 [智能上下文管理系统完整文档.md](ai_assistant/智能上下文管理系统完整文档.md)

#### 快速使用
```python
# 获取 AI 助手模块
ai_module = module_manager.get_module("ai_assistant")

# 获取 UI
chat_window = ai_module.get_widget()
```

---

### 📦 Asset Manager - 资产管理器

**目录**: `asset_manager/`

#### 功能概述
- 资产导入（文件/文件夹）
- 自动分类管理
- 缩略图生成
- 资产搜索和筛选
- 批量操作

#### 核心功能
- **资产导入**: 支持拖拽、批量导入
- **分类管理**: 自定义分类，自动归类
- **缩略图**: 自动生成预览图
- **搜索**: 按名称、分类、类型搜索

#### 数据模型
```python
Asset:
  - name: 资产名称
  - category: 分类
  - asset_type: 类型（文件/文件夹）
  - path: 路径
  - thumbnail_path: 缩略图路径
  - description: 描述
  - size: 大小
  - tags: 标签
```

#### 快速使用
```python
# 获取资产管理器模块
asset_module = module_manager.get_module("asset_manager")

# 获取逻辑层
asset_logic = asset_module.logic

# 获取所有资产
assets = asset_logic.get_all_assets()

# 搜索资产
results = asset_logic.search_assets("蓝图")
```

---

### ⚙️ Config Tool - 配置工具

**目录**: `config_tool/`

#### 功能概述
- 读取 UE 项目配置文件
- 保存配置为模板
- 应用模板到项目
- 配置对比
- 批量管理多个项目

#### 支持的配置文件
- DefaultEngine.ini
- DefaultGame.ini
- DefaultInput.ini
- DefaultEditor.ini
- 所有 UE 配置文件

#### 核心功能
- **模板管理**: 保存/编辑/删除配置模板
- **项目管理**: 添加/管理 UE 项目
- **一键应用**: 快速应用模板到项目
- **配置对比**: 对比不同模板

#### 快速使用
```python
# 获取配置工具模块
config_module = module_manager.get_module("config_tool")

# 获取逻辑层
config_logic = config_module.logic

# 获取所有模板
templates = config_logic.get_templates()

# 应用模板到项目
config_logic.apply_template(template_id, project_path)
```

---

### 🌐 Site Recommendations - 网站推荐

**目录**: `site_recommendations/`

#### 功能概述
- 快速访问常用 UE 网站
- 分类管理网站
- 自定义添加网站
- 一键打开浏览器

#### 网站分类
- 官方文档
- 学习资源
- 资产商店
- 社区论坛
- 开发工具

#### 快速使用
```python
# 获取网站推荐模块
site_module = module_manager.get_module("site_recommendations")

# 获取 UI
site_widget = site_module.get_widget()
```

---

## 模块结构

### 标准模块结构

```
module_name/
├── __init__.py                     # 包初始化
├── __main__.py                     # 模块主类
├── manifest.json                   # 模块配置 ⭐
│
├── logic/                          # 业务逻辑层
│   ├── __init__.py
│   └── module_name_logic.py        # 核心逻辑
│
├── ui/                             # 用户界面层
│   ├── __init__.py
│   └── module_name_ui.py           # 主界面
│
├── resources/                      # 资源文件（可选）
│   ├── themes/
│   └── icons/
│
└── README.md                       # 模块说明（推荐）
```

### manifest.json 配置

```json
{
  "name": "module_name",              // 模块唯一标识
  "display_name": "模块显示名称",      // UI 中显示的名称
  "version": "1.0.0",                 // 版本号
  "description": "模块描述",          // 简短描述
  "author": "作者名",                 // 作者
  "entry_point": "module_name",       // 入口点（类名）
  "dependencies": []                  // 依赖的其他模块
}
```

---

## 开发指南

### 创建新模块

#### 步骤 1: 复制模板

```bash
cp -r modules/_template modules/my_module
```

#### 步骤 2: 修改 manifest.json

```json
{
  "name": "my_module",
  "display_name": "我的模块",
  "version": "1.0.0",
  "description": "这是我的新模块",
  "entry_point": "my_module",
  "dependencies": []
}
```

#### 步骤 3: 实现模块主类

**文件**: `my_module/__main__.py`

```python
from core.module_interface import ModuleInterface
from .logic.my_module_logic import MyModuleLogic
from .ui.my_module_ui import MyModuleUI

class MyModule(ModuleInterface):
    def __init__(self):
        self.logic = None
        self.ui = None
    
    @property
    def name(self):
        return "my_module"
    
    @property
    def display_name(self):
        return "我的模块"
    
    def initialize(self, config_manager, logger):
        """初始化模块"""
        self.config = config_manager
        self.logger = logger
        
        # 初始化逻辑层
        self.logic = MyModuleLogic(config_manager, logger)
        
        # 初始化 UI
        self.ui = MyModuleUI(self.logic)
        
        return True
    
    def get_widget(self):
        """获取模块UI"""
        return self.ui
    
    def cleanup(self):
        """清理资源"""
        if self.logic:
            self.logic.cleanup()
```

#### 步骤 4: 实现业务逻辑

**文件**: `my_module/logic/my_module_logic.py`

```python
from core.base_logic import BaseLogic

class MyModuleLogic(BaseLogic):
    def __init__(self, config_manager, logger):
        super().__init__(config_manager, logger)
        # 初始化你的逻辑
    
    def do_something(self):
        """实现你的业务逻辑"""
        self.logger.info("执行某操作")
        # 你的代码
        return result
```

#### 步骤 5: 实现用户界面

**文件**: `my_module/ui/my_module_ui.py`

```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton

class MyModuleUI(QWidget):
    def __init__(self, logic):
        super().__init__()
        self.logic = logic
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        btn = QPushButton("执行操作")
        btn.clicked.connect(self.on_button_click)
        layout.addWidget(btn)
        
        self.setLayout(layout)
    
    def on_button_click(self):
        result = self.logic.do_something()
        # 更新 UI
```

#### 步骤 6: 测试模块

```bash
python main.py
# 新模块会自动被发现和加载
```

---

## 模块通信

### 方法 1: 通过 ModuleManager

```python
# 在一个模块中获取另一个模块
module_manager = self.config.get("module_manager")
other_module = module_manager.get_module("other_module")

# 访问其他模块的逻辑层
other_logic = other_module.logic
result = other_logic.some_method()
```

### 方法 2: 通过依赖注入

在 `manifest.json` 中声明依赖：

```json
{
  "dependencies": ["asset_manager", "config_tool"]
}
```

在 `initialize()` 中接收依赖：

```python
def initialize(self, config_manager, logger, dependencies=None):
    if dependencies:
        self.asset_manager = dependencies.get("asset_manager")
        self.config_tool = dependencies.get("config_tool")
```

### 方法 3: 信号槽机制（推荐）

```python
# 在模块中定义信号
from PyQt6.QtCore import pyqtSignal

class MyModuleLogic:
    data_changed = pyqtSignal(dict)  # 定义信号
    
    def update_data(self):
        self.data_changed.emit({"key": "value"})  # 发射信号

# 在其他模块中连接信号
def on_data_changed(self, data):
    print(f"接收到数据: {data}")

my_module.logic.data_changed.connect(self.on_data_changed)
```

---

## 最佳实践

### 1. 模块设计原则

- ✅ **单一职责**: 每个模块只做一件事
- ✅ **松耦合**: 模块间依赖最小化
- ✅ **高内聚**: 相关功能放在一起
- ✅ **可测试**: 易于编写单元测试

### 2. 代码组织

- ✅ Logic 和 UI 分离
- ✅ 使用类型提示
- ✅ 添加文档字符串
- ✅ 遵循 PEP 8 规范

### 3. 错误处理

```python
def some_method(self):
    try:
        # 业务逻辑
        result = self.do_something()
        return result
    except Exception as e:
        self.logger.error(f"操作失败: {e}", exc_info=True)
        return None
```

### 4. 资源清理

```python
def cleanup(self):
    """模块卸载时清理资源"""
    # 关闭文件
    # 断开连接
    # 释放内存
    self.logger.info(f"{self.name} 清理完成")
```

---

## 配置管理

### 模块配置

每个模块可以有自己的配置文件：

**位置**: `{用户数据目录}/config/modules/{module_name}.json`

**使用示例**:
```python
def initialize(self, config_manager, logger):
    # 加载模块配置
    self.config = config_manager.get_module_config(self.name)
    
    # 读取配置
    setting = self.config.get("setting_key", default="default")
    
    # 保存配置
    self.config.set("setting_key", "new_value")
    self.config.save()
```

---

## 调试技巧

### 1. 启用详细日志

```python
logger.setLevel(logging.DEBUG)
```

### 2. 模块加载失败排查

1. 检查 `manifest.json` 格式
2. 查看 `logs/ue_toolkit_YYYYMMDD.log`
3. 验证类名和 entry_point 匹配
4. 检查依赖是否满足

### 3. UI 调试

```python
# 在 UI 类中添加调试输出
def init_ui(self):
    print(f"[DEBUG] {self.__class__.__name__} 初始化")
    # UI 代码
```

---

## 测试

### 单元测试模板

```python
# tests/test_modules/test_my_module.py

import pytest
from modules.my_module.logic.my_module_logic import MyModuleLogic

def test_my_module_logic():
    logic = MyModuleLogic(None, None)
    result = logic.do_something()
    assert result is not None

def test_my_module_error_handling():
    logic = MyModuleLogic(None, None)
    # 测试错误情况
```

### 运行测试

```bash
pytest tests/test_modules/
```

---

## 性能优化

### 1. 延迟加载

```python
@property
def heavy_resource(self):
    if not hasattr(self, '_heavy_resource'):
        self._heavy_resource = self.load_heavy_resource()
    return self._heavy_resource
```

### 2. 缓存结果

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_computation(self, param):
    # 耗时计算
    return result
```

### 3. 异步操作

```python
from core.utils.thread_utils import run_in_thread

@run_in_thread
def long_running_task(self):
    # 长时间运行的任务
    pass
```

---

## 常见问题

### Q: 模块无法加载？
A: 检查 manifest.json 和类名是否匹配

### Q: 如何访问其他模块？
A: 通过 ModuleManager.get_module()

### Q: 模块间如何通信？
A: 推荐使用信号槽机制

### Q: 如何持久化模块数据？
A: 使用 ConfigManager 保存配置

---

## 模块开发检查清单

开发新模块时的检查项：

- [ ] manifest.json 配置正确
- [ ] 实现 ModuleInterface 接口
- [ ] logic 和 ui 分离
- [ ] 添加错误处理
- [ ] 实现 cleanup() 方法
- [ ] 添加日志记录
- [ ] 编写文档
- [ ] 编写单元测试
- [ ] 测试模块加载/卸载
- [ ] 测试与其他模块交互

---

## 参考资源

- [模块接口定义](../core/module_interface.py)
- [模块模板](_template/)
- [AI 助手模块](ai_assistant/) - 完整实现示例

---

**最后更新**: 2025-11-04  
**维护者**: UE Toolkit Development Team

