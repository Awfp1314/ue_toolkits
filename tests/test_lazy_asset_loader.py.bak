# -*- coding: utf-8 -*-

"""
测试 LazyAssetLoader 组件
"""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch
from PyQt6.QtCore import QCoreApplication


@pytest.fixture(scope="module")
def qapp():
    """创建 QApplication 实例（整个模块共享）"""
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    return app


class TestLazyAssetLoaderImplementation:
    """测试 LazyAssetLoader 的实现（代码检查）"""
    
    def test_file_exists(self):
        """测试文件存在"""
        from pathlib import Path
        file_path = Path('ue_toolkits - ai/modules/asset_manager/logic/lazy_asset_loader.py')
        assert file_path.exists()
    
    def test_classes_exist(self):
        """测试类存在"""
        from modules.asset_manager.logic.lazy_asset_loader import AssetLoadThread, LazyAssetLoader
        assert AssetLoadThread is not None
        assert LazyAssetLoader is not None
    
    def test_asset_load_thread_inherits_qthread(self):
        """测试 AssetLoadThread 继承 QThread"""
        from modules.asset_manager.logic.lazy_asset_loader import AssetLoadThread
        from PyQt6.QtCore import QThread
        assert issubclass(AssetLoadThread, QThread)
    
    def test_asset_load_thread_has_signal(self):
        """测试 AssetLoadThread 有 load_complete 信号"""
        from modules.asset_manager.logic.lazy_asset_loader import AssetLoadThread
        assert hasattr(AssetLoadThread, 'load_complete')
    
    def test_lazy_asset_loader_methods_exist(self):
        """测试 LazyAssetLoader 的方法存在"""
        from modules.asset_manager.logic.lazy_asset_loader import LazyAssetLoader
        
        assert hasattr(LazyAssetLoader, 'ensure_loaded')
        assert hasattr(LazyAssetLoader, 'is_loaded')
        assert hasattr(LazyAssetLoader, 'is_loading')
        assert hasattr(LazyAssetLoader, 'get_error')
        assert hasattr(LazyAssetLoader, 'reset')
    
    def test_ensure_loaded_signature(self):
        """测试 ensure_loaded 方法签名"""
        import inspect
        from modules.asset_manager.logic.lazy_asset_loader import LazyAssetLoader
        
        sig = inspect.signature(LazyAssetLoader.ensure_loaded)
        assert 'on_complete' in sig.parameters
    
    def test_implementation_has_state_flags(self):
        """测试实现包含状态标志"""
        import inspect
        from modules.asset_manager.logic.lazy_asset_loader import LazyAssetLoader
        
        source = inspect.getsource(LazyAssetLoader.__init__)
        assert '_loaded' in source
        assert '_loading' in source
        assert '_error_message' in source
    
    def test_implementation_handles_concurrent_calls(self):
        """测试实现处理并发调用"""
        import inspect
        from modules.asset_manager.logic.lazy_asset_loader import LazyAssetLoader
        
        source = inspect.getsource(LazyAssetLoader)
        # 检查是否有回调队列
        assert '_pending_callbacks' in source or 'callbacks' in source.lower()
    
    def test_implementation_has_logging(self):
        """测试实现包含日志记录"""
        import inspect
        from modules.asset_manager.logic.lazy_asset_loader import LazyAssetLoader
        
        source = inspect.getsource(LazyAssetLoader)
        assert 'logger' in source.lower()
        assert 'logger.info' in source or 'self.logger.info' in source


class TestLazyAssetLoaderBehavior:
    """测试 LazyAssetLoader 的行为（需要 QApplication）"""
    
    def test_initial_state(self, qapp):
        """测试初始状态"""
        from modules.asset_manager.logic.lazy_asset_loader import LazyAssetLoader
        
        mock_logic = Mock()
        loader = LazyAssetLoader(mock_logic)
        
        assert loader.is_loaded() == False
        assert loader.is_loading() == False
        assert loader.get_error() == ""
    
    def test_ensure_loaded_starts_loading(self, qapp):
        """测试 ensure_loaded 启动加载"""
        from modules.asset_manager.logic.lazy_asset_loader import LazyAssetLoader
        
        mock_logic = Mock()
        loader = LazyAssetLoader(mock_logic)
        
        callback = Mock()
        loader.ensure_loaded(callback)
        
        # 应该开始加载
        assert loader.is_loading() == True
        assert loader.is_loaded() == False
    
    def test_ensure_loaded_success(self, qapp):
        """测试加载成功"""
        from modules.asset_manager.logic.lazy_asset_loader import LazyAssetLoader
        
        mock_logic = Mock()
        mock_logic.get_all_assets = Mock()
        
        loader = LazyAssetLoader(mock_logic)
        
        callback = Mock()
        loader.ensure_loaded(callback)
        
        # 等待加载完成
        if loader._load_thread:
            loader._load_thread.wait(2000)
        
        # 应该加载成功
        assert loader.is_loaded() == True
        assert loader.is_loading() == False
        assert loader.get_error() == ""
        
        # 回调应该被调用
        callback.assert_called_once()
        args = callback.call_args[0]
        assert args[0] == True  # success
        assert args[1] == ""    # no error
    
    def test_ensure_loaded_already_loaded(self, qapp):
        """测试已加载时立即返回"""
        from modules.asset_manager.logic.lazy_asset_loader import LazyAssetLoader
        
        mock_logic = Mock()
        loader = LazyAssetLoader(mock_logic)
        loader._loaded = True
        
        callback = Mock()
        loader.ensure_loaded(callback)
        
        # 应该立即调用回调
        callback.assert_called_once_with(True, "")
        
        # 不应该启动新线程
        assert loader._load_thread is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

