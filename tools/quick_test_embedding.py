# -*- coding: utf-8 -*-

"""
快速测试 EmbeddingService（不触发模型加载）
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("="*60)
print("快速测试 EmbeddingService")
print("="*60)

try:
    print("\n1. 导入 EmbeddingService...")
    from core.ai_services import EmbeddingService
    print("   ✅ 导入成功")
    
    print("\n2. 创建第一个实例...")
    service1 = EmbeddingService()
    print(f"   ✅ 实例创建成功: {service1}")
    print(f"   - 实例 ID: {id(service1)}")
    print(f"   - 模型已加载: {service1.is_loaded()}")
    
    print("\n3. 创建第二个实例（测试单例）...")
    service2 = EmbeddingService()
    print(f"   ✅ 实例创建成功: {service2}")
    print(f"   - 实例 ID: {id(service2)}")
    
    print("\n4. 验证单例模式...")
    if service1 is service2:
        print("   ✅ 单例模式正常：两个实例是同一个对象")
    else:
        print("   ❌ 单例模式失败：两个实例不同")
        sys.exit(1)
    
    print("\n5. 检查模型状态（不触发加载）...")
    print(f"   - 模型已加载: {service1.is_loaded()}")
    print(f"   - 向量维度: {service1.get_embedding_dimension()}")
    
    print("\n" + "="*60)
    print("✅ 基础功能测试通过！")
    print("="*60)
    print("\n如果要测试模型加载和编码功能，请运行:")
    print("  python tools/test_embedding_service.py")
    print("\n注意：首次运行会下载模型（约100MB），需要等待几分钟")
    
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

