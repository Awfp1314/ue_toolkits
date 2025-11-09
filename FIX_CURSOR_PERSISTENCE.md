# 🔧 修复光标样式持久性问题

## 问题描述

用户报告：光标悬停效果在初始时正常，但后续会出现状态切换错误，光标放在文本上没有变化。

---

## 根本原因分析

### 问题根源

1. **QTextBrowser 的 viewport 光标**

   - `CursorStyleManager.set_bubble_cursor()` 设置的是 `bubble.setCursor()`
   - 但 `QTextBrowser` 需要设置 `bubble.viewport().setCursor()`
   - 两者不同，导致光标样式未正确应用

2. **setHtml() 重置光标样式**

   - 每次调用 `markdown_browser.setHtml()` 时，可能会重置 viewport 的光标样式
   - 流式输出时频繁调用 `setHtml()`，导致光标样式丢失
   - 主题切换时也会调用 `setHtml()`，同样会重置光标

3. **主题切换重置样式**
   - `load_theme()` 方法会重新设置整个窗口的样式表
   - 可能覆盖之前设置的光标样式

---

## 修复方案

### 修复 1：正确设置 QTextBrowser 的光标

#### 修改文件：`cursor_style_manager.py`

**修改 `set_bubble_cursor` 方法**：

```python
@staticmethod
def set_bubble_cursor(bubble):
    """
    为聊天气泡设置光标样式

    Args:
        bubble: 聊天气泡组件（QTextBrowser 或 QLabel）
    """
    try:
        from PyQt6.QtWidgets import QTextBrowser, QLabel

        if isinstance(bubble, QTextBrowser):
            # QTextBrowser 需要设置 viewport 的光标
            bubble.viewport().setCursor(Qt.CursorShape.IBeamCursor)
            print(f"[CursorStyleManager] 已设置 QTextBrowser viewport 光标为 IBeam")
        elif isinstance(bubble, QLabel):
            # QLabel 直接设置光标
            bubble.setCursor(Qt.CursorShape.IBeamCursor)
            print(f"[CursorStyleManager] 已设置 QLabel 光标为 IBeam")
        else:
            # 其他类型，尝试直接设置
            bubble.setCursor(Qt.CursorShape.IBeamCursor)
            print(f"[CursorStyleManager] 已设置 {type(bubble).__name__} 光标为 IBeam")
    except Exception as e:
        print(f"[CursorStyleManager] 设置气泡光标失败: {e}")
```

---

### 修复 2：在 setHtml() 后重新设置光标

#### 修改文件：`markdown_message.py`

**修改 `MarkdownMessage.append_text` 方法**：

```python
def append_text(self, text):
    """追加文本（用于流式输出）"""
    self.message += text
    html_content = markdown_to_html(self.message, self.theme)
    self.markdown_browser.setHtml(html_content)

    # 重新设置光标样式（setHtml 可能会重置）
    if hasattr(self, 'markdown_browser'):
        self.markdown_browser.viewport().setCursor(Qt.CursorShape.IBeamCursor)
```

**修改 `MarkdownMessage.set_theme` 方法**：

```python
# 如果是助手消息，重新渲染 Markdown HTML（使用新主题的CSS）
if self.role == "assistant" and hasattr(self, 'markdown_browser'):
    html_content = markdown_to_html(self.message, self.theme)
    self.markdown_browser.setHtml(html_content)

    # 重新设置光标样式（setHtml 可能会重置）
    self.markdown_browser.viewport().setCursor(Qt.CursorShape.IBeamCursor)
```

**修改 `StreamingMarkdownMessage.append_text` 方法**：

```python
self.current_text += text
html_content = markdown_to_html(self.current_text, self.theme)
self.markdown_browser.setHtml(html_content)

# 重新设置光标样式（setHtml 可能会重置）
self.markdown_browser.viewport().setCursor(Qt.CursorShape.IBeamCursor)
```

**修改 `StreamingMarkdownMessage.finish` 方法**：

```python
# 最后一次渲染
final_html = markdown_to_html(self.current_text, self.theme)
self.markdown_browser.setHtml(final_html)

# 重新设置光标样式（setHtml 可能会重置）
self.markdown_browser.viewport().setCursor(Qt.CursorShape.IBeamCursor)

# 重新连接信号
self.markdown_browser.document().contentsChanged.connect(self.adjust_height)
```

**修改 `StreamingMarkdownMessage.set_theme` 方法**：

```python
# 重新渲染 Markdown HTML（使用新主题的CSS）
if hasattr(self, 'markdown_browser') and self.current_text:
    html_content = markdown_to_html(self.current_text, self.theme)
    self.markdown_browser.setHtml(html_content)

    # 重新设置光标样式（setHtml 可能会重置）
    self.markdown_browser.viewport().setCursor(Qt.CursorShape.IBeamCursor)
```

---

### 修复 3：主题切换后重新应用光标样式

#### 修改文件：`chat_window.py`

**修改 `load_theme` 方法**：

```python
# 合并主题样式 + 所有组件样式
full_stylesheet = main_stylesheet + "\n" + "\n".join(component_stylesheets)
self.setStyleSheet(full_stylesheet)

# 重新应用光标样式（主题切换后可能被重置）
self._reapply_cursor_styles()
```

**添加 `_reapply_cursor_styles` 方法**：

```python
def _reapply_cursor_styles(self):
    """
    重新应用所有气泡的光标样式

    在主题切换或样式表更新后调用，确保光标样式不被覆盖
    """
    try:
        from modules.ai_assistant.ui.cursor_style_manager import CursorStyleManager

        # 重新应用全局光标样式
        CursorStyleManager.apply_styles(self)

        # 重新应用所有消息气泡的光标样式
        if hasattr(self, 'messages_layout') and self.messages_layout:
            from modules.ai_assistant.ui.markdown_message import MarkdownMessage, StreamingMarkdownMessage

            for i in range(self.messages_layout.count()):
                widget = self.messages_layout.itemAt(i).widget()
                if widget and isinstance(widget, (MarkdownMessage, StreamingMarkdownMessage)):
                    # 助手消息使用 markdown_browser
                    if hasattr(widget, 'markdown_browser'):
                        CursorStyleManager.set_bubble_cursor(widget.markdown_browser)
                    # 用户消息使用 text_label
                    elif hasattr(widget, 'text_label'):
                        CursorStyleManager.set_bubble_cursor(widget.text_label)

            print(f"[DEBUG] [UI管理器] 已重新应用所有气泡的光标样式")

    except Exception as e:
        print(f"[ERROR] [UI管理器] 重新应用光标样式失败: {e}")
```

---

## 测试步骤

### 测试 1：初始光标样式

1. 启动程序
2. 发送消息："你好"
3. 等待 AI 回复
4. 将鼠标悬停在 AI 回复的文本上

**预期结果**：

- ✅ 光标应该变为 I-beam 光标（|）

---

### 测试 2：流式输出过程中的光标

1. 发送一条较长的消息，触发流式输出
2. 在流式输出过程中，将鼠标悬停在正在生成的文本上

**预期结果**：

- ✅ 光标应该始终保持 I-beam 样式
- ✅ 不应该变回箭头光标

---

### 测试 3：流式输出完成后的光标

1. 等待流式输出完成
2. 将鼠标悬停在完成的文本上

**预期结果**：

- ✅ 光标应该保持 I-beam 样式
- ✅ 不应该丢失光标样式

---

### 测试 4：主题切换后的光标

1. 发送几条消息
2. 切换主题（如果有主题切换功能）
3. 将鼠标悬停在之前的消息文本上

**预期结果**：

- ✅ 光标应该保持 I-beam 样式
- ✅ 所有消息的光标样式都应该正确

---

### 测试 5：多条消息的光标

1. 发送多条消息（至少 5 条）
2. 依次将鼠标悬停在每条消息的文本上

**预期结果**：

- ✅ 所有消息的光标都应该是 I-beam 样式
- ✅ 用户消息和 AI 消息都应该正确

---

## 检查日志

启动程序后，应该看到：

```
[CursorStyleManager] 已设置 QTextBrowser viewport 光标为 IBeam
[DEBUG] [UI管理器] 已注册流式气泡到 SelectionManager
```

主题切换后，应该看到：

```
[DEBUG] [UI管理器] 已重新应用所有气泡的光标样式
[CursorStyleManager] 已设置 QTextBrowser viewport 光标为 IBeam
```

---

## 成功标准

- ✅ 初始光标样式正确（I-beam）
- ✅ 流式输出过程中光标样式保持
- ✅ 流式输出完成后光标样式保持
- ✅ 主题切换后光标样式保持
- ✅ 所有消息的光标样式都正确
- ✅ 不再出现光标样式丢失的问题

---

## 技术细节

### QTextBrowser 的光标设置

QTextBrowser 有两个光标：

1. **组件光标**：`widget.setCursor()` - 设置组件边框的光标
2. **viewport 光标**：`widget.viewport().setCursor()` - 设置内容区域的光标

对于文本内容，我们需要设置 **viewport 光标**。

### setHtml() 的副作用

`QTextBrowser.setHtml()` 方法会：

1. 清空当前内容
2. 解析新的 HTML
3. 重新渲染内容
4. **可能重置某些属性**，包括 viewport 的光标样式

因此，每次调用 `setHtml()` 后，都需要重新设置光标样式。

---

## 相关文件

- `ue_toolkits - ai/modules/ai_assistant/ui/cursor_style_manager.py`
- `ue_toolkits - ai/modules/ai_assistant/ui/markdown_message.py`
- `ue_toolkits - ai/modules/ai_assistant/ui/chat_window.py`

---

**修复完成！** 🎉

现在光标样式应该在所有情况下都能正确保持。
