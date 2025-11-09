# -*- coding: utf-8 -*-
"""验证 FAISS 是否正常工作"""

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

# 初始化日志系统
from core.logger import init_logger
init_logger()

print("=" * 60)
print("验证 FAISS 集成...")
print("=" * 60)

# 1. 测试 FAISS 导入
try:
    import faiss
    import numpy as np
    print(f"OK: FAISS {faiss.__version__}, NumPy {np.__version__}")
except Exception as e:
    print(f"ERROR: FAISS 导入失败: {e}")
    sys.exit(1)

# 2. 测试 FaissMemoryStore 导入
try:
    from modules.ai_assistant.logic.faiss_memory_store import FaissMemoryStore
    print("OK: FaissMemoryStore 导入成功")
except Exception as e:
    print(f"ERROR: FaissMemoryStore 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 3. 测试 EmbeddingService
try:
    from core.ai_services import EmbeddingService
    print("OK: EmbeddingService 导入成功")
    print("    正在初始化 EmbeddingService...")
    embedding_service = EmbeddingService()
    print(f"    模型维度: {embedding_service.get_embedding_dimension()}")
except Exception as e:
    print(f"ERROR: EmbeddingService 初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 4. 测试 EnhancedMemoryManager 集成
try:
    from modules.ai_assistant.logic.enhanced_memory_manager import EnhancedMemoryManager
    print("OK: EnhancedMemoryManager 导入成功")
    
    # 创建实例
    print("    正在初始化 EnhancedMemoryManager...")
    mm = EnhancedMemoryManager(
        user_id="test_verify",
        embedding_service=embedding_service
    )
    
    if mm.faiss_store is not None:
        print(f"OK: FAISS 已集成到 EnhancedMemoryManager")
        print(f"    FAISS 记录数: {mm.faiss_store.count()}")
    else:
        print("ERROR: FAISS 未集成（faiss_store = None）")
        sys.exit(1)
        
except Exception as e:
    print(f"ERROR: EnhancedMemoryManager 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n所有验证通过！FAISS 已成功集成。")

