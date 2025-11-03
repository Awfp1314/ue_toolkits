# 📦 Asset Manager - 资产管理器

> 虚幻引擎资产的导入、分类、管理工具

---

## 功能概述

Asset Manager 是 UE Toolkit 的核心模块之一，提供完整的资产管理解决方案。

### ✨ 主要功能

- ✅ 资产导入（文件/文件夹）
- ✅ 自动分类管理
- ✅ 缩略图生成和显示
- ✅ 资产搜索和筛选
- ✅ 批量操作
- ✅ 资产详情编辑
- ✅ 拖拽导入

---

## 快速开始

### 首次使用

1. **设置资产库路径**
   - 首次启动会弹出路径设置对话框
   - 选择一个目录作为资产库根目录
   - 所有导入的资产会保存在此目录下

2. **导入资产**
   - 点击"添加资产"按钮
   - 选择文件或文件夹
   - 选择分类
   - 完成导入

3. **浏览资产**
   - 使用分类筛选
   - 使用搜索功能
   - 点击资产卡片查看详情

---

## 文件结构

```
asset_manager/
├── __init__.py
├── asset_manager.py                # 模块主类
├── manifest.json                   # 模块配置
├── config_template.json            # 配置模板
│
├── logic/                          # 业务逻辑层
│   ├── asset_manager_logic.py      # 核心逻辑 ⭐
│   ├── asset_model.py              # 资产数据模型
│   └── thumbnail_generator.py      # 缩略图生成
│
└── ui/                             # 用户界面层
    ├── asset_manager_ui.py         # 主界面
    ├── asset_card.py               # 资产卡片
    ├── add_asset_dialog.py         # 添加资产对话框
    ├── edit_asset_dialog.py        # 编辑资产对话框
    ├── first_launch_dialog.py      # 首次启动对话框
    ├── set_paths_dialog.py         # 路径设置对话框
    ├── category_management_dialog.py  # 分类管理
    ├── confirm_delete_category_dialog.py
    ├── dialogs.py                  # 其他对话框
    ├── custom_checkbox.py          # 自定义复选框
    └── progress_dialog.py          # 进度对话框
```

---

## 核心组件

### 1. AssetManagerLogic - 核心逻辑

**文件**: `logic/asset_manager_logic.py`

**职责**:
- 资产的增删改查
- 分类管理
- 资产库路径管理
- 数据持久化

**关键方法**:
```python
class AssetManagerLogic:
    # 资产操作
    def add_asset(self, asset_data: dict) -> Asset
    def remove_asset(self, asset_id: str) -> bool
    def update_asset(self, asset_id: str, data: dict) -> bool
    def get_asset(self, asset_id: str) -> Asset
    def get_all_assets(self) -> List[Asset]
    
    # 搜索和筛选
    def search_assets(self, keyword: str) -> List[Asset]
    def filter_by_category(self, category: str) -> List[Asset]
    
    # 分类管理
    def get_categories(self) -> List[str]
    def add_category(self, name: str) -> bool
    def remove_category(self, name: str) -> bool
    
    # 路径管理
    def set_asset_library_path(self, path: str) -> bool
    def get_asset_library_path(self) -> str
```

---

### 2. Asset - 资产数据模型

**文件**: `logic/asset_model.py`

**数据结构**:
```python
class Asset:
    id: str                    # 唯一标识
    name: str                  # 资产名称
    category: str              # 分类
    asset_type: AssetType      # 类型（文件/文件夹）
    path: Path                 # 文件路径
    thumbnail_path: Path       # 缩略图路径
    description: str           # 描述
    tags: List[str]            # 标签
    size: int                  # 大小（字节）
    created_at: datetime       # 创建时间
    updated_at: datetime       # 更新时间
```

**枚举类型**:
```python
class AssetType(Enum):
    FILE = "file"              # 单个文件
    DIRECTORY = "directory"    # 文件夹
```

---

### 3. ThumbnailGenerator - 缩略图生成

**文件**: `logic/thumbnail_generator.py`

**功能**:
- 生成图片缩略图
- 生成视频第一帧
- 生成文件类型图标

**使用示例**:
```python
from .thumbnail_generator import ThumbnailGenerator

generator = ThumbnailGenerator()
thumbnail_path = generator.generate(file_path, output_dir)
```

---

## 用户界面

### 主界面布局

```
┌────────────────────────────────────────────┐
│  搜索框  | [分类下拉]  | [+ 添加资产]     │
├────────────────────────────────────────────┤
│  ┌────┐  ┌────┐  ┌────┐  ┌────┐          │
│  │资产│  │资产│  │资产│  │资产│          │
│  │卡片│  │卡片│  │卡片│  │卡片│          │
│  └────┘  └────┘  └────┘  └────┘          │
│  ┌────┐  ┌────┐  ┌────┐  ┌────┐          │
│  │资产│  │资产│  │资产│  │资产│          │
│  │卡片│  │卡片│  │卡片│  │卡片│          │
│  └────┘  └────┘  └────┘  └────┘          │
└────────────────────────────────────────────┘
```

### 资产卡片

**组件**: `ui/asset_card.py`

**显示内容**:
- 缩略图
- 资产名称
- 分类标签
- 大小
- 操作按钮（编辑/删除）

---

## 数据存储

### 配置文件

**位置**: `{用户数据目录}/config/modules/asset_manager.json`

**内容**:
```json
{
  "asset_library_path": "D:/Assets",
  "default_category": "未分类",
  "auto_generate_thumbnail": true,
  "thumbnail_size": [256, 256]
}
```

### 资产数据

**位置**: `{asset_library_path}/.asset_db/`

**文件**:
- `assets.json` - 资产元数据
- `thumbnails/` - 缩略图目录

---

## 使用示例

### 通过代码添加资产

```python
# 获取资产管理器
asset_manager = module_manager.get_module("asset_manager")
logic = asset_manager.logic

# 添加资产
asset_data = {
    "name": "我的蓝图",
    "category": "Blueprints",
    "asset_type": "file",
    "source_path": "C:/MyBlueprint.uasset",
    "description": "这是一个蓝图资产"
}

asset = logic.add_asset(asset_data)
print(f"资产已添加: {asset.id}")
```

### 搜索资产

```python
# 搜索关键词
results = logic.search_assets("蓝图")

for asset in results:
    print(f"{asset.name} - {asset.category}")
```

### 按分类筛选

```python
# 获取所有材质资产
materials = logic.filter_by_category("Materials")

print(f"共有 {len(materials)} 个材质")
```

---

## API 参考

### AssetManagerLogic

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `add_asset(data)` | dict | Asset | 添加新资产 |
| `remove_asset(id)` | str | bool | 删除资产 |
| `update_asset(id, data)` | str, dict | bool | 更新资产 |
| `get_asset(id)` | str | Asset | 获取单个资产 |
| `get_all_assets()` | - | List[Asset] | 获取所有资产 |
| `search_assets(keyword)` | str | List[Asset] | 搜索资产 |
| `filter_by_category(cat)` | str | List[Asset] | 按分类筛选 |

---

## 配置选项

### 资产库设置

```python
# 设置资产库路径
logic.set_asset_library_path("D:/MyAssets")

# 获取当前路径
path = logic.get_asset_library_path()
```

### 缩略图设置

```python
# 配置缩略图大小
config = {
    "thumbnail_size": [512, 512],  # 更大的缩略图
    "thumbnail_quality": 90         # JPEG 质量
}
logic.update_config(config)
```

---

## 最佳实践

### 1. 资产组织

- ✅ 使用清晰的分类名称
- ✅ 添加描述性的标签
- ✅ 定期清理未使用的资产
- ✅ 使用有意义的资产名称

### 2. 性能优化

- ✅ 大型资产库启用缩略图缓存
- ✅ 使用筛选而非全量加载
- ✅ 定期压缩缩略图目录

### 3. 数据安全

- ✅ 定期备份资产数据库
- ✅ 不要手动修改 `.asset_db` 目录
- ✅ 保持资产库路径稳定

---

## 故障排查

### 资产无法导入

**可能原因**:
1. 文件权限问题
2. 磁盘空间不足
3. 路径包含特殊字符

**解决方案**:
- 检查文件权限
- 清理磁盘空间
- 使用英文路径

### 缩略图不显示

**可能原因**:
1. 缩略图生成失败
2. 缩略图文件丢失

**解决方案**:
- 重新生成缩略图
- 检查 thumbnails/ 目录

### 搜索结果不准确

**可能原因**:
- 索引未更新

**解决方案**:
- 重建搜索索引
- 重启应用

---

## 扩展开发

### 添加新的资产类型

```python
# 在 asset_model.py 中
class AssetType(Enum):
    FILE = "file"
    DIRECTORY = "directory"
    CUSTOM_TYPE = "custom"  # 新类型
```

### 自定义缩略图生成

```python
class CustomThumbnailGenerator(ThumbnailGenerator):
    def generate_for_custom_type(self, file_path):
        # 自定义生成逻辑
        pass
```

---

## 未来功能

- [ ] 资产标签系统
- [ ] 资产版本管理
- [ ] 云端同步
- [ ] 批量编辑
- [ ] 智能分类建议
- [ ] 资产使用统计

---

**维护者**: Asset Manager Team  
**最后更新**: 2025-11-04

