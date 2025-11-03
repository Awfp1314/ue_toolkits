# 🧪 Tests - 测试系统

> UE Toolkit 的单元测试和集成测试

---

## 概述

Tests 目录包含所有测试代码，使用 pytest 框架进行测试。

### 测试覆盖

- ✅ 核心系统测试
- ✅ 模块测试
- ✅ UI 组件测试
- ✅ 集成测试

---

## 文件结构

```
tests/
├── __init__.py
├── conftest.py                     # pytest 配置 ⭐
│
├── test_core/                      # 核心系统测试
│   ├── __init__.py
│   ├── test_config_validator.py    # 配置验证测试
│   └── test_module_manager.py      # 模块管理测试
│
├── test_modules/                   # 模块测试（待添加）
│   ├── test_ai_assistant.py
│   ├── test_asset_manager.py
│   └── test_config_tool.py
│
└── test_ui/                        # UI 测试（待添加）
    ├── test_main_window.py
    └── test_dialogs.py
```

---

## 快速开始

### 安装测试依赖

```bash
pip install pytest pytest-qt pytest-cov
```

### 运行所有测试

```bash
# 运行所有测试
pytest tests/

# 运行特定目录的测试
pytest tests/test_core/

# 运行特定文件的测试
pytest tests/test_core/test_config_validator.py

# 运行特定测试函数
pytest tests/test_core/test_config_validator.py::test_validate_config
```

### 查看测试覆盖率

```bash
pytest --cov=core --cov=modules tests/
```

---

## conftest.py 配置

**文件**: `conftest.py`

**内容示例**:
```python
import pytest
from PyQt6.QtWidgets import QApplication

@pytest.fixture(scope="session")
def qapp():
    """提供 QApplication 实例"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def config_manager():
    """提供 ConfigManager 实例"""
    from core.config.config_manager import ConfigManager
    return ConfigManager()

@pytest.fixture
def logger():
    """提供 Logger 实例"""
    from core.logger import get_logger
    return get_logger("test")
```

---

## 测试示例

### 测试核心功能

**文件**: `test_core/test_config_validator.py`

```python
import pytest
from core.config.config_validator import ConfigValidator

def test_validate_valid_config():
    """测试验证有效配置"""
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "number"}
        },
        "required": ["name"]
    }
    
    config = {
        "name": "Test",
        "age": 25
    }
    
    validator = ConfigValidator(schema)
    assert validator.validate(config) == True

def test_validate_invalid_config():
    """测试验证无效配置"""
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"}
        },
        "required": ["name"]
    }
    
    config = {}  # 缺少必需字段
    
    validator = ConfigValidator(schema)
    assert validator.validate(config) == False
```

---

### 测试模块功能

**文件**: `test_modules/test_asset_manager.py`

```python
import pytest
from modules.asset_manager.logic.asset_manager_logic import AssetManagerLogic

@pytest.fixture
def asset_logic(config_manager, logger):
    """创建 AssetManagerLogic 实例"""
    return AssetManagerLogic(config_manager, logger)

def test_add_asset(asset_logic):
    """测试添加资产"""
    asset_data = {
        "name": "Test Asset",
        "category": "Test",
        "asset_type": "file",
        "source_path": "/test/path.txt"
    }
    
    asset = asset_logic.add_asset(asset_data)
    assert asset is not None
    assert asset.name == "Test Asset"

def test_search_assets(asset_logic):
    """测试搜索资产"""
    # 添加测试数据
    asset_logic.add_asset({"name": "Blueprint1", "category": "Blueprints"})
    asset_logic.add_asset({"name": "Material1", "category": "Materials"})
    
    # 搜索
    results = asset_logic.search_assets("Blueprint")
    assert len(results) >= 1
    assert "Blueprint" in results[0].name
```

---

### 测试 UI 组件

**文件**: `test_ui/test_dialogs.py`

```python
import pytest
from PyQt6.QtWidgets import QDialog
from ui.dialogs.close_confirmation_dialog import CloseConfirmationDialog

def test_dialog_creation(qapp):
    """测试对话框创建"""
    dialog = CloseConfirmationDialog()
    assert isinstance(dialog, QDialog)
    assert dialog.windowTitle() != ""

def test_dialog_buttons(qapp, qtbot):
    """测试对话框按钮"""
    dialog = CloseConfirmationDialog()
    
    # 使用 qtbot 测试 UI 交互
    qtbot.addWidget(dialog)
    
    # 模拟点击按钮
    # qtbot.mouseClick(dialog.confirm_button, Qt.MouseButton.LeftButton)
    
    assert dialog is not None
```

---

## 测试最佳实践

### 1. 测试命名

```python
# ✅ 好 - 清晰描述测试内容
def test_validate_config_with_missing_required_field():
    pass

def test_add_asset_with_valid_data():
    pass

# ❌ 不好 - 命名不清晰
def test_1():
    pass

def test_config():
    pass
```

### 2. 使用 Fixture

```python
# ✅ 好 - 使用 fixture 减少重复
@pytest.fixture
def sample_asset():
    return {
        "name": "Test",
        "category": "Test"
    }

def test_function_1(sample_asset):
    # 使用 sample_asset
    pass

def test_function_2(sample_asset):
    # 复用 sample_asset
    pass
```

### 3. 测试组织

```python
class TestAssetManager:
    """资产管理器测试套件"""
    
    def test_add_asset(self):
        """测试添加资产"""
        pass
    
    def test_remove_asset(self):
        """测试删除资产"""
        pass
    
    def test_update_asset(self):
        """测试更新资产"""
        pass
```

### 4. 使用参数化测试

```python
@pytest.mark.parametrize("input,expected", [
    ("test", True),
    ("", False),
    (None, False),
])
def test_validate_input(input, expected):
    result = validate(input)
    assert result == expected
```

---

## pytest 常用选项

### 基本选项

```bash
# 显示详细输出
pytest -v

# 显示打印语句
pytest -s

# 只运行失败的测试
pytest --lf

# 停在第一个失败的测试
pytest -x

# 运行特定标记的测试
pytest -m "slow"
```

### 覆盖率选项

```bash
# 生成覆盖率报告
pytest --cov=core --cov=modules

# 生成 HTML 报告
pytest --cov=core --cov-report=html

# 显示未覆盖的代码
pytest --cov=core --cov-report=term-missing
```

---

## 测试标记

### 定义标记

```python
import pytest

@pytest.mark.slow
def test_long_running_operation():
    """慢速测试"""
    pass

@pytest.mark.integration
def test_integration():
    """集成测试"""
    pass

@pytest.mark.skip(reason="功能未实现")
def test_future_feature():
    """跳过测试"""
    pass

@pytest.mark.skipif(sys.platform == "win32", reason="Windows 不支持")
def test_linux_only():
    """条件跳过"""
    pass
```

### 运行标记的测试

```bash
# 只运行慢速测试
pytest -m slow

# 排除慢速测试
pytest -m "not slow"

# 运行多个标记
pytest -m "slow or integration"
```

---

## Mock 和 Patch

### 使用 Mock

```python
from unittest.mock import Mock, patch

def test_with_mock():
    """使用 mock 对象"""
    mock_logger = Mock()
    
    # 调用被测试的函数
    some_function(mock_logger)
    
    # 验证调用
    mock_logger.info.assert_called_once()

@patch('core.logger.get_logger')
def test_with_patch(mock_get_logger):
    """使用 patch 替换函数"""
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger
    
    # 测试代码
    pass
```

---

## 测试 Qt 应用

### 使用 pytest-qt

```python
def test_button_click(qtbot):
    """测试按钮点击"""
    from PyQt6.QtWidgets import QPushButton
    
    button = QPushButton("Click Me")
    
    # 添加到 qtbot
    qtbot.addWidget(button)
    
    # 模拟点击
    with qtbot.waitSignal(button.clicked, timeout=1000):
        qtbot.mouseClick(button, Qt.MouseButton.LeftButton)
```

---

## 持续集成

### GitHub Actions 示例

**文件**: `.github/workflows/test.yml`

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-qt pytest-cov
    
    - name: Run tests
      run: pytest --cov=core --cov=modules tests/
    
    - name: Upload coverage
      run: bash <(curl -s https://codecov.io/bash)
```

---

## 测试覆盖率目标

| 组件 | 目标覆盖率 | 当前状态 |
|------|-----------|---------|
| core/ | 80%+ | 🟡 进行中 |
| modules/ | 70%+ | 🟡 进行中 |
| ui/ | 60%+ | 🔴 待开始 |

---

## 调试测试

### 在测试中使用断点

```python
def test_something():
    import pdb; pdb.set_trace()  # 设置断点
    # 测试代码
    pass
```

### 使用 pytest 调试

```bash
# 在失败时进入调试器
pytest --pdb

# 在第一个测试开始时进入调试器
pytest --trace
```

---

## 常见问题

### Q: 如何测试异步代码？
A: 使用 pytest-asyncio

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected
```

### Q: 如何测试数据库操作？
A: 使用测试数据库或 mock

```python
@pytest.fixture
def test_db():
    # 创建测试数据库
    db = create_test_database()
    yield db
    # 清理
    db.drop()
```

### Q: 如何测试文件操作？
A: 使用 tmp_path fixture

```python
def test_file_operation(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    assert test_file.read_text() == "test content"
```

---

## 贡献测试

### 编写新测试

1. 在相应目录创建测试文件
2. 遵循命名约定 `test_*.py`
3. 编写测试函数 `test_*()`
4. 运行测试确保通过
5. 提交代码

### 测试检查清单

- [ ] 测试覆盖主要功能
- [ ] 测试边界条件
- [ ] 测试错误处理
- [ ] 使用有意义的测试名称
- [ ] 添加必要的注释
- [ ] 所有测试通过

---

**维护者**: Testing Team  
**最后更新**: 2025-11-04

