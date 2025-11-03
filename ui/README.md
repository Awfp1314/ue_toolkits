# 🎨 UI - 主界面系统

> UE Toolkit 的用户界面框架和组件

---

## 概述

UI 层负责应用的主窗口框架、通用组件和界面交互。

### 核心职责

- ✅ 主窗口管理
- ✅ 模块内容区显示
- ✅ 侧边栏导航
- ✅ 设置界面
- ✅ 系统托盘
- ✅ 主题切换

---

## 文件结构

```
ui/
├── ue_main_window.py               # 主窗口 ⭐
├── ue_main_window_core.py          # 主窗口核心
├── settings_widget.py              # 设置界面
├── system_tray_manager.py          # 系统托盘
│
├── dialogs/                        # 对话框
│   └── close_confirmation_dialog.py
│
├── main_window_components/         # 主窗口组件
│   └── title_bar.py                # 自定义标题栏
│
├── main_window_handlers/           # 事件处理
│   ├── module_loader.py            # 模块加载
│   └── navigation_handler.py       # 导航处理
│
└── icons/                          # 图标资源
    └── toolbar.png
```

---

## 核心组件

### 1. UEMainWindow - 主窗口

**文件**: `ue_main_window.py`

**布局结构**:
```
┌──────────────────────────────────────────┐
│  自定义标题栏（拖拽/最小化/最大化/关闭）  │
├──────────┬───────────────────────────────┤
│          │                               │
│  侧边栏  │        模块内容区             │
│  导航    │      (动态加载模块 UI)        │
│          │                               │
│  [图标]  │                               │
│  模块1   │                               │
│  模块2   │                               │
│  模块3   │                               │
│  ...     │                               │
│  设置    │                               │
│          │                               │
└──────────┴───────────────────────────────┘
```

**特点**:
- 无边框窗口设计
- 自定义标题栏
- 响应式布局
- 主题支持

---

### 2. 侧边栏导航

**功能**:
- 模块列表显示
- 模块切换
- 图标 + 文字
- 选中状态高亮

**使用示例**:
```python
# 添加模块到侧边栏
sidebar.add_module_button(
    name="ai_assistant",
    display_name="AI 助手",
    icon=module_icon
)
```

---

### 3. 设置界面

**文件**: `settings_widget.py`

**设置项**:
- 主题切换（深色/浅色/自定义）
- 语言设置
- 启动选项
- 模块管理
- 关于信息

---

### 4. 自定义标题栏

**文件**: `main_window_components/title_bar.py`

**功能**:
- 窗口拖拽
- 最小化按钮
- 最大化/还原按钮
- 关闭按钮
- 窗口标题

**实现**:
```python
class TitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.dragging = False
        self.init_ui()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.parent.pos()
    
    def mouseMoveEvent(self, event):
        if self.dragging:
            self.parent.move(event.globalPosition().toPoint() - self.drag_position)
```

---

### 5. 系统托盘

**文件**: `system_tray_manager.py`

**功能**:
- 托盘图标
- 右键菜单
- 最小化到托盘
- 快速操作
- 消息通知

**使用示例**:
```python
tray = SystemTrayManager(main_window)
tray.show()
tray.show_message("标题", "消息内容")
```

---

## 模块加载

### ModuleLoader

**文件**: `main_window_handlers/module_loader.py`

**职责**:
- 动态加载模块 UI
- 管理模块生命周期
- 处理模块切换

**加载流程**:
```
用户点击侧边栏
    ↓
NavigationHandler 处理导航
    ↓
ModuleLoader 加载模块
    ↓
获取模块 widget
    ↓
显示在内容区
```

---

## 主题系统

### 主题切换

```python
from core.utils.theme_manager import ThemeManager

# 切换主题
theme_mgr = ThemeManager()
theme_mgr.load_theme("dark")  # dark / light / custom
theme_mgr.apply_theme(app)
```

### 自定义主题

在 `resources/themes/` 中创建 JSON 配置文件。

---

## 样式管理

### QSS 样式

主窗口相关样式位于:
- `resources/qss/main_window.qss`
- `resources/qss/sidebar.qss`
- `resources/qss/components/title_bar.qss`

### 加载样式

```python
from core.utils.style_loader import StyleLoader

loader = StyleLoader()
stylesheet = loader.load("main_window.qss")
window.setStyleSheet(stylesheet)
```

---

## 事件处理

### NavigationHandler

**文件**: `main_window_handlers/navigation_handler.py`

**职责**:
- 处理侧边栏导航
- 模块切换动画
- 历史记录管理

**使用示例**:
```python
nav_handler = NavigationHandler(main_window)
nav_handler.navigate_to_module("ai_assistant")
```

---

## 对话框

### CloseConfirmationDialog

**文件**: `dialogs/close_confirmation_dialog.py`

**功能**:
- 关闭确认
- 最小化到托盘选项
- 记住选择

---

## 响应式设计

### 窗口大小适配

```python
def resizeEvent(self, event):
    # 根据窗口大小调整布局
    if self.width() < 800:
        self.sidebar.hide()  # 小窗口隐藏侧边栏
    else:
        self.sidebar.show()
```

### 最小窗口尺寸

```python
self.setMinimumSize(1024, 768)  # 最小尺寸
```

---

## 最佳实践

### 1. 界面响应

- ✅ 使用多线程处理耗时操作
- ✅ 显示进度提示
- ✅ 避免阻塞 UI 线程

### 2. 用户体验

- ✅ 提供快捷键
- ✅ 记住窗口位置和大小
- ✅ 平滑的动画过渡

### 3. 样式一致性

- ✅ 使用统一的颜色变量
- ✅ 遵循设计规范
- ✅ 支持多主题

---

## API 参考

### UEMainWindow

| 方法 | 说明 |
|------|------|
| `show_module(name)` | 显示指定模块 |
| `hide_module()` | 隐藏当前模块 |
| `toggle_sidebar()` | 切换侧边栏显示 |
| `show_settings()` | 显示设置界面 |

### SystemTrayManager

| 方法 | 说明 |
|------|------|
| `show()` | 显示托盘图标 |
| `hide()` | 隐藏托盘图标 |
| `show_message(title, msg)` | 显示通知 |

---

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+1~9` | 切换到模块 1-9 |
| `Ctrl+,` | 打开设置 |
| `Ctrl+Q` | 退出程序 |
| `F11` | 全屏切换 |

---

## 扩展点

### 添加自定义组件

```python
# 在主窗口中添加自定义组件
custom_widget = MyCustomWidget()
main_window.add_to_toolbar(custom_widget)
```

### 自定义标题栏按钮

```python
title_bar.add_button(
    icon="custom_icon.png",
    callback=self.on_custom_action
)
```

---

**维护者**: UI Team  
**最后更新**: 2025-11-04

