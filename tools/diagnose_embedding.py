# -*- coding: utf-8 -*-

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("Step 1: 测试基础导入...")
try:
    from core.logger import get_logger
    print("  ✅ core.logger 导入成功")
except Exception as e:
    print(f"  ❌ core.logger 导入失败: {e}")
    sys.exit(1)

print("\nStep 2: 测试 ai_services 包...")
try:
    import core.ai_services
    print("  ✅ core.ai_services 包导入成功")
except Exception as e:
    print(f"  ❌ core.ai_services 包导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nStep 3: 测试 EmbeddingService 类...")
try:
    from core.ai_services.embedding_service import EmbeddingService
    print("  ✅ EmbeddingService 类导入成功")
except Exception as e:
    print(f"  ❌ EmbeddingService 类导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nStep 4: 创建实例...")
try:
    service = EmbeddingService()
    print(f"  ✅ 实例创建成功")
    print(f"     ID: {id(service)}")
except Exception as e:
    print(f"  ❌ 实例创建失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ 所有步骤完成！阶段 1 代码运行正常")

