# -*- coding: utf-8 -*-
"""超简化迁移脚本 - 逐步导入诊断"""

import sys
print("Step 1: Python imports OK", flush=True)

from pathlib import Path
print("Step 2: pathlib OK", flush=True)

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
print(f"Step 3: Project root added: {project_root}", flush=True)

# 逐个导入来找出问题
try:
    print("Step 4: Importing core.logger...", flush=True)
    from core.logger import get_logger
    print("  -> core.logger OK", flush=True)
except Exception as e:
    print(f"  -> ERROR: {e}", flush=True)
    sys.exit(1)

try:
    print("Step 5: Importing EmbeddingService...", flush=True)
    from core.ai_services import EmbeddingService
    print("  -> EmbeddingService OK", flush=True)
except Exception as e:
    print(f"  -> ERROR: {e}", flush=True)
    sys.exit(1)

try:
    print("Step 6: Importing EnhancedMemoryManager...", flush=True)
    from modules.ai_assistant.logic.enhanced_memory_manager import EnhancedMemoryManager
    print("  -> EnhancedMemoryManager OK", flush=True)
except Exception as e:
    print(f"  -> ERROR: {e}", flush=True)
    sys.exit(1)

try:
    print("Step 7: Importing chromadb...", flush=True)
    import chromadb
    print("  -> chromadb OK", flush=True)
except Exception as e:
    print(f"  -> ERROR: {e}", flush=True)
    sys.exit(1)

print("\n" + "="*60, flush=True)
print("All imports successful! Starting migration...", flush=True)
print("="*60, flush=True)

try:
    print("\nInitializing ChromaDB client...", flush=True)
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
    print(f"ChromaDB client OK: {db_path}", flush=True)
    
    print("\nCreating EmbeddingService (may take time)...", flush=True)
    embedding_service = EmbeddingService()
    print("EmbeddingService created", flush=True)
    
    print("\nCreating MemoryManager...", flush=True)
    memory_manager = EnhancedMemoryManager(
        user_id="default",
        embedding_service=embedding_service,
        db_client=db_client
    )
    
    count = len(memory_manager.user_memories)
    print(f"Loaded {count} memories from JSON", flush=True)
    
    if count == 0:
        print("No memories to migrate", flush=True)
    else:
        print(f"\nReady to migrate {count} memories!", flush=True)
        print("Migration would start here...", flush=True)
    
except Exception as e:
    print(f"\nERROR during execution: {e}", flush=True)
    import traceback
    traceback.print_exc()

