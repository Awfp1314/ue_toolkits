# -*- coding: utf-8 -*-
import sys
import os
import json
from pathlib import Path

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 文件路径
mem_path = Path(os.environ['APPDATA']) / 'ue_toolkit' / 'user_data' / 'ai_memory' / 'default_memory.json'
faiss_dir = Path(os.environ['APPDATA']) / 'ue_toolkit' / 'user_data' / 'ai_memory' / 'faiss_index'

print("=" * 60)
print("🧹 清理垃圾记忆")
print("=" * 60)

# 1. 清理 JSON
print(f"\n1. 读取: {mem_path}")
with open(mem_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

original_count = len(data['memories'])
print(f"   原始记忆数: {original_count}")

# 过滤规则
def is_valid_memory(content):
    content_lower = content.lower()
    
    # 强问句标志：以问句开头或包含明显疑问词
    strong_question_indicators = ['你还记得', '你知道', '你觉得', '是不是', '能不能', '会不会', '有没有']
    if any(q in content_lower for q in strong_question_indicators):
        return False  # 直接排除强问句
    
    # 一般问句：包含疑问词
    question_words = ['吗', '呢', '？', '?', '什么', '怎么', '如何', '为什么', '哪', '谁']
    is_question = any(w in content for w in question_words)
    
    # 陈述关键词（必须在句子开头附近）
    statement_patterns = ['我喜欢玩', '我喜欢', '我是', '我叫', '我在', '我的名字', '我想', '我觉得', '我认为', '我需要', '我有', '我用', '正在开发', '正在做', '擅长', '最喜欢的']
    has_statement = any(content.startswith(p) or content.startswith('用户相关信息: ' + p) for p in statement_patterns)
    
    # 如果是问句但没有强陈述，排除
    if is_question and not has_statement:
        return False
    
    return True

valid_memories = [m for m in data['memories'] if is_valid_memory(m['content'])]
invalid_count = original_count - len(valid_memories)

print(f"   清理后: {len(valid_memories)} 条")
print(f"   删除: {invalid_count} 条垃圾记忆")

# 保存
data['memories'] = valid_memories
with open(mem_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("   ✅ JSON 已更新")

# 2. 删除 FAISS 索引
print(f"\n2. 清理 FAISS 索引: {faiss_dir}")
faiss_index = faiss_dir / 'default_faiss.bin'
faiss_metadata = faiss_dir / 'default_faiss_metadata.json'

deleted = 0
if faiss_index.exists():
    faiss_index.unlink()
    print(f"   🗑️ 已删除: default_faiss.bin")
    deleted += 1

if faiss_metadata.exists():
    faiss_metadata.unlink()
    print(f"   🗑️ 已删除: default_faiss_metadata.json")
    deleted += 1

if deleted > 0:
    print("   ✅ FAISS 索引已清理")
else:
    print("   ℹ️ 没有找到 FAISS 索引文件")

print("\n" + "=" * 60)
print("🎉 清理完成！")
print("=" * 60)
print("\n下次启动时，FAISS 将从 JSON 重建，只包含有效记忆。\n")

# 显示保留的记忆
print("保留的有效记忆：")
for i, m in enumerate(valid_memories, 1):
    print(f"  {i}. {m['content'][:70]}...")

