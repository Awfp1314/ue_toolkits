# -*- coding: utf-8 -*-

"""
ModuleManager 单元测试
"""

import json
import pytest
from pathlib import Path
from core.module_manager import ModuleManager, ModuleState, ModuleInfo


class TestModuleManager:
    """ModuleManager 测试类"""
    
    def test_init(self, temp_module_dir):
        """测试初始化"""
        manager = ModuleManager(modules_dir=temp_module_dir)
        assert manager.modules_dir == temp_module_dir
        assert len(manager.modules) == 0
        assert len(manager.load_order) == 0
    
    def test_discover_modules_empty(self, temp_module_dir):
        """测试发现空模块目录"""
        manager = ModuleManager(modules_dir=temp_module_dir)
        modules = manager.discover_modules()
        assert len(modules) == 0
    
    def test_discover_modules_with_valid_module(self, temp_module_dir, sample_manifest):
        """测试发现有效模块"""
        module_dir = temp_module_dir / "test_module"
        module_dir.mkdir()
        
        manifest_path = module_dir / "manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(sample_manifest, f)
        
        manager = ModuleManager(modules_dir=temp_module_dir)
        modules = manager.discover_modules()
        
        assert "test_module" in modules
        assert modules["test_module"].name == "test_module"
        assert modules["test_module"].version == "1.0.0"
        assert modules["test_module"].display_name == "测试模块"
        assert modules["test_module"].state == ModuleState.DISCOVERED
    
    def test_discover_modules_skip_template(self, temp_module_dir):
        """测试跳过模板模块"""
        module_dir = temp_module_dir / "_template"
        module_dir.mkdir()
        
        manifest_path = module_dir / "manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump({"_template": True, "name": "_template"}, f)
        
        manager = ModuleManager(modules_dir=temp_module_dir)
        modules = manager.discover_modules()
        
        assert "_template" not in modules
    
    def test_resolve_dependencies_no_dependencies(self, temp_module_dir, sample_manifest):
        """测试无依赖的模块"""
        module_a_dir = temp_module_dir / "module_a"
        module_a_dir.mkdir()
        manifest_a = sample_manifest.copy()
        manifest_a["name"] = "module_a"
        manifest_a["dependencies"] = []
        with open(module_a_dir / "manifest.json", 'w', encoding='utf-8') as f:
            json.dump(manifest_a, f)
        
        module_b_dir = temp_module_dir / "module_b"
        module_b_dir.mkdir()
        manifest_b = sample_manifest.copy()
        manifest_b["name"] = "module_b"
        manifest_b["dependencies"] = []
        with open(module_b_dir / "manifest.json", 'w', encoding='utf-8') as f:
            json.dump(manifest_b, f)
        
        manager = ModuleManager(modules_dir=temp_module_dir)
        manager.discover_modules()
        load_order = manager.resolve_dependencies()
        
        assert len(load_order) == 2
        assert set(load_order) == {"module_a", "module_b"}
    
    def test_resolve_dependencies_with_dependencies(self, temp_module_dir, sample_manifest):
        """测试有依赖的模块"""
        module_a_dir = temp_module_dir / "module_a"
        module_a_dir.mkdir()
        manifest_a = sample_manifest.copy()
        manifest_a["name"] = "module_a"
        manifest_a["dependencies"] = []
        with open(module_a_dir / "manifest.json", 'w', encoding='utf-8') as f:
            json.dump(manifest_a, f)
        
        module_b_dir = temp_module_dir / "module_b"
        module_b_dir.mkdir()
        manifest_b = sample_manifest.copy()
        manifest_b["name"] = "module_b"
        manifest_b["dependencies"] = ["module_a"]
        with open(module_b_dir / "manifest.json", 'w', encoding='utf-8') as f:
            json.dump(manifest_b, f)
        
        manager = ModuleManager(modules_dir=temp_module_dir)
        manager.discover_modules()
        load_order = manager.resolve_dependencies()
        
        assert len(load_order) == 2
        # module_a 应该在 module_b 之前
        assert load_order.index("module_a") < load_order.index("module_b")
    
    def test_detect_circular_dependency_simple(self, temp_module_dir, sample_manifest):
        """测试简单循环依赖检测"""
        module_a_dir = temp_module_dir / "module_a"
        module_a_dir.mkdir()
        manifest_a = sample_manifest.copy()
        manifest_a["name"] = "module_a"
        manifest_a["dependencies"] = ["module_b"]
        with open(module_a_dir / "manifest.json", 'w', encoding='utf-8') as f:
            json.dump(manifest_a, f)
        
        module_b_dir = temp_module_dir / "module_b"
        module_b_dir.mkdir()
        manifest_b = sample_manifest.copy()
        manifest_b["name"] = "module_b"
        manifest_b["dependencies"] = ["module_a"]
        with open(module_b_dir / "manifest.json", 'w', encoding='utf-8') as f:
            json.dump(manifest_b, f)
        
        manager = ModuleManager(modules_dir=temp_module_dir)
        manager.discover_modules()
        
        with pytest.raises(ValueError, match="循环依赖"):
            manager.resolve_dependencies()
    
    def test_detect_self_dependency(self, temp_module_dir, sample_manifest):
        """测试自依赖检测"""
        module_dir = temp_module_dir / "module_a"
        module_dir.mkdir()
        manifest = sample_manifest.copy()
        manifest["name"] = "module_a"
        manifest["dependencies"] = ["module_a"]  # 自依赖
        with open(module_dir / "manifest.json", 'w', encoding='utf-8') as f:
            json.dump(manifest, f)
        
        manager = ModuleManager(modules_dir=temp_module_dir)
        manager.discover_modules()
        
        with pytest.raises(ValueError, match="自依赖"):
            manager.resolve_dependencies()
    
    def test_detect_unknown_dependency(self, temp_module_dir, sample_manifest):
        """测试未知依赖检测"""
        module_dir = temp_module_dir / "module_a"
        module_dir.mkdir()
        manifest = sample_manifest.copy()
        manifest["name"] = "module_a"
        manifest["dependencies"] = ["non_existent_module"]
        with open(module_dir / "manifest.json", 'w', encoding='utf-8') as f:
            json.dump(manifest, f)
        
        manager = ModuleManager(modules_dir=temp_module_dir)
        manager.discover_modules()
        
        with pytest.raises(ValueError, match="未知依赖"):
            manager.resolve_dependencies()

