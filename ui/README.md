# UI 用户界面层

本目录包含应用程序的主窗口和全局 UI 组件，不包括模块特定的 UI（模块 UI 在各自的模块目录下）。

## 📁 目录结构

```
ui/
├── dialogs/                        # 对话框组件
│   ├── close_confirmation_dialog.py  # 关闭确认对话框
│   └── __init__.py
├── icons/                          # 图标资源
│   └── toolbar.png                 # 工具栏图标
├── main_window_components/         # 主窗口组件
│   ├── title_bar.py                # 自定义标题栏
│   └── __init__.py
├── main_window_handlers/           # 主窗口处理器
│   ├── module_loader.py            # 模块加载器
│   ├── navigation_handler.py       # 导航处理器
│   └── __init__.py
├── settings_widget.py              # 设置界面
├── system_tray_manager.py          # 系统托盘管理
├── ue_main_window_core.py          # 主窗口核心逻辑
├── ue_main_window.py               # 主窗口入口
└── __init__.py
```

## 🪟 主窗口组件

### 1. `ue_main_window.py` - 主窗口入口

应用程序的主窗口类，负责初始化和协调所有 UI 组件。

**功能**:
- 创建主窗口布局
- 加载和显示模块
- 处理窗口事件
- 管理窗口状态

**核心方法**:

```python
class UEMainWindow(QMainWindow):
    def __init__(self):
        """初始化主窗口"""
        
    def init_ui(self):
        """初始化 UI"""
        
    def load_module(self, module_name):
        """加载模块"""
        
    def closeEvent(self, event):
        """关闭事件处理"""
```

**使用示例**:

```python
from ui.ue_main_window import UEMainWindow

app = QApplication(sys.argv)
window = UEMainWindow()
window.show()
sys.exit(app.exec())
```

---

### 2. `ue_main_window_core.py` - 主窗口核心逻辑

主窗口的核心业务逻辑，处理模块管理、导航和状态。

**功能**:
- 模块生命周期管理
- 侧边栏导航
- 状态栏更新
- 事件分发

**核心方法**:

```python
class UEMainWindowCore:
    def setup_modules(self):
        """设置模块"""
        
    def switch_module(self, module_name):
        """切换模块"""
        
    def update_status(self, message):
        """更新状态栏"""
```

---

### 3. `title_bar.py` - 自定义标题栏

自定义的窗口标题栏，支持拖动、最小化、最大化、关闭等功能。

**功能**:
- 无边框窗口支持
- 拖动窗口
- 窗口控制按钮（最小化、最大化、关闭）
- 自定义主题样式

**UI 元素**:
- 应用图标
- 窗口标题
- 最小化按钮
- 最大化/还原按钮
- 关闭按钮

**样式定制**:

```css
/* title_bar.qss */
QWidget#TitleBar {
    background-color: #2d333a;
    height: 40px;
}

QPushButton#MinimizeButton {
    /* 最小化按钮样式 */
}

QPushButton#MaximizeButton {
    /* 最大化按钮样式 */
}

QPushButton#CloseButton {
    background-color: #E81123;  /* 红色关闭按钮 */
}
```

---

### 4. `settings_widget.py` - 设置界面

全局应用设置界面，包含主题、语言、AI 配置等。

**功能**:
- 主题切换（深色/浅色）
- 语言设置
- AI 助手配置
  - LLM 提供商选择（Ollama / API）
  - 模型选择
  - API Key 配置
- 窗口设置
- 日志设置

**配置项**:

| 分类 | 配置项 | 说明 |
|------|--------|------|
| 外观 | 主题 | 深色/浅色主题 |
| 外观 | 自定义主题 | 加载自定义主题文件 |
| 语言 | 界面语言 | 中文/英文 |
| AI | LLM 提供商 | Ollama / API |
| AI | Ollama 模型 | 模型选择（自动扫描） |
| AI | API 地址 | API 服务地址 |
| AI | API Key | API 密钥 |
| AI | 模型名称 | API 模型名称 |
| 窗口 | 启动大小 | 窗口初始大小 |
| 窗口 | 启动位置 | 窗口初始位置 |
| 日志 | 日志级别 | DEBUG/INFO/WARNING/ERROR |

**自动保存**:
设置修改后自动保存，使用防抖机制（500ms 延迟）。

---

### 5. `system_tray_manager.py` - 系统托盘管理

管理系统托盘图标和菜单。

**功能**:
- 显示托盘图标
- 托盘菜单
- 最小化到托盘
- 从托盘恢复
- 退出应用

**托盘菜单**:
- 🏠 显示主窗口
- ⚙️ 设置
- 📖 帮助
- 🚪 退出

**使用示例**:

```python
from ui.system_tray_manager import SystemTrayManager

# 创建托盘管理器
tray = SystemTrayManager(main_window)

# 显示托盘图标
tray.show()

# 托盘图标点击
tray.activated.connect(handle_tray_activated)
```

---

## 📂 对话框组件

### `close_confirmation_dialog.py` - 关闭确认对话框

关闭应用时的确认对话框。

**功能**:
- 确认关闭操作
- 最小化到托盘选项
- 记住选择

**对话框选项**:
- ✅ 确认退出
- ❌ 取消
- 📌 最小化到托盘
- ☑️ 不再提示

**使用示例**:

```python
from ui.dialogs.close_confirmation_dialog import CloseConfirmationDialog

dialog = CloseConfirmationDialog(parent)
result = dialog.exec()

if result == QDialog.DialogCode.Accepted:
    # 用户确认关闭
    ...
```

---

## 🔄 主窗口处理器

### 1. `module_loader.py` - 模块加载器

负责动态加载和卸载模块 UI。

**功能**:
- 懒加载模块 UI
- 模块 UI 缓存
- 模块切换动画
- 模块 UI 生命周期管理

**核心方法**:

```python
class ModuleLoader:
    def load_module_ui(self, module_name):
        """加载模块 UI"""
        
    def unload_module_ui(self, module_name):
        """卸载模块 UI"""
        
    def get_cached_ui(self, module_name):
        """获取缓存的 UI"""
```

---

### 2. `navigation_handler.py` - 导航处理器

处理侧边栏导航和模块切换。

**功能**:
- 侧边栏按钮管理
- 模块切换逻辑
- 导航历史记录
- 快捷键支持

**导航方式**:
1. 侧边栏点击
2. 快捷键（Ctrl+1, Ctrl+2, ...）
3. 程序化调用

**核心方法**:

```python
class NavigationHandler:
    def navigate_to(self, module_name):
        """导航到模块"""
        
    def go_back(self):
        """返回上一个模块"""
        
    def get_current_module(self):
        """获取当前模块"""
```

---

## 🎨 UI 开发规范

### 布局规范

- **主窗口布局**: QVBoxLayout + QHBoxLayout
- **组件对齐**: 使用 Qt 对齐常量
- **间距**: 统一使用 8px/16px/24px
- **边距**: 统一使用 16px

### 样式规范

- **使用 QSS**: 避免在代码中硬编码样式
- **对象名**: 使用驼峰命名（如 `MainWindow`）
- **主题支持**: 确保深色/浅色主题兼容

### 信号槽规范

- **命名**: 信号使用过去式（如 `clicked`）
- **槽函数**: 使用 `on_` 前缀（如 `on_button_clicked`）
- **连接**: 使用新式信号槽连接

```python
# 新式信号槽连接（推荐）
button.clicked.connect(self.on_button_clicked)

# 旧式连接（不推荐）
# self.connect(button, SIGNAL('clicked()'), self.on_button_clicked)
```

### 线程安全

- **UI 更新**: 仅在主线程更新 UI
- **工作线程**: 使用 `QThread` 处理耗时操作
- **信号槽**: 跨线程通信使用信号槽

```python
from PyQt6.QtCore import QThread, pyqtSignal

class WorkerThread(QThread):
    finished = pyqtSignal(object)
    
    def run(self):
        result = do_heavy_work()
        self.finished.emit(result)

# 使用
thread = WorkerThread()
thread.finished.connect(self.on_work_finished)
thread.start()
```

## 🚀 使用示例

### 创建自定义对话框

```python
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton

class CustomDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("自定义对话框")
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 添加控件
        button = QPushButton("确定")
        button.clicked.connect(self.accept)
        
        layout.addWidget(button)
```

### 添加状态栏消息

```python
from ui.ue_main_window import UEMainWindow

# 在主窗口中
self.statusBar().showMessage("操作成功", 3000)  # 显示 3 秒
```

### 显示托盘通知

```python
from ui.system_tray_manager import SystemTrayManager

# 显示通知
tray.showMessage(
    "标题",
    "消息内容",
    QSystemTrayIcon.MessageIcon.Information,
    3000  # 显示时长（毫秒）
)
```

## ⚠️ 注意事项

- **内存泄漏**: 及时清理不再使用的 UI 组件
- **事件循环**: 避免阻塞主线程事件循环
- **响应式**: UI 应适配不同屏幕尺寸
- **性能**: 避免频繁的 UI 更新
- **测试**: 在不同操作系统上测试 UI

## 🔗 相关文档

- [PyQt6 官方文档](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [Qt 官方文档](https://doc.qt.io/)
- [UI 设计指南](../docs/ui_design_guidelines.md)
- [主题开发指南](../resources/README.md)

