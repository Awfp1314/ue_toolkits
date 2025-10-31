@echo off
REM ============================================
REM UE Toolkit 启动脚本 (无控制台版本)
REM 后台运行，不显示控制台窗口
REM ============================================

REM 切换到脚本所在目录
cd /d "%~dp0"

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    REM 如果 Python 未安装，显示错误信息
    msg "%username%" "未检测到 Python，请先安装 Python 3.8 或更高版本！"
    exit /b 1
)

REM 使用 pythonw.exe 在后台运行（无控制台窗口）
REM pythonw.exe 是 Python 的无窗口版本，专门用于 GUI 程序
start "" pythonw.exe main.py

REM 脚本立即退出，程序在后台运行
exit

