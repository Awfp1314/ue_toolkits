# 📦 Resources - 资源文件

> 应用的样式、主题、图标等资源文件

---

## 概述

Resources 目录包含所有非代码资源文件，包括 QSS 样式表、主题配置、图标等。

---

## 文件结构

```
resources/
├── qss/                            # QSS 样式表
│   ├── main_window.qss             # 主窗口样式
│   ├── sidebar.qss                 # 侧边栏样式
│   ├── config_tool.qss             # 配置工具样式
│   ├── variables.qss               # 变量定义 ⭐
│   │
│   ├── components/                 # 组件样式
│   │   ├── buttons.qss             # 按钮
│   │   ├── dialogs.qss             # 对话框
│   │   ├── scrollbars.qss          # 滚动条
│   │   └── title_bar.qss           # 标题栏
│   │
│   └── themes/                     # 主题变体
│       ├── dark.qss                # 深色主题
│       └── light.qss               # 浅色主题
│
├── themes/                         # 自定义主题配置
│   ├── README.md                   # 主题说明
│   ├── example_custom_theme.json   # 示例主题
│   ├── forest_green.json           # 森林绿主题
│   ├── sunset_orange.json          # 日落橙主题
│   └── violet.json                 # 紫罗兰主题
│
├── templates/                      # 配置模板
│   └── global_settings.json        # 全局设置模板
│
└── tubiao.ico                      # 应用图标
```

---

## QSS 样式系统

### 样式组织

```
qss/
├── variables.qss          # 变量定义（颜色、字体等）
├── main_window.qss        # 主窗口
├── sidebar.qss            # 侧边栏
├── components/            # 可复用组件
└── themes/                # 主题变体
```

### variables.qss - 变量定义

**位置**: `qss/variables.qss`

**内容示例**:
```css
/* 颜色变量 */
:root {
    --primary-color: #2196F3;
    --secondary-color: #FFC107;
    --background-color: #1E1E1E;
    --text-color: #FFFFFF;
    --border-color: #3E3E3E;
}

/* 字体 */
* {
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 14px;
}
```

### 使用样式变量

```css
/* 在其他 QSS 文件中引用变量 */
QPushButton {
    background-color: var(--primary-color);
    color: var(--text-color);
    border: 1px solid var(--border-color);
}
```

---

## 主题系统

### 主题配置格式

**位置**: `themes/*.json`

**格式**:
```json
{
  "name": "Forest Green",
  "display_name": "森林绿",
  "author": "UE Toolkit Team",
  "version": "1.0.0",
  "colors": {
    "primary": "#4CAF50",
    "secondary": "#8BC34A",
    "background": "#1B5E20",
    "surface": "#2E7D32",
    "text": "#FFFFFF",
    "text_secondary": "#C8E6C9",
    "border": "#388E3C",
    "accent": "#CDDC39"
  },
  "fonts": {
    "family": "Microsoft YaHei",
    "size": 14,
    "bold_size": 16
  },
  "spacing": {
    "padding": 8,
    "margin": 4,
    "border_radius": 4
  }
}
```

### 内置主题

| 主题 | 文件 | 说明 |
|------|------|------|
| 深色 | `dark.qss` | 默认深色主题 |
| 浅色 | `light.qss` | 浅色主题 |
| 森林绿 | `forest_green.json` | 绿色主题 |
| 日落橙 | `sunset_orange.json` | 橙色主题 |
| 紫罗兰 | `violet.json` | 紫色主题 |

### 创建自定义主题

1. **复制示例主题**
   ```bash
   cp resources/themes/example_custom_theme.json my_theme.json
   ```

2. **修改颜色配置**
   ```json
   {
     "name": "my_theme",
     "display_name": "我的主题",
     "colors": {
       "primary": "#YOUR_COLOR",
       ...
     }
   }
   ```

3. **在应用中使用**
   ```python
   theme_mgr.load_theme("my_theme")
   ```

---

## 样式开发指南

### 编写 QSS 样式

**推荐结构**:
```css
/* 1. 重置默认样式 */
* {
    margin: 0;
    padding: 0;
    border: none;
}

/* 2. 通用样式 */
QWidget {
    background-color: var(--background-color);
    color: var(--text-color);
}

/* 3. 组件样式 */
QPushButton {
    /* 按钮样式 */
}

/* 4. 状态样式 */
QPushButton:hover {
    /* 悬停状态 */
}

QPushButton:pressed {
    /* 按下状态 */
}
```

### 选择器优先级

```css
/* 低优先级 - 类型选择器 */
QPushButton { }

/* 中优先级 - 类选择器 */
.custom-button { }

/* 高优先级 - ID 选择器 */
#specific-button { }

/* 最高优先级 - 内联样式 */
/* widget.setStyleSheet("...") */
```

### 样式组合

```css
/* 多个选择器 */
QPushButton, QToolButton {
    background-color: #2196F3;
}

/* 后代选择器 */
QWidget QPushButton {
    margin: 4px;
}

/* 子选择器 */
QWidget > QPushButton {
    margin: 8px;
}
```

---

## 组件样式示例

### 按钮样式

**文件**: `qss/components/buttons.qss`

```css
QPushButton {
    background-color: var(--primary-color);
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    min-height: 32px;
}

QPushButton:hover {
    background-color: #1976D2;
}

QPushButton:pressed {
    background-color: #0D47A1;
}

QPushButton:disabled {
    background-color: #BDBDBD;
    color: #9E9E9E;
}
```

### 滚动条样式

**文件**: `qss/components/scrollbars.qss`

```css
QScrollBar:vertical {
    background: transparent;
    width: 12px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: var(--border-color);
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: var(--primary-color);
}
```

---

## 图标管理

### 应用图标

**文件**: `tubiao.ico`

**用途**:
- 窗口图标
- 托盘图标
- 可执行文件图标

**规格**: 256x256, ICO 格式

### 模块图标

每个模块可以在自己的目录中提供图标：
```
modules/my_module/
└── resources/
    └── icons/
        └── module_icon.png
```

---

## 配置模板

### global_settings.json

**位置**: `templates/global_settings.json`

**内容**:
```json
{
  "app": {
    "language": "zh_CN",
    "theme": "dark",
    "auto_start": false
  },
  "window": {
    "width": 1280,
    "height": 720,
    "remember_position": true
  },
  "modules": {
    "auto_load": true,
    "enabled_modules": []
  }
}
```

---

## 样式加载

### 方式 1: 加载单个文件

```python
from core.utils.style_loader import StyleLoader

loader = StyleLoader()
stylesheet = loader.load("main_window.qss")
widget.setStyleSheet(stylesheet)
```

### 方式 2: 加载多个文件

```python
stylesheets = [
    "main_window.qss",
    "components/buttons.qss",
    "components/dialogs.qss"
]

combined = loader.load_multiple(stylesheets)
app.setStyleSheet(combined)
```

### 方式 3: 加载主题

```python
from core.utils.theme_manager import ThemeManager

theme_mgr = ThemeManager()
theme_mgr.load_theme("dark")
theme_mgr.apply_theme(app)
```

---

## 最佳实践

### 1. 样式组织

- ✅ 使用变量定义颜色
- ✅ 按组件分文件
- ✅ 复用样式规则
- ✅ 添加注释说明

### 2. 主题开发

- ✅ 保持颜色一致性
- ✅ 测试深色和浅色模式
- ✅ 考虑可访问性
- ✅ 提供预览

### 3. 资源管理

- ✅ 使用合适的文件格式
- ✅ 优化图标大小
- ✅ 避免资源冗余

---

## 调试技巧

### 实时预览样式

```python
# 在开发时实时加载样式
def reload_styles():
    loader = StyleLoader()
    stylesheet = loader.load("main_window.qss")
    app.setStyleSheet(stylesheet)

# 绑定到快捷键
shortcut = QShortcut(QKeySequence("F5"), main_window)
shortcut.activated.connect(reload_styles)
```

### 检查样式应用

```python
# 打印当前样式
print(widget.styleSheet())

# 检查有效样式
print(widget.style())
```

---

## 性能优化

### 1. 减少样式重复

```css
/* 不好 - 重复定义 */
QPushButton { color: white; }
QToolButton { color: white; }
QComboBox { color: white; }

/* 好 - 使用组合选择器 */
QPushButton, QToolButton, QComboBox {
    color: white;
}
```

### 2. 使用变量

```css
/* 不好 - 硬编码 */
QPushButton { background-color: #2196F3; }
QLabel { color: #2196F3; }

/* 好 - 使用变量 */
QPushButton { background-color: var(--primary-color); }
QLabel { color: var(--primary-color); }
```

---

## 资源打包

### PyInstaller 配置

在 `ue_toolkit.spec` 中包含资源：

```python
datas = [
    ('resources/qss', 'resources/qss'),
    ('resources/themes', 'resources/themes'),
    ('resources/tubiao.ico', 'resources'),
]
```

---

**维护者**: Resources Team  
**最后更新**: 2025-11-04

