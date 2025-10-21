# 发布打包指南

本文档介绍了如何构建和打包UE Toolkit的发布版本。

## 打包流程

UE Toolkit使用`build_release.py`脚本来自动化构建和打包过程。该脚本提供了三个主要命令：

1. `build` - 构建项目
2. `package` - 创建发布包
3. `clean` - 清理构建文件

## 构建项目

要构建项目，请运行以下命令：

```bash
python build_release.py build
```

此命令将：
1. 清理之前的构建文件
2. 使用PyInstaller构建独立的可执行文件
3. 优化生成的二进制文件
4. 显示构建结果信息

构建完成后，可执行文件将位于 `dist/ue_toolkit/` 目录中。

### 构建选项

构建命令支持以下选项：

- `--no-upx`: 禁用UPX压缩
- `--optimize [0,1,2]`: 设置优化等级（0=无优化，1=简单优化，2=完整优化，默认为2）

示例：
```bash
# 禁用UPX压缩的构建
python build_release.py build --no-upx

# 使用较低优化等级的构建
python build_release.py build --optimize 1
```

### UPX压缩

UPX（Ultimate Packer for eXecutables）是一个开源的可执行文件压缩工具。在Release构建中，默认启用UPX压缩来减小可执行文件的大小。如果遇到与UPX相关的问题，可以使用`--no-upx`选项禁用压缩。

### 优化等级

构建脚本支持三种优化等级：

- **0（无优化）**: 不进行任何优化，构建速度最快
- **1（简单优化）**: 启用基本的Python字节码优化
- **2（完整优化）**: 启用所有可用的优化，包括更激进的字节码优化

默认情况下，Release构建使用等级2进行完整优化。

## 创建发布包

要创建发布包，请运行以下命令：

```bash
python build_release.py package
```

此命令将：
1. 检查是否存在构建目录(`dist/ue_toolkit`)
2. 删除旧的发布目录(`release`)
3. 创建新的发布目录
4. 将构建文件复制到发布目录
5. 生成版本信息文件(`version_info.txt`)

发布包将位于 `release/` 目录中。

## 清理构建文件

要清理所有构建文件，请运行以下命令：

```bash
python build_release.py clean
```

此命令将删除 `dist/` 和 `build/` 目录。

## 注意事项

1. 在运行`package`命令之前，必须先运行`build`命令来生成必要的构建文件。
2. 发布包包含了运行程序所需的所有依赖项，可以直接分发给用户。
3. 版本信息文件包含了构建时间、版本号等重要信息。

## 故障排除

### 分发目录不存在

如果遇到"分发目录不存在"错误，请确保先运行构建命令：

```bash
python build_release.py build
```

然后再运行打包命令：

```bash
python build_release.py package
```

### 未找到主程序文件

如果遇到"未找到主程序文件"错误，请检查构建过程是否成功完成。确保没有构建错误，并且 `dist/ue_toolkit/ue_toolkit.exe` 文件存在。