# -*- coding: utf-8 -*-

"""
记忆迁移脚本
将 JSON 文件中的旧记忆迁移到 ChromaDB 向量数据库
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.logger import get_logger
from core.ai_services import EmbeddingService
from modules.ai_assistant.logic.enhanced_memory_manager import EnhancedMemoryManager

logger = get_logger(__name__)


def migrate_memories(user_id: str = "default"):
    """
    迁移指定用户的记忆到 ChromaDB
    
    Args:
        user_id: 用户ID
    """
    print("="*60, flush=True)
    print("记忆迁移工具 - 将 JSON 记忆迁移到 ChromaDB", flush=True)
    print("="*60, flush=True)
    
    try:
        # 1. 初始化 ChromaDB 客户端
        print("\n[步骤 1/4] 初始化 ChromaDB...", flush=True)
        import chromadb
        from chromadb.config import Settings
        from core.utils.path_utils import PathUtils
        
        path_utils = PathUtils()
        db_path = path_utils.get_user_data_dir() / "chroma_db"
        db_path.mkdir(parents=True, exist_ok=True)
        
        db_client = chromadb.PersistentClient(
            path=str(db_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        print(f"  [OK] ChromaDB 初始化成功: {db_path}", flush=True)
        
        # 2. 创建嵌入服务
        print("\n[步骤 2/4] 初始化嵌入服务...", flush=True)
        embedding_service = EmbeddingService()
        print(f"  [OK] 嵌入服务初始化成功", flush=True)
        
        # 3. 创建记忆管理器（会自动加载 JSON 文件）
        print(f"\n[步骤 3/4] 加载现有记忆（用户: {user_id}）...", flush=True)
        memory_manager = EnhancedMemoryManager(
            user_id=user_id,
            embedding_service=embedding_service,
            db_client=db_client
        )
        
        user_memories_count = len(memory_manager.user_memories)
        print(f"  [OK] 从 JSON 加载了 {user_memories_count} 条用户级记忆", flush=True)
        
        if user_memories_count == 0:
            print("\n[结果] 没有需要迁移的记忆", flush=True)
            return
        
        # 4. 检查 ChromaDB 中已有的记忆
        if memory_manager._memory_collection is not None:
            existing_count = memory_manager._memory_collection.count()
            print(f"  [INFO] ChromaDB 中已有 {existing_count} 条记忆", flush=True)
        else:
            print("  [ERROR] ChromaDB 集合初始化失败", flush=True)
            return
        
        # 5. 迁移记忆
        print(f"\n[步骤 4/4] 迁移记忆到 ChromaDB...", flush=True)
        print(f"  [INFO] 开始逐条迁移...", flush=True)
        migrated = 0
        skipped = 0
        errors = 0
        
        for i, memory in enumerate(memory_manager.user_memories, 1):
            print(f"  处理第 {i}/{user_memories_count} 条记忆...", end='', flush=True)
            
            try:
                # 生成唯一 ID
                memory_id = f"{user_id}_{memory.timestamp}_{hash(memory.content) % 100000}"
                
                # 检查是否已存在
                try:
                    existing = memory_manager._memory_collection.get(ids=[memory_id])
                    if existing['ids']:
                        skipped += 1
                        print(" [已存在,跳过]", flush=True)
                        continue
                except:
                    pass
                
                print(" [向量化中]...", end='', flush=True)
                
                # 准备元数据
                metadata = {
                    'timestamp': memory.timestamp,
                    'importance': float(memory.importance),
                    'level': 'user',
                    'user_id': user_id
                }
                
                # 合并原有元数据
                if memory.metadata:
                    metadata.update({k: str(v) for k, v in memory.metadata.items()})
                
                # 存入 ChromaDB（这一步会触发向量化，可能较慢）
                memory_manager._memory_collection.upsert(
                    ids=[memory_id],
                    documents=[memory.content],
                    metadatas=[metadata]
                )
                
                migrated += 1
                print(" [完成]", flush=True)
                
                # 阶段性总结
                if i % 5 == 0:
                    print(f"  >>> 已处理: {i}/{user_memories_count}, 迁移: {migrated}, 跳过: {skipped}", flush=True)
                
            except Exception as e:
                errors += 1
                print(f" [失败: {e}]", flush=True)
                logger.error(f"迁移记忆失败: {e}")
        
        # 6. 总结
        print("\n" + "="*60, flush=True)
        print("[迁移完成]", flush=True)
        print("="*60, flush=True)
        print(f"总记忆数:     {user_memories_count}", flush=True)
        print(f"成功迁移:     {migrated}", flush=True)
        print(f"已存在(跳过): {skipped}", flush=True)
        print(f"失败:         {errors}", flush=True)
        print(f"\nChromaDB 总记忆数: {memory_manager._memory_collection.count()}", flush=True)
        print("="*60, flush=True)
        
        if migrated > 0:
            print("\n✅ 迁移成功！现在可以使用向量语义检索旧记忆了。", flush=True)
        elif skipped == user_memories_count:
            print("\n✅ 所有记忆已经在 ChromaDB 中，无需迁移。", flush=True)
        else:
            print(f"\n⚠️ 迁移完成，但有 {errors} 条记忆迁移失败。", flush=True)
        
    except KeyboardInterrupt:
        print("\n\n迁移被用户中断", flush=True)
    except Exception as e:
        print(f"\n\n❌ 迁移过程出错: {e}", flush=True)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 支持命令行参数指定用户ID
    user_id = sys.argv[1] if len(sys.argv) > 1 else "default"
    migrate_memories(user_id)

