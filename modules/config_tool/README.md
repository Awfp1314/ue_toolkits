# ⚙️ Config Tool - 配置工具

> UE 项目配置文件的模板化管理工具

---

## 功能概述

Config Tool 帮助你轻松管理多个 UE 项目的配置文件，支持配置模板的保存、应用和对比。

### ✨ 核心功能

- ✅ 读取 UE 项目配置文件（.ini）
- ✅ 保存配置为模板
- ✅ 一键应用模板到项目
- ✅ 管理多个 UE 项目
- ✅ 配置对比
- ✅ 批量操作

---

## 支持的配置文件

- `DefaultEngine.ini` - 引擎配置
- `DefaultGame.ini` - 游戏配置
- `DefaultInput.ini` - 输入配置
- `DefaultEditor.ini` - 编辑器配置
- 以及所有其他 `.ini` 配置文件

---

## 快速开始

### 1. 创建配置模板

1. 点击"创建模板"
2. 选择 UE 项目的 Config 目录
3. 输入模板名称和描述
4. 选择要包含的配置文件
5. 保存模板

### 2. 应用模板

1. 添加 UE 项目
2. 选择要应用的模板
3. 点击"应用到项目"
4. 确认操作

### 3. 管理项目

- 添加/删除项目
- 查看项目配置
- 批量应用模板

---

## 文件结构

```
config_tool/
├── __init__.py
├── __main__.py
├── manifest.json
│
├── logic/
│   └── config_tool_logic.py        # 核心逻辑 ⭐
│
└── ui/
    ├── config_tool_ui.py            # 主界面
    ├── config_tool_ui_core.py       # 核心 UI
    │
    ├── components/                  # UI 组件
    │   ├── config_item_widget.py
    │   ├── project_card.py
    │   ├── template_card.py
    │   └── tree_builder.py
    │
    ├── dialogs/                     # 对话框
    │   ├── add_project_dialog.py
    │   ├── apply_template_dialog.py
    │   ├── create_template_dialog.py
    │   ├── edit_template_dialog.py
    │   └── select_config_dialog.py
    │
    ├── handlers/                    # 事件处理
    │   └── config_handler.py
    │
    └── layouts/                     # 布局
        └── layout_builder.py
```

---

## 核心功能

### 1. 配置模板管理

**创建模板**:
```python
template_data = {
    "name": "Forward Rendering 模板",
    "description": "适用于移动端的前向渲染配置",
    "config_path": "D:/MyProject/Config"
}
logic.create_template(template_data)
```

**编辑模板**:
```python
logic.update_template(template_id, {
    "description": "更新后的描述"
})
```

**删除模板**:
```python
logic.delete_template(template_id)
```

---

### 2. 项目管理

**添加项目**:
```python
project_data = {
    "name": "我的游戏",
    "path": "D:/Projects/MyGame",
    "version": "5.3"
}
logic.add_project(project_data)
```

**获取所有项目**:
```python
projects = logic.get_projects()
for project in projects:
    print(f"{project.name} - {project.path}")
```

---

### 3. 应用配置

**应用模板到项目**:
```python
logic.apply_template(
    template_id="template_123",
    project_path="D:/Projects/MyGame"
)
```

**批量应用**:
```python
for project in projects:
    logic.apply_template(template_id, project.path)
```

---

## 数据模型

### ConfigTemplate - 配置模板

```python
class ConfigTemplate:
    id: str                    # 唯一标识
    name: str                  # 模板名称
    description: str           # 描述
    path: Path                 # 配置文件路径
    created_at: datetime       # 创建时间
    last_modified: datetime    # 最后修改时间
    projects: int              # 应用的项目数
```

### Project - UE 项目

```python
class Project:
    id: str                    # 唯一标识
    name: str                  # 项目名称
    path: Path                 # 项目路径
    version: str               # UE 版本
    last_template: str         # 最后应用的模板
    last_updated: datetime     # 最后更新时间
```

---

## 使用示例

### 示例 1: 批量配置多个项目

```python
# 创建模板
template = logic.create_template({
    "name": "移动端优化配置",
    "config_path": "D:/Templates/Mobile"
})

# 应用到所有项目
projects = logic.get_projects()
for project in projects:
    logic.apply_template(template.id, project.path)
    print(f"已应用到: {project.name}")
```

### 示例 2: 对比配置差异

```python
# 获取两个模板
template1 = logic.get_template("template_1")
template2 = logic.get_template("template_2")

# 对比配置
diff = logic.compare_templates(template1.id, template2.id)
print(f"差异项: {len(diff)}")
```

---

## API 参考

### ConfigToolLogic

| 方法 | 说明 |
|------|------|
| `create_template(data)` | 创建配置模板 |
| `update_template(id, data)` | 更新模板 |
| `delete_template(id)` | 删除模板 |
| `get_template(id)` | 获取模板详情 |
| `get_templates()` | 获取所有模板 |
| `add_project(data)` | 添加项目 |
| `remove_project(id)` | 删除项目 |
| `get_projects()` | 获取所有项目 |
| `apply_template(template_id, project_path)` | 应用模板 |
| `compare_templates(id1, id2)` | 对比模板 |

---

## 配置存储

### 模板存储位置

**Windows**: `%LOCALAPPDATA%\UE_Toolkit\config_templates\`
**macOS**: `~/Library/Application Support/UE_Toolkit/config_templates/`
**Linux**: `~/.local/share/UE_Toolkit/config_templates/`

### 数据文件

- `templates.json` - 模板元数据
- `projects.json` - 项目列表
- `{template_id}/` - 模板配置文件

---

## 最佳实践

### 1. 模板命名

- ✅ 使用描述性名称（如"移动端优化配置"）
- ✅ 包含适用场景（如"Forward Rendering"）
- ❌ 避免使用"模板1"、"测试"等

### 2. 项目管理

- ✅ 定期更新项目列表
- ✅ 记录每次配置变更
- ✅ 备份重要配置

### 3. 批量操作

- ✅ 应用前先备份
- ✅ 分批应用，验证效果
- ✅ 记录应用日志

---

## 故障排查

### 模板无法应用

**可能原因**:
1. 项目路径不存在
2. 配置文件被锁定
3. 权限不足

**解决方案**:
- 验证项目路径
- 关闭 UE 编辑器
- 以管理员身份运行

### 配置丢失

**可能原因**:
- 模板目录被删除

**解决方案**:
- 从备份恢复
- 重新创建模板

---

**维护者**: Config Tool Team  
**最后更新**: 2025-11-04

