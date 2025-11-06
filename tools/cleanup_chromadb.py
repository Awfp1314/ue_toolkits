#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理废弃的 ChromaDB 数据目录
"""

import sys
import shutil
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.utils.path_utils import PathUtils


def format_size(size_bytes):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def get_dir_size(path):
    """递归计算目录大小"""
    total = 0
    try:
        for entry in path.rglob('*'):
            if entry.is_file():
                total += entry.stat().st_size
    except Exception as e:
        print(f"[警告] 计算大小时出错: {e}")
    return total


def main():
    # 获取 ChromaDB 目录
    path_utils = PathUtils()
    user_data_dir = path_utils.get_user_data_dir()
    chroma_dir = user_data_dir / "chroma_db"
    
    print("=" * 80)
    print("[清理] ChromaDB 废弃数据目录")
    print("=" * 80)
    print()
    
    print(f"[路径] ChromaDB 目录: {chroma_dir}")
    print()
    
    # 检查目录是否存在
    if not chroma_dir.exists():
        print("[信息] ChromaDB 目录不存在，无需清理")
        print()
        return
    
    # 计算目录大小
    print("[扫描] 正在计算目录大小...")
    dir_size = get_dir_size(chroma_dir)
    print(f"[大小] {format_size(dir_size)}")
    print()
    
    # 列出目录内容
    try:
        file_count = sum(1 for _ in chroma_dir.rglob('*') if _.is_file())
        dir_count = sum(1 for _ in chroma_dir.rglob('*') if _.is_dir())
        print(f"[内容] 文件数: {file_count}, 目录数: {dir_count}")
        print()
    except Exception as e:
        print(f"[警告] 无法统计内容: {e}")
        print()
    
    # 确认删除
    print("=" * 80)
    print("[提示] ChromaDB 已被 FAISS 替代，此目录不再使用")
    print("=" * 80)
    print()
    
    # 执行删除
    try:
        print("[操作] 正在删除目录...")
        shutil.rmtree(chroma_dir)
        print("[成功] ChromaDB 目录已删除！")
        print()
        print(f"[释放] 磁盘空间: {format_size(dir_size)}")
        print()
    except Exception as e:
        print(f"[错误] 删除失败: {e}")
        print()
        print("[建议] 请手动删除该目录:")
        print(f"   {chroma_dir}")
        print()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

