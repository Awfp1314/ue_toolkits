# 🔧 修复清除选中后光标样式丢失问题

## 问题描述

用户报告：

- 回答完后的静态文本光标正确切换 ✅
- 但是当选择文本后点击其他区域，再把光标放到静态文本，光标就不会自动切换了 ❌

---

## 根本原因分析

### 问题根源

当用户选中文本后点击其他区域时，会触发以下流程：

1. `ChatWindow.mousePressEvent()` 被调用
2. 调用 `SelectionManager.clear_all_selections()`
3. 在 `clear_all_selections()` 中：
   - 调用 `cursor.clearSelection()`
   - 调用 `bubble.setTextCursor(cursor)`
4. **问题**：`setTextCursor()` 操作可能会触发 `QTextBrowser` 的内部状态变化
5. **结果**：viewport 的光标样式被重置为默认箭头光标

### 为什么初始时正常？

- 初始时，气泡创建后立即设置了光标样式
- 没有经过 `clearSelection()` 和 `setTextCursor()` 操作
- 因此光标样式保持正常

### 为什么清除选中后光标丢失？

- `clearSelection()` + `setTextCursor()` 组合操作会重置某些状态
- 只重新设置了 `selected_bubbles` 列表中的气泡光标
- 但用户可能悬停在其他没有被选中过的气泡上
- 这些气泡的光标样式也被间接影响

---

## 修复方案

### 修复 1：在清除选中后立即重新设置光标

#### 修改文件：`selection_manager.py`

**修改 `clear_all_selections` 方法**：

```python
def clear_all_selections(self):
    """清除所有气泡的选中状态"""
    from PyQt6.QtCore import Qt

    for bubble in self.selected_bubbles[:]:  # 使用副本遍历
        try:
            if isinstance(bubble, QTextBrowser):
                # QTextBrowser：使用 textCursor 清除选中
                cursor = bubble.textCursor()
                cursor.clearSelection()
                bubble.setTextCursor(cursor)

                # 重新设置光标样式（clearSelection 可能会重置）
                bubble.viewport().setCursor(Qt.CursorShape.IBeamCursor)

            elif isinstance(bubble, QLabel):
                # QLabel：清除选中文本（如果有）
                if bubble.hasSelectedText():
                    bubble.setSelection(0, 0)

                # 重新设置光标样式
                bubble.setCursor(Qt.CursorShape.IBeamCursor)

        except Exception as e:
            print(f"[SelectionManager] 清除选中状态失败: {e}")

    self.selected_bubbles.clear()
    print(f"[SelectionManager] 已清除所有选中状态并重新设置光标样式")
```

---

### 修复 2：在点击事件后重新应用所有气泡的光标

#### 修改文件：`chat_window.py`

**修改 `mousePressEvent` 方法**：

```python
def mousePressEvent(self, event):
    """
    鼠标点击事件处理

    用于清除所有聊天气泡的选中状态
    """
    try:
        # 清除所有选中状态
        if hasattr(self, 'selection_manager') and self.selection_manager:
            self.selection_manager.clear_all_selections()

            # 重新应用所有气泡的光标样式（清除选中可能会重置光标）
            self._reapply_all_bubble_cursors()

    except Exception as e:
        print(f"[ERROR] [ChatWindow] 处理鼠标点击事件失败: {e}")

    # 调用父类方法
    super().mousePressEvent(event)
```

**添加 `_reapply_all_bubble_cursors` 方法**：

```python
def _reapply_all_bubble_cursors(self):
    """
    重新应用所有消息气泡的光标样式

    在清除选中状态后调用，确保光标样式不被重置
    """
    try:
        from modules.ai_assistant.ui.cursor_style_manager import CursorStyleManager
        from modules.ai_assistant.ui.markdown_message import MarkdownMessage, StreamingMarkdownMessage

        if hasattr(self, 'messages_layout') and self.messages_layout:
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
        print(f"[ERROR] [UI管理器] 重新应用气泡光标样式失败: {e}")
```

**重构 `_reapply_cursor_styles` 方法**：

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
        self._reapply_all_bubble_cursors()

    except Exception as e:
        print(f"[ERROR] [UI管理器] 重新应用光标样式失败: {e}")
```

---

## 测试步骤

### 测试 1：初始光标样式（基准测试）

1. 启动程序
2. 发送消息："你好"
3. 等待 AI 回复完成
4. 将鼠标悬停在 AI 回复的文本上

**预期结果**：

- ✅ 光标应该变为 I-beam 光标（|）

---

### 测试 2：选中文本后清除（核心测试）

1. 用鼠标选中 AI 回复中的一段文本
2. 点击聊天窗口的空白区域
3. 将鼠标悬停在 AI 回复的文本上（同一条消息）

**预期结果**：

- ✅ 光标应该**仍然**是 I-beam 光标
- ✅ 不应该变成箭头光标

---

### 测试 3：选中后清除，悬停在其他消息（扩展测试）

1. 发送多条消息（至少 3 条）
2. 选中第一条 AI 回复中的文本
3. 点击空白区域清除选中
4. 依次将鼠标悬停在第二条、第三条 AI 回复的文本上

**预期结果**：

- ✅ 所有消息的光标都应该是 I-beam 光标
- ✅ 不应该有任何消息的光标变成箭头

---

### 测试 4：多次选中和清除（压力测试）

1. 选中文本 → 点击空白区域清除
2. 重复步骤 1 至少 5 次
3. 每次清除后，将鼠标悬停在不同的消息文本上

**预期结果**：

- ✅ 无论重复多少次，光标都应该保持 I-beam 样式
- ✅ 不应该出现光标样式丢失

---

### 测试 5：选中后点击输入框（边界测试）

1. 选中 AI 回复中的文本
2. 点击输入框（而不是空白区域）
3. 将鼠标悬停在 AI 回复的文本上

**预期结果**：

- ✅ 光标应该是 I-beam 光标
- ✅ 与点击空白区域的效果一致

---

## 检查日志

点击空白区域清除选中后，应该看到：

```
[SelectionManager] 已清除所有选中状态并重新设置光标样式
[DEBUG] [UI管理器] 已重新应用所有气泡的光标样式
[CursorStyleManager] 已设置 QTextBrowser viewport 光标为 IBeam
```

---

## 成功标准

- ✅ 初始光标样式正确（I-beam）
- ✅ 选中文本后清除，光标样式保持
- ✅ 清除后悬停在其他消息，光标样式保持
- ✅ 多次选中和清除，光标样式保持
- ✅ 点击输入框清除，光标样式保持
- ✅ 不再出现"选中后清除导致光标丢失"的问题

---

## 技术细节

### 为什么需要两层保护？

1. **第一层**：在 `clear_all_selections()` 中立即重新设置光标

   - 保护被选中过的气泡
   - 确保清除操作不会破坏这些气泡的光标

2. **第二层**：在 `mousePressEvent()` 中重新应用所有气泡的光标
   - 保护所有气泡（包括没有被选中过的）
   - 确保整个窗口的光标状态一致

### QTextBrowser 的状态管理

`QTextBrowser` 的光标样式可能在以下操作后被重置：

- `setTextCursor()` - 设置文本光标
- `clearSelection()` - 清除选中
- `setHtml()` - 设置 HTML 内容
- `setStyleSheet()` - 设置样式表

因此，我们需要在这些操作后立即重新设置光标样式。

---

## 相关文件

- `ue_toolkits - ai/modules/ai_assistant/ui/selection_manager.py`
- `ue_toolkits - ai/modules/ai_assistant/ui/chat_window.py`
- `ue_toolkits - ai/modules/ai_assistant/ui/cursor_style_manager.py`

---

## 修复历史

1. **第一次修复**：正确设置 viewport 光标
2. **第二次修复**：在 setHtml() 后重新设置光标
3. **第三次修复**：在清除选中后重新设置光标 ← **当前修复**

---

**修复完成！** 🎉

现在光标样式应该在所有情况下都能正确保持，包括选中文本后清除的场景。
