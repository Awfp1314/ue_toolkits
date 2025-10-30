# UE Toolkit - 虚幻引擎工具箱

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![Platform](https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macos-lightgrey.svg)

一个功能丰富的虚幻引擎辅助工具箱，专为虚幻引擎开发者设计，提供资产管理、配置管理和资源推荐等功能。

---

## 📖 快速文档

> **[👉 点击查看完整的使用指南](虚幻资产工具箱使用文档.md)**
> 
> 包含：安装、快速开始、资产管理、配置管理、主题自定义等详细说明

---

## 功能特性

### 🎨 资产管理模块

- 资源包和文件的统一管理
- 分类和标签系统
- 智能搜索（支持拼音搜索）
- 缩略图预览
- 一键迁移至目标工程
- 预览功能
- **本地化配置存储** - 资产配置、缩略图和文档存储在各资产库路径下
- **智能截图扫描** - 优先使用用户主动截图，自动过滤自动保存截图
- **自动文档管理** - 删除资产时同步删除关联文档

### ⚙️ 配置工具模块

- UE 工程配置模板管理
- 一键应用配置到项目
- 自定义配置模板

### 🔗 站点推荐模块

- 精选虚幻引擎学习资源
- 资产商店推荐
- 开发者社区链接
- 工具网站集合

### 🎯 其他特性

- 模块化架构设计
- 多主题支持（深色/浅色/自定义）
- 响应式界面
- 单实例运行
- 完善的日志系统
- **自定义主题对话框** - 统一的 UI 风格，所有对话框支持主题切换
- **精美的标题栏** - 自定义标题栏，带透明程序图标
- **配置备份系统** - 自动备份配置文件，支持版本控制和恢复
- **模块特定配置** - 每个模块独立配置目录，避免配置冲突

## 界面预览
_主界面展示_
<img width="1950" height="1200" alt="image" src="https://github.com/user-attachments/assets/4d3da947-48f0-4efa-9f54-1d8fcd5cc6d7" />

_配置工具界面_
<img width="1950" height="1200" alt="image" src="https://github.com/user-attachments/assets/35049bb3-c60f-478d-98d0-0a227ef73d85" />

_站点推荐_
<img width="1950" height="1200" alt="image" src="https://github.com/user-attachments/assets/6aadd5c9-3a54-43cd-af91-f4740986d628" />

_设置界面_
<img width="1950" height="1200" alt="image" src="https://github.com/user-attachments/assets/ee080824-482a-450d-baae-06038dacbcea" />


## 安装要求

- Python 3.8 或更高版本
- Windows/Linux/macOS 操作系统

## 安装步骤

### 1. 克隆仓库

```bash
git clone https://github.com/Awfp1314/ue_toolkits.git
cd ue_toolkits
```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

如果下载速度较慢，可以使用国内镜像源：

```bash
# 清华大学镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### 4. 运行程序

```bash
python main.py
```

## 使用说明

### 首次启动

1. 程序启动后会自动检测是否为首次运行
2. 根据提示设置资产库路径和预览工程路径
3. 开始使用各个功能模块

### 资产管理

1. 点击"添加资产"按钮导入资源包或文件
2. 使用分类和搜索功能快速定位资产
3. 通过预览功能查看资产效果
4. 使用迁移功能将资产复制到目标 UE 工程
5. 资产配置和缩略图自动保存在资产库路径的 `.asset_config` 目录中
6. 在 UE 中截图后，程序会自动检测并更新资产缩略图
7. 删除资产时会自动清理关联的缩略图和文档文件

### 配置工具

1. 管理 UE 工程配置模板
2. 一键将配置应用到项目中

### 站点推荐

1. 浏览推荐的虚幻引擎资源网站和一些论坛（国内有些网站是需要魔法的）
2. 直接点击链接访问相关网站

## 主题定制

程序支持多种主题：

- 深色主题（默认）
- 浅色主题
<img width="622" height="342" alt="image" src="https://github.com/user-attachments/assets/0aaa6fbe-421f-46da-bc32-b0f3e6a7e014" />

在设置界面中可以切换主题。

## 🎯 新特性亮点

### 资产配置本地化

从 v1.0.0 开始，资产管理器采用本地化配置策略：

- **本地存储**: 每个资产库的配置、缩略图和文档存储在其路径下的 `.asset_config` 目录中
- **便于迁移**: 移动资产库时，配置和缩略图会跟随移动，无需重新配置
- **版本控制**: 本地配置文件支持版本控制和自动备份
- **目录结构**:
  ```
  资产库路径/
  └── .asset_config/
      ├── asset_config.json      # 资产配置文件
      ├── thumbnails/            # 缩略图目录
      ├── documents/             # 文档目录
      └── backup/                # 配置备份目录
  ```

### 智能截图扫描

优化的截图检测逻辑，提供更智能的缩略图管理：

- **优先级策略**: 优先使用 `Saved/Screenshots/` 目录下的用户主动截图
- **自动过滤**: 仅在无用户截图时才使用 `Saved/` 下的自动保存截图
- **增量更新**: 已获取用户截图后，仅在有新截图时才更新缩略图
- **自动迁移**: 检测到截图后自动复制到资产库的缩略图目录

### 配置备份与恢复

完善的配置备份机制，保障数据安全：

- **自动备份**: 配置更新前自动备份当前配置
- **版本升级**: 配置文件版本升级时自动备份旧版本
- **备份限制**: 保留最近 5 个备份文件，自动清理旧备份
- **独立存储**: 全局配置和模块配置分别备份，互不影响

## 项目结构

```
ue_toolkit/
├── core/                      # 核心模块
│   ├── config/                # 配置管理
│   │   ├── config_manager.py  # 配置管理器
│   │   ├── config_backup.py   # 配置备份
│   │   └── config_validator.py # 配置验证
│   └── utils/                 # 工具函数
├── modules/                   # 功能模块
│   ├── asset_manager/         # 资产管理模块
│   │   ├── logic/             # 业务逻辑
│   │   └── ui/                # 用户界面
│   ├── config_tool/           # 配置工具模块
│   └── site_recommendations/  # 站点推荐模块
├── ui/                        # 主界面
│   └── main_window_components/ # 界面组件
│       └── title_bar.py       # 自定义标题栏
├── resources/                 # 资源文件
│   ├── themes/                # 主题配置
│   ├── qss/                   # 样式文件
│   └── templates/             # 配置模板
├── tests/                     # 测试文件
├── main.py                    # 程序入口
├── build_release.py           # 发布打包脚本
└── requirements.txt           # 依赖文件
```

### 用户数据目录

程序运行时会在用户目录创建以下结构（Windows 下为 `%APPDATA%\ue_toolkit`）：

```
%APPDATA%\ue_toolkit\
└── user_data/
    ├── configs/               # 全局配置
    │   ├── app/               # 应用配置
    │   │   ├── app_config.json
    │   │   └── backup/        # 配置备份
    │   └── asset_manager/     # 资产管理器配置
    │       ├── asset_manager_config.json
    │       └── backup/        # 配置备份
    └── logs/                  # 日志文件
        └── ue_toolkit.log
```

## 开发指南

### 添加新模块

1. 在 `modules/` 目录下创建新模块文件夹
2. 参考 `_template/` 目录中的模板
3. 实现模块的逻辑和界面
4. 在 `manifest.json` 中定义模块信息

### 主题定制

1. 在 `resources/themes/` 目录下创建新的主题文件
2. 参考现有主题文件格式
3. 在程序中切换使用新主题

## 技术栈

- **Python**: 主要编程语言
- **PyQt6**: 图形界面框架
- **Pillow**: 图像处理
- **psutil**: 系统监控
- **pypinyin**: 拼音转换

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目。

### 开发环境设置

```bash
# 安装开发依赖
pip install -r requirements.txt

# 运行测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=core --cov=modules --cov-report=html
```

## 许可证

本项目采用 MIT 许可证，详情请见 [LICENSE](LICENSE) 文件。

## 发布打包

有关如何构建和打包发布版本的详细信息，请参阅 [RELEASE.md](RELEASE.md) 文件。

## 📋 更新日志

### v1.0.0 (2025-10-30)

**核心改进**
- ✨ 资产配置本地化 - 配置、缩略图和文档存储在资产库路径下
- ✨ 智能截图扫描 - 优先使用用户主动截图，支持增量更新
- ✨ 自动文档管理 - 删除资产时同步删除关联文档
- ✨ 配置备份系统 - 支持配置版本控制和自动备份
- ✨ 模块特定配置 - 每个模块独立配置目录

**UI 改进**
- 🎨 自定义主题对话框 - 统一的 UI 风格
- 🎨 精美的标题栏 - 带透明程序图标的自定义标题栏
- 🎨 优化对话框布局 - 更好的文本显示和居中效果

**技术优化**
- 🔧 重构配置管理器 - 支持模块特定配置目录
- 🔧 优化备份策略 - 备份新配置而非旧文件
- 🔧 改进截图检测逻辑 - 多层级目录扫描
- 🐛 修复全局目录创建问题 - 避免不必要的目录创建

## ❓ 常见问题

### Q: 资产配置文件存储在哪里？
A: 从 v1.0.0 开始，资产配置存储在各资产库路径下的 `.asset_config` 目录中。全局配置（如资产库路径列表）存储在 `%APPDATA%\ue_toolkit\user_data\configs\asset_manager\` 目录。

### Q: 如何备份我的资产配置？
A: 资产配置会自动备份到资产库路径下的 `.asset_config/backup/` 目录。每次配置更新前都会创建备份，保留最近 5 个备份文件。

### Q: 缩略图为什么没有自动更新？
A: 程序会优先扫描 UE 项目的 `Saved/Screenshots/` 目录（用户主动截图）。如果该目录下有新截图，程序会自动更新。如果只有自动保存的截图（在 `Saved/` 目录下），程序会在首次添加资产时使用，但不会自动更新。

### Q: 迁移资产库后需要重新配置吗？
A: 不需要！由于配置存储在资产库路径下的 `.asset_config` 目录中，迁移资产库时配置会跟随移动。只需在程序中重新选择新的资产库路径即可。

### Q: 删除资产时会删除源文件吗？
A: 不会。删除资产只会删除程序中的配置记录和关联的缩略图、文档文件，不会删除资产库中的实际资产文件。

## 作者

HUTAO

## 致谢

感谢所有为虚幻引擎社区做出贡献的开发者们。



