@echo off
chcp 65001 >nul
echo ========================================
echo   语义模型手动下载工具
echo ========================================
echo.

echo [1/3] 删除损坏的模型文件...
if exist "C:\Users\wang\.cache\huggingface\hub\models--BAAI--bge-small-zh-v1.5" (
    rmdir /s /q "C:\Users\wang\.cache\huggingface\hub\models--BAAI--bge-small-zh-v1.5"
    echo ✓ 已删除损坏文件
) else (
    echo ✓ 无需删除
)

echo.
echo [2/3] 创建目录...
mkdir "C:\Users\wang\.cache\huggingface\hub" 2>nul
echo ✓ 目录已创建

echo.
echo [3/3] 开始下载模型...
echo.
echo ========================================
echo  方法选择
echo ========================================
echo.
echo 1. 使用 Python 自动下载（推荐）
echo 2. 使用 Git 克隆
echo 3. 手动浏览器下载
echo.
set /p choice="请选择方法 (1-3): "

if "%choice%"=="1" goto python_download
if "%choice%"=="2" goto git_download
if "%choice%"=="3" goto manual_download

:python_download
echo.
echo 使用 Python 下载...
cd /d "C:\Users\wang\Desktop\ue_toolkits - ai"
python -c "import os; os.environ['HF_ENDPOINT']='https://hf-mirror.com'; from sentence_transformers import SentenceTransformer; model = SentenceTransformer('BAAI/bge-small-zh-v1.5'); print('\n✓ 模型下载成功！')"
if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo  下载完成！
    echo ========================================
    echo.
    echo 现在可以启动程序了：
    echo   python main.py
    echo.
) else (
    echo.
    echo ✗ 下载失败，请尝试其他方法
)
pause
exit

:git_download
echo.
echo 使用 Git 克隆...
echo.
echo 正在克隆仓库（约 130MB）...
cd "C:\Users\wang\.cache\huggingface\hub"
git clone https://hf-mirror.com/BAAI/bge-small-zh-v1.5 models--BAAI--bge-small-zh-v1.5
if %errorlevel% equ 0 (
    echo ✓ 克隆成功！
) else (
    echo ✗ 克隆失败，请确保已安装 Git
)
pause
exit

:manual_download
echo.
echo ========================================
echo  手动下载指南
echo ========================================
echo.
echo 1. 打开浏览器访问：
echo    https://hf-mirror.com/BAAI/bge-small-zh-v1.5/tree/main
echo.
echo 2. 点击页面右上角的 "Download" 按钮
echo    或逐个下载以下文件：
echo.
echo    必需文件：
echo    - config.json
echo    - config_sentence_transformers.json
echo    - model.safetensors (约 130MB)
echo    - modules.json
echo    - tokenizer.json
echo    - tokenizer_config.json
echo    - vocab.txt
echo    - special_tokens_map.json
echo    - sentence_bert_config.json
echo    - 1_Pooling/config.json
echo.
echo 3. 下载后放置到：
echo    C:\Users\wang\.cache\huggingface\hub\models--BAAI--bge-small-zh-v1.5\snapshots\main\
echo.
echo 4. 完成后运行程序：python main.py
echo.
pause
exit

