# Ollama Function Calling 支持 - 修复报告

## 🐛 问题描述

**错误信息**:
```
⚠️ Function Calling 执行失败: Ollama 请求失败: 
Attempted to access streaming response content, without having called read().
```

**根本原因**:
1. **httpx 使用不当**: 在 `httpx.stream()` 上下文中错误地访问 `response.text`
2. **缺少 Function Calling 支持**: OllamaLLMClient 没有实现 tool_calls 检测和非流式方法

---

## ✅ 修复内容

### 1. 修复 httpx 流式响应错误

**原代码** (第 83-98 行):
```python
with httpx.stream("POST", self.chat_endpoint, ...) as response:
    if response.status_code != 200:
        error_text = response.text  # ❌ 错误！不能在 stream 模式下访问 text
```

**修复后**:
```python
with httpx.Client() as client:
    response = client.post(self.chat_endpoint, ...)
    if response.status_code != 200:
        error_text = response.text  # ✅ 正确！普通请求可以访问 text
```

### 2. 添加 tool_calls 检测

**新增代码** (第 113-140 行):
```python
if 'message' in data:
    message = data['message']
    
    # 检查是否有 tool_calls
    tool_calls = message.get('tool_calls')
    if tool_calls:
        self._accumulate_tool_calls(tool_calls)
        continue
    
    # 提取普通内容
    content = message.get('content', '')
    if content:
        # 返回新格式
        yield {'type': 'content', 'text': content}

# 检查是否完成
if data.get('done', False):
    if self._tool_calls_buffer:
        yield {
            'type': 'tool_calls',
            'tool_calls': self._get_accumulated_tool_calls()
        }
```

### 3. 实现非流式方法

**新增方法** (第 235-320 行):
```python
def generate_response_non_streaming(
    self,
    context_messages: List[Dict[str, str]],
    temperature: float = None,
    tools: List[Dict] = None
) -> Dict:
    """
    非流式调用（用于工具调用检测）
    
    Returns:
        Dict: {
            'type': 'tool_calls' | 'content',
            'tool_calls': [...] | None,
            'content': str | None
        }
    """
    # 构建请求（stream=False）
    payload = {
        "model": self.model_name,
        "messages": context_messages,
        "stream": False,
        ...
    }
    
    # 检查响应中的 tool_calls
    if 'tool_calls' in message:
        return {'type': 'tool_calls', ...}
    else:
        return {'type': 'content', ...}
```

### 4. 添加工具缓冲区

**初始化** (第 46 行):
```python
def __init__(self, config):
    ...
    # Tool calls 累积缓冲区
    self._tool_calls_buffer = []
```

**辅助方法** (第 214-233 行):
```python
def _accumulate_tool_calls(self, tool_calls_delta):
    """累积 tool_calls"""
    for tc in tool_calls_delta:
        self._tool_calls_buffer.append(tc)

def _get_accumulated_tool_calls(self):
    """获取并清空缓冲区"""
    result = self._tool_calls_buffer.copy()
    self._tool_calls_buffer = []
    return result
```

---

## 📊 修改统计

| 项目 | 数量 |
|------|------|
| 新增代码 | +145 行 |
| 删除代码 | -11 行 |
| 新增方法 | 3 个 |
| 修复的 bug | 2 个 |

---

## 🎯 现在支持的功能

### ✅ ApiLLMClient (OpenAI-compatible)
- ✅ tool_calls 检测
- ✅ 非流式工具调用
- ✅ 流式最终回复
- ✅ 多轮工具调用

### ✅ OllamaLLMClient (本地模型)
- ✅ tool_calls 检测
- ✅ 非流式工具调用
- ✅ 流式最终回复
- ✅ 多轮工具调用

---

## 🧪 测试方法

### 1. 使用 Ollama 测试单工具调用

```
用户: 列出所有资产
```

**预期行为**:
1. 显示 "🔧 正在调用工具 [tool_list_assets]..."
2. 执行工具
3. LLM 基于结果生成回复

### 2. 测试多轮工具调用

```
用户: 比较资产管理器和AI助手的日志
```

**预期行为**:
1. 调用 tool_analyze_logs (asset_manager)
2. 调用 tool_analyze_logs (ai_assistant)
3. LLM 综合结果生成对比分析

---

## 🔧 兼容性

- ✅ 向后兼容：无工具调用时，正常对话不受影响
- ✅ 格式兼容：同时支持 dict 和 str 格式的 chunk
- ✅ 模型切换：API 和 Ollama 可以无缝切换

---

## 📝 注意事项

### Ollama 工具调用支持

并非所有 Ollama 模型都支持 Function Calling。支持的模型包括：

- ✅ `llama3.1` 和更新版本
- ✅ `mistral-nemo`
- ✅ `qwen2.5`
- ❌ `llama2` (不支持)
- ❌ 部分较旧模型

**如何检查**:
```bash
ollama show <model_name>
```

查看输出中是否提到 "function calling" 或 "tools"。

### 如果模型不支持工具调用

系统会自动降级为普通对话模式，不会报错。

---

## 🎉 总结

通过此次修复：

1. **解决了 httpx 流式响应错误** - 不再崩溃
2. **添加了完整的 Function Calling 支持** - Ollama 可以调用工具
3. **统一了 API 和 Ollama 的实现** - 相同的 Function Calling 体验
4. **保持了向后兼容** - 不影响现有功能

**现在可以愉快地使用 Ollama 本地模型调用工具了！** 🎊

---

**修复版本**: Commit 20fb332  
**修复日期**: 2025-11-06  
**修复文件**: `modules/ai_assistant/clients/ollama_llm_client.py`

