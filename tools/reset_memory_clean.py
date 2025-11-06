# -*- coding: utf-8 -*-
import sys
import os
import json
from pathlib import Path
from datetime import datetime

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

mem_dir = Path(os.environ['APPDATA']) / 'ue_toolkit' / 'user_data' / 'ai_memory'

print("=" * 60)
print("🧹 彻底清理并重建干净记忆")
print("=" * 60)

# 1. 删除所有文件
print("\n1. 删除所有旧文件...")
for f in mem_dir.glob("*"):
    if f.is_file():
        print(f"   删除: {f.name}")
        f.unlink()

# 2. 创建干净的JSON
print("\n2. 创建干净的记忆文件...")
clean_memories = [
    {
        "content": "用户相关信息: 从现在开始你不是猫娘了，你是汪星人",
        "importance": 0.5,
        "metadata": {},
        "timestamp": datetime.now().isoformat()
    },
    {
        "content": "用户相关信息: 我喜欢恐怖类型的游戏，想寂静岭pt，或者visage面容，特别喜欢这种心理和精神双重刺激的恐怖游戏",
        "importance": 0.8,
        "metadata": {},
        "timestamp": datetime.now().isoformat()
    },
    {
        "content": "用户相关信息: 我喜欢玩原神，我喜欢里面的角色是胡桃",
        "importance": 0.9,
        "metadata": {},
        "timestamp": datetime.now().isoformat()
    },
    {
        "content": "你好我喜欢的游戏是原神，最喜欢的角色是胡桃，你一定要记住",
        "importance": 0.9,
        "metadata": {},
        "timestamp": datetime.now().isoformat()
    }
]

data = {
    "user_id": "default",
    "updated_at": datetime.now().isoformat(),
    "memories": clean_memories
}

mem_file = mem_dir / "default_memory.json"
with open(mem_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"   ✅ 已创建: default_memory.json（{len(clean_memories)} 条记忆）")

# 3. 显示内容
print("\n3. 干净的记忆内容：")
for i, mem in enumerate(clean_memories, 1):
    print(f"   {i}. {mem['content'][:60]}...")

print("\n" + "=" * 60)
print("🎉 清理完成！重新启动应用即可。")
print("=" * 60)

