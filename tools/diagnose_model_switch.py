# -*- coding: utf-8 -*-
"""
诊断：切换模型时的记忆状态
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 初始化日志
from core.logger import init_logger, get_logger
init_logger()
logger = get_logger(__name__)

print("=" * 60)
print("🔍 诊断：模型切换时的记忆状态")
print("=" * 60)

# 1. 检查 FAISS 文件
import os
from pathlib import Path

mem_dir = Path(os.environ['APPDATA']) / 'ue_toolkit' / 'user_data' / 'ai_memory'
faiss_index = mem_dir / 'default_faiss.index'
faiss_metadata = mem_dir / 'default_metadata.pkl'

print(f"\n📂 FAISS 文件状态:")
print(f"  索引文件: {faiss_index.exists()} ({faiss_index.stat().st_size if faiss_index.exists() else 0} bytes)")
print(f"  元数据文件: {faiss_metadata.exists()} ({faiss_metadata.stat().st_size if faiss_metadata.exists() else 0} bytes)")

# 2. 初始化 EnhancedMemoryManager（第一次）
print(f"\n1️⃣ 初始化记忆管理器（第一次）...")
from modules.ai_assistant.logic.enhanced_memory_manager import EnhancedMemoryManager

memory1 = EnhancedMemoryManager(user_id="default")
print(f"  FAISS 启用: {memory1.faiss_store is not None}")
if memory1.faiss_store:
    print(f"  FAISS 记忆数: {memory1.faiss_store.count()}")
    print(f"  JSON 记忆数: {len(memory1.user_memories)}")

# 3. 查询记忆
print(f"\n2️⃣ 查询记忆（第一次）...")
results = memory1.get_relevant_memories("你还记得我喜欢什么游戏吗", level="user", top_k=3)
print(f"  检索到 {len(results)} 条记忆:")
for i, mem in enumerate(results[:3], 1):
    print(f"    {i}. {mem.content[:50]}...")

# 4. 模拟切换模型（重新创建 EnhancedMemoryManager）
print(f"\n3️⃣ 模拟切换模型（重新创建实例）...")
del memory1  # 删除旧实例

memory2 = EnhancedMemoryManager(user_id="default")
print(f"  FAISS 启用: {memory2.faiss_store is not None}")
if memory2.faiss_store:
    print(f"  FAISS 记忆数: {memory2.faiss_store.count()}")
    print(f"  JSON 记忆数: {len(memory2.user_memories)}")

# 5. 再次查询
print(f"\n4️⃣ 查询记忆（第二次）...")
results2 = memory2.get_relevant_memories("你还记得我喜欢什么游戏吗", level="user", top_k=3)
print(f"  检索到 {len(results2)} 条记忆:")
for i, mem in enumerate(results2[:3], 1):
    print(f"    {i}. {mem.content[:50]}...")

# 6. 对比
print(f"\n5️⃣ 对比结果:")
if len(results) == len(results2):
    print(f"  ✅ 记忆数量一致（{len(results)} 条）")
else:
    print(f"  ❌ 记忆数量不一致！第一次: {len(results)}, 第二次: {len(results2)}")

print("\n" + "=" * 60)
print("✅ 诊断完成")
print("=" * 60)

