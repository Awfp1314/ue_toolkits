# AI 助手模块

## 📖 简介

这是一个集成在 UE Toolkit 中的 AI 聊天助手模块，提供类似 ChatGPT 官方界面的聊天体验。

## ✨ 功能特性

### 🎨 界面特色
- **ChatGPT 风格设计**: 完全仿照 ChatGPT 官方界面
- **气泡式消息**: 用户消息右对齐（绿色），AI 消息左对齐（灰色）
- **流式输出**: 打字机效果，实时显示 AI 回复
- **主题切换**: 支持深色/浅色主题
- **Markdown 渲染**: 支持粗体、代码、代码块等格式

### 🚀 核心功能
- ✅ 多轮对话支持
- ✅ 模型选择（gpt-3.5-turbo / gpt-4 / gpt-4-turbo）
- ✅ Enter 发送，Shift+Enter 换行
- ✅ 自动滚动到最新消息
- ✅ 友好的错误提示
- ✅ 对话历史记录

## 🎯 使用方法

### 基本操作
1. **发送消息**:
   - 在底部输入框输入内容
   - 按 `Enter` 键发送
   - 按 `Shift + Enter` 换行

2. **切换模型**:
   - 点击底部的模型选择下拉框
   - 选择合适的模型（gpt-3.5/gpt-4/gpt-4-turbo）

3. **主题切换**:
   - 点击右上角的主题按钮
   - 在深色和浅色主题间切换

4. **清空对话**:
   - 点击"清空对话"按钮
   - 开始新的对话（系统提示词保留）

### Markdown 支持

AI 回复支持以下 Markdown 格式：
- **粗体文本**: `**粗体**`
- `行内代码`: `` `代码` ``
- 代码块:
  ````
  ```python
  def hello():
      print("Hello")
  ```
  ````

## 🔧 配置

### API 配置

编辑 `modules/ai_assistant/logic/api_client.py`:

```python
# 修改 API URL 和密钥
self.api_url = "https://api.openai-hk.com/v1/chat/completions"
self.headers = {
    "Content-Type": "application/json",
    "Authorization": "你的API密钥"  # 在这里修改
}
```

### 系统提示词

编辑 `modules/ai_assistant/logic/config.py`:

```python
SYSTEM_PROMPT = """你是一位虚幻引擎专家...
（在这里自定义系统提示词）
"""
```

### 温度参数

编辑 `modules/ai_assistant/logic/api_client.py` 第 22 行:

```python
def __init__(self, messages, model="gpt-3.5-turbo", temperature=0.8):
    # temperature: 0-2，越高越随机，越低越确定
```

## 📁 模块结构

```
modules/ai_assistant/
├── manifest.json           # 模块元信息
├── ai_assistant.py         # 模块主类
├── __init__.py
├── __main__.py
├── logic/                  # 业务逻辑层
│   ├── __init__.py
│   ├── api_client.py       # API 客户端（异步请求）
│   └── config.py           # 配置文件（系统提示词）
├── ui/                     # 用户界面层
│   ├── __init__.py
│   ├── chat_window.py      # 主聊天窗口
│   ├── message_bubble.py   # 消息气泡组件
│   ├── markdown_message.py # Markdown 渲染组件
│   ├── chat_input.py       # 输入框组件
│   └── chat_input_bar.py   # 输入栏组件
└── resources/              # 资源文件
    └── themes/             # 主题样式
        ├── dark.qss        # 深色主题
        └── light.qss       # 浅色主题
```

## 🎨 主题定制

### 修改颜色

编辑 `modules/ai_assistant/resources/themes/dark.qss` 或 `light.qss`:

```css
/* 用户消息气泡 */
QFrame#user_message {
    background-color: #2a6f3f;  /* 修改这里 */
}

/* AI 消息气泡 */
QFrame#ai_message {
    background-color: #444654;  /* 修改这里 */
}
```

## 💡 技术细节

### 异步架构

```
用户输入
   ↓
APIClient (QThread)
   ↓ 发送信号
ChatWindow
   ↓ 更新UI
StreamingBubble (流式显示)
```

### 流式输出原理

1. API 请求启用 `stream=True`
2. 服务器逐块返回数据
3. `APIClient` 接收每个数据块
4. 发出 `chunk_received` 信号
5. UI 实时追加显示内容

### 消息格式

```python
{
    "role": "user",      # 或 "assistant" 或 "system"
    "content": "消息内容"
}
```

## 🐛 常见问题

### Q: API 请求失败？

**A**: 检查以下几点：
1. 网络连接是否正常
2. API Key 是否有效
3. API URL 是否正确
4. 是否有防火墙阻止

### Q: 主题样式不生效？

**A**: 确保 `resources/themes/` 文件夹存在，且包含 `dark.qss` 和 `light.qss`

### Q: 流式输出卡顿？

**A**: 
1. 检查网络速度
2. 尝试切换模型
3. 减小 temperature 参数

### Q: Markdown 不渲染？

**A**: 当前支持基础 Markdown：
- ✅ 粗体、代码、代码块
- ❌ 图片、表格等复杂格式暂不支持

## 📊 性能特点

- ✅ 异步 API 请求，UI 不卡顿
- ✅ 流式输出，减少等待时间
- ✅ 模块化设计，易于维护
- ✅ 独立主题文件，易于定制

## 🔐 安全提示

1. ⚠️ 妥善保管 API Key，不要提交到代码仓库
2. ⚠️ 不要在对话中分享敏感信息
3. ⚠️ 定期检查 API 使用量
4. ⚠️ 注意保护个人隐私

## 📝 版本历史

### v1.0.0 (2025-11-03)
- ✅ 初始版本
- ✅ 集成到 UE Toolkit 模块系统
- ✅ 支持流式输出
- ✅ 支持主题切换
- ✅ 支持 Markdown 渲染

## 🙏 致谢

- OpenAI-HK 提供 API 接口
- PyQt6 提供强大的 GUI 框架
- ChatGPT 官方界面设计灵感

---

**作者**: AI Assistant  
**更新日期**: 2025-11-03

享受与 AI 的优雅对话！ 🎉

