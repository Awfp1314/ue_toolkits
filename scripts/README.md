# Scripts 构建和运行脚本

本目录包含用于构建、打包和运行应用程序的脚本文件。

## 📁 目录结构

```
scripts/
├── build.py                  # 开发环境构建脚本
├── build_release.py          # 发布版本打包脚本
├── run_with_console.bat      # 带控制台运行（Windows）
└── run_without_console.bat   # 无控制台运行（Windows）
```

## 🔨 构建脚本

### 1. `build.py` - 开发构建

用于开发环境的快速构建和测试。

**功能**:
- 检查 Python 环境
- 安装依赖包
- 生成资源文件
- 运行单元测试（可选）

**使用方法**:

```bash
# 基本构建
python scripts/build.py

# 带测试的构建
python scripts/build.py --test

# 清理构建文件
python scripts/build.py --clean
```

**参数说明**:
- `--test` - 运行单元测试
- `--clean` - 清理临时文件和缓存
- `--verbose` - 显示详细输出

---

### 2. `build_release.py` - 发布打包

用于生成最终的发布版本可执行文件。

**功能**:
- 使用 PyInstaller 打包应用
- 生成独立可执行文件
- 包含所有依赖和资源
- 压缩和优化
- 生成版本信息

**使用方法**:

```bash
# 打包应用
python scripts/build_release.py

# 指定输出目录
python scripts/build_release.py --output dist/

# 清理旧的构建
python scripts/build_release.py --clean
```

**参数说明**:
- `--output DIR` - 指定输出目录（默认: `release/`）
- `--clean` - 清理旧的构建文件
- `--onefile` - 打包为单个 exe 文件
- `--debug` - 包含调试信息
- `--icon PATH` - 指定应用图标

**打包配置**:

打包配置在 `ue_toolkit.spec` 文件中定义：

```python
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('resources', 'resources'),
        ('modules', 'modules'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
```

**输出结构**:

```
release/
├── ue_toolkit/               # 应用程序文件夹
│   ├── _internal/            # 依赖库和资源
│   └── ue_toolkit.exe        # 主程序
├── run_with_console.bat      # 带控制台启动
├── run_without_console.bat   # 无控制台启动
└── version_info.txt          # 版本信息
```

---

## 🚀 运行脚本 (Windows)

### 1. `run_with_console.bat` - 带控制台

启动应用并显示控制台窗口，用于查看日志和调试信息。

**功能**:
- 显示控制台窗口
- 实时输出日志
- 便于调试和问题排查

**使用方法**:

```batch
# 开发环境
python scripts\run_with_console.bat

# 发布版本
release\run_with_console.bat
```

**脚本内容**:

```batch
@echo off
cd /d "%~dp0"
python main.py
pause
```

---

### 2. `run_without_console.bat` - 无控制台

静默启动应用，不显示控制台窗口。

**功能**:
- 隐藏控制台窗口
- 正常生产环境启动
- 用户友好的启动方式

**使用方法**:

```batch
# 开发环境
python scripts\run_without_console.bat

# 发布版本
release\run_without_console.bat
```

**脚本内容**:

```batch
@echo off
cd /d "%~dp0"
pythonw main.py
```

---

## 🛠️ 开发工作流

### 日常开发

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行应用（带控制台）
python main.py

# 或使用脚本
python scripts/run_with_console.bat
```

### 测试构建

```bash
# 1. 运行开发构建
python scripts/build.py --test

# 2. 测试应用
python main.py
```

### 发布打包

```bash
# 1. 清理旧构建
python scripts/build_release.py --clean

# 2. 打包应用
python scripts/build_release.py

# 3. 测试打包结果
cd release/ue_toolkit
ue_toolkit.exe

# 4. 创建发布压缩包
# (手动或使用打包工具)
```

## 📦 依赖管理

### requirements.txt

项目依赖定义在 `requirements.txt` 中：

```
PyQt6>=6.5.0
requests>=2.31.0
markdown>=3.4.0
Pygments>=2.15.0
faiss-cpu>=1.7.4
sentence-transformers>=2.2.2
...
```

### 安装依赖

```bash
# 安装所有依赖
pip install -r requirements.txt

# 更新依赖
pip install --upgrade -r requirements.txt

# 安装特定版本
pip install PyQt6==6.5.0
```

### 生成依赖列表

```bash
# 导出当前环境依赖
pip freeze > requirements.txt

# 仅导出项目依赖（推荐使用 pipreqs）
pip install pipreqs
pipreqs . --force
```

## ⚙️ PyInstaller 配置

### ue_toolkit.spec

PyInstaller 配置文件，控制打包行为：

**关键配置项**:

- **`datas`** - 包含的数据文件和目录
- **`binaries`** - 包含的二进制文件
- **`hiddenimports`** - 隐式导入的模块
- **`excludes`** - 排除的模块
- **`icon`** - 应用图标

**常见问题**:

1. **缺少模块**: 添加到 `hiddenimports`
2. **资源文件丢失**: 添加到 `datas`
3. **体积过大**: 添加不需要的模块到 `excludes`

### 自定义打包

```bash
# 使用自定义 spec 文件
pyinstaller ue_toolkit.spec

# 单文件模式
pyinstaller --onefile main.py

# 指定图标
pyinstaller --icon=resources/tubiao.ico main.py

# 隐藏控制台
pyinstaller --noconsole main.py
```

## 🐛 调试和故障排查

### 常见问题

**问题 1: 打包后无法启动**

```bash
# 使用带控制台的方式启动，查看错误信息
cd release/ue_toolkit
ue_toolkit.exe
```

**问题 2: 缺少依赖模块**

编辑 `ue_toolkit.spec`，添加到 `hiddenimports`:

```python
hiddenimports=['missing_module'],
```

**问题 3: 资源文件找不到**

编辑 `ue_toolkit.spec`，添加到 `datas`:

```python
datas=[
    ('path/to/resource', 'destination'),
],
```

**问题 4: 打包体积过大**

添加不需要的模块到 `excludes`:

```python
excludes=['tkinter', 'matplotlib'],
```

### 日志调试

```python
# 在 main.py 中启用详细日志
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## ⚠️ 注意事项

- **Python 版本**: 确保使用 Python 3.9+
- **虚拟环境**: 建议使用虚拟环境隔离依赖
- **路径问题**: 打包后使用相对路径访问资源
- **权限**: Windows 下可能需要管理员权限
- **杀毒软件**: 打包的 exe 可能被误报，需添加白名单

## 🔗 相关文档

- [PyInstaller 官方文档](https://pyinstaller.org/)
- [构建和部署指南](../docs/build_and_deploy.md)
- [故障排查指南](../docs/troubleshooting.md)

