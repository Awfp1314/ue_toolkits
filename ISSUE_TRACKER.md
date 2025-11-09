# 🐛 问题追踪清单

> **最后更新**: 2025-11-08  
> **待修复问题**: 5 个（P0: 2 个, P1: 2 个, P2: 1 个）

---

## 🔥 P0 - 严重问题（需立即修复）

### Issue #1: 非流式 API 阻塞 UI ✅

**优先级**: 🔥🔥🔥 最高  
**发现时间**: 2025-11-08  
**报告者**: 用户测试反馈  
**状态**: ✅ 已修复（2025-11-09）

#### 问题描述

点击发送按钮后，UI 会冻结 1-3 秒（对话历史越长越明显），用户报告"界面无响应一段时间"。

#### 影响范围

- ✅ 所有对话都会触发
- ✅ 对话轮次越多，阻塞越久
- ✅ 严重影响用户体验

#### 根本原因

`function_calling_coordinator.py` 中的 `_call_llm_non_streaming()` 是同步调用，会阻塞 PyQt 主线程。

#### 代码位置

```
文件: modules/ai_assistant/logic/function_calling_coordinator.py
行号: 120-140
函数: _call_llm_non_streaming()
```

#### 复现步骤

1. 运行程序
2. 发送任意消息
3. 观察 UI 状态：冻结 1-3 秒
4. 查看终端：此期间无任何输出

#### 解决方案建议

**方案 A: QThread 异步化（推荐）**

```python
class NonStreamingWorker(QThread):
    result_ready = pyqtSignal(dict)

    def __init__(self, llm_client, messages, tools):
        super().__init__()
        self.llm_client = llm_client
        self.messages = messages
        self.tools = tools

    def run(self):
        response = self.llm_client.generate_response_non_streaming(
            messages=self.messages,
            tools=self.tools
        )
        self.result_ready.emit(response)

# 在 FunctionCallingCoordinator.run() 中使用
worker = NonStreamingWorker(self.llm_client, messages, tools)
worker.result_ready.connect(self._handle_non_streaming_result)
worker.start()
```

**方案 B: 移除非流式调用（重构量大）**

- 完全移除 `_call_llm_non_streaming()`
- 改用流式调用来检测工具调用
- 需要重构工具调用检测逻辑

#### 验证方法

```python
# 添加计时日志
import time
start = time.time()
response = self.llm_client.generate_response_non_streaming(...)
elapsed = time.time() - start
print(f"[BLOCKING] 非流式调用耗时: {elapsed:.2f}秒")

# 预期结果：修复后UI不应冻结
```

#### 风险评估

- 方案 A 风险：低（只需异步化现有逻辑）
- 方案 B 风险：中（需重构工具调用检测）

---

### Issue #2: 特定场景重复 API 调用 ❌

**优先级**: 🔥🔥🔥 最高  
**发现时间**: 2025-11-08  
**报告者**: 用户测试反馈  
**状态**: ❌ 未修复

#### 问题描述

用户报告："从我问蓝图 UE5 中蓝图和 C++各有什么优缺点后，后面的问题都调用了两次 api"。

#### 影响范围

- ⚠️ 不是所有对话都触发
- ⚠️ 从某个"触发点"开始，后续都重复调用
- ⚠️ 浪费双倍 Token 和时间

#### 可能原因

1. **工具调用场景的重复**

   - LLM 返回工具调用时，可能触发额外的 API 调用
   - `function_calling_coordinator.py` 的工具调用循环逻辑有 bug

2. **记忆压缩触发重发**

   - `memory_compressor.py` 压缩后可能重置状态
   - 导致消息重新发送

3. **特定消息模式触发**
   - 对话历史长度 > 20 轮时触发
   - 上下文复杂度达到某个阈值

#### 代码位置

```
可疑位置1: modules/ai_assistant/logic/function_calling_coordinator.py (150-250行)
可疑位置2: modules/ai_assistant/logic/memory_compressor.py (80-120行)
可疑位置3: modules/ai_assistant/ui/chat_window.py (send_message方法)
```

#### 复现步骤

1. 运行程序
2. 使用 `QUICK_TEST.txt` 进行完整测试
3. 到达"UE5 蓝图和 C++"问题后，观察日志
4. 后续每个问题都会出现 2 次 `[COORDINATOR]` 日志

#### 调试线索

```bash
# 搜索终端日志中的关键字
[COORDINATOR] !!! FunctionCallingCoordinator.run() 被调用
[API_CALL] !!! generate_response 被调用

# 正常：每个用户消息只有1次
# 异常：会出现2次（调用栈可能相同或不同）
```

#### 已排除的原因

- ✅ Enter 键重复处理（已在之前修复）
- ✅ 简单查询的流式重复调用（已在之前修复）
- ✅ 按钮状态重入（已在之前修复）

#### 调试检查清单

- [ ] 在 `send_message` 入口添加调用栈日志，检查是否被调用 2 次
- [ ] 检查工具调用后是否触发了额外的 `send_message()`
- [ ] 检查 `memory_compressor` 的 `loop.exec()` 是否导致事件重入
- [ ] 检查对话历史长度阈值（20 轮）是否触发特殊逻辑
- [ ] 测试不同对话模式：纯文本、工具调用、长对话

#### 解决方案建议

1. **添加更详细的日志**

   ```python
   # 在 chat_window.py 的 send_message 开头
   import traceback
   call_stack = ''.join(traceback.format_stack())
   print(f"[SEND_MESSAGE] 被调用，调用栈:\n{call_stack}")
   ```

2. **添加防重入保护**

   ```python
   # 在 chat_window.py 中
   if self._is_sending:
       print("[WARNING] send_message 重入，忽略")
       return
   self._is_sending = True
   try:
       # ... 原有逻辑
   finally:
       self._is_sending = False
   ```

3. **排查工具调用循环**
   ```python
   # 在 function_calling_coordinator.py 的循环中添加计数器
   iteration_count = 0
   while True:
       iteration_count += 1
       print(f"[LOOP] 工具调用循环第 {iteration_count} 次")
       # ... 原有逻辑
       if iteration_count > 10:
           print("[ERROR] 工具调用循环超过10次，强制退出")
           break
   ```

#### 风险评估

- 风险：高（问题根因不明确，需要深入调试）

---

## ⚠️ P1 - 重要问题（影响体验）

### Issue #3: 滚动条抽搐问题 ❌

**优先级**: ⚠️ 中高  
**发现时间**: 2025-11-08  
**状态**: ❌ 未修复

#### 问题描述

在流式输出时，聊天区域的滚动条会抽搐、跳动，视觉效果不佳。

#### 根本原因

- `chat_window.py` 的 `on_stream_chunk()` 每次更新都调用 `scrollToBottom()`
- Markdown 渲染导致内容高度频繁变化
- 8ms 的更新频率过高，导致滚动计算不稳定

#### 代码位置

```
文件: modules/ai_assistant/ui/chat_window.py
行号: ~1500
函数: on_stream_chunk()
```

#### 解决方案

```python
# 方案1: 降低滚动更新频率
self._scroll_update_counter += 1
if self._scroll_update_counter % 5 == 0:  # 每5次更新才滚动一次
    self.scroll_to_bottom()

# 方案2: 使用防抖动
if time.time() - self._last_scroll_time > 0.1:  # 100ms防抖
    self.scroll_to_bottom()
    self._last_scroll_time = time.time()
```

---

### Issue #4: 文本选中状态不消失 ❌

**优先级**: ⚠️ 中  
**发现时间**: 2025-11-08  
**状态**: ❌ 未修复

#### 问题描述

用户选中聊天气泡中的文本后，选中状态（蓝色高亮）不会消失。

#### 根本原因

- `chat_bubble.py` 或 `markdown_renderer.py` 的文本选择事件未正确处理
- QTextBrowser 的默认行为未被覆盖

#### 代码位置

```
文件: modules/ai_assistant/ui/chat_bubble.py
文件: modules/ai_assistant/ui/markdown_renderer.py
```

#### 解决方案

```python
# 在 chat_bubble.py 中
def mousePressEvent(self, event):
    super().mousePressEvent(event)
    # 点击其他地方时清除选中
    if not self.textCursor().hasSelection():
        self.clearSelection()

def clearSelection(self):
    cursor = self.textCursor()
    cursor.clearSelection()
    self.setTextCursor(cursor)
```

---

## ℹ️ P2 - 次要问题（可优化）

### Issue #5: 光标样式问题 ❌

**优先级**: ℹ️ 低  
**发现时间**: 2025-11-08  
**状态**: ❌ 未修复

#### 问题描述

某些 UI 元素的光标样式不正确（具体场景未详细说明）。

#### 解决方案

```python
# 在相应的UI组件中设置光标
self.setCursor(Qt.CursorShape.PointingHandCursor)  # 手型光标
self.setCursor(Qt.CursorShape.IBeamCursor)         # 文本选择光标
self.setCursor(Qt.CursorShape.ArrowCursor)         # 默认箭头
```

---

## 📊 问题统计

| 优先级   | 总数  | 已修复 | 未修复 | 进度   |
| -------- | ----- | ------ | ------ | ------ |
| 🔥 P0    | 2     | 0      | 2      | 0%     |
| ⚠️ P1    | 2     | 0      | 2      | 0%     |
| ℹ️ P2    | 1     | 0      | 1      | 0%     |
| **总计** | **5** | **0**  | **5**  | **0%** |

---

## 📝 修复记录

### 2025-11-08

- 创建问题追踪清单
- 识别并记录 5 个待修复问题
- 提供详细的调试线索和解决方案

---

## 🎯 下一步行动

1. **立即修复 P0 问题** 🔥

   - [ ] 异步化非流式 API 调用
   - [ ] 排查重复 API 调用的根因

2. **验证修复效果** 📝

   - [ ] 使用 `QUICK_TEST.txt` 完整测试
   - [ ] 确认 UI 不再冻结
   - [ ] 确认无重复 API 调用

3. **优化 P1 问题** ⚠️

   - [ ] 修复滚动条抽搐
   - [ ] 修复文本选中状态

4. **细节优化 P2 问题** ℹ️
   - [ ] 修复光标样式

---

**备注**: 所有问题的详细技术分析见 `AI_PROJECT_HANDOVER.md`
