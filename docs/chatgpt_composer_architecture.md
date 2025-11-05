# ChatGPTComposer 样式架构设计

## 🎯 设计目标

1. ✅ **使用外部 QSS 文件**管理样式（便于主题切换）
2. ✅ **只作用于组件实例本身**，不走 `app.setStyleSheet()` 的全局通道
3. ✅ **避免 ThemeManager 覆盖**组件样式
4. ✅ **自动响应主题切换**

---

## 🏗️ 架构设计

### 样式加载流程

```
组件初始化
    ↓
_get_current_theme() → 获取当前主题 (dark/light)
    ↓
_load_qss_from_file(theme) → 加载外部 QSS 文件
    ↓
├─ 成功 → self.setStyleSheet(qss_content)
└─ 失败 → self.setStyleSheet(_get_fallback_qss(theme))
    ↓
刷新所有子组件样式
```

### 文件结构

```
modules/ai_assistant/
├── ui/
│   └── chat_composer.py          # 组件实现
└── resources/
    └── themes/
        ├── chatgpt_composer_dark.qss   # 深色主题
        └── chatgpt_composer_light.qss  # 浅色主题
```

---

## 🔑 核心方法

### 1. `_load_qss_from_file(theme: str) -> str`

**功能：**从外部文件加载 QSS 样式

**查找优先级：**
```python
1. modules/ai_assistant/resources/themes/chatgpt_composer_{theme}.qss
2. modules/ai_assistant/resources/themes/chatgpt_composer_dark.qss  # 回退
3. resources/qss/components/chatgpt_composer.qss                     # 全局回退
```

**示例：**
```python
qss = self._load_qss_from_file("dark")  # 加载深色主题
```

---

### 2. `_get_current_theme() -> str`

**功能：**获取当前全局主题名称

**实现：**
```python
from core.utils.theme_manager import get_theme_manager
theme_manager = get_theme_manager()
theme = theme_manager.current_theme.value  # 'dark' 或 'light'
```

---

### 3. `_get_fallback_qss(theme: str) -> str`

**功能：**提供兜底的内联样式（当外部文件加载失败时使用）

**支持主题：**
- `dark`：深色主题（ChatGPT 深色模式配色）
- `light`：浅色主题（ChatGPT 浅色模式配色）

---

### 4. `_force_style_refresh()`

**功能：**强制刷新组件样式

**执行时机：**
- 组件初始化时（通过 `QTimer.singleShot(0, ...)`）
- 主题切换时（通过 `refresh_theme()` 调用）

**流程：**
```python
theme = self._get_current_theme()
qss = self._load_qss_from_file(theme)
if qss:
    self.setStyleSheet(qss)  # 使用外部 QSS
else:
    self.setStyleSheet(self._get_fallback_qss(theme))  # 兜底
```

---

### 5. `refresh_theme(theme: str = None)`

**功能：**响应主题切换（可被外部调用）

**参数：**
- `theme`：主题名称，`None` 时自动检测

**示例：**
```python
# 自动检测主题
composer.refresh_theme()

# 指定主题
composer.refresh_theme("light")
```

---

## 🔄 主题切换流程

### 1. 用户切换主题

```
用户在设置中切换主题
    ↓
ThemeManager.set_theme(Theme.LIGHT)
    ↓
主窗口调用 module.refresh_theme()
    ↓
ChatWindow.refresh_theme()
    ↓
self.input_area.refresh_theme()  ← 关键！
    ↓
ChatGPTComposer._force_style_refresh()
    ↓
重新加载外部 QSS（light 主题）
    ↓
组件样式更新完成 ✅
```

### 2. 代码实现

**ChatWindow.refresh_theme()：**
```python
def refresh_theme(self):
    """刷新主题（响应主题切换）"""
    try:
        from core.utils.theme_manager import get_theme_manager, Theme
        theme_manager = get_theme_manager()
        current_theme = theme_manager.get_theme()
        
        # 根据主题管理器的主题切换
        if current_theme == Theme.LIGHT:
            self.current_theme = "light"
        else:
            self.current_theme = "dark"
        
        # 加载主题样式
        self.load_theme(self.current_theme)
        
        # 刷新输入框主题（关键！）
        if hasattr(self, 'input_area') and hasattr(self.input_area, 'refresh_theme'):
            self.input_area.refresh_theme()  # ← 调用组件的 refresh_theme()
            
    except Exception as e:
        print(f"[ERROR] 刷新AI助手主题失败: {e}")
```

---

## 🎨 主题样式对比

### Dark Theme（深色主题）

| 元素 | 颜色/样式 |
|------|----------|
| 胶囊背景 | `#40414F` |
| 胶囊边框 | `#565869` |
| 文本颜色 | `#ECECF1` |
| 发送按钮 | `#b23565`（粉色） |
| 按钮悬停 | `rgba(255, 255, 255, 0.08)` |

### Light Theme（浅色主题）

| 元素 | 颜色/样式 |
|------|----------|
| 胶囊背景 | `#ffffff` |
| 胶囊边框 | `#d1d5db` |
| 文本颜色 | `#111827` |
| 发送按钮 | `#10a37f`（绿色，ChatGPT 风格） |
| 按钮悬停 | `rgba(0, 0, 0, 0.05)` |

---

## ✅ 优势

| 特性 | 说明 |
|------|------|
| ✅ **组件独立** | 不依赖全局 `app.setStyleSheet()`，避免被覆盖 |
| ✅ **主题支持** | 支持 dark/light 两套主题，自动切换 |
| ✅ **外部管理** | QSS 文件独立，便于修改和维护 |
| ✅ **兜底保护** | 外部文件加载失败时使用内联样式兜底 |
| ✅ **自动刷新** | 主题切换时自动重新加载样式 |
| ✅ **零侵入** | 不修改 ThemeManager 或全局样式系统 |

---

## 🔍 调试

### 查看加载的 QSS 文件

**控制台输出：**
```
[ChatGPTComposer] Loaded QSS from: chatgpt_composer_dark.qss
[ChatGPTComposer] Applied external QSS (theme: dark)
```

**主题切换时：**
```
[ChatGPTComposer] Theme refresh requested (theme: auto)
[ChatGPTComposer] Loaded QSS from: chatgpt_composer_light.qss
[ChatGPTComposer] Applied external QSS (theme: light)
```

### 如果 QSS 加载失败

**控制台输出：**
```
[ChatGPTComposer] QSS file not found: chatgpt_composer_xxx.qss
[ChatGPTComposer] Using fallback inline styles (theme: dark)
```

---

## 📦 如何添加新主题

### 1. 创建新的 QSS 文件

```bash
modules/ai_assistant/resources/themes/chatgpt_composer_custom.qss
```

### 2. 修改主题检测逻辑

如果需要支持自定义主题，修改 `_get_current_theme()` 方法：

```python
def _get_current_theme(self) -> str:
    try:
        from core.utils.theme_manager import get_theme_manager, Theme
        theme_manager = get_theme_manager()
        
        if theme_manager.current_theme == Theme.CUSTOM:
            # 自定义主题，可以根据 custom_theme_name 返回不同的值
            return "custom"  # 对应 chatgpt_composer_custom.qss
        elif theme_manager.current_theme == Theme.LIGHT:
            return "light"
        else:
            return "dark"
    except Exception as e:
        return "dark"
```

### 3. 创建对应的兜底样式

在 `_get_fallback_qss()` 中添加新主题的兜底样式：

```python
def _get_fallback_qss(self, theme: str = "dark") -> str:
    if theme == "custom":
        return """
        QFrame#ComposerShell {
            background-color: #yourcolor;
            ...
        }
        """
    elif theme == "light":
        ...
    else:
        ...
```

---

## 🎯 总结

这个架构设计实现了：

1. **外部 QSS 管理**：样式文件独立，便于维护
2. **组件级样式**：通过 `self.setStyleSheet()` 直接作用于组件
3. **避免覆盖**：不依赖全局样式，不受 ThemeManager 影响
4. **自动刷新**：主题切换时自动重新加载外部 QSS
5. **兜底保护**：加载失败时使用内联样式确保可用

**关键实现：**
- 组件自己管理样式加载
- 通过 `refresh_theme()` 响应主题切换
- 支持多主题（dark/light/custom）
- 完全独立于全局样式系统

**🎉 这是一个解耦、可维护、可扩展的样式架构！**

