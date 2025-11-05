# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("A: Basic imports", flush=True)
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import deque
print("  OK", flush=True)

print("B: Import core.logger", flush=True)
from core.logger import get_logger
print("  OK", flush=True)

print("C: Import EmbeddingService", flush=True)
from core.ai_services import EmbeddingService
print("  OK", flush=True)

print("D: Get logger instance", flush=True)
logger = get_logger("test")
print("  OK", flush=True)

print("E: Define test class with logger", flush=True)
class TestClass:
    def __init__(self):
        self.logger = logger
        self.logger.info("Test init")
print("  OK", flush=True)

print("F: Create test instance", flush=True)
t = TestClass()
print("  OK", flush=True)

print("\n[SUCCESS] Logger is NOT the problem", flush=True)

