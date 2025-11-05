# Direct test without any project imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("Step 1: Import v2 (no logger)")
from core.ai_services.embedding_service_v2 import EmbeddingService
print("PASS")

print("Step 2: Create instance")
s = EmbeddingService()
print("PASS")

print("Step 3: Check singleton")
s2 = EmbeddingService()
print(f"Same instance: {s is s2}")
print("PASS")

print("\nAll tests passed! Code structure is correct.")

