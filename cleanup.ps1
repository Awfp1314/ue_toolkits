# 项目清理脚本
# 删除测试文档和临时文件

Write-Host "开始清理项目..." -ForegroundColor Cyan
Write-Host ""

$deletedCount = 0
$failedCount = 0

# 定义要删除的文件列表
$filesToDelete = @(
    # 临时文件
    "temp_diff.txt",
    "temp_old_dark.qss",
    "temp_working_diff.txt",
    "test_run.log",
    "FORCE_SAVE_MARKER.txt",
    "DIAGNOSE_MEMORY.py",
    
    # 重复的光标修复文档
    "FIX_CURSOR_AND_SELECTION.md",
    "FIX_CURSOR_PERSISTENCE.md",
    "FIX_CURSOR_AFTER_INTERACTION.md",
    
    # 重复的测试文档
    "HOW_TO_TEST.md",
    "TEST_FIXES.md",
    "QUICK_FIX_TEST.md",
    "TEST_RESULTS_ANALYSIS.md",
    
    # 重复的总结文档
    "FIXES_SUMMARY.md",
    "QUICK_FIX_SUMMARY.md",
    "FINAL_TEST_SUMMARY.md",
    
    # 历史实现文档
    "AI_7.0_IMPLEMENTATION_COMPLETE.md",
    "AI_FEATURE_TEST.md",
    "TOKEN_OPTIMIZATION_COMPLETE.md",
    "TOKEN_OPTIMIZATION_TEST_GUIDE.md"
)

Write-Host "将删除以下文件：" -ForegroundColor Yellow
foreach ($file in $filesToDelete) {
    if (Test-Path $file) {
        Write-Host "  - $file" -ForegroundColor Gray
    }
}
Write-Host ""

# 询问确认
$confirmation = Read-Host "确认删除这些文件吗？(y/n)"
if ($confirmation -ne 'y' -and $confirmation -ne 'Y') {
    Write-Host "已取消清理。" -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "开始删除文件..." -ForegroundColor Cyan

# 删除文件
foreach ($file in $filesToDelete) {
    try {
        if (Test-Path $file) {
            Remove-Item $file -ErrorAction Stop
            Write-Host "✓ 已删除: $file" -ForegroundColor Green
            $deletedCount++
        } else {
            Write-Host "○ 不存在: $file" -ForegroundColor DarkGray
        }
    } catch {
        Write-Host "✗ 删除失败: $file - $($_.Exception.Message)" -ForegroundColor Red
        $failedCount++
    }
}

Write-Host ""
Write-Host "清理完成！" -ForegroundColor Green
Write-Host "  成功删除: $deletedCount 个文件" -ForegroundColor Green
if ($failedCount -gt 0) {
    Write-Host "  删除失败: $failedCount 个文件" -ForegroundColor Red
}

Write-Host ""
Write-Host "保留的重要文档：" -ForegroundColor Cyan
Write-Host "  - QUICK_TEST.txt (测试脚本)" -ForegroundColor Gray
Write-Host "  - FIX_CURSOR_AFTER_CLEAR_SELECTION.md (最新光标修复)" -ForegroundColor Gray
Write-Host "  - ALL_FIXES_COMPLETE.md (最新修复总结)" -ForegroundColor Gray
Write-Host "  - docs/ (文档目录)" -ForegroundColor Gray

Write-Host ""
Write-Host "下一步：" -ForegroundColor Yellow
Write-Host "  1. 运行 'git status' 查看变更" -ForegroundColor Gray
Write-Host "  2. 运行 'git add -A' 暂存删除" -ForegroundColor Gray
Write-Host "  3. 运行 'git commit -m \"清理测试文档和临时文件\"' 提交" -ForegroundColor Gray
