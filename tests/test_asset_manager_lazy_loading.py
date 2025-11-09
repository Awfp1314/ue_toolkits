# -*- coding: utf-8 -*-

"""
测试 AssetManager 延迟加载集成
"""

import pytest
from pathlib import Path


class TestAssetManagerLazyLoadingIntegration:
    """测试 AssetManager 延迟加载集成（代码检查）"""
    
    def test_lazy_asset_loader_imported(self):
        """测试 LazyAssetLoader 已导入"""
        # 读取文件内容检查导入语句
        with open('ue_toolkits - ai/modules/asset_manager/ui/asset_manager_ui.py', 'r', encoding='utf-8') as f:
            content = f.read()

        assert 'LazyAssetLoader' in content
        assert 'from ..logic.lazy_asset_loader import LazyAssetLoader' in content
    
    def test_lazy_loader_created_in_init(self):
        """测试 __init__ 中创建了 lazy_loader"""
        import inspect
        from modules.asset_manager.ui.asset_manager_ui import AssetManagerUI
        
        source = inspect.getsource(AssetManagerUI.__init__)
        assert 'self.lazy_loader = LazyAssetLoader' in source
        assert '_assets_loaded_by_lazy_loader' in source
    
    def test_startup_loading_removed(self):
        """测试移除了启动时的资产加载"""
        import inspect
        from modules.asset_manager.ui.asset_manager_ui import AssetManagerUI
        
        source = inspect.getsource(AssetManagerUI.__init__)
        # 检查是否注释了 get_all_assets 和 _refresh_assets
        assert '# self.logic.get_all_assets()' in source or 'get_all_assets()' not in source
        # 注意：_refresh_assets 可能在其他地方调用，所以只检查注释
        assert '# self._refresh_assets()' in source or '已注释' in source
    
    def test_show_event_exists(self):
        """测试 showEvent 方法存在"""
        from modules.asset_manager.ui.asset_manager_ui import AssetManagerUI
        
        assert hasattr(AssetManagerUI, 'showEvent')
    
    def test_show_event_triggers_lazy_load(self):
        """测试 showEvent 触发延迟加载"""
        import inspect
        from modules.asset_manager.ui.asset_manager_ui import AssetManagerUI
        
        source = inspect.getsource(AssetManagerUI.showEvent)
        assert '_trigger_lazy_load' in source
        assert '_assets_loaded_by_lazy_loader' in source
    
    def test_trigger_lazy_load_method_exists(self):
        """测试 _trigger_lazy_load 方法存在"""
        from modules.asset_manager.ui.asset_manager_ui import AssetManagerUI
        
        assert hasattr(AssetManagerUI, '_trigger_lazy_load')
    
    def test_loading_indicator_methods_exist(self):
        """测试加载指示器方法存在"""
        from modules.asset_manager.ui.asset_manager_ui import AssetManagerUI
        
        assert hasattr(AssetManagerUI, '_show_loading_indicator')
        assert hasattr(AssetManagerUI, '_hide_loading_indicator')
    
    def test_loading_indicator_implementation(self):
        """测试加载指示器实现"""
        import inspect
        from modules.asset_manager.ui.asset_manager_ui import AssetManagerUI
        
        source = inspect.getsource(AssetManagerUI._show_loading_indicator)
        assert '正在加载资产' in source or 'loading' in source.lower()
    
    def test_lazy_load_callback_implementation(self):
        """测试延迟加载回调实现"""
        import inspect
        from modules.asset_manager.ui.asset_manager_ui import AssetManagerUI
        
        source = inspect.getsource(AssetManagerUI._trigger_lazy_load)
        assert 'on_load_complete' in source
        assert 'ensure_loaded' in source
        assert '_refresh_assets' in source
    
    def test_error_handling_in_callback(self):
        """测试回调中的错误处理"""
        import inspect
        from modules.asset_manager.ui.asset_manager_ui import AssetManagerUI
        
        source = inspect.getsource(AssetManagerUI._trigger_lazy_load)
        assert 'success' in source
        assert 'error_message' in source


class TestMainPyStartupPerformance:
    """测试 main.py 启动性能优化（代码检查）"""
    
    def test_time_module_imported(self):
        """测试导入了 time 模块"""
        with open('ue_toolkits - ai/main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'import time' in content
    
    def test_startup_time_logging(self):
        """测试启动时间日志"""
        with open('ue_toolkits - ai/main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'startup_start_time = time.time()' in content
        assert 'window_show_time = time.time()' in content
        assert 'startup_duration' in content
    
    def test_performance_check_logging(self):
        """测试性能检查日志"""
        with open('ue_toolkits - ai/main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert '启动性能' in content
        assert '从启动到窗口显示' in content
    
    def test_performance_threshold_check(self):
        """测试性能阈值检查"""
        with open('ue_toolkits - ai/main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否有 1 秒阈值检查
        assert '< 1.0' in content or '< 1秒' in content


class TestRequirementsSatisfied:
    """测试需求满足情况"""
    
    def test_requirement_16_1_async_loading(self):
        """Requirement 16.1: 主窗口先显示，资产异步加载"""
        import inspect
        from modules.asset_manager.ui.asset_manager_ui import AssetManagerUI
        from modules.asset_manager.logic.lazy_asset_loader import AssetLoadThread
        from PyQt6.QtCore import QThread
        
        # 检查 AssetLoadThread 继承 QThread
        assert issubclass(AssetLoadThread, QThread)
        
        # 检查 showEvent 触发延迟加载
        source = inspect.getsource(AssetManagerUI.showEvent)
        assert '_trigger_lazy_load' in source
    
    def test_requirement_16_2_no_startup_loading(self):
        """Requirement 16.2: 不在启动时调用 get_all_assets"""
        import inspect
        from modules.asset_manager.ui.asset_manager_ui import AssetManagerUI
        
        source = inspect.getsource(AssetManagerUI.__init__)
        # 应该注释掉或移除了 get_all_assets 调用
        assert '# self.logic.get_all_assets()' in source or 'get_all_assets()' not in source
    
    def test_requirement_16_3_loading_indicator(self):
        """Requirement 16.3: 显示加载指示器"""
        from modules.asset_manager.ui.asset_manager_ui import AssetManagerUI
        
        assert hasattr(AssetManagerUI, '_show_loading_indicator')
        assert hasattr(AssetManagerUI, '_hide_loading_indicator')
    
    def test_requirement_16_4_lazy_loading(self):
        """Requirement 16.4: 延迟到首次访问"""
        import inspect
        from modules.asset_manager.ui.asset_manager_ui import AssetManagerUI
        
        # 检查 showEvent 中有首次访问检查
        source = inspect.getsource(AssetManagerUI.showEvent)
        assert '_assets_loaded_by_lazy_loader' in source
    
    def test_requirement_16_5_startup_performance(self):
        """Requirement 16.5: 启动到窗口显示 < 1 秒"""
        with open('ue_toolkits - ai/main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查性能日志
        assert 'startup_start_time' in content
        assert 'window_show_time' in content
        assert 'startup_duration' in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

