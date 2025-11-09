# 🔧 修复光标在交互后失效的问题

## 问题描述（用户反馈）

**现象**：

1. ✅ AI 正在回答时（流式输出中）- 光标正常切换为 I-beam
2. ❌ AI 回答完成后 - 光标不再切换，保持箭头
3. ❌ 在文本区域点击/移动鼠标后 - 光标切换完全失效
4. ❌ 之前的文本 - 光标不会切换

**关键发现**：

- 流式输出过程中光标正常 ✅
- 流式输出完成后光标失效 ❌
- 用户交互（点击、移动）后光标失效 ❌

---

## 根本原因分析

### 问题 1：viewport 的鼠标追踪未启用

`QTextBrowser` 的 viewport 默认不启用鼠标追踪，导致：

- 鼠标移动事件不会触发
- 光标样式不会动态更新
- 只有在特定情况下（如流式输出时）光标才会更新

### 问题 2：WA_Hover 属性未设置

`WA_Hover` 属性控制组件是否响应鼠标悬停事件：

- 未设置时，组件不会响应鼠标进入/离开事件
- 光标样式不会在鼠标移动时更新

### 问题 3：setHtml() 后光标样式丢失

每次调用 `setHtml()` 后：

- viewport 可能被重新创建或重置
- 光标样式设置丢失
- 需要重新设置光标样式

---

## 修复方案

### 修复 1：启用 viewport 的鼠标追踪和悬停

#### 修改文件：`markdown_message.py`

**在 `StreamingMarkdownMessage.__init__` 中添加**：

```python
# 设置鼠标指针为文本编辑样式（I-beam）
self.markdown_browser.viewport().setCursor(Qt.CursorShape.IBeamCursor)

# 设置选中文本的样式（深色主题/浅色主题都保持高对比度）
selection_bg = "#3390FF" if self.theme == "dark" else "#0078D7"
selection_fg = "#FFFFFF"
self.markdown_browser.setStyleSheet(f"""
    QTextBrowser {{
        selection-background-color: {selection_bg};
        selection-color: {selection_fg};
    }}
""")

# 强制设置 viewport 属性，确保光标样式持久化
self.markdown_browser.viewport().setAttribute(Qt.WidgetAttribute.WA_Hover, True)
self.markdown_browser.viewport().setMouseTracking(True)
```

**在 `MarkdownMessage._init_assistant_message` 中添加**：

```python
# 设置鼠标指针为文本编辑样式（I-beam）
self.markdown_browser.viewport().setCursor(Qt.CursorShape.IBeamCursor)

# 设置选中文本的样式（深色主题/浅色主题都保持高对比度）
selection_bg = "#3390FF" if self.theme == "dark" else "#0078D7"
selection_fg = "#FFFFFF"
self.markdown_browser.setStyleSheet(f"""
    QTextBrowser {{
        selection-background-color: {selection_bg};
        selection-color: {selection_fg};
    }}
""")

# 强制设置 viewport 属性，确保光标样式持久化
self.markdown_browser.viewport().setAttribute(Qt.WidgetAttribute.WA_Hover, True)
self.markdown_browser.viewport().setMouseTracking(True)

# 连接链接点击信号，手动处理链接打开
self.markdown_browser.anchorClicked.connect(lambda url: QDesktopServices.openUrl(url))

# 设置QTextBrowser占满整个容器宽度
self.markdown_browser.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

# 渲染 Markdown 为 HTML
html_content = markdown_to_html(self.message, self.theme)
self.markdown_browser.setHtml(html_content)

# 确保渲染后光标样式仍然正确
self.markdown_browser.viewport().setCursor(Qt.CursorShape.IBeamCursor)
```

---

### 修复 2：在所有 setHtml() 调用后重新设置光标

这个修复已经在之前完成，确保每次调用 `setHtml()` 后都重新设置光标：

- `append_text()` 方法 ✅
- `finish()` 方法 ✅
- `set_theme()` 方法 ✅

---

## 技术细节

### WA_Hover 属性

`Qt.WidgetAttribute.WA_Hover` 控制组件是否响应鼠标悬停事件：

```python
widget.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
```

**作用**：

- 启用鼠标进入/离开事件
- 允许光标样式动态更新
- 确保鼠标移动时触发样式变化

### setMouseTracking

`setMouseTracking(True)` 启用鼠标追踪：

```python
widget.setMouseTracking(True)
```

**作用**：

- 即使没有按下鼠标按钮，也会接收鼠标移动事件
- 允许光标样式实时更新
- 确保鼠标移动时光标正确切换

### 为什么流式输出时光标正常？

流式输出时，`append_text()` 频繁调用：

1. 每次调用都会 `setHtml()`
2. 每次 `setHtml()` 后都重新设置光标
3. 频繁的更新导致光标样式"看起来"一直正常

但实际上，如果停止更新（流式输出完成），光标样式就会失效。

---

## 测试步骤

### 测试 1：流式输出完成后的光标

1. 启动程序
2. 发送消息："你好"
3. 等待 AI 回答完成
4. 将鼠标在 AI 回答的文本上来回移动

**预期结果**：

- ✅ 光标应该始终保持 I-beam 样式
- ✅ 不应该变回箭头光标

---

### 测试 2：点击文本后的光标

1. 发送消息并等待回答完成
2. 在 AI 回答的文本上点击几次
3. 将鼠标移动到文本的不同位置

**预期结果**：

- ✅ 光标应该始终保持 I-beam 样式
- ✅ 点击不应该影响光标样式

---

### 测试 3：乱点击乱移动后的光标

1. 发送消息并等待回答完成
2. 在文本区域快速点击、移动鼠标（模拟"乱点击乱移动"）
3. 观察光标样式

**预期结果**：

- ✅ 光标应该始终保持 I-beam 样式
- ✅ 不应该出现光标切换失效

---

### 测试 4：多条消息的光标

1. 发送多条消息（至少 5 条）
2. 等待所有回答完成
3. 依次在每条消息上移动鼠标

**预期结果**：

- ✅ 所有消息的光标都应该正确
- ✅ 旧消息和新消息的光标都应该正常

---

### 测试 5：流式输出过程中的光标

1. 发送一条较长的消息
2. 在流式输出过程中，将鼠标在文本上移动

**预期结果**：

- ✅ 光标应该保持 I-beam 样式
- ✅ 流式输出不应该影响光标

---

## 检查日志

启动程序后，应该看到：

```
[CursorStyleManager] 已设置 QTextBrowser viewport 光标为 IBeam
[DEBUG] [UI管理器] 已注册流式气泡到 SelectionManager
```

---

## 成功标准

- ✅ 流式输出完成后光标保持 I-beam
- ✅ 点击文本后光标保持 I-beam
- ✅ 乱点击乱移动后光标保持 I-beam
- ✅ 所有消息（新旧）的光标都正确
- ✅ 流式输出过程中光标正常
- ✅ 不再出现"光标切换失效"的问题

---

## 对比修复前后

### 修复前

| 场景           | 光标状态  |
| -------------- | --------- |
| 流式输出中     | ✅ I-beam |
| 流式输出完成后 | ❌ 箭头   |
| 点击文本后     | ❌ 箭头   |
| 乱点击乱移动后 | ❌ 箭头   |
| 旧消息         | ❌ 箭头   |

### 修复后

| 场景           | 光标状态  |
| -------------- | --------- |
| 流式输出中     | ✅ I-beam |
| 流式输出完成后 | ✅ I-beam |
| 点击文本后     | ✅ I-beam |
| 乱点击乱移动后 | ✅ I-beam |
| 旧消息         | ✅ I-beam |

---

## 相关文件

- `ue_toolkits - ai/modules/ai_assistant/ui/markdown_message.py`
- `ue_toolkits - ai/modules/ai_assistant/ui/cursor_style_manager.py`
- `ue_toolkits - ai/modules/ai_assistant/ui/chat_window.py`

---

**修复完成！** 🎉

现在光标应该在所有情况下都能正确保持，包括：

- 流式输出完成后
- 用户点击/移动鼠标后
- 旧消息和新消息
