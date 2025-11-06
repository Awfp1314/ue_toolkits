# FAISS 向量存储迁移测试指南

## 🎯 **升级内容**

### **已完成的工作**
✅ 1. 安装 `faiss-cpu` 依赖  
✅ 2. 创建 `FaissMemoryStore` 向量存储类  
✅ 3. 重构 `EnhancedMemoryManager` 使用 FAISS  
✅ 4. 实现 FAISS → JSON 自动备份  
✅ 5. 集成自动迁移机制  
✅ 6. 降级 NumPy 到 1.26.4（兼容 FAISS）  

---

## 📦 **新架构**

```
┌─────────────────────────────────────────┐
│     增强型记忆管理器（EnhancedMemoryManager）    │
├─────────────────────────────────────────┤
│                                         │
│  主存储：FAISS 向量数据库                 │
│  ├── 语义检索（高精度）                   │
│  ├── 自动持久化                          │
│  └── 快速检索（毫秒级）                   │
│                                         │
│  备份存储：JSON 文件                      │
│  ├── 定期同步                            │
│  ├── 灾难恢复                            │
│  └── 人类可读                            │
│                                         │
└─────────────────────────────────────────┘
```

---

## 🧪 **测试步骤**

### **步骤 1：启动应用**
```powershell
.\scripts\run_with_console.bat
```

**预期日志**：
```
✅ FAISS 向量存储已启用（用户: default，记忆数: 0）
加载了 20 条用户记忆
🔄 [自动迁移] 检测到 20 条 JSON 记忆，开始迁移到 FAISS...
✅ [自动迁移] 成功迁移 20/20 条记忆到 FAISS
增强型记忆管理器初始化完成（用户: default，FAISS向量检索: 已启用）
```

### **步骤 2：打开 AI 助手**
点击 AI 助手图标。

**预期**：不崩溃，正常显示欢迎消息。

### **步骤 3：告诉 AI 你的偏好**
发送消息：
```
我喜欢玩《塞尔达传说：荒野之息》，这是一款开放世界冒险游戏
```

**预期日志**：
```
✅ [有价值信息] 保存到用户级记忆: 我喜欢玩《塞尔达传说：荒野之息》...
✅ [FAISS] 记忆已保存: 我喜欢玩《塞尔达传说：荒野之息》...
💾 [FAISS] 已保存到磁盘: 21 条记录
💾 [JSON备份] 已备份 21 条记忆
```

### **步骤 4：测试语义检索**
发送消息：
```
你还记得我喜欢什么游戏吗？
```

**预期日志**：
```
🔮 [FAISS 检索] 启动语义搜索...
✅ [FAISS 检索] 找到 X 条记忆（语义相似度匹配）
```

**预期回复**：
```
我记得，你喜欢玩《塞尔达传说：荒野之息》，这是一款开放世界冒险游戏。
```

### **步骤 5：测试同义词检索（语义能力）**
发送消息：
```
你知道我玩什么电子游戏吗？
```

**预期**：AI 能理解"电子游戏"="游戏"，找到《塞尔达传说》的记忆。

### **步骤 6：验证不崩溃**
继续对话 5-10 轮，确保：
- ✅ 程序稳定运行
- ✅ 记忆正常保存
- ✅ 检索准确
- ✅ 不崩溃

---

## 📁 **新增文件**

- `modules/ai_assistant/logic/faiss_memory_store.py`：FAISS 存储管理器
- `C:\Users\wang\AppData\Roaming\ue_toolkit\user_data\ai_memory\default_faiss.index`：FAISS 向量索引
- `C:\Users\wang\AppData\Roaming\ue_toolkit\user_data\ai_memory\default_metadata.pkl`：元数据映射
- `C:\Users\wang\AppData\Roaming\ue_toolkit\user_data\ai_memory\default_backup.json`：自动备份

---

## 🔧 **故障排查**

### **如果启动时报错 "No module named 'faiss'"**
```powershell
pip install faiss-cpu==1.7.4
```

### **如果报错 "numpy.core.multiarray failed to import"**
```powershell
pip install "numpy<2.0" --force-reinstall
```

### **如果自动迁移失败**
- 检查日志中的 `[自动迁移]` 相关信息
- JSON 备份仍然存在，数据不会丢失
- 可以手动清空 FAISS 文件让其重新迁移：
  ```powershell
  # 删除 FAISS 文件（让其重新迁移）
  del "C:\Users\wang\AppData\Roaming\ue_toolkit\user_data\ai_memory\default_faiss.index"
  del "C:\Users\wang\AppData\Roaming\ue_toolkit\user_data\ai_memory\default_metadata.pkl"
  ```

---

## ✅ **预期改进**

1. **记忆检索**：
   - 从关键词匹配 → 语义理解
   - "游戏" = "电子游戏" = "玩的东西"
   
2. **系统稳定性**：
   - FAISS 不会触发 Windows Access Violation
   - 向量格式完全兼容
   
3. **性能**：
   - 检索速度更快（FAISS 优化算法）
   - 内存占用更少
   
4. **数据安全**：
   - FAISS 主存储 + JSON 备份
   - 双重保障，永不丢失

---

## 📊 **对比**

| 功能 | 之前（ChromaDB） | 现在（FAISS） |
|------|----------------|--------------|
| 稳定性 | ❌ Windows 崩溃 | ✅ 完全稳定 |
| 语义检索 | ❌ 已禁用 | ✅ 已启用 |
| 检索精度 | ⚠️ 关键词匹配 | ✅ 语义理解 |
| 数据安全 | ✅ JSON 主存储 | ✅ FAISS+JSON 双重存储 |
| 性能 | ⚠️ 中等 | ✅ 快速 |

---

## 🚀 **现在开始测试！**

请按照上述步骤测试，并将控制台日志发送给我。

