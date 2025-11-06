# Function Calling 完整实现总结

## 🎯 项目目标

实现真正的两段式 Function Calling（方案B），让 AI 能够：
1. 智能决定何时调用工具
2. 执行工具并获取结果
3. 基于工具结果生成最终回复
4. 支持多轮工具调用
5. 提供清晰的 UI 反馈

## ✅ 完成状态

所有计划任务已完成！

## 📋 实现步骤回顾

### 步骤 1: 创建 FunctionCallingCoordinator 类

**文件**: `modules/ai_assistant/logic/function_calling_coordinator.py` (270 行)

**核心功能**:
- 实现多轮工具调用循环逻辑
- 管理 LLM 和工具执行的交互
- 提供 PyQt6 信号支持 UI 更新
- 安全限制：最大 5 轮迭代，防止无限循环

**关键方法**:
```python
class FunctionCallingCoordinator(QThread):
    def run(self):
        # 多轮循环
        while iteration < max_iterations:
            # 1. 调用 LLM（非流式，检测 tool_calls）
            response = _call_llm_non_streaming(messages, tools)
            
            # 2. 如果有 tool_calls，执行工具
            if response['type'] == 'tool_calls':
                for tool_call in tool_calls:
                    result = _execute_tool(tool_name, args)
                    messages.append(tool_result_message)
                continue  # 继续下一轮
            
            # 3. 没有 tool_calls，流式输出最终回复
            _stream_final_response(messages, tools)
            break
```

**信号定义**:
- `tool_start`: 工具开始执行
- `tool_complete`: 工具执行完成
- `chunk_received`: 文本流式输出
- `request_finished`: 请求完成
- `error_occurred`: 错误发生

---

### 步骤 2: 修改 ApiLLMClient 支持 tool_calls 检测

**文件**: `modules/ai_assistant/clients/api_llm_client.py` (+160 行)

**修改点 1: 流式响应中检测 tool_calls**

```python
# 在 generate_response() 方法中（第 156-171 行）
delta = choice.get('delta', {})

# 检测 tool_calls（优先级更高）
tool_calls = delta.get('tool_calls')
if tool_calls:
    self._accumulate_tool_calls(tool_calls)
    continue

# 检测 finish_reason
finish_reason = choice.get('finish_reason')
if finish_reason == 'tool_calls':
    yield {
        'type': 'tool_calls',
        'tool_calls': self._get_accumulated_tool_calls()
    }
    return

# 正常的文本内容
content = delta.get('content', '')
if content:
    yield {'type': 'content', 'text': content}
```

**修改点 2: 累积 tool_calls**

```python
def _accumulate_tool_calls(self, tool_calls_delta):
    # tool_calls 可能分多个 chunk 返回
    for tc_delta in tool_calls_delta:
        index = tc_delta.get('index', 0)
        # 扩展 buffer
        while len(self._tool_calls_buffer) <= index:
            self._tool_calls_buffer.append({...})
        # 累积 name 和 arguments
        ...
```

**修改点 3: 新增非流式方法**

```python
def generate_response_non_streaming(self, context_messages, ...):
    # 用于工具调用检测，返回完整的 tool_calls
    payload = {"stream": False, ...}
    response = session.post(...)
    data = response.json()
    
    if 'tool_calls' in message:
        return {'type': 'tool_calls', 'tool_calls': ...}
    else:
        return {'type': 'content', 'content': ...}
```

---

### 步骤 3: 修改 ChatWindow 集成协调器

**文件**: `modules/ai_assistant/ui/chat_window.py` (+180 行)

**修改点 1: 自动检测并启用协调器**

```python
# 在 send_message() 中（第 816-832 行）
if tools and self.tools_registry:
    # 使用协调器（支持真正的 Function Calling）
    self._start_with_coordinator(request_messages, model, tools)
else:
    # 普通模式（无工具）
    self.current_api_client = APIClient(...)
```

**修改点 2: 实现协调器启动方法**

```python
def _start_with_coordinator(self, messages, model, tools):
    # 创建 LLM 客户端
    llm_client = create_llm_client(config)
    
    # 创建协调器
    self.current_coordinator = FunctionCallingCoordinator(
        messages=messages,
        tools_registry=self.tools_registry,
        llm_client=llm_client,
        max_iterations=5
    )
    
    # 连接信号
    self.current_coordinator.tool_start.connect(self.on_tool_start)
    self.current_coordinator.tool_complete.connect(self.on_tool_complete)
    ...
    
    # 启动
    self.current_coordinator.start()
```

**修改点 3: 实现工具状态回调**

```python
def on_tool_start(self, tool_name):
    if self.current_streaming_bubble:
        self.current_streaming_bubble.show_tool_status(
            f"正在调用工具 [{tool_name}]..."
        )

def on_tool_complete(self, tool_name, result):
    if result.get('success'):
        self.current_streaming_bubble.show_tool_status(
            f"工具 [{tool_name}] 执行成功"
        )
    else:
        self.current_streaming_bubble.show_tool_status(
            f"工具 [{tool_name}] 执行失败: {error}"
        )
```

**修改点 4: 修改 on_chunk_received 支持新格式**

```python
def on_chunk_received(self, chunk):
    # 检查 chunk 类型
    if isinstance(chunk, dict):
        # 新格式：{'type': 'content', 'text': '...'}
        if chunk.get('type') == 'content':
            text = chunk.get('text', '')
            if text:
                self.current_streaming_bubble.append_text(text)
        # 忽略 tool_calls 类型（由协调器处理）
        elif chunk.get('type') == 'tool_calls':
            pass
    else:
        # 旧格式：纯字符串（向后兼容）
        self.current_streaming_bubble.append_text(chunk)
```

---

### 步骤 4: 扩展 StreamingMarkdownMessage 支持工具状态

**文件**: `modules/ai_assistant/ui/markdown_message.py` (+30 行)

**实现方法**:

```python
def show_tool_status(self, status_text):
    if not self.tool_status_label:
        # 创建状态标签
        self.tool_status_label = QLabel()
        self.tool_status_label.setObjectName("tool_status")
        # 插入到布局顶部
        container_layout.insertWidget(0, self.tool_status_label)
    
    # 更新状态文本
    self.tool_status_label.setText(f"🔧 {status_text}")
    self.tool_status_label.show()
    
    # 3秒后自动隐藏
    QTimer.singleShot(3000, self.tool_status_label.hide)
```

---

### 步骤 5: 添加 QSS 样式

**文件**: 
- `modules/ai_assistant/resources/themes/dark.qss`
- `modules/ai_assistant/resources/themes/light.qss`

**样式定义**:

```css
/* 工具调用状态标签 */
QLabel#tool_status {
    color: #FFA500;  /* 橙色，表示正在执行 */
    font-size: 12px;
    padding: 5px;
    background-color: rgba(255, 165, 0, 0.1);
    border-radius: 3px;
    margin-bottom: 5px;
}
```

---

## 🔑 关键技术决策

### 1. 为什么需要非流式方法？

**问题**: 流式响应中的 `tool_calls` 可能分多个 chunk 返回，难以判断何时完成。

**解决方案**: 
- 工具调用检测阶段使用**非流式**方法（快速获取完整 tool_calls）
- 最终回复阶段使用**流式**方法（提供打字机效果）

### 2. 为什么返回 dict 而不是 str？

**问题**: 需要区分 `tool_calls` 和普通 `content`。

**解决方案**: 
- 修改 `generate_response()` 返回 `{'type': 'tool_calls'/'content', ...}`
- 保持向后兼容：`on_chunk_received` 同时支持 dict 和 str

### 3. 为什么使用协调器而不是直接在 ChatWindow 中实现？

**问题**: 工具调用逻辑复杂，混入 ChatWindow 会导致代码难以维护。

**解决方案**: 
- 创建独立的 `FunctionCallingCoordinator` 类
- 通过 PyQt6 信号与 UI 解耦
- 易于测试和扩展

---

## 🧪 测试建议

详见 `FUNCTION_CALLING_TEST_GUIDE.md`

核心测试场景：
1. ✅ 单工具调用
2. ✅ 多轮工具调用
3. ✅ 工具失败处理
4. ✅ 无工具调用
5. ✅ 循环限制

---

## 📊 代码统计

| 文件 | 类型 | 行数 |
|------|------|------|
| `function_calling_coordinator.py` | 新增 | 270 |
| `api_llm_client.py` | 修改 | +160 |
| `chat_window.py` | 修改 | +180 |
| `markdown_message.py` | 修改 | +30 |
| QSS 样式文件 | 修改 | +20 |
| **总计** | | **~660 行** |

---

## 🎨 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        ChatWindow                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  send_message()                                        │  │
│  │    ↓                                                   │  │
│  │  检测工具可用？                                         │  │
│  │    ├─ Yes → _start_with_coordinator()                 │  │
│  │    └─ No  → APIClient (普通模式)                      │  │
│  └───────────────────────────────────────────────────────┘  │
│                        ↓                                     │
│  ┌───────────────────────────────────────────────────────┐  │
│  │          FunctionCallingCoordinator                    │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  while iteration < max_iterations:               │  │  │
│  │  │    1. LLM (非流式) → tool_calls?                 │  │  │
│  │  │    2. 如果有，执行工具                            │  │  │
│  │  │    3. 将结果返回 LLM                             │  │  │
│  │  │    4. 重复直到 LLM 返回文本                       │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                        ↓                               │  │
│  │           信号：tool_start, tool_complete              │  │
│  └───────────────────────────────────────────────────────┘  │
│                        ↓                                     │
│  ┌───────────────────────────────────────────────────────┐  │
│  │      StreamingMarkdownMessage                          │  │
│  │    show_tool_status("正在调用工具...")                 │  │
│  │          ↓                                             │  │
│  │    [🔧 正在调用工具 [tool_name]...]                   │  │
│  │          ↓ (3秒后自动隐藏)                             │  │
│  │    [最终回复流式输出...]                               │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 后续优化方向

### 1. Ollama 支持
- 为 `OllamaLLMClient` 实现相同的 tool_calls 逻辑
- 可能需要适配不同的响应格式

### 2. 工具并行调用
- 当前是串行执行，可优化为并行
- 需要考虑工具间的依赖关系

### 3. UI 增强
- 添加工具调用进度条
- 显示工具调用参数和结果（可折叠）
- 支持工具调用历史查看

### 4. 错误恢复
- 工具失败后自动重试
- 更智能的降级策略
- 用户手动干预选项

### 5. 性能优化
- 缓存常用工具结果
- 优化 LLM 调用次数
- 减少不必要的工具调用

---

## 📝 开发日志

**时间**: 2025-11-06  
**版本**: Commit c5da9c2  
**开发者**: AI Assistant (Cursor)  
**用户**: wang  

**实施时长**: ~2 小时  
**代码质量**: ✅ 无 Linter 错误  
**测试状态**: 待用户测试  

---

## 🎉 总结

此次实现完成了**真正的两段式 Function Calling**，与之前的"伪Function Calling"（直接在 prompt 中提示工具）有本质区别：

### 之前（方案A：工具提示方案）
```
用户: 列出所有资产
↓
LLM: 我应该调用 tool_list_assets 工具...（文本）
↓
❌ 不会真正执行工具
```

### 现在（方案B：真Function Calling）
```
用户: 列出所有资产
↓
LLM: {tool_calls: [{name: "tool_list_assets", args: {}}]}
↓
✅ 真正执行工具，获取结果
↓
LLM: 根据工具结果生成回复："您有以下资产：..."
```

这才是真正的 AI Agent 能力！🎊

