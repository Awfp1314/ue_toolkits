# -*- coding: utf-8 -*-
import sys
import os
import json
from pathlib import Path

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

mem_path = Path(os.environ['APPDATA']) / 'ue_toolkit' / 'user_data' / 'ai_memory' / 'default_memory.json'

print(f"文件路径: {mem_path}")
print(f"文件存在: {mem_path.exists()}")

if mem_path.exists():
    with open(mem_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    memories = data.get('memories', [])
    print(f"\n总记忆数: {len(memories)}")
    print("\n前 15 条记忆:")
    
    for i, mem in enumerate(memories[:15], 1):
        content = mem.get('content', '')
        print(f"{i}. {content[:80]}...")

