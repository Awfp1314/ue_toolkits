# -*- coding: utf-8 -*-
"""
快速记忆诊断
"""
import sys
import os
from pathlib import Path

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("🔍 快速记忆诊断")
print("=" * 60)

# 检查 FAISS 文件
mem_dir = Path(os.environ['APPDATA']) / 'ue_toolkit' / 'user_data' / 'ai_memory'
faiss_index = mem_dir / 'default_faiss.index'
faiss_metadata = mem_dir / 'default_metadata.pkl'
json_file = mem_dir / 'default_memory.json'

print(f"\n📂 文件状态:")
print(f"  FAISS 索引: {'✅' if faiss_index.exists() else '❌'} ({faiss_index.stat().st_size if faiss_index.exists() else 0} bytes)")
print(f"  FAISS 元数据: {'✅' if faiss_metadata.exists() else '❌'} ({faiss_metadata.stat().st_size if faiss_metadata.exists() else 0} bytes)")
print(f"  JSON 备份: {'✅' if json_file.exists() else '❌'} ({json_file.stat().st_size if json_file.exists() else 0} bytes)")

# 检查 JSON 内容
if json_file.exists():
    import json
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n📄 JSON 记忆内容（{len(data['memories'])} 条）:")
    for i, mem in enumerate(data['memories'][:10], 1):  # 只显示前10条
        content = mem['content'][:60] + "..." if len(mem['content']) > 60 else mem['content']
        print(f"  {i}. {content}")

# 测试 FAISS 加载
if faiss_index.exists():
    try:
        print(f"\n🔧 测试 FAISS 加载...")
        from modules.ai_assistant.logic.faiss_memory_store import FaissMemoryStore
        
        store = FaissMemoryStore(storage_dir=mem_dir, vector_dim=512, user_id="default")
        count = store.count()
        print(f"  ✅ FAISS 加载成功：{count} 条记忆")
        
        # 测试搜索
        print(f"\n🔍 测试语义搜索...")
        from core.ai_services.embedding_service import EmbeddingService
        
        embedding_service = EmbeddingService()
        query = "原神"
        query_vec = embedding_service.encode_text([query], convert_to_numpy=True)
        
        results = store.search(query_vec, top_k=3)
        print(f"  查询: '{query}'")
        print(f"  结果: {len(results)} 条")
        for i, (dist, metadata) in enumerate(results, 1):
            content = metadata['content'][:50] + "..." if len(metadata['content']) > 50 else metadata['content']
            print(f"    {i}. 距离:{dist:.3f} | {content}")
            
    except Exception as e:
        print(f"  ❌ FAISS 测试失败: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 60)
print("✅ 诊断完成")
print("=" * 60)

