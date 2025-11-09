# 代码清理报告

生成时间: 2025-11-09 23:50:04
分析耗时: 2.07 秒

## 统计摘要

- 扫描文件数: 150
- 发现问题数: 399
- 预计可删除代码行数: 685

### 按类别统计

| 类别 | 数量 |
| ---- | ---- |
| 未使用导入 | 131 |
| 未使用变量 | 131 |
| 未使用文件 | 137 |

### 按严重程度统计

| 严重程度 | 数量 |
| -------- | ---- |
| 低 | 262 |
| 高 | 137 |

## 详细问题列表

### 未使用导入 (131)

#### 1. 未使用的导入: os

**文件**: `main.py`
**行号**: 8
**严重程度**: 低

**建议**: 删除第 8 行的导入语句

---

#### 2. 未使用的导入: Qt

**文件**: `main.py`
**行号**: 17
**严重程度**: 低

**建议**: 删除第 17 行的导入语句

---

#### 3. 未使用的导入: Optional

**文件**: `core\base_logic.py`
**行号**: 15
**严重程度**: 低

**建议**: 删除第 15 行的导入语句

---

#### 4. 未使用的导入: Path

**文件**: `core\logger.py`
**行号**: 6
**严重程度**: 低

**建议**: 删除第 6 行的导入语句

---

#### 5. 未使用的导入: logging

**文件**: `core\module_manager.py`
**行号**: 5
**严重程度**: 低

**建议**: 删除第 5 行的导入语句

---

#### 6. 未使用的导入: sys

**文件**: `core\single_instance.py`
**行号**: 8
**严重程度**: 低

**建议**: 删除第 8 行的导入语句

---

#### 7. 未使用的导入: QMessageBox

**文件**: `core\single_instance.py`
**行号**: 11
**严重程度**: 低

**建议**: 删除第 11 行的导入语句

---

#### 8. 未使用的导入: shutil

**文件**: `core\config\config_backup.py`
**行号**: 9
**严重程度**: 低

**建议**: 删除第 9 行的导入语句

---

#### 9. 未使用的导入: StyleLoader

**文件**: `core\utils\theme_manager.py`
**行号**: 18
**严重程度**: 低

**建议**: 删除第 18 行的导入语句

---

#### 10. 未使用的导入: logging

**文件**: `core\utils\ue_process_utils.py`
**行号**: 5
**严重程度**: 低

**建议**: 删除第 5 行的导入语句

---

*还有 121 个问题未显示...*

### 未使用变量 (131)

#### 1. 未使用的变量: logger

**文件**: `core\base_logic.py`
**行号**: 21
**严重程度**: 低

**建议**: 删除第 21 行的变量定义，或重命名为 _logger

---

#### 2. 未使用的变量: CURRENT_CONFIG_VERSION

**文件**: `core\base_logic.py`
**行号**: 65
**严重程度**: 低

**建议**: 删除第 65 行的变量定义，或重命名为 _CURRENT_CONFIG_VERSION

---

#### 3. 未使用的变量: DISCOVERED

**文件**: `core\module_manager.py`
**行号**: 19
**严重程度**: 低

**建议**: 删除第 19 行的变量定义，或重命名为 _DISCOVERED

---

#### 4. 未使用的变量: LOADED

**文件**: `core\module_manager.py`
**行号**: 20
**严重程度**: 低

**建议**: 删除第 20 行的变量定义，或重命名为 _LOADED

---

#### 5. 未使用的变量: INITIALIZED

**文件**: `core\module_manager.py`
**行号**: 21
**严重程度**: 低

**建议**: 删除第 21 行的变量定义，或重命名为 _INITIALIZED

---

#### 6. 未使用的变量: UNLOADED

**文件**: `core\module_manager.py`
**行号**: 22
**严重程度**: 低

**建议**: 删除第 22 行的变量定义，或重命名为 _UNLOADED

---

#### 7. 未使用的变量: ERROR

**文件**: `core\module_manager.py`
**行号**: 23
**严重程度**: 低

**建议**: 删除第 23 行的变量定义，或重命名为 _ERROR

---

#### 8. 未使用的变量: DANGEROUS_PATTERNS

**文件**: `core\utils\file_utils.py`
**行号**: 33
**严重程度**: 低

**建议**: 删除第 33 行的变量定义，或重命名为 _DANGEROUS_PATTERNS

---

#### 9. 未使用的变量: DANGEROUS_NAMES

**文件**: `core\utils\file_utils.py`
**行号**: 39
**严重程度**: 低

**建议**: 删除第 39 行的变量定义，或重命名为 _DANGEROUS_NAMES

---

#### 10. 未使用的变量: DARK

**文件**: `core\utils\theme_manager.py`
**行号**: 26
**严重程度**: 低

**建议**: 删除第 26 行的变量定义，或重命名为 _DARK

---

*还有 121 个问题未显示...*

### 未使用文件 (137)

#### 1. 未使用的文件: base_logic.py

**文件**: `core\base_logic.py`
**行号**: 1
**严重程度**: 高

**建议**: 考虑删除文件 core\base_logic.py

---

#### 2. 未使用的文件: embedding_service.py

**文件**: `core\ai_services\embedding_service.py`
**行号**: 1
**严重程度**: 高

**建议**: 考虑删除文件 core\ai_services\embedding_service.py

---

#### 3. 未使用的文件: config_backup.py

**文件**: `core\config\config_backup.py`
**行号**: 1
**严重程度**: 高

**建议**: 考虑删除文件 core\config\config_backup.py

---

#### 4. 未使用的文件: config_validator.py

**文件**: `core\config\config_validator.py`
**行号**: 1
**严重程度**: 高

**建议**: 考虑删除文件 core\config\config_validator.py

---

#### 5. 未使用的文件: custom_widgets.py

**文件**: `core\utils\custom_widgets.py`
**行号**: 1
**严重程度**: 高

**建议**: 考虑删除文件 core\utils\custom_widgets.py

---

#### 6. 未使用的文件: error_handler.py

**文件**: `core\utils\error_handler.py`
**行号**: 1
**严重程度**: 高

**建议**: 考虑删除文件 core\utils\error_handler.py

---

#### 7. 未使用的文件: file_utils.py

**文件**: `core\utils\file_utils.py`
**行号**: 1
**严重程度**: 高

**建议**: 考虑删除文件 core\utils\file_utils.py

---

#### 8. 未使用的文件: lru_cache.py

**文件**: `core\utils\lru_cache.py`
**行号**: 1
**严重程度**: 高

**建议**: 考虑删除文件 core\utils\lru_cache.py

---

#### 9. 未使用的文件: performance_monitor.py

**文件**: `core\utils\performance_monitor.py`
**行号**: 1
**严重程度**: 高

**建议**: 考虑删除文件 core\utils\performance_monitor.py

---

#### 10. 未使用的文件: thread_cleanup.py

**文件**: `core\utils\thread_cleanup.py`
**行号**: 1
**严重程度**: 高

**建议**: 考虑删除文件 core\utils\thread_cleanup.py

---

*还有 127 个问题未显示...*

## 建议操作

1. **优先处理高严重程度问题** - 这些问题可能影响代码质量
2. **审查废弃代码** - 确认是否可以安全删除
3. **清理未使用导入** - 可以自动清理
4. **人工审查公共 API 相关问题** - 避免破坏外部依赖

