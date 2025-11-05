# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("Test 1: Import")
from core.ai_services import EmbeddingService
print("OK")

print("Test 2: Create instance")
s1 = EmbeddingService()
print("OK")

print("Test 3: Singleton")
s2 = EmbeddingService()
assert s1 is s2
print("OK")

print("Test 4: Methods exist")
assert hasattr(s1, 'get_embedder')
assert hasattr(s1, 'encode_text')
assert hasattr(s1, 'is_loaded')
print("OK")

print("\n[SUCCESS] Stage 1 works!")

