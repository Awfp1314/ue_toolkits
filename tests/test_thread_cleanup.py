"""
Unit tests for ThreadCleanupMixin implementation

Tests cover:
- Normal exit flow (request_stop → wait → success)
- Timeout forced termination flow (wait timeout → terminate)
- __del__ fallback cleanup

Requirements tested: 4.1, 4.2, 4.3
"""

import unittest
import time
import sys
import os

# Add parent directory to path to allow importing core module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt6.QtCore import QThread, QCoreApplication
from core.utils.thread_cleanup import ThreadCleanupMixin


# Test worker classes
class NormalWorker(QThread, ThreadCleanupMixin):
    """Worker that stops normally when requested"""
    
    def __init__(self):
        QThread.__init__(self)
        self._should_stop = False
        self.work_done = False
    
    def request_stop(self) -> None:
        """Implement abstract method: request stop"""
        self._should_stop = True
    
    def run(self):
        """Run loop that checks stop flag"""
        while not self._should_stop:
            time.sleep(0.01)  # Small sleep to avoid busy loop
        self.work_done = True


class SlowWorker(QThread, ThreadCleanupMixin):
    """Worker that takes time to stop (for timeout testing)"""
    
    def __init__(self, stop_delay_ms: int = 2000):
        QThread.__init__(self)
        self._should_stop = False
        self._stop_delay_ms = stop_delay_ms
        self.work_done = False
    
    def request_stop(self) -> None:
        """Implement abstract method: request stop"""
        self._should_stop = True
    
    def run(self):
        """Run loop that delays before checking stop flag"""
        start_time = time.time()
        while not self._should_stop:
            time.sleep(0.01)
        
        # Simulate slow cleanup
        time.sleep(self._stop_delay_ms / 1000.0)
        self.work_done = True


class UnresponsiveWorker(QThread, ThreadCleanupMixin):
    """Worker that ignores stop requests (for forced termination testing)"""
    
    def __init__(self):
        QThread.__init__(self)
        self._should_stop = False
        self.stop_requested = False
    
    def request_stop(self) -> None:
        """Implement abstract method: request stop (but worker ignores it)"""
        self.stop_requested = True
        # Note: We don't set _should_stop, simulating unresponsive thread
    
    def run(self):
        """Run loop that never checks stop flag"""
        # Infinite loop that ignores stop requests
        while True:
            time.sleep(0.01)


class TestThreadCleanupMixin(unittest.TestCase):
    """Test ThreadCleanupMixin functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up QCoreApplication for QThread tests"""
        # QThread requires a QCoreApplication instance
        if not QCoreApplication.instance():
            cls.app = QCoreApplication(sys.argv)
        else:
            cls.app = QCoreApplication.instance()
    
    def test_normal_exit_flow(self):
        """Test normal exit flow: request_stop → wait → success
        
        Requirement 4.1: cleanup() should call request_stop()
        Requirement 4.2: cleanup() should wait for normal exit
        """
        worker = NormalWorker()
        worker.start()
        
        # Wait for thread to start
        time.sleep(0.05)
        self.assertTrue(worker.isRunning())
        
        # Cleanup should succeed
        result = worker.cleanup(timeout_ms=1000)
        
        self.assertTrue(result, "Cleanup should return True for normal exit")
        self.assertFalse(worker.isRunning(), "Thread should not be running after cleanup")
        self.assertTrue(worker.work_done, "Worker should have completed its work")
    
    def test_timeout_forced_termination(self):
        """Test timeout forced termination: wait timeout → terminate
        
        Requirement 4.2: cleanup() should wait with timeout
        Requirement 4.3: cleanup() should terminate if timeout exceeded
        """
        # Worker that takes 2 seconds to stop, but we only wait 500ms
        worker = SlowWorker(stop_delay_ms=2000)
        worker.start()
        
        # Wait for thread to start
        time.sleep(0.05)
        self.assertTrue(worker.isRunning())
        
        # Cleanup with short timeout should force termination
        result = worker.cleanup(timeout_ms=500)
        
        self.assertFalse(result, "Cleanup should return False when forced to terminate")
        self.assertFalse(worker.isRunning(), "Thread should not be running after forced termination")
    
    def test_unresponsive_worker_termination(self):
        """Test that unresponsive workers are forcefully terminated
        
        Requirement 4.3: cleanup() should terminate unresponsive threads
        """
        worker = UnresponsiveWorker()
        worker.start()
        
        # Wait for thread to start
        time.sleep(0.05)
        self.assertTrue(worker.isRunning())
        
        # Cleanup should force termination
        result = worker.cleanup(timeout_ms=500)
        
        self.assertFalse(result, "Cleanup should return False for forced termination")
        self.assertTrue(worker.stop_requested, "request_stop() should have been called")
        self.assertFalse(worker.isRunning(), "Thread should be terminated")
    
    def test_cleanup_already_stopped_thread(self):
        """Test cleanup on already stopped thread"""
        worker = NormalWorker()
        worker.start()
        
        # Stop normally
        worker.request_stop()
        worker.wait(1000)
        
        self.assertFalse(worker.isRunning())
        
        # Cleanup should succeed immediately
        result = worker.cleanup(timeout_ms=1000)
        
        self.assertTrue(result, "Cleanup should return True for already stopped thread")
    
    def test_cleanup_never_started_thread(self):
        """Test cleanup on thread that was never started"""
        worker = NormalWorker()
        
        # Thread never started
        self.assertFalse(worker.isRunning())
        
        # Cleanup should succeed immediately
        result = worker.cleanup(timeout_ms=1000)
        
        self.assertTrue(result, "Cleanup should return True for never-started thread")
    
    def test_request_stop_exception_handling(self):
        """Test that exceptions in request_stop() are handled gracefully"""
        
        class FaultyWorker(QThread, ThreadCleanupMixin):
            def __init__(self):
                QThread.__init__(self)
            
            def request_stop(self) -> None:
                raise RuntimeError("Simulated error in request_stop")
            
            def run(self):
                time.sleep(0.1)
        
        worker = FaultyWorker()
        worker.start()
        
        time.sleep(0.05)
        
        # Cleanup should handle the exception and still terminate
        result = worker.cleanup(timeout_ms=500)
        
        # Should eventually stop (either normally or forced)
        self.assertFalse(worker.isRunning())
    
    def test_multiple_cleanup_calls(self):
        """Test that multiple cleanup calls are safe"""
        worker = NormalWorker()
        worker.start()
        
        time.sleep(0.05)
        
        # First cleanup
        result1 = worker.cleanup(timeout_ms=1000)
        self.assertTrue(result1)
        self.assertFalse(worker.isRunning())
        
        # Second cleanup should be safe (no-op)
        result2 = worker.cleanup(timeout_ms=1000)
        self.assertTrue(result2)
        self.assertFalse(worker.isRunning())
    
    def test_del_fallback_cleanup(self):
        """Test __del__ fallback cleanup
        
        Requirement 4.3: __del__ should provide fallback cleanup
        
        Note: This test is tricky because __del__ timing is unpredictable.
        We test that a running thread can be cleaned up when the object
        is deleted, but we can't guarantee __del__ is called immediately.
        """
        worker = NormalWorker()
        worker.start()
        
        time.sleep(0.05)
        self.assertTrue(worker.isRunning())
        
        # Delete the worker object
        # __del__ should be called and cleanup the thread
        worker_id = id(worker)
        del worker
        
        # Give some time for __del__ to be called
        time.sleep(0.2)
        
        # We can't directly verify the thread stopped since we deleted the object,
        # but if __del__ works correctly, it should have cleaned up
        # This test mainly ensures __del__ doesn't crash
    
    def test_cleanup_with_custom_timeout(self):
        """Test cleanup with various timeout values"""
        # Fast worker with long timeout
        worker1 = NormalWorker()
        worker1.start()
        time.sleep(0.05)
        
        result1 = worker1.cleanup(timeout_ms=5000)
        self.assertTrue(result1, "Fast worker should exit before long timeout")
        
        # Slow worker with very short timeout
        worker2 = SlowWorker(stop_delay_ms=1000)
        worker2.start()
        time.sleep(0.05)
        
        result2 = worker2.cleanup(timeout_ms=100)
        self.assertFalse(result2, "Slow worker should be terminated with short timeout")


class TestThreadCleanupMixinEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions"""
    
    @classmethod
    def setUpClass(cls):
        """Set up QCoreApplication for QThread tests"""
        if not QCoreApplication.instance():
            cls.app = QCoreApplication(sys.argv)
        else:
            cls.app = QCoreApplication.instance()
    
    def test_zero_timeout(self):
        """Test cleanup with zero timeout (immediate termination)"""
        worker = SlowWorker(stop_delay_ms=1000)
        worker.start()
        
        time.sleep(0.05)
        
        # Zero timeout should force immediate termination
        result = worker.cleanup(timeout_ms=0)
        
        self.assertFalse(result, "Zero timeout should force termination")
        self.assertFalse(worker.isRunning())
    
    def test_very_long_timeout(self):
        """Test cleanup with very long timeout"""
        worker = NormalWorker()
        worker.start()
        
        time.sleep(0.05)
        
        # Long timeout, but worker stops quickly
        result = worker.cleanup(timeout_ms=30000)
        
        self.assertTrue(result, "Worker should stop before long timeout")
        self.assertFalse(worker.isRunning())
    
    def test_rapid_start_stop_cycles(self):
        """Test rapid start/stop cycles"""
        for i in range(5):
            worker = NormalWorker()
            worker.start()
            time.sleep(0.02)
            
            result = worker.cleanup(timeout_ms=1000)
            self.assertTrue(result, f"Cycle {i} should cleanup successfully")
            self.assertFalse(worker.isRunning())


if __name__ == '__main__':
    unittest.main()
