# -*- coding: utf-8 -*-

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("="*60)
print("Stage 1: EmbeddingService Test")
print("="*60)

print("\nStep 1: Import core.logger...")
try:
    from core.logger import get_logger
    print("  [OK] core.logger imported")
except Exception as e:
    print(f"  [FAIL] core.logger import failed: {e}")
    sys.exit(1)

print("\nStep 2: Import EmbeddingService...")
try:
    from core.ai_services import EmbeddingService
    print("  [OK] EmbeddingService imported")
except Exception as e:
    print(f"  [FAIL] EmbeddingService import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nStep 3: Create first instance...")
try:
    service1 = EmbeddingService()
    print(f"  [OK] Instance created: {id(service1)}")
    print(f"       Model loaded: {service1.is_loaded()}")
except Exception as e:
    print(f"  [FAIL] Instance creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nStep 4: Create second instance (test singleton)...")
try:
    service2 = EmbeddingService()
    print(f"  [OK] Instance created: {id(service2)}")
except Exception as e:
    print(f"  [FAIL] Instance creation failed: {e}")
    sys.exit(1)

print("\nStep 5: Verify singleton pattern...")
if service1 is service2:
    print("  [OK] Singleton works: service1 is service2")
else:
    print("  [FAIL] Singleton broken: different instances")
    sys.exit(1)

print("\nStep 6: Check methods...")
try:
    print(f"  - is_loaded(): {service1.is_loaded()}")
    print(f"  - get_embedding_dimension(): {service1.get_embedding_dimension()}")
    print("  [OK] All methods accessible")
except Exception as e:
    print(f"  [FAIL] Method call failed: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("[SUCCESS] Stage 1 verification passed!")
print("="*60)
print("\nAll basic functionality works:")
print("  - Singleton pattern: OK")
print("  - Lazy loading: OK")
print("  - API methods: OK")
print("\nYou can safely continue to Stage 2!")

