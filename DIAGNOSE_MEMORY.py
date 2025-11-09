# -*- coding: utf-8 -*-
"""
记忆系统诊断脚本
运行此脚本检查记忆系统是否正常
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.ai_assistant.logic.enhanced_memory_manager import EnhancedMemoryManager, MemoryLevel
from core.logger import get_logger

logger = get_logger(__name__)

print("=" * 80)
print("记忆系统诊断")
print("=" * 80)

try:
    # 初始化记忆管理器
    memory_manager = EnhancedMemoryManager(
        user_id="default",
        embedding_service=None  # 暂时不用
    )
    
    print("\n1. 检查用户身份记忆")
    print("-" * 40)
    
    # 获取完整身份
    full_identity = memory_manager.get_user_identity()
    if full_identity:
        lines = full_identity.split('\n')
        print(f"找到 {len(lines)} 条用户身份记忆：")
        for i, line in enumerate(lines[:10], 1):
            print(f"  {i}. {line[:80]}...")
    else:
        print("  ⚠️ 未找到用户身份记忆！")
    
    print("\n2. 检查压缩身份")
    print("-" * 40)
    
    # 获取压缩身份
    try:
        minimal_identity = memory_manager.get_user_identity_minimal()
        print(f"压缩身份: {minimal_identity}")
        
        if '猫娘' in minimal_identity:
            print("  ✅ 猫娘身份已保留")
        elif '汪星人' in minimal_identity:
            print("  ⚠️ 当前是汪星人身份")
        else:
            print("  ❌ 身份信息丢失")
    except Exception as e:
        print(f"  ❌ 压缩身份失败: {e}")
        import traceback
        print(traceback.format_exc())
    
    print("\n3. 检查记忆搜索功能")
    print("-" * 40)
    
    # 测试搜索
    test_queries = [
        "你喜欢什么游戏",
        "你还记得我的偏好吗",
        "原神"
    ]
    
    for query in test_queries:
        print(f"\n搜索: '{query}'")
        try:
            results = memory_manager.search_memories(query, top_k=3)
            if results:
                print(f"  找到 {len(results)} 条相关记忆:")
                for i, result in enumerate(results, 1):
                    print(f"    {i}. {result[:60]}...")
            else:
                print("  ⚠️ 未找到相关记忆")
        except Exception as e:
            print(f"  ❌ 搜索失败: {e}")
    
    print("\n4. 检查总记忆数量")
    print("-" * 40)
    
    # 统计各级别记忆
    try:
        user_memories = memory_manager.get_memories_by_level(MemoryLevel.USER)
        session_memories = memory_manager.get_memories_by_level(MemoryLevel.SESSION)
        context_memories = memory_manager.get_memories_by_level(MemoryLevel.CONTEXT)
        
        print(f"  用户级记忆: {len(user_memories)} 条")
        print(f"  会话级记忆: {len(session_memories)} 条")
        print(f"  上下文记忆: {len(context_memories)} 条")
        print(f"  总计: {len(user_memories) + len(session_memories) + len(context_memories)} 条")
    except Exception as e:
        print(f"  ❌ 统计失败: {e}")
    
    print("\n" + "=" * 80)
    print("诊断完成")
    print("=" * 80)

except Exception as e:
    print(f"\n❌ 诊断失败: {e}")
    import traceback
    print(traceback.format_exc())

