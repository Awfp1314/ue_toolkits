# -*- coding: utf-8 -*-
"""清理 FAISS 记忆中的垃圾数据（问句）"""

import sys
import os
from pathlib import Path

# 修复 Windows 控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.logger import get_logger
import json

logger = get_logger(__name__)

def contains_valuable_info(text: str) -> bool:
    """判断是否为有价值信息（陈述句）"""
    text_lower = text.lower()
    
    # 排除疑问句
    question_words = ['吗', '呢', '？', '?', '什么', '怎么', '如何', '为什么', '哪', '谁', '是不是', '能不能']
    if any(word in text_lower for word in question_words):
        return False
    
    # 包含偏好、身份、喜好等关键词的陈述句
    valuable_indicators = [
        '我喜欢', '我是', '我叫', '我在', '我的', '我想',
        '我觉得', '我认为', '我需要', '我有', '我用',
        '喜欢玩', '正在开发', '正在做', '擅长', '最喜欢'
    ]
    
    return any(indicator in text_lower for indicator in valuable_indicators)

def clean_faiss_memory():
    """清理 FAISS 和 JSON 中的垃圾记忆"""
    
    print("=" * 60)
    print("🧹 FAISS 记忆清理工具")
    print("=" * 60)
    
    # 1. 清理 JSON 备份
    user_data_dir = Path(os.environ.get('APPDATA', '')) / 'ue_toolkit' / 'user_data'
    memory_file = user_data_dir / 'ai_memory' / 'memory_default.json'
    
    if not memory_file.exists():
        print(f"⚠️ 找不到记忆文件: {memory_file}")
        return
    
    print(f"📂 正在读取: {memory_file}")
    
    with open(memory_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    original_count = len(data.get('memories', []))
    print(f"📊 原始记忆数: {original_count}")
    
    # 过滤垃圾记忆
    valid_memories = []
    invalid_memories = []
    
    for mem in data.get('memories', []):
        content = mem.get('content', '')
        if contains_valuable_info(content):
            valid_memories.append(mem)
        else:
            invalid_memories.append(content[:50] + '...' if len(content) > 50 else content)
    
    print(f"\n✅ 有效记忆: {len(valid_memories)}")
    print(f"🗑️ 垃圾记忆: {len(invalid_memories)}")
    
    if invalid_memories:
        print("\n将被删除的垃圾记忆：")
        for i, mem in enumerate(invalid_memories[:10], 1):  # 最多显示10条
            print(f"  {i}. {mem}")
        if len(invalid_memories) > 10:
            print(f"  ... 还有 {len(invalid_memories) - 10} 条")
    
    # 确认删除
    print(f"\n⚠️ 这将删除 {len(invalid_memories)} 条垃圾记忆（问句）")
    confirm = input("是否继续？(y/n): ")
    
    if confirm.lower() != 'y':
        print("❌ 已取消")
        return
    
    # 保存清理后的 JSON
    data['memories'] = valid_memories
    
    with open(memory_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ JSON 备份已清理，保留 {len(valid_memories)} 条有效记忆")
    
    # 2. 删除 FAISS 索引（让系统从 JSON 重建）
    faiss_dir = user_data_dir / 'ai_memory' / 'faiss_index'
    faiss_index = faiss_dir / 'default_faiss.bin'
    faiss_metadata = faiss_dir / 'default_faiss_metadata.json'
    
    if faiss_index.exists():
        faiss_index.unlink()
        print(f"🗑️ 已删除 FAISS 索引: {faiss_index}")
    
    if faiss_metadata.exists():
        faiss_metadata.unlink()
        print(f"🗑️ 已删除 FAISS 元数据: {faiss_metadata}")
    
    print("\n" + "=" * 60)
    print("🎉 清理完成！")
    print("=" * 60)
    print("\n下次启动应用时，FAISS 将自动从 JSON 重建索引。")
    print("只有有效的陈述句会被保存到向量数据库中。\n")

if __name__ == "__main__":
    try:
        clean_faiss_memory()
    except Exception as e:
        logger.error(f"❌ 清理失败: {e}", exc_info=True)
        sys.exit(1)

