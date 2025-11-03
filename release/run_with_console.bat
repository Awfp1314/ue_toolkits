@echo off
REM ============================================
REM UE Toolkit 启动脚本 (控制台版本)
REM 显示控制台窗口，方便查看日志和调试信息
REM ============================================

REM 设置标题
title UE Toolkit - Console Mode

REM 切换到脚本所在目录
cd /d "%~dp0"

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8 或更高版本
    echo.
    echo 您可以从以下地址下载 Python:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM 显示启动信息
echo ============================================
echo UE Toolkit 正在启动 (控制台模式)
echo ============================================
echo.
echo 工作目录: %CD%
echo Python 版本:
python --version
echo.
echo 按 Ctrl+C 可以强制停止程序
echo ============================================
echo.

REM 运行程序
python main.py

REM 程序退出后的处理
echo.
echo ============================================
echo 程序已退出
echo ============================================
echo.
pause

