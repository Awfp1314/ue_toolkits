# 🎯 Core - 核心系统

> UE Toolkit 的基础设施层，提供应用框架、模块管理、配置管理等核心功能

---

## 📋 目录

- [概述](#概述)
- [核心组件](#核心组件)
- [配置系统](#配置系统)
- [工具集](#工具集)
- [使用指南](#使用指南)

---

## 概述

Core 层是整个应用的基础，负责：
- ✅ 应用生命周期管理
- ✅ 模块的动态加载和管理
- ✅ 配置的读取、验证、备份
- ✅ 日志系统
- ✅ 通用工具类

**设计原则**：
- 高内聚、低耦合
- 提供稳定的 API
- 不依赖具体业务模块

---

## 核心组件

### 📦 文件结构

```
core/
├── app_manager.py              # 应用管理器（总调度）
├── module_manager.py           # 模块管理器
├── module_interface.py         # 模块接口定义
├── base_logic.py               # 基础逻辑类
├── logger.py                   # 日志系统
├── single_instance.py          # 单例管理
├── config_manager.py           # 配置管理器（兼容层）
│
├── config/                     # 配置子系统
│   ├── config_manager.py       # 配置管理
│   ├── config_validator.py     # 配置验证
│   └── config_backup.py        # 配置备份
│
├── config_templates/           # 配置模板
│   └── app_config_template.json
│
└── utils/                      # 工具集
    ├── path_utils.py           # 路径工具
    ├── file_utils.py           # 文件操作
    ├── validators.py           # 验证器
    ├── custom_widgets.py       # 自定义控件
    ├── style_loader.py         # 样式加载
    ├── theme_manager.py        # 主题管理
    ├── thread_utils.py         # 线程工具
    ├── ue_process_utils.py     # UE进程工具
    └── performance_monitor.py  # 性能监控
```

---

## 核心组件详解

### 1. AppManager - 应用管理器

**文件**: `app_manager.py`

**职责**：
- 管理应用的整个生命周期
- 协调各子系统的初始化
- 处理应用启动、运行、关闭

**关键方法**：
```python
class AppManager:
    def __init__(self, app: QApplication)
    def initialize(self) -> bool        # 初始化应用
    def run(self) -> int                # 运行应用
    def shutdown(self)                  # 关闭应用
```

**使用示例**：
```python
from PyQt6.QtWidgets import QApplication
from core.app_manager import AppManager

app = QApplication(sys.argv)
app_manager = AppManager(app)
app_manager.initialize()
sys.exit(app_manager.run())
```

---

### 2. ModuleManager - 模块管理器

**文件**: `module_manager.py`

**职责**：
- 扫描和发现模块
- 动态加载/卸载模块
- 管理模块生命周期
- 处理模块依赖

**关键方法**：
```python
class ModuleManager:
    def scan_modules(self) -> List[str]          # 扫描可用模块
    def load_module(self, name: str) -> bool     # 加载模块
    def unload_module(self, name: str) -> bool   # 卸载模块
    def get_module(self, name: str) -> Module    # 获取模块实例
    def get_all_modules(self) -> List[Module]    # 获取所有模块
```

**模块发现机制**：
- 扫描 `modules/` 目录
- 读取 `manifest.json` 配置
- 验证模块完整性
- 按依赖顺序加载

**使用示例**：
```python
from core.module_manager import ModuleManager

manager = ModuleManager()
manager.scan_modules()
manager.load_module("ai_assistant")

# 获取模块实例
ai_module = manager.get_module("ai_assistant")
```

---

### 3. ModuleInterface - 模块接口

**文件**: `module_interface.py`

**职责**：
- 定义标准模块接口
- 确保模块一致性

**接口定义**：
```python
class ModuleInterface:
    @property
    def name(self) -> str:
        """模块名称"""
        
    @property
    def display_name(self) -> str:
        """显示名称"""
        
    def initialize(self, config_manager, logger) -> bool:
        """初始化模块"""
        
    def get_widget(self) -> QWidget:
        """获取模块UI"""
        
    def cleanup(self):
        """清理资源"""
```

**所有模块必须实现此接口**

---

### 4. Logger - 日志系统

**文件**: `logger.py`

**职责**：
- 统一的日志管理
- 多级别日志（DEBUG/INFO/WARNING/ERROR）
- 自动日志轮转
- 文件和控制台输出

**日志级别**：
- `DEBUG` - 调试信息
- `INFO` - 一般信息
- `WARNING` - 警告
- `ERROR` - 错误
- `CRITICAL` - 严重错误

**使用示例**：
```python
from core.logger import get_logger

logger = get_logger(__name__)

logger.debug("调试信息")
logger.info("程序启动")
logger.warning("警告信息")
logger.error("错误发生", exc_info=True)
```

**日志位置**：
- Windows: `%LOCALAPPDATA%\UE_Toolkit\logs\`
- macOS: `~/Library/Application Support/UE_Toolkit/logs/`
- Linux: `~/.local/share/UE_Toolkit/logs/`

---

### 5. SingleInstance - 单例管理

**文件**: `single_instance.py`

**职责**：
- 防止程序多开
- 确保只有一个实例运行

**使用示例**：
```python
from core.single_instance import SingleInstance

single = SingleInstance()
if not single.is_first_instance():
    print("程序已经在运行")
    sys.exit(1)
```

---

## 配置系统

### 📁 config/ 子系统

#### ConfigManager - 配置管理

**文件**: `config/config_manager.py`

**职责**：
- 读取/保存配置文件
- 配置的增删改查
- 默认配置管理

**配置格式**: JSON

**使用示例**：
```python
from core.config.config_manager import ConfigManager

config = ConfigManager()
config.load("app_config.json")

# 读取配置
value = config.get("key", default="default_value")

# 设置配置
config.set("key", "new_value")

# 保存配置
config.save()
```

---

#### ConfigValidator - 配置验证

**文件**: `config/config_validator.py`

**职责**：
- 验证配置格式
- 检查必需字段
- 类型检查

**使用示例**：
```python
from core.config.config_validator import ConfigValidator

validator = ConfigValidator(schema)
is_valid = validator.validate(config_data)
```

---

#### ConfigBackup - 配置备份

**文件**: `config/config_backup.py`

**职责**：
- 自动备份配置
- 恢复配置
- 备份管理

**使用示例**：
```python
from core.config.config_backup import ConfigBackupManager

backup = ConfigBackupManager()
backup.create_backup("app_config.json")
backup.restore_backup(backup_id)
```

---

## 工具集

### 🔧 utils/ 工具类

#### PathUtils - 路径工具

**文件**: `utils/path_utils.py`

**功能**：
- 跨平台路径处理
- 获取系统目录
- 路径验证

**关键方法**：
```python
class PathUtils:
    def get_user_data_dir(self) -> Path          # 用户数据目录
    def get_user_config_dir(self) -> Path        # 配置目录
    def get_user_logs_dir(self) -> Path          # 日志目录
    def get_app_root_dir(self) -> Path           # 应用根目录
    def ensure_dir_exists(self, path: Path)      # 确保目录存在
```

**使用示例**：
```python
from core.utils.path_utils import PathUtils

path_utils = PathUtils()
config_dir = path_utils.get_user_config_dir()
path_utils.ensure_dir_exists(config_dir)
```

---

#### FileUtils - 文件操作

**文件**: `utils/file_utils.py`

**功能**：
- 安全的文件操作
- 文件复制/移动/删除
- 目录遍历

**使用示例**：
```python
from core.utils.file_utils import FileUtils

FileUtils.copy_file(src, dst)
FileUtils.move_file(src, dst)
FileUtils.delete_file(path)
```

---

#### ThemeManager - 主题管理

**文件**: `utils/theme_manager.py`

**功能**：
- 加载主题配置
- 主题切换
- 自定义主题

**使用示例**：
```python
from core.utils.theme_manager import ThemeManager

theme_mgr = ThemeManager()
theme_mgr.load_theme("dark")
theme_mgr.apply_theme(app)
```

---

#### StyleLoader - 样式加载

**文件**: `utils/style_loader.py`

**功能**：
- 加载 QSS 样式表
- 样式变量替换
- 样式合并

**使用示例**：
```python
from core.utils.style_loader import StyleLoader

loader = StyleLoader()
stylesheet = loader.load("main_window.qss")
widget.setStyleSheet(stylesheet)
```

---

#### ThreadUtils - 线程工具

**文件**: `utils/thread_utils.py`

**功能**：
- 后台任务执行
- 线程池管理
- 异步操作

**使用示例**：
```python
from core.utils.thread_utils import run_in_thread

@run_in_thread
def long_task():
    # 耗时操作
    pass
```

---

## 使用指南

### 创建新模块

1. **继承 ModuleInterface**
```python
from core.module_interface import ModuleInterface

class MyModule(ModuleInterface):
    @property
    def name(self):
        return "my_module"
    
    def initialize(self, config_manager, logger):
        self.config = config_manager
        self.logger = logger
        return True
    
    def get_widget(self):
        return MyWidget()
```

2. **创建 manifest.json**
```json
{
  "name": "my_module",
  "display_name": "我的模块",
  "version": "1.0.0",
  "entry_point": "my_module"
}
```

3. **模块自动被发现和加载**

---

### 使用配置管理

```python
from core.config.config_manager import ConfigManager

# 初始化
config = ConfigManager()
config.load_or_create("my_config.json", default_config)

# 读取
value = config.get("section.key", default="default")

# 修改
config.set("section.key", "new_value")

# 保存
config.save()
```

---

### 使用日志系统

```python
from core.logger import get_logger

logger = get_logger(__name__)

try:
    # 业务逻辑
    logger.info("操作开始")
    result = do_something()
    logger.info("操作成功")
except Exception as e:
    logger.error(f"操作失败: {e}", exc_info=True)
```

---

## 最佳实践

### 1. 日志使用
- ✅ 关键操作记录 INFO 日志
- ✅ 异常捕获记录 ERROR 日志
- ✅ 调试信息使用 DEBUG 日志
- ❌ 不要记录敏感信息

### 2. 配置管理
- ✅ 使用默认值
- ✅ 验证配置格式
- ✅ 定期备份配置
- ❌ 不要硬编码配置

### 3. 模块开发
- ✅ 实现完整的接口
- ✅ 正确处理初始化失败
- ✅ 清理资源
- ❌ 不要直接访问其他模块

### 4. 错误处理
- ✅ 捕获所有异常
- ✅ 提供有意义的错误信息
- ✅ 记录错误日志
- ❌ 不要吞掉异常

---

## API 参考

### AppManager

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `initialize()` | 初始化应用 | bool |
| `run()` | 运行应用 | int (退出码) |
| `shutdown()` | 关闭应用 | None |

### ModuleManager

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `scan_modules()` | 扫描模块 | List[str] |
| `load_module(name)` | 加载模块 | bool |
| `get_module(name)` | 获取模块 | Module |

### ConfigManager

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `load(filename)` | 加载配置 | bool |
| `save()` | 保存配置 | bool |
| `get(key, default)` | 读取配置 | Any |
| `set(key, value)` | 设置配置 | None |

---

## 依赖关系

```
AppManager
    ↓
ModuleManager
    ↓
各个模块
    ↓
ConfigManager, Logger, Utils
```

**核心层不依赖业务模块，保持独立性**

---

## 性能考虑

- ⚡ 模块延迟加载
- ⚡ 配置缓存
- ⚡ 日志异步写入
- ⚡ 线程池复用

---

## 故障排查

### 模块加载失败
1. 检查 manifest.json 格式
2. 查看日志文件
3. 验证依赖关系

### 配置丢失
1. 检查备份目录
2. 使用默认配置恢复

### 日志无法写入
1. 检查目录权限
2. 检查磁盘空间

---

## 扩展点

Core 层提供的扩展点：

1. **自定义模块加载器**
2. **自定义配置格式**
3. **自定义日志处理器**
4. **自定义工具类**

---

**最后更新**: 2025-11-04  
**维护者**: UE Toolkit Core Team

