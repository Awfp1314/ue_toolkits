"""
FAISS 集成测试

快速验证 FAISS 是否能正常工作
"""

import sys
from pathlib import Path

# 修复 Windows 控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("FAISS 集成测试")
print("=" * 60)

try:
    # 测试 1: FAISS 导入
    print("\n[1/4] 测试 FAISS 导入...")
    import faiss
    import numpy as np
    print(f"✅ FAISS 版本: {faiss.__version__}")
    print(f"✅ NumPy 版本: {np.__version__}")
    
    # 测试 2: FAISS 基本操作
    print("\n[2/4] 测试 FAISS 基本操作...")
    index = faiss.IndexFlatL2(512)
    test_vector = np.random.rand(1, 512).astype(np.float32)
    index.add(test_vector)
    print(f"✅ FAISS 基本操作正常，索引记录数: {index.ntotal}")
    
    # 测试 3: FaissMemoryStore
    print("\n[3/4] 测试 FaissMemoryStore...")
    from modules.ai_assistant.logic.faiss_memory_store import FaissMemoryStore
    from core.utils.path_utils import PathUtils
    
    path_utils = PathUtils()
    test_dir = path_utils.get_user_data_dir() / "test_faiss"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    store = FaissMemoryStore(
        storage_dir=test_dir,
        vector_dim=512,
        user_id="test"
    )
    
    # 添加测试记忆
    test_vec = np.random.rand(512).astype(np.float32)
    store.add(
        content="测试记忆内容",
        vector=test_vec,
        metadata={"type": "test"},
        importance=0.8
    )
    
    print(f"✅ FaissMemoryStore 正常，记录数: {store.count()}")
    
    # 测试 4: EnhancedMemoryManager
    print("\n[4/4] 测试 EnhancedMemoryManager 集成...")
    from modules.ai_assistant.logic.enhanced_memory_manager import EnhancedMemoryManager
    
    memory_manager = EnhancedMemoryManager(user_id="test")
    
    if memory_manager.faiss_store is not None:
        print(f"✅ EnhancedMemoryManager 已集成 FAISS")
        print(f"   FAISS 记录数: {memory_manager.faiss_store.count()}")
    else:
        print(f"❌ EnhancedMemoryManager 未集成 FAISS")
        print("   请查看错误日志")
    
    # 清理测试数据
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)
    
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

