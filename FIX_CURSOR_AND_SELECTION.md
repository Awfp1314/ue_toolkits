# 🔧 光标样式和选中状态修复

## 问题描述

用户报告了两个问题：

1. **光标悬停效果消失** - 鼠标悬停在回答文本上时，没有显示文本选择光标（I-beam）
2. **选中状态只能通过输入框取消** - 选中文本后点击其他区域，选中状态仍然存在，只有点击输入框才能取消

---

## 根本原因分析

### 问题 1：光标样式未正确应用

**原因**：

- 在 `add_message` 方法中，代码尝试访问 `markdown_msg.content_label`
- 但实际上：
  - 助手消息使用 `markdown_msg.markdown_browser`（QTextBrowser）
  - 用户消息使用 `markdown_msg.text_label`（QLabel）
- 因此光标样式从未被正确设置

### 问题 2：选中状态只能通过输入框取消

**原因**：

- 只在 `ChatComposer` 的输入框获得焦点时清除选中状态
- 没有在 `ChatWindow` 的 `mousePressEvent` 中监听点击事件
- 因此点击其他区域（如空白区域）不会清除选中状态

---

## 修复方案

### 修复 1：正确设置光标样式

#### 修改文件：`chat_window.py`

**修改 `add_message` 方法**：

```python
# 注册到 SelectionManager 和设置光标样式
try:
    if hasattr(self, 'selection_manager') and self.selection_manager:
        # 助手消息使用 markdown_browser，用户消息使用 text_label
        text_widget = None
        if hasattr(markdown_msg, 'markdown_browser'):
            text_widget = markdown_msg.markdown_browser
        elif hasattr(markdown_msg, 'text_label'):
            text_widget = markdown_msg.text_label

        if text_widget:
            self.selection_manager.register_bubble(text_widget)

            # 设置光标样式
            from modules.ai_assistant.ui.cursor_style_manager import CursorStyleManager
            CursorStyleManager.set_bubble_cursor(text_widget)

            print(f"[DEBUG] [UI管理器] 已注册消息气泡到 SelectionManager")
except Exception as e:
    print(f"[ERROR] [UI管理器] 注册消息气泡失败: {e}")
```

**修改 `add_streaming_bubble` 方法**：

```python
# 注册到 SelectionManager 和设置光标样式
try:
    if hasattr(self, 'selection_manager') and self.selection_manager:
        if hasattr(self.current_streaming_bubble, 'markdown_browser'):
            self.selection_manager.register_bubble(self.current_streaming_bubble.markdown_browser)

            # 设置光标样式
            from modules.ai_assistant.ui.cursor_style_manager import CursorStyleManager
            CursorStyleManager.set_bubble_cursor(self.current_streaming_bubble.markdown_browser)

            print(f"[DEBUG] [UI管理器] 已注册流式气泡到 SelectionManager")
except Exception as e:
    print(f"[ERROR] [UI管理器] 注册流式气泡失败: {e}")
```

---

### 修复 2：监听窗口点击事件清除选中状态

#### 修改文件：`chat_window.py`

**添加 `mousePressEvent` 方法**：

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
    except Exception as e:
        print(f"[ERROR] [ChatWindow] 处理鼠标点击事件失败: {e}")

    # 调用父类方法
    super().mousePressEvent(event)
```

---

### 修复 3：支持 QLabel 的选中状态清除

#### 修改文件：`selection_manager.py`

**更新类型提示**：

```python
from typing import List, Union
from PyQt6.QtWidgets import QTextBrowser, QLabel

class SelectionManager:
    def __init__(self, chat_window):
        self.chat_window = chat_window
        self.selected_bubbles: List[Union[QTextBrowser, QLabel]] = []
```

**更新 `register_bubble` 方法**：

```python
def register_bubble(self, bubble: Union[QTextBrowser, QLabel]):
    """
    注册一个聊天气泡

    Args:
        bubble: 聊天气泡组件（QTextBrowser 或 QLabel）
    """
    # 只有 QTextBrowser 有 selectionChanged 信号
    if isinstance(bubble, QTextBrowser) and hasattr(bubble, 'selectionChanged'):
        bubble.selectionChanged.connect(
            lambda: self._on_selection_changed(bubble)
        )
    # QLabel 不需要连接信号，因为它的选中状态由系统管理
```

**更新 `clear_all_selections` 方法**：

```python
def clear_all_selections(self):
    """清除所有气泡的选中状态"""
    for bubble in self.selected_bubbles[:]:  # 使用副本遍历
        try:
            if isinstance(bubble, QTextBrowser):
                # QTextBrowser：使用 textCursor 清除选中
                cursor = bubble.textCursor()
                cursor.clearSelection()
                bubble.setTextCursor(cursor)
            elif isinstance(bubble, QLabel):
                # QLabel：清除选中文本（如果有）
                if bubble.hasSelectedText():
                    bubble.setSelection(0, 0)
        except Exception as e:
            print(f"[SelectionManager] 清除选中状态失败: {e}")

    self.selected_bubbles.clear()
    print(f"[SelectionManager] 已清除所有选中状态")
```

---

## 测试步骤

### 测试 1：光标样式

1. 启动程序
2. 发送一条消息并等待 AI 回复
3. 将鼠标悬停在 AI 回复的文本上
4. **预期结果**：光标应该变为文本选择光标（I-beam，|）

### 测试 2：选中状态清除

1. 选中 AI 回复中的一段文本
2. 点击聊天窗口的空白区域
3. **预期结果**：选中状态应该消失
4. 再次选中文本
5. 点击输入框
6. **预期结果**：选中状态应该消失

### 测试 3：用户消息光标

1. 发送一条消息
2. 将鼠标悬停在用户消息气泡上
3. **预期结果**：光标应该变为文本选择光标（I-beam，|）

---

## 检查日志

启动程序后，应该看到以下日志：

```
[DEBUG] [UI管理器] SelectionManager 已初始化
[DEBUG] [UI管理器] CursorStyleManager 已应用
[DEBUG] [UI管理器] ScrollController 已初始化并连接事件
```

发送消息后，应该看到：

```
[DEBUG] [UI管理器] 已注册流式气泡到 SelectionManager
```

点击空白区域后，应该看到：

```
[SelectionManager] 已清除所有选中状态
```

---

## 成功标准

- ✅ 鼠标悬停在文本上时显示 I-beam 光标
- ✅ 点击任何区域都能清除选中状态
- ✅ 不再只能通过点击输入框清除选中状态
- ✅ 用户消息和助手消息都正确支持

---

## 相关文件

- `ue_toolkits - ai/modules/ai_assistant/ui/chat_window.py`
- `ue_toolkits - ai/modules/ai_assistant/ui/selection_manager.py`
- `ue_toolkits - ai/modules/ai_assistant/ui/cursor_style_manager.py`
- `ue_toolkits - ai/modules/ai_assistant/ui/markdown_message.py`

---

**修复完成！** 🎉
