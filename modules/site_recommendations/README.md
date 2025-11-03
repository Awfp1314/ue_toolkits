# 🌐 Site Recommendations - 网站推荐

> 快速访问常用 UE 相关网站的工具

---

## 功能概述

Site Recommendations 提供分类整理的 UE 相关网站列表，支持快速访问和自定义添加。

### ✨ 主要功能

- ✅ 分类网站列表
- ✅ 一键打开浏览器
- ✅ 自定义添加网站
- ✅ 收藏管理
- ✅ 搜索功能

---

## 文件结构

```
site_recommendations/
├── __init__.py
├── __main__.py
├── manifest.json
│
├── logic/
│   └── site_recommendations_logic.py
│
└── ui/
    └── site_recommendations_ui.py
```

---

## 预置网站分类

### 官方资源
- Unreal Engine 官网
- Unreal Engine 文档
- Epic Games Launcher

### 学习资源
- Unreal Engine 官方教程
- Unreal Engine 学习中心
- YouTube 官方频道

### 资产商店
- Unreal Marketplace
- Epic Games Store
- Quixel Megascans

### 社区论坛
- Unreal Engine 论坛
- Reddit r/unrealengine
- Discord 社区

### 开发工具
- Unreal Engine GitHub
- Unreal Engine Issue Tracker
- Unreal Engine API 文档

---

## 使用方法

### 浏览网站

1. 选择分类
2. 点击网站卡片
3. 自动在浏览器中打开

### 添加自定义网站

```python
logic.add_site({
    "name": "我的网站",
    "url": "https://example.com",
    "category": "自定义",
    "description": "网站描述"
})
```

### 搜索网站

```python
results = logic.search_sites("marketplace")
```

---

## 快速开始

```python
# 获取模块
site_module = module_manager.get_module("site_recommendations")

# 获取 UI
site_widget = site_module.get_widget()

# 打开特定网站
logic.open_site("unreal_docs")
```

---

**维护者**: Site Recommendations Team  
**最后更新**: 2025-11-04

