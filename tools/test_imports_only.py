# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("Test 1: Import EmbeddingService", flush=True)
from core.ai_services import EmbeddingService
print("  OK", flush=True)

print("Test 2: Create EmbeddingService instance (no model load)", flush=True)
service = EmbeddingService()
print(f"  OK - is_loaded: {service.is_loaded()}", flush=True)

print("Test 3: Import local_retriever", flush=True)
from modules.ai_assistant.logic.local_retriever import LocalDocIndex, BGEEmbeddingFunction
print("  OK", flush=True)

print("Test 4: Import EnhancedMemoryManager", flush=True)
from modules.ai_assistant.logic.enhanced_memory_manager import EnhancedMemoryManager
print("  OK", flush=True)

print("\n[SUCCESS] All imports work!", flush=True)

