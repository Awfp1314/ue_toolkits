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

## 项目结构

```
ue_toolkit/
├── core/              # 核心模块
├── modules/           # 功能模块
│   ├── asset_manager/ # 资产管理模块
│   ├── config_tool/   # 配置工具模块
│   └── site_recommendations/ # 站点推荐模块
├── ui/                # 用户界面
├── resources/         # 资源文件
├── tests/             # 测试文件
├── main.py            # 程序入口
└── requirements.txt   # 依赖文件
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

## 作者

HUTAO

## 致谢

感谢所有为虚幻引擎社区做出贡献的开发者们。



