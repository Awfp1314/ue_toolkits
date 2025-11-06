# Function Calling 功能测试指南

## 概述

已成功实现**真正的两段式 Function Calling**（方案B），支持 LLM → 工具执行 → LLM 最终回复的完整流程。

## 实现的功能

### 1. 核心组件

- **FunctionCallingCoordinator**: 协调器类，负责管理工具调用的完整流程
- **ApiLLMClient 增强**: 支持 `tool_calls` 检测和非流式调用
- **ChatWindow 集成**: 自动检测工具可用性并启用协调器
- **UI 反馈**: 工具状态实时显示在消息气泡中

### 2. 工作流程

```
1. 用户发送消息
   ↓
2. ChatWindow 检测到工具可用
   ↓
3. 启动 FunctionCallingCoordinator
   ↓
4. LLM 分析并返回 tool_calls
   ↓
5. 执行工具，获取结果
   ↓
6. 将结果返回给 LLM
   ↓
7. LLM 生成最终回复（流式输出）
   ↓
8. 显示给用户
```

### 3. 安全机制

- **循环限制**: 最多 5 轮工具调用，防止无限循环
- **错误处理**: 工具执行失败时，错误信息会返回给 LLM
- **状态追踪**: 每次工具调用都会更新 UI 状态

## 测试场景

### 场景 1: 单工具调用

**测试查询**:
```
列出所有资产
```

**预期行为**:
1. UI 显示: "🔧 正在调用工具 [tool_list_assets]..."
2. 工具执行完成后显示: "🔧 工具 [tool_list_assets] 执行成功"
3. LLM 基于工具结果生成最终回复

**验证点**:
- [ ] 工具状态标签正确显示
- [ ] 工具状态标签自动隐藏（3秒后）
- [ ] LLM 回复包含工具返回的数据

---

### 场景 2: 多轮工具调用

**测试查询**:
```
比较资产管理器和AI助手的日志错误数量
```

**预期行为**:
1. 第一轮: 调用 `tool_analyze_logs(module='asset_manager')`
2. 第二轮: 调用 `tool_analyze_logs(module='ai_assistant')`
3. LLM 综合两次结果生成对比分析

**验证点**:
- [ ] 两次工具调用都正确显示状态
- [ ] LLM 能够综合多次工具结果
- [ ] 不会超过最大迭代次数

---

### 场景 3: 工具执行失败

**测试查询**:
```
读取不存在的配置文件: /path/to/nonexistent.json
```

**预期行为**:
1. UI 显示: "🔧 正在调用工具 [tool_read_config]..."
2. 工具执行失败，显示: "🔧 工具 [tool_read_config] 执行失败: 文件不存在"
3. LLM 基于错误信息生成友好的解释和建议

**验证点**:
- [ ] 错误状态正确显示
- [ ] LLM 能够理解工具失败并给出建议
- [ ] 不会因工具失败而崩溃

---

### 场景 4: 无工具调用

**测试查询**:
```
你好，今天天气怎么样？
```

**预期行为**:
1. LLM 判断不需要调用工具
2. 直接生成文本回复（不显示工具状态）

**验证点**:
- [ ] 不会显示工具状态标签
- [ ] 正常的流式输出
- [ ] 不会尝试调用工具

---

### 场景 5: 循环限制测试

**测试方法**:
模拟一个会导致 LLM 持续调用工具的场景（需要构造特殊的工具或查询）

**预期行为**:
1. 最多执行 5 轮工具调用
2. 达到限制后停止，显示错误: "工具调用次数过多（5 次），已终止"

**验证点**:
- [ ] 不会无限循环
- [ ] 错误消息清晰明确

---

## 调试日志

在测试过程中，关注以下日志输出：

```
[DEBUG] [工具系统] 启用 Function Calling 协调器
[DEBUG] [FunctionCalling] 第 X 轮迭代开始
[DEBUG] [FunctionCalling] LLM 请求调用 N 个工具
[DEBUG] [FunctionCalling] 执行工具: tool_name
[DEBUG] [工具] 执行成功: tool_name
[DEBUG] [FunctionCalling] LLM 返回最终回复，开始流式输出
```

## 已知限制

1. **图片消息**: 图片消息也会尝试使用工具（如果工具系统可用）
2. **Ollama 支持**: 目前仅在 `ApiLLMClient` 中实现，`OllamaLLMClient` 需要后续支持
3. **工具并行调用**: 当前是串行执行，未来可优化为并行

## 代码修改总结

### 新增文件
- `modules/ai_assistant/logic/function_calling_coordinator.py` (270 行)

### 修改文件
- `modules/ai_assistant/clients/api_llm_client.py` (+160 行)
  - 添加 tool_calls 检测和累积
  - 实现 `generate_response_non_streaming` 方法
  
- `modules/ai_assistant/ui/chat_window.py` (+180 行)
  - 添加 `_start_with_coordinator` 方法
  - 实现工具状态回调
  - 修改 `on_chunk_received` 支持新格式

- `modules/ai_assistant/ui/markdown_message.py` (+30 行)
  - 添加 `show_tool_status` 方法

- QSS 样式文件 (+20 行)
  - `modules/ai_assistant/resources/themes/dark.qss`
  - `modules/ai_assistant/resources/themes/light.qss`

### 总代码量
- **新增/修改**: ~660 行

## 下一步

1. **测试验证**: 按照上述场景逐一测试
2. **Ollama 支持**: 为 `OllamaLLMClient` 添加相同的 tool_calls 支持
3. **性能优化**: 考虑并行工具调用
4. **UI 优化**: 改进工具状态显示（可选的进度条、动画等）
5. **错误恢复**: 更智能的错误处理和重试机制

## 测试清单

### 基础功能
- [ ] 单工具调用成功
- [ ] 多轮工具调用成功
- [ ] 工具失败处理正确
- [ ] 无工具调用时正常工作
- [ ] 循环限制生效

### UI/UX
- [ ] 工具状态标签正确显示
- [ ] 工具状态标签自动隐藏
- [ ] 流式输出流畅
- [ ] 错误消息清晰易懂

### 集成测试
- [ ] 模型切换不影响工具调用
- [ ] "重新生成"按钮正确工作
- [ ] 图片消息支持工具调用
- [ ] 记忆系统与工具调用协同工作

### 性能
- [ ] 工具调用延迟可接受（< 2秒）
- [ ] 不阻塞 UI 主线程
- [ ] 内存占用正常

---

**测试人员**: _______  
**测试日期**: _______  
**测试版本**: Commit c5da9c2

