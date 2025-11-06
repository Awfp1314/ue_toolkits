#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
显示 FAISS 向量数据库的存储位置和文件信息
"""

import os
import sys
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


def main():
    # 获取存储目录
    path_utils = PathUtils()
    user_data_dir = path_utils.get_user_data_dir()
    ai_memory_dir = user_data_dir / "ai_memory"
    
    print("=" * 80)
    print("[FAISS] 向量数据库存储位置")
    print("=" * 80)
    print()
    
    print("[路径] 用户数据根目录:")
    print(f"   {user_data_dir}")
    print()
    
    print("[路径] AI 记忆存储目录:")
    print(f"   {ai_memory_dir}")
    print()
    
    # 检查目录是否存在
    if not ai_memory_dir.exists():
        print("[警告] 目录不存在（首次运行后会自动创建）")
        return
    
    print("=" * 80)
    print("[文件] FAISS 相关文件")
    print("=" * 80)
    print()
    
    user_id = "default"
    files = [
        (f"{user_id}_faiss.index", "FAISS 向量索引（主存储）"),
        (f"{user_id}_metadata.pkl", "记忆元数据（重要性、时间戳等）"),
        (f"{user_id}_backup.json", "JSON 备份文件"),
        (f"{user_id}_memory.json", "旧版 JSON 记忆文件（用于迁移）"),
    ]
    
    total_size = 0
    found_files = 0
    
    for filename, description in files:
        file_path = ai_memory_dir / filename
        exists_str = "[存在]" if file_path.exists() else "[缺失]"
        
        print(f"{exists_str} {filename}")
        print(f"   说明: {description}")
        
        if file_path.exists():
            size = file_path.stat().st_size
            total_size += size
            found_files += 1
            
            from datetime import datetime
            mtime = file_path.stat().st_mtime
            mod_time = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"   路径: {file_path}")
            print(f"   大小: {format_size(size)}")
            print(f"   修改: {mod_time}")
        else:
            print(f"   路径: {file_path}")
            print(f"   状态: 文件不存在")
        print()
    
    print("=" * 80)
    print("[统计] 文件统计信息")
    print("=" * 80)
    print(f"找到文件: {found_files}/{len(files)}")
    print(f"总大小: {format_size(total_size)}")
    print()
    
    # 额外信息：查看 FAISS 索引记录数
    faiss_index_path = ai_memory_dir / f"{user_id}_faiss.index"
    if faiss_index_path.exists():
        try:
            import faiss
            index = faiss.read_index(str(faiss_index_path))
            print(f"[记录] FAISS 索引记录数: {index.ntotal}")
            print()
        except Exception as e:
            print(f"[警告] 无法读取 FAISS 索引: {e}")
            print()
    
    # 显示如何在文件管理器中打开
    print("=" * 80)
    print("[提示] 快速操作")
    print("=" * 80)
    print("在文件管理器中打开该目录:")
    if os.name == 'nt':  # Windows
        print(f"   explorer \"{ai_memory_dir}\"")
    else:
        print(f"   xdg-open \"{ai_memory_dir}\"")
    print()
    
    print("复制路径到剪贴板:")
    print(f"   {ai_memory_dir}")
    print()


if __name__ == "__main__":
    main()

