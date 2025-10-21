# build_offline.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
离线友好打包脚本 - 避免网络依赖导致的卡顿
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def set_offline_environment():
    """设置离线环境变量"""
    # 禁用可能的网络请求
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'  # 对于PyQt
    os.environ['PIL_DEBUG'] = '0'  # 禁用PIL调试
    
    print("🔧 设置离线打包环境...")

def build_with_timeout():
    """带超时的打包过程"""
    project_root = Path(__file__).parent.absolute()
    os.chdir(project_root)
    
    set_offline_environment()
    
    print("🚀 开始打包（离线模式）...")
    
    # 使用简化的命令，避免复杂分析
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "main.py",
        "--name=ue_toolkit",
        f"--icon={project_root / 'resources' / 'tubiao.ico'}",
        "--onedir",
        "--noconsole",
        "--clean",
        "--noconfirm",
        f"--add-data={project_root / 'resources'};resources",
        f"--add-data={project_root / 'modules'};modules",
        f"--add-data={project_root / 'core'};core",
        # 只添加最必要的隐藏导入
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtGui",
        "--hidden-import=PyQt6.QtWidgets",
        "--hidden-import=uuid",
        "--hidden-import=PIL",
        "--hidden-import=PIL.Image",
        "--hidden-import=PIL.ImageDraw",
        "--hidden-import=PIL.ImageFont",
        "--hidden-import=PIL.ImageQt",
        "--nowindowed",  # 替代 --noconsole 在某些版本中更稳定
        "--noupx",  # 禁用UPX压缩，避免卡住
        "--log-level=WARN"  # 减少日志输出
    ]
    
    print(f"⚙️  执行命令: {' '.join(cmd)}")
    
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
        
        # 设置超时（15分钟）
        timeout = 900  # 15分钟
        start_time = time.time()
        
        print("⏳ 打包进行中...")
        
        # 实时输出处理
        while True:
            # 检查超时
            if time.time() - start_time > timeout:
                print("❌ 打包超时，终止进程...")
                process.terminate()
                return False
            
            # 检查进程状态
            return_code = process.poll()
            if return_code is not None:
                # 进程结束
                if return_code == 0:
                    print("✅ 打包成功完成!")
                    return True
                else:
                    print(f"❌ 打包失败，返回码: {return_code}")
                    return False
            
            # 读取输出
            output = process.stdout.readline()
            if output:
                # 只输出重要信息，避免刷屏
                if any(keyword in output for keyword in ['INFO:', 'WARNING:', 'ERROR:', 'building']):
                    print(f"📋 {output.strip()}")
            
            time.sleep(0.1)  # 避免CPU占用过高
            
    except subprocess.TimeoutExpired:
        print("❌ 打包进程超时")
        return False
    except Exception as e:
        print(f"❌ 打包异常: {e}")
        return False

def check_dependencies():
    """检查并预加载所有依赖"""
    print("🔍 预检查依赖...")
    
    # 预导入所有可能用到的包
    packages_to_preload = [
        'PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets',
        'json', 'os', 'sys', 'pathlib', 'sqlite3',
        'PIL', 'PIL.Image', 'PIL.ImageQt'
    ]
    
    for package in packages_to_preload:
        try:
            __import__(package)
            print(f"✅ {package} 可正常导入")
        except ImportError as e:
            print(f"⚠️  {package} 导入警告: {e}")
        except Exception as e:
            print(f"❌ {package} 导入错误: {e}")

if __name__ == "__main__":
    print("=== UE工具集离线打包 ===")
    
    # 预检查依赖
    check_dependencies()
    
    # 开始打包
    success = build_with_timeout()
    
    if success:
        print("\n🎉 打包成功!")
        # 显示输出信息
        dist_dir = Path(__file__).parent.absolute() / "dist" / "ue_toolkit"
        if dist_dir.exists():
            print(f"📁 输出目录: {dist_dir}")
            exe_path = dist_dir / "ue_toolkit.exe"
            if exe_path.exists():
                print(f"🎯 主程序: {exe_path}")
    else:
        print("\n💡 打包失败建议:")
        print("   1. 检查网络连接")
        print("   2. 尝试使用管理员权限运行")
        print("   3. 暂时禁用杀毒软件")
        print("   4. 确保磁盘空间充足")
    
    sys.exit(0 if success else 1)