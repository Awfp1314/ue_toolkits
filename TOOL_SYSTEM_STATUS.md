# 工具系统状态诊断报告

## ❌ 当前问题

工具系统虽然已初始化，但**没有真正工作**。

### 问题根源

1. **工具定义被发送给 LLM**  
   ✅ `tools` 参数已正确传递到 `ApiLLMClient.generate_response()`
   
2. **但 tool_calls 响应没有被处理**  
   ❌ `api_llm_client.py` 只提取 `content`，忽略了 `tool_calls`
   
3. **ActionEngine 没有被使用**  
   ❌ `ChatWindow.send_message()` 直接调用 `APIClient`，绕过了 `ActionEngine`

### 代码路径对比

**当前路径（错误）**：
```
ChatWindow.send_message()
  → APIClient.__init__(messages, tools=tools)
    → ApiLLMClient.generate_response(messages, tools=tools)
      → 发送 tools 到 LLM ✅
      → 只提取 content，忽略 tool_calls ❌
      → 直接返回文本 ❌
```

**应该的路径（正确）**：
```
ChatWindow.send_message()
  → ActionEngine.execute_with_tools(messages)
    → 第一阶段：调用 LLM（带 tools）
    → 检测 tool_calls
    → 第二阶段：执行工具
    → 第三阶段：将结果返回 LLM，生成最终回复
```

### 当前 ActionEngine 的限制

`ActionEngine.execute_with_tools()` 实现了简化版本：
- 使用**意图引擎**（规则匹配）决定调用工具
- 不依赖 LLM 返回的 `tool_calls`
- 这意味着只能识别预定义的模式

例如：
```python
# action_engine.py 第 139-152 行
if intent == IntentType.ASSET_QUERY and entities:
    return [{
        "function": {
            "name": "search_assets",
            "arguments": json.dumps({"keyword": entities[0]})
        }
    }]
```

## 🛠️ 解决方案

### 方案 A：使用 ActionEngine（推荐，简单）

修改 `ChatWindow.send_message()` 使用 `ActionEngine.execute_with_tools()`：

**优点**：
- 立即可用，无需实现复杂的 tool_calls 解析
- 基于意图引擎，匹配用户查询模式
- 已有的代码，经过测试

**缺点**：
- 只能识别预定义模式（"查看资产"、"读取配置"等）
- 不是真正的 LLM 驱动的工具选择

### 方案 B：实现真正的 Function Calling（完整，复杂）

在 `ApiLLMClient` 中添加 `tool_calls` 处理逻辑：

1. 检测响应中的 `tool_calls`
2. 执行工具
3. 将结果追加到消息历史
4. 再次调用 LLM（非流式）
5. 返回最终响应（流式）

**优点**：
- 真正的 LLM 驱动工具选择
- 更灵活，可以处理复杂场景

**缺点**：
- 实现复杂（约 200 行代码）
- 需要处理流式/非流式切换
- 需要处理多轮工具调用
- 需要错误恢复机制

## 📊 工具系统架构

### 已实现的组件

- ✅ `ToolsRegistry` - 工具注册表
- ✅ `ActionEngine` - 动作引擎（简化版）
- ✅ `ControlledTools` - 受控工具（需要确认）
- ✅ `AssetReader`, `ConfigReader`, `LogAnalyzer`, `DocumentReader` - 工具实现
- ✅ `APIClient` - 支持 tools 参数

### 缺失的集成

- ❌ `ChatWindow` 没有使用 `ActionEngine`
- ❌ `ApiLLMClient` 没有处理 `tool_calls` 响应

## 🎯 推荐行动

**立即修复（方案 A）**：
1. 修改 `ChatWindow.send_message()` 使用 `ActionEngine.execute_with_tools()`
2. 确保信号连接正确（`on_chunk_received`, `on_finished`, `on_error`）
3. 测试基本工具调用场景

**后续优化（方案 B）**：
1. 实现真正的 tool_calls 解析
2. 支持 LLM 自主选择工具
3. 支持多轮工具调用
4. 改进错误处理

## 🧪 测试计划

### 阶段 1：验证意图引擎（当前可用）

测试查询：
- "列出所有资产" → 应触发 `tool_list_assets`
- "读取 DefaultEngine.ini" → 应触发 `tool_read_config`
- "分析日志错误" → 应触发 `tool_analyze_logs`

### 阶段 2：验证 Function Calling（需要实现）

测试查询：
- 自然语言查询，无需匹配特定模式
- 复杂场景，需要多步工具调用

---

**当前状态**: 工具系统 50% 完成（已初始化，未集成）
**下一步**: 实施方案 A（预计 1-2 小时）


