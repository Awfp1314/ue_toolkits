# 代码清理需求文档

## 简介

本文档定义了对 UE Toolkit 项目进行全面代码清理的需求。该项目是一个基于 PyQt6 的虚幻引擎辅助工具箱，包含资产管理、AI 助手、配置工具等多个模块。清理目标是识别并移除所有无用的废弃代码、死代码和无用文件，确保代码库的整洁性和可维护性。

## 术语表

- **System**: UE Toolkit 应用程序
- **Dead Code**: 永远不会被执行的代码段
- **Deprecated Code**: 已标记为废弃但仍存在的代码
- **Unused File**: 未被任何模块引用或使用的文件
- **Code Review**: 逐行审查代码的过程
- **Module**: 应用程序的功能模块（如 asset_manager、ai_assistant 等）
- **Core Component**: 核心功能组件（如 config、utils 等）
- **Import Analysis**: 分析代码中的导入语句以确定依赖关系
- **Reference Check**: 检查代码元素（函数、类、变量）的引用情况

## 需求

### 需求 1: 全面代码审查

**用户故事**: 作为项目维护者，我希望对项目中的每个文件进行逐行审查，以便识别所有无用代码和文件

#### 验收标准

1. WHEN 执行代码审查时，THE System SHALL 扫描项目中的所有 Python 文件（.py）
2. WHEN 审查每个文件时，THE System SHALL 逐行分析代码以识别未使用的导入、函数、类和变量
3. WHEN 发现潜在的死代码时，THE System SHALL 记录该代码的位置和原因
4. THE System SHALL 生成包含所有审查文件列表的报告，确保没有文件被遗漏
5. WHEN 审查完成时，THE System SHALL 提供审查覆盖率统计（已审查文件数/总文件数）

### 需求 2: 死代码检测

**用户故事**: 作为开发者，我希望自动检测永远不会被执行的代码段，以便清理冗余代码

#### 验收标准

1. WHEN 分析代码时，THE System SHALL 识别不可达的代码块（如 return 后的语句）
2. WHEN 检测条件语句时，THE System SHALL 识别永远为 False 的条件分支
3. WHEN 分析函数时，THE System SHALL 识别从未被调用的私有方法和函数
4. WHEN 检测类时，THE System SHALL 识别从未被实例化的类
5. THE System SHALL 为每个检测到的死代码提供具体的文件路径和行号

### 需求 3: 废弃代码识别

**用户故事**: 作为项目维护者，我希望识别所有标记为废弃但仍存在的代码，以便决定是否移除

#### 验收标准

1. WHEN 扫描代码时，THE System SHALL 识别包含 @deprecated 装饰器的函数和类
2. WHEN 检测注释时，THE System SHALL 识别包含 "deprecated"、"废弃"、"已弃用" 等关键词的代码段
3. WHEN 发现废弃代码时，THE System SHALL 检查该代码是否仍被其他部分引用
4. THE System SHALL 生成废弃代码清单，包括废弃原因和替代方案（如果注释中有说明）
5. WHERE 废弃代码仍被引用，THE System SHALL 标记为"需要迁移"而非"可直接删除"

### 需求 4: 未使用文件检测

**用户故事**: 作为项目维护者，我希望识别所有未被引用的文件，以便清理项目结构

#### 验收标准

1. THE System SHALL 分析所有 Python 文件的导入语句以构建依赖关系图
2. WHEN 构建依赖图时，THE System SHALL 从入口点（main.py）开始追踪所有可达文件
3. WHEN 分析完成时，THE System SHALL 识别未被任何文件导入的 Python 模块
4. THE System SHALL 识别未被代码引用的资源文件（如 .qss、.json、.png 等）
5. WHERE 文件位于 tests/ 目录，THE System SHALL 单独标记为测试文件并检查其有效性

### 需求 5: 未使用导入清理

**用户故事**: 作为开发者，我希望清理所有未使用的导入语句，以便提高代码可读性

#### 验收标准

1. WHEN 分析文件时，THE System SHALL 识别所有导入但未使用的模块、类和函数
2. THE System SHALL 区分标准库导入、第三方库导入和项目内部导入
3. WHEN 检测到未使用导入时，THE System SHALL 验证该导入是否用于类型注解
4. THE System SHALL 生成可自动应用的清理建议（移除未使用导入的具体行）
5. WHERE 导入用于副作用（如注册装饰器），THE System SHALL 标记为"需要人工确认"

### 需求 6: 未使用变量和参数检测

**用户故事**: 作为开发者，我希望识别未使用的变量和函数参数，以便简化代码

#### 验收标准

1. WHEN 分析函数时，THE System SHALL 识别声明但从未使用的局部变量
2. WHEN 检测函数参数时，THE System SHALL 识别从未在函数体中使用的参数
3. WHERE 参数以下划线开头（如 \_unused），THE System SHALL 跳过该参数（约定俗成的未使用标记）
4. THE System SHALL 识别赋值后从未读取的变量
5. WHEN 检测到未使用变量时，THE System SHALL 提供重命名为 \_ 或删除的建议

### 需求 7: 重复代码检测

**用户故事**: 作为项目维护者，我希望识别重复的代码段，以便进行重构和复用

#### 验收标准

1. WHEN 分析代码库时，THE System SHALL 识别相似度超过 80% 的代码块（至少 5 行）
2. THE System SHALL 计算代码块之间的相似度分数
3. WHEN 发现重复代码时，THE System SHALL 提供所有重复位置的列表
4. THE System SHALL 建议可能的重构方案（如提取公共函数）
5. WHERE 重复代码位于不同模块，THE System SHALL 建议将其移至 core/utils

### 需求 8: 配置文件验证

**用户故事**: 作为项目维护者，我希望验证所有配置文件的有效性，以便移除无效配置

#### 验收标准

1. THE System SHALL 验证所有 JSON 配置文件的语法正确性
2. WHEN 检测 manifest.json 时，THE System SHALL 验证其包含所有必需字段
3. WHEN 检测配置模板时，THE System SHALL 验证其与实际使用的配置键匹配
4. THE System SHALL 识别配置文件中未被代码使用的配置项
5. WHERE 发现无效配置，THE System SHALL 提供修复或删除建议

### 需求 9: 测试文件有效性检查

**用户故事**: 作为开发者，我希望验证所有测试文件是否有效且可执行，以便移除无效测试

#### 验收标准

1. THE System SHALL 识别 tests/ 目录下的所有测试文件
2. WHEN 分析测试文件时，THE System SHALL 验证其导入的模块是否存在
3. WHEN 检测测试函数时，THE System SHALL 验证其命名符合 pytest 约定（test\_ 前缀）
4. THE System SHALL 识别测试文件中被注释掉的测试用例
5. WHERE 测试文件导入不存在的模块，THE System SHALL 标记为"无效测试"

### 需求 10: 清理报告生成

**用户故事**: 作为项目维护者，我希望获得详细的清理报告，以便做出清理决策

#### 验收标准

1. WHEN 分析完成时，THE System SHALL 生成包含所有发现问题的 Markdown 格式报告
2. THE System SHALL 按类别组织报告（死代码、废弃代码、未使用文件等）
3. WHEN 生成报告时，THE System SHALL 为每个问题提供严重程度评级（高/中/低）
4. THE System SHALL 在报告中包含统计摘要（总问题数、各类别问题数、预计可删除代码行数）
5. THE System SHALL 为每个问题提供具体的文件路径、行号和建议操作

### 需求 11: 安全清理验证

**用户故事**: 作为项目维护者，我希望在删除代码前进行安全验证，以便避免破坏功能

#### 验收标准

1. WHEN 建议删除代码时，THE System SHALL 验证该代码不是公共 API 的一部分
2. THE System SHALL 检查待删除代码是否在文档中被引用
3. WHEN 删除文件时，THE System SHALL 验证该文件不在 requirements.txt 或 setup.py 中被引用
4. THE System SHALL 提供"影响分析"，列出删除代码可能影响的其他部分
5. WHERE 删除操作风险较高，THE System SHALL 要求人工确认

### 需求 12: 增量清理支持

**用户故事**: 作为开发者，我希望能够分批次清理代码，以便逐步验证清理效果

#### 验收标准

1. THE System SHALL 支持按模块进行独立的代码清理分析
2. WHEN 执行清理时，THE System SHALL 允许选择特定类别的问题进行清理
3. THE System SHALL 记录已清理的问题，避免重复报告
4. WHEN 清理完成时，THE System SHALL 生成清理前后的对比报告
5. THE System SHALL 支持回滚操作，保留清理前的代码备份
