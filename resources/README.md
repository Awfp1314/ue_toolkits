# Resources 资源文件

本目录包含应用程序的静态资源文件，包括样式表、主题、模板和图标等。

## 📁 目录结构

```
resources/
├── qss/                      # QSS 样式表
│   ├── components/           # 组件样式
│   ├── themes/               # 主题样式
│   └── variables.qss         # 样式变量
├── templates/                # 配置模板
│   └── global_settings.json  # 全局设置模板
├── themes/                   # 主题配置
│   ├── example_custom_theme.json  # 示例自定义主题
│   ├── forest_green.json     # 森林绿主题
│   ├── sunset_orange.json    # 日落橙主题
│   └── violet.json           # 紫罗兰主题
└── tubiao.ico                # 应用图标
```

## 🎨 QSS 样式表

### 组件样式 (`qss/components/`)

组件化的样式文件，每个组件对应一个 QSS 文件：

- **`buttons.qss`** - 按钮样式
  - 普通按钮
  - 主按钮 (Primary)
  - 危险按钮 (Danger)
  - 文本按钮 (Text)

- **`chat_input.qss`** - 聊天输入框样式
  - 输入区域样式
  - 发送按钮样式

- **`chatgpt_composer.qss`** - ChatGPT 风格输入框
  - 胶囊容器样式
  - 焦点状态
  - 阴影效果

- **`config_tool.qss`** - 配置工具样式
  - 配置编辑器样式
  - 参数输入样式

- **`confirmation_dialog.qss`** - 确认对话框样式
  - 对话框布局
  - 按钮组样式

- **`dialogs.qss`** - 通用对话框样式
  - 模态对话框
  - 消息框

- **`main_window.qss`** - 主窗口样式
  - 窗口背景
  - 布局样式

- **`markdown_message.qss`** - Markdown 消息样式
  - 消息气泡
  - Markdown 渲染样式

- **`scrollbars.qss`** - 滚动条样式
  - 垂直滚动条
  - 水平滚动条
  - 滚动条手柄

- **`title_bar.qss`** - 标题栏样式
  - 自定义标题栏
  - 窗口控制按钮

### 主题样式 (`qss/themes/`)

全局主题样式文件：

- **`dark.qss`** - 深色主题
  - 背景色: #212121
  - 文本色: #EDEDED
  - 强调色: 蓝色系

- **`light.qss`** - 浅色主题
  - 背景色: #FFFFFF
  - 文本色: #2d333a
  - 强调色: 蓝色系

### 样式变量 (`variables.qss`)

定义全局样式变量（CSS 变量风格）：

```css
/* 颜色变量 */
--primary-color: #3390FF;
--danger-color: #FF4D4F;
--success-color: #52C41A;
--warning-color: #FAAD14;

/* 间距变量 */
--spacing-xs: 4px;
--spacing-sm: 8px;
--spacing-md: 16px;
--spacing-lg: 24px;

/* 圆角变量 */
--border-radius-sm: 4px;
--border-radius-md: 8px;
--border-radius-lg: 12px;
```

## 🌈 主题配置 (`themes/`)

### 主题文件格式

```json
{
    "name": "主题名称",
    "description": "主题描述",
    "colors": {
        "primary": "#3390FF",
        "background": "#212121",
        "text": "#EDEDED",
        "accent": "#8E8EA0"
    },
    "styles": {
        "font_family": "Microsoft YaHei UI",
        "font_size": "14px",
        "border_radius": "8px"
    }
}
```

### 内置主题

1. **森林绿 (forest_green.json)**
   - 主色: 绿色系
   - 适合长时间使用，护眼

2. **日落橙 (sunset_orange.json)**
   - 主色: 橙色系
   - 温暖、活力

3. **紫罗兰 (violet.json)**
   - 主色: 紫色系
   - 优雅、神秘

## 📋 配置模板 (`templates/`)

### 全局设置模板 (`global_settings.json`)

```json
{
    "app": {
        "theme": "dark",
        "language": "zh_CN",
        "auto_save": true
    },
    "ui": {
        "window_size": [1280, 720],
        "window_position": [100, 100],
        "sidebar_width": 200
    }
}
```

## 🖼️ 图标 (`tubiao.ico`)

应用程序图标，支持多尺寸：
- 16x16
- 32x32
- 48x48
- 256x256

## 🚀 使用指南

### 加载样式

```python
from core.utils.style_loader import StyleLoader

# 加载主题样式
StyleLoader.load_theme("dark")

# 加载组件样式
StyleLoader.load_component("buttons")

# 加载自定义 QSS
style = StyleLoader.load_qss("path/to/style.qss")
widget.setStyleSheet(style)
```

### 切换主题

```python
from core.utils.theme_manager import ThemeManager

# 获取主题管理器
theme_manager = ThemeManager.instance()

# 切换主题
theme_manager.set_theme("light")  # 或 "dark"

# 加载自定义主题
theme_manager.load_custom_theme("path/to/theme.json")
```

### 使用主题配置

```python
from core.utils.theme_manager import ThemeManager

theme_manager = ThemeManager.instance()

# 获取主题配置
theme_config = theme_manager.get_theme_config()

# 使用主题颜色
primary_color = theme_config["colors"]["primary"]
background_color = theme_config["colors"]["background"]
```

## 🎨 自定义样式

### 创建自定义组件样式

1. 在 `qss/components/` 目录下创建新的 `.qss` 文件
2. 编写样式规则
3. 使用 `StyleLoader` 加载

示例 (`custom_button.qss`):

```css
QPushButton#CustomButton {
    background-color: #3390FF;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 14px;
}

QPushButton#CustomButton:hover {
    background-color: #5CA6FF;
}

QPushButton#CustomButton:pressed {
    background-color: #2E7FDB;
}
```

### 创建自定义主题

1. 复制 `example_custom_theme.json`
2. 修改颜色和样式配置
3. 使用 `ThemeManager.load_custom_theme()` 加载

示例 (`my_theme.json`):

```json
{
    "name": "我的主题",
    "description": "自定义主题",
    "colors": {
        "primary": "#FF6B6B",
        "background": "#1A1A2E",
        "text": "#E0E0E0",
        "accent": "#16213E"
    },
    "styles": {
        "font_family": "Arial",
        "font_size": "14px",
        "border_radius": "6px"
    }
}
```

## 📝 样式开发规范

### QSS 命名规范

- **类名**: 使用 `QWidgetName` (Qt 标准类名)
- **对象名**: 使用 `#ObjectName` (驼峰命名)
- **状态**: 使用 `:state` (如 `:hover`, `:pressed`)

### 样式组织

- **模块化**: 每个组件一个文件
- **复用性**: 定义可复用的样式类
- **一致性**: 保持颜色、间距一致

### 注释规范

```css
/* ==================== 按钮样式 ==================== */

/* 主按钮 */
QPushButton#PrimaryButton {
    /* 样式规则 */
}

/* 危险按钮 */
QPushButton#DangerButton {
    /* 样式规则 */
}
```

## ⚠️ 注意事项

- **路径**: 使用相对路径引用资源
- **编码**: QSS 文件使用 UTF-8 编码
- **性能**: 避免过度嵌套的样式规则
- **兼容性**: 测试不同操作系统下的样式表现
- **版本控制**: 重要样式修改需要版本说明

## 🔗 相关文档

- [Qt QSS 参考](https://doc.qt.io/qt-6/stylesheet-reference.html)
- [主题开发指南](../docs/theme_development.md)
- [样式最佳实践](../docs/styling_best_practices.md)

