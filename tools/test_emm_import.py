# -*- coding: utf-8 -*-
"""测试 EnhancedMemoryManager 导入的每一步"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("="*60, flush=True)
print("Testing EnhancedMemoryManager import step by step", flush=True)
print("="*60, flush=True)

print("\n1. Opening enhanced_memory_manager.py file...", flush=True)
emm_path = Path(__file__).parent.parent / "modules" / "ai_assistant" / "logic" / "enhanced_memory_manager.py"
print(f"   Path: {emm_path}", flush=True)
print(f"   Exists: {emm_path.exists()}", flush=True)

print("\n2. Import core.logger...", flush=True)
from core.logger import get_logger
print("   OK", flush=True)

print("\n3. Import EmbeddingService...", flush=True)
from core.ai_services import EmbeddingService  
print("   OK", flush=True)

print("\n4. Create logger instance...", flush=True)
logger = get_logger(__name__)
print(f"   OK - {logger}", flush=True)

print("\n5. Define BGEEmbeddingFunctionForMemory class...", flush=True)
class BGEEmbeddingFunctionForMemory:
    def __init__(self, embedding_service):
        self.embedding_service = embedding_service
    def __call__(self, input):
        return [[0.0] * 384]
print("   OK", flush=True)

print("\n6. Try actual import of EnhancedMemoryManager...", flush=True)
try:
    from modules.ai_assistant.logic.enhanced_memory_manager import EnhancedMemoryManager
    print("   OK", flush=True)
except Exception as e:
    print(f"   FAILED: {e}", flush=True)
    import traceback
    traceback.print_exc()

print("\n[DONE]", flush=True)

