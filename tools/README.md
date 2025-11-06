# Tools 工具脚本

本目录包含用于维护、调试和管理应用程序的辅助工具脚本。

## 📁 目录结构

```
tools/
├── __init__.py
├── clean_faiss_memory.py     # 清理 FAISS 记忆
├── clean_memory_now.py       # 立即清理记忆
├── fix_ai_config.py          # 修复 AI 配置
├── show_faiss_location.py    # 显示 FAISS 位置
└── verify_faiss.py           # 验证 FAISS 状态
```

## 🛠️ 工具说明

### 1. `clean_faiss_memory.py` - 清理 FAISS 记忆

清理 AI 助手的 FAISS 向量记忆数据库。

**功能**:
- 清空 FAISS 索引
- 删除记忆元数据
- 重置记忆系统
- 可选备份旧数据

**使用方法**:

```bash
# 清理所有记忆
python tools/clean_faiss_memory.py

# 清理并备份
python tools/clean_faiss_memory.py --backup

# 仅清理特定用户的记忆
python tools/clean_faiss_memory.py --user default
```

**参数说明**:
- `--backup` - 在清理前创建备份
- `--user USER` - 指定用户名（默认: default）
- `--force` - 跳过确认直接清理

**注意事项**:
- ⚠️ 清理操作不可逆（除非有备份）
- 建议先备份重要记忆
- 清理后需重启应用

---

### 2. `clean_memory_now.py` - 立即清理记忆

快速清理内存中的临时记忆数据。

**功能**:
- 清理会话级记忆
- 清理上下文记忆
- 保留用户级记忆（可选）
- 释放内存

**使用方法**:

```bash
# 清理会话和上下文记忆
python tools/clean_memory_now.py

# 清理所有记忆（包括用户级）
python tools/clean_memory_now.py --all

# 仅清理上下文记忆
python tools/clean_memory_now.py --context-only
```

**参数说明**:
- `--all` - 清理所有级别的记忆
- `--context-only` - 仅清理上下文记忆
- `--session-only` - 仅清理会话记忆

**使用场景**:
- 记忆占用过多内存
- 对话出现混乱
- 需要"遗忘"特定对话

---

### 3. `fix_ai_config.py` - 修复 AI 配置

修复损坏或不完整的 AI 助手配置文件。

**功能**:
- 检测配置文件错误
- 修复 JSON 格式问题
- 恢复默认配置
- 合并缺失字段

**使用方法**:

```bash
# 自动修复配置
python tools/fix_ai_config.py

# 重置为默认配置
python tools/fix_ai_config.py --reset

# 验证配置（不修改）
python tools/fix_ai_config.py --check-only
```

**参数说明**:
- `--reset` - 重置为默认配置
- `--check-only` - 仅检查不修复
- `--backup` - 修复前创建备份

**修复项目**:
- JSON 语法错误
- 缺失必需字段
- 无效的参数值
- 版本不兼容

---

### 4. `show_faiss_location.py` - 显示 FAISS 位置

显示 FAISS 向量数据库文件的存储位置。

**功能**:
- 显示 FAISS 索引文件路径
- 显示元数据文件路径
- 显示文件大小和记录数
- 检查文件完整性

**使用方法**:

```bash
# 显示 FAISS 位置信息
python tools/show_faiss_location.py

# 显示详细信息
python tools/show_faiss_location.py --verbose

# 检查文件完整性
python tools/show_faiss_location.py --check
```

**参数说明**:
- `--verbose` - 显示详细信息
- `--check` - 检查文件完整性
- `--user USER` - 指定用户名

**输出示例**:

```
FAISS 向量数据库位置:
  索引文件: C:\Users\wang\AppData\Roaming\ue_toolkit\user_data\memory\default\faiss_index.bin
  元数据文件: C:\Users\wang\AppData\Roaming\ue_toolkit\user_data\memory\default\faiss_metadata.json
  文件大小: 2.3 MB
  记录数: 10 条
  状态: ✓ 正常
```

---

### 5. `verify_faiss.py` - 验证 FAISS 状态

验证 FAISS 向量数据库的完整性和可用性。

**功能**:
- 验证索引文件完整性
- 验证元数据一致性
- 测试向量检索功能
- 生成诊断报告

**使用方法**:

```bash
# 基本验证
python tools/verify_faiss.py

# 完整验证（包括性能测试）
python tools/verify_faiss.py --full

# 生成诊断报告
python tools/verify_faiss.py --report
```

**参数说明**:
- `--full` - 完整验证（包括性能测试）
- `--report` - 生成详细诊断报告
- `--user USER` - 指定用户名
- `--fix` - 尝试修复发现的问题

**验证项目**:
1. 文件存在性
2. 文件完整性（校验和）
3. 索引可加载性
4. 元数据一致性
5. 向量维度正确性
6. 检索功能可用性

**输出示例**:

```
FAISS 验证报告:
  ✓ 索引文件存在
  ✓ 元数据文件存在
  ✓ 文件完整性检查通过
  ✓ 索引可成功加载
  ✓ 记录数匹配 (10/10)
  ✓ 向量维度正确 (512)
  ✓ 检索功能正常

总体状态: ✓ 正常
```

---

## 📝 使用场景

### 场景 1: AI 记忆出现混乱

```bash
# 1. 备份现有记忆
python tools/clean_faiss_memory.py --backup

# 2. 清理记忆
python tools/clean_faiss_memory.py

# 3. 重启应用
```

### 场景 2: 配置文件损坏

```bash
# 1. 检查配置
python tools/fix_ai_config.py --check-only

# 2. 修复配置
python tools/fix_ai_config.py --backup

# 3. 验证修复结果
python tools/fix_ai_config.py --check-only
```

### 场景 3: FAISS 数据异常

```bash
# 1. 验证 FAISS 状态
python tools/verify_faiss.py --full

# 2. 查看 FAISS 位置
python tools/show_faiss_location.py --verbose

# 3. 如果有问题，尝试修复
python tools/verify_faiss.py --fix

# 4. 如果无法修复，清理重建
python tools/clean_faiss_memory.py --backup
```

### 场景 4: 内存占用过高

```bash
# 清理临时记忆
python tools/clean_memory_now.py --context-only

# 或清理所有非持久化记忆
python tools/clean_memory_now.py
```

## 🔧 开发新工具

### 工具脚本模板

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
工具名称

描述工具的功能和用途。
"""

import argparse
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.logger import get_logger

logger = get_logger(__name__)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='工具描述')
    parser.add_argument('--option', help='选项说明')
    args = parser.parse_args()
    
    try:
        # 实现工具逻辑
        logger.info("工具开始执行")
        
        # ... 你的代码 ...
        
        logger.info("工具执行完成")
        
    except Exception as e:
        logger.error(f"工具执行失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
```

### 工具开发规范

1. **命名规范**: 使用动词开头的描述性名称（如 `clean_`, `fix_`, `verify_`）
2. **文档**: 提供清晰的功能说明和使用示例
3. **参数**: 使用 `argparse` 处理命令行参数
4. **日志**: 使用 `core.logger` 记录日志
5. **错误处理**: 捕获并友好地处理异常
6. **退出码**: 使用标准退出码（0=成功，非0=失败）

## ⚠️ 注意事项

- **备份**: 执行破坏性操作前先备份
- **权限**: 某些工具可能需要管理员权限
- **应用状态**: 运行工具时关闭主应用
- **数据一致性**: 避免同时运行多个工具
- **日志**: 查看工具日志了解执行情况

## 🔗 相关文档

- [AI 助手架构](../modules/ai_assistant/README.md)
- [配置系统说明](../docs/configuration.md)
- [故障排查指南](../docs/troubleshooting.md)

