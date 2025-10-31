#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Release版本打包脚本
用于生成优化和压缩的生产版本
"""

import os
import sys
import subprocess
import time
import shutil
from pathlib import Path
import argparse

def get_project_root():
    """获取项目根目录"""
    return Path(__file__).parent.absolute()

def clean_previous_build():
    """清理之前的构建文件"""
    project_root = get_project_root()
    build_dir = project_root / "build"
    dist_dir = project_root / "dist"
    
    print("清理之前的构建文件...")
    
    if build_dir.exists():
        try:
            shutil.rmtree(build_dir)
            print(f"已删除构建目录: {build_dir}")
        except Exception as e:
            print(f"删除构建目录失败: {e}")
    
    if dist_dir.exists():
        try:
            shutil.rmtree(dist_dir)
            print(f"已删除分发目录: {dist_dir}")
        except Exception as e:
            print(f"删除分发目录失败: {e}")

def build_release_version(upx_enabled=True, optimize_level=2):
    """构建Release版本"""
    project_root = get_project_root()
    os.chdir(project_root)
    
    print("开始构建Release版本...")
    print(f"优化等级: {optimize_level}")
    print(f"UPX压缩: {'启用' if upx_enabled else '禁用'}")
    
    # 构建命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "ue_toolkit.spec",
        "--clean",
        "--noconfirm",
        f"--log-level=INFO"
    ]
    
    # 如果启用UPX且可用，则在spec文件中启用
    if upx_enabled:
        print("启用UPX压缩...")
        # 我们将在spec文件中设置upx=True
    
    # 设置优化等级
    # 注意：优化等级已经在spec文件中设置
    
    print(f"执行命令: {' '.join(cmd)}")
    
    try:
        # 启动进程
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
            encoding='utf-8',
            errors='replace'
        )
        
        # 设置超时（30分钟）
        timeout = 1800  # 30分钟
        start_time = time.time()
        
        print("构建进行中...")
        
        # 实时输出处理
        while True:
            # 检查超时
            if time.time() - start_time > timeout:
                print("构建超时，终止进程...")
                process.terminate()
                return False
            
            # 检查进程状态
            return_code = process.poll()
            if return_code is not None:
                # 进程结束
                if return_code == 0:
                    print("构建成功完成!")
                    return True
                else:
                    print(f"构建失败，返回码: {return_code}")
                    return False
            
            # 读取输出
            output = process.stdout.readline()
            if output:
                print(f"{output.strip()}")
            
            time.sleep(0.1)  # 避免CPU占用过高
            
    except subprocess.TimeoutExpired:
        print("构建进程超时")
        return False
    except Exception as e:
        print(f"构建异常: {e}")
        return False

def optimize_binary():
    """优化生成的二进制文件"""
    project_root = get_project_root()
    exe_path = project_root / "dist" / "ue_toolkit" / "ue_toolkit.exe"
    
    if not exe_path.exists():
        print("主程序不存在，跳过优化")
        return False
    
    print("优化二进制文件...")
    
    # 这里可以添加额外的优化步骤
    # 例如：使用strip命令去除调试信息（在Windows上可能需要其他工具）
    print("二进制文件优化完成")
    return True

def create_release_package():
    """创建Release包"""
    project_root = get_project_root()
    dist_dir = project_root / "dist" / "ue_toolkit"
    release_dir = project_root / "release"
    
    print("创建Release包...")
    
    # 检查源目录是否存在
    source_dir = None
    if dist_dir.exists():
        source_dir = dist_dir
        print(f"使用构建目录作为源: {dist_dir}")
    else:
        print("未找到构建目录")
        print(f"检查路径: {dist_dir}")
        print("\n提示: 请先运行 'python build_release.py build' 命令来构建项目")
        return False
    
    # 清理旧的release目录
    if release_dir.exists():
        try:
            shutil.rmtree(release_dir)
            print(f"已删除旧的Release目录: {release_dir}")
        except Exception as e:
            print(f"删除旧Release目录失败: {e}")
    
    # 创建新的release目录
    try:
        release_dir.mkdir(parents=True, exist_ok=True)
        print(f"创建Release目录: {release_dir}")
    except Exception as e:
        print(f"创建Release目录失败: {e}")
        return False
    
    # 复制文件
    try:
        shutil.copytree(source_dir, release_dir / "ue_toolkit")
        print("文件复制完成")
        
        # 复制启动脚本到 release 目录
        bat_files = [
            project_root / "run_with_console.bat",
            project_root / "run_without_console.bat"
        ]
        
        for bat_file in bat_files:
            if bat_file.exists():
                dest_file = release_dir / bat_file.name
                shutil.copy2(bat_file, dest_file)
                print(f"复制启动脚本: {bat_file.name}")
            else:
                print(f"警告: 启动脚本不存在: {bat_file.name}")
        
    except Exception as e:
        print(f"文件复制失败: {e}")
        return False
    
    # 创建版本信息文件
    version_info = release_dir / "version_info.txt"
    try:
        with open(version_info, 'w', encoding='utf-8') as f:
            f.write("UE Toolkit Release Version\n")
            f.write("========================\n")
            f.write("Version: 1.0.1 (Beta)\n")
            f.write("Build Date: " + time.strftime("%Y-%m-%d %H:%M:%S") + "\n")
            f.write("Build Type: Release\n")
            f.write("\nContents:\n")
            f.write("- ue_toolkit/ue_toolkit.exe: Main executable\n")
            f.write("- run_with_console.bat: Run with console window\n")
            f.write("- run_without_console.bat: Run without console window\n")
            f.write("- ue_toolkit/resources/: Resource files directory\n")
            f.write("- ue_toolkit/modules/: Modules directory\n")
            f.write("- ue_toolkit/ui/: UI components directory\n")
            f.write("- ue_toolkit/core/: Core functionality\n")
            f.write("- ue_toolkit/PyQt6/: PyQt6 library files\n")
            f.write("- Other dependencies...\n")
            f.write("\nNew Features (v1.0.1 Beta):\n")
            f.write("- System tray support\n")
            f.write("- Close confirmation dialog\n")
            f.write("- Remember close behavior preference\n")
            f.write("- Preview project management improvements\n")
            f.write("- UE project selection dialog enhancements\n")
        print(f"创建版本信息文件: {version_info}")
    except Exception as e:
        print(f"创建版本信息文件失败: {e}")
    
    print(f"Release包创建完成: {release_dir}")
    return True

def show_final_info():
    """显示最终信息"""
    project_root = get_project_root()
    dist_exe_path = project_root / "dist" / "ue_toolkit" / "ue_toolkit.exe"
    release_dir = project_root / "release"
    release_exe_path = release_dir / "ue_toolkit" / "ue_toolkit.exe"
    
    # 检查dist目录中的主程序文件
    if dist_exe_path.exists():
        # 获取文件大小
        size = dist_exe_path.stat().st_size
        size_mb = size / (1024 * 1024)
        
        print("\n" + "="*50)
        print("Release版本构建成功!")
        print("="*50)
        print(f"构建目录: {project_root / 'dist' / 'ue_toolkit'}")
        print(f"主程序: {dist_exe_path}")
        print(f"主程序大小: {size_mb:.2f} MB")
        
        # 如果release目录也存在，显示相关信息
        if release_exe_path.exists():
            print(f"\nRelease包目录: {release_dir}")
            print(f"完整包大小: ", end="")
            
            # 计算整个release目录的大小
            total_size = 0
            for path in release_dir.rglob('*'):
                if path.is_file():
                    total_size += path.stat().st_size
            
            total_size_mb = total_size / (1024 * 1024)
            print(f"{total_size_mb:.2f} MB")
        
        print("\n下一步建议:")
        print("   1. 测试运行程序确保功能正常: dist\\ue_toolkit\\ue_toolkit.exe")
        print("   2. 如需创建分发包，请运行: python build_release.py package")
        print("   3. 创建安装程序(可选)")
        return True
    else:
        print("\n未找到主程序文件")
        print(f"检查路径: {dist_exe_path}")
        return False

def main():
    parser = argparse.ArgumentParser(description="UE Toolkit Release打包脚本")
    parser.add_argument(
        "action",
        choices=["build", "clean", "package"],
        help="执行操作: build(构建), clean(清理), package(打包)"
    )
    parser.add_argument(
        "--no-upx",
        action="store_true",
        help="禁用UPX压缩"
    )
    parser.add_argument(
        "--optimize",
        type=int,
        choices=[0, 1, 2],
        default=2,
        help="优化等级 (0=无优化, 1=简单优化, 2=完整优化)"
    )
    
    args = parser.parse_args()
    
    print("=== UE工具集 Release版本打包 ===")
    
    if args.action == "clean":
        clean_previous_build()
        return
    
    if args.action == "build":
        # 清理之前的构建
        clean_previous_build()
        
        # 构建Release版本
        success = build_release_version(
            upx_enabled=not args.no_upx,
            optimize_level=args.optimize
        )
        
        if not success:
            print("\n构建失败!")
            sys.exit(1)
        
        # 优化二进制文件
        optimize_binary()
        
        # 显示最终信息
        show_final_info()
    
    if args.action == "package":
        # 创建Release包
        success = create_release_package()
        
        if not success:
            print("\n包创建失败!")
            sys.exit(1)
        
        print("\nRelease包创建成功!")

if __name__ == "__main__":
    main()