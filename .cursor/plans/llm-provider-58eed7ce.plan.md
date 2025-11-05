<!-- 58eed7ce-0e9b-4654-92ee-d13faf9bbefb 48bc6ea4-e279-41af-96df-414e3738ca45 -->
# LLM Provider 切换重构计划

## 架构设计

采用策略模式（Strategy Pattern）实现 LLM 供应商的无缝切换：

- 抽象接口：`BaseLLMClient`
- 具体策略：`ApiLLMClient`（封装现有 API）、`OllamaLLMClient`（新增）
- 工厂：`LLMClientFactory`（根据配置选择策略）

## 阶段 1：配置层

创建配置模板并迁移 API Key

文件：`modules/ai_assistant/config_template.json`（新建）

```json
{
  "_version": "1.0.0",
  "llm_provider": "api",
  "api_settings": {
    "api_url": "https://api.openai-hk.com/v1/chat/completions",
    "api_key": "hk-rf256210000027899536cbcb497417e8dfc70c2960229c22",
    "default_model": "gemini-2.5-flash",
    "temperature": 0.8,
    "timeout": 60
  },
  "ollama_settings": {
    "base_url": "http://localhost:11434",
    "model_name": "llama3",
    "stream": true,
    "timeout": 60
  }
}
```

## 阶段 2：抽象接口层

创建 LLM 客户端的抽象基类

文件：`modules/ai_assistant/clients/base_llm_client.py`（新建）

目录：`modules/ai_assistant/clients/__init__.py`（新建）

定义策略接口，所有客户端必须实现 `generate_response()` 方法。

## 阶段 3：API 客户端策略

封装现有 API 逻辑

文件：`modules/ai_assistant/clients/api_llm_client.py`（新建）

从 `api_client.py` 迁移核心逻辑：

- 迁移 HTTP 请求逻辑到 `generate_response()`
- 从配置读取 API URL、Key、Model
- 保持流式响应生成器接口
- 保留代理禁用逻辑

修改：`modules/ai_assistant/logic/api_client.py`

- 改为继承自 `BaseLLMClient` 并调用策略客户端
- 或直接被新的客户端替代（需保持 QThread 信号）

## 阶段 4：Ollama 客户端策略

实现本地 Ollama 支持

文件：`modules/ai_assistant/clients/ollama_llm_client.py`（新建）

使用 `httpx` 库实现：

- POST 到 `{base_url}/api/chat`
- 请求体：`{"model": "llama3", "messages": [...], "stream": true}`
- 流式解析：`httpx.stream()` 逐行读取 JSON
- 错误处理：连接失败、超时、模型不存在

依赖：添加 `httpx` 到 `requirements.txt`

## 阶段 5：工厂模式

创建客户端工厂

文件：`modules/ai_assistant/clients/llm_client_factory.py`（新建）

```python
def create_llm_client(config: Dict) -> BaseLLMClient:
    provider = config.get("llm_provider", "api")
    if provider == "ollama":
        return OllamaLLMClient(config["ollama_settings"])
    else:
        return ApiLLMClient(config["api_settings"])
```

## 阶段 6：集成到主逻辑

重构 `api_client.py` 使用工厂模式

文件：`modules/ai_assistant/logic/api_client.py`

修改 `APIClient.__init__()`:

- 接受 `config` 参数
- 调用工厂创建策略客户端
- 在 `run()` 中调用 `self.strategy.generate_response()`
- 将生成器输出通过信号发送到 UI

## 阶段 7：UI 配置界面

在主设置窗口添加 AI 助手配置标签页

文件：`ui/settings_widget.py`

添加新的 QGroupBox："AI 助手设置"

- QComboBox：LLM 供应商选择（API / Ollama）
- QLineEdit：API Key（仅 API 模式可见）
- QLineEdit：Ollama URL（仅 Ollama 模式可见）
- QLineEdit：Ollama 模型名称（仅 Ollama 模式可见）
- 保存/加载逻辑集成到现有的配置管理

## 关键文件

核心重构文件：

- `modules/ai_assistant/config_template.json`（新建）
- `modules/ai_assistant/clients/base_llm_client.py`（新建）
- `modules/ai_assistant/clients/api_llm_client.py`（新建）
- `modules/ai_assistant/clients/ollama_llm_client.py`（新建）
- `modules/ai_assistant/clients/llm_client_factory.py`（新建）
- `modules/ai_assistant/logic/api_client.py`（重构）
- `ui/settings_widget.py`（添加 UI）
- `requirements.txt`（添加 httpx）

### To-dos

- [ ] 创建 AI 助手配置模板并迁移 API Key
- [ ] 创建 BaseLLMClient 抽象基类
- [ ] 实现 ApiLLMClient 策略（封装现有逻辑）
- [ ] 实现 OllamaLLMClient 策略（使用 httpx）
- [ ] 创建 LLMClientFactory 工厂类
- [ ] 重构 APIClient 使用工厂模式
- [ ] 在主设置窗口添加 AI 助手配置界面
- [ ] 添加 httpx 依赖到 requirements.txt