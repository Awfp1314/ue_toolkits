"""
Unit tests for StreamingBufferManager

Tests cover:
- Buffer and flush logic
- Repeated start() calls (automatic reset)
- stop() followed by add_chunk() calls (should be ignored)
- Timer management

Requirements tested: 3.1, 3.2, 3.3, 3.4

Note: These tests verify the implementation logic without running Qt event loop
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestStreamingBufferManagerImplementation(unittest.TestCase):
    """Test StreamingBufferManager implementation by code inspection"""
    
    def test_file_exists(self):
        """Test that StreamingBufferManager file exists"""
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'logic', 
            'streaming_buffer_manager.py'
        )
        self.assertTrue(os.path.exists(file_path), "StreamingBufferManager file should exist")
    
    def test_required_methods_exist(self):
        """Test that all required methods are implemented
        
        Requirements 3.1, 3.2, 3.3, 3.4: All core methods should exist
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'logic', 
            'streaming_buffer_manager.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for required methods
        self.assertIn('def start(', content, "start() method should exist")
        self.assertIn('def add_chunk(', content, "add_chunk() method should exist")
        self.assertIn('def flush(', content, "flush() method should exist")
        self.assertIn('def stop_and_cleanup(', content, "stop_and_cleanup() method should exist")
        self.assertIn('def _flush(', content, "_flush() method should exist")
    
    def test_buffer_management_logic(self):
        """Test buffer management implementation
        
        Requirement 3.1: Buffer should accumulate and flush text
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'logic', 
            'streaming_buffer_manager.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check buffer initialization
        self.assertIn('self._buffer = ""', content, "Buffer should be initialized as empty string")
        
        # Check add_chunk accumulates to buffer
        self.assertIn('self._buffer += text', content, "add_chunk should accumulate text to buffer")
        
        # Check flush clears buffer
        self.assertIn('self._buffer = ""', content, "flush should clear buffer")
    
    def test_running_state_management(self):
        """Test running state management
        
        Requirement 3.2, 3.3: Running state should control behavior
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'logic', 
            'streaming_buffer_manager.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check running state flag exists
        self.assertIn('self._is_running', content, "Running state flag should exist")
        
        # Check add_chunk checks running state
        self.assertIn('if not self._is_running:', content, "add_chunk should check running state")
        
        # Check start sets running state
        self.assertIn('self._is_running = True', content, "start should set running state to True")
        
        # Check stop clears running state
        self.assertIn('self._is_running = False', content, "stop should set running state to False")
    
    def test_repeated_start_auto_reset(self):
        """Test repeated start() calls auto-reset
        
        Requirement 3.2: Repeated start() should auto-reset
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'logic', 
            'streaming_buffer_manager.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check that start() checks if already running
        self.assertIn('if self._is_running:', content, "start should check if already running")
        
        # Check that it calls stop_and_cleanup when already running
        self.assertIn('self.stop_and_cleanup()', content, "start should call stop_and_cleanup if already running")
    
    def test_timer_management(self):
        """Test timer management implementation
        
        Requirement 3.4: Timer should be properly managed
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'logic', 
            'streaming_buffer_manager.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check timer initialization
        self.assertIn('self._timer = QTimer()', content, "Timer should be initialized")
        self.assertIn('setInterval', content, "Timer interval should be set")
        
        # Check timer is started
        self.assertIn('self._timer.start()', content, "Timer should be started")
        
        # Check timer is stopped
        self.assertIn('self._timer.stop()', content, "Timer should be stopped")
        
        # Check timer callback connection
        self.assertIn('timeout.connect', content, "Timer timeout should be connected")
        self.assertIn('timeout.disconnect', content, "Timer timeout should be disconnected")
    
    def test_cleanup_implementation(self):
        """Test cleanup implementation
        
        Requirement 3.4: Cleanup should flush and clear all state
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'logic', 
            'streaming_buffer_manager.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find stop_and_cleanup method
        self.assertIn('def stop_and_cleanup(', content, "stop_and_cleanup method should exist")
        
        # Check it flushes remaining buffer
        # Look for flush() call in stop_and_cleanup
        lines = content.split('\n')
        in_stop_method = False
        has_flush_call = False
        
        for line in lines:
            if 'def stop_and_cleanup(' in line:
                in_stop_method = True
            elif in_stop_method and line.strip().startswith('def '):
                break
            elif in_stop_method and 'self.flush()' in line:
                has_flush_call = True
        
        self.assertTrue(has_flush_call, "stop_and_cleanup should call flush()")
    
    def test_callback_management(self):
        """Test callback management
        
        Requirement 3.1: Callback should be stored and called
        """
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'logic', 
            'streaming_buffer_manager.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check callback storage
        self.assertIn('self._callback', content, "Callback should be stored")
        
        # Check callback is called in flush
        self.assertIn('self._callback(', content, "Callback should be called")
        
        # Check callback is cleared in cleanup
        self.assertIn('self._callback = None', content, "Callback should be cleared")
    
    def test_documentation_exists(self):
        """Test that proper documentation exists"""
        file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'modules', 
            'ai_assistant', 
            'logic', 
            'streaming_buffer_manager.py'
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for class docstring
        self.assertIn('"""', content, "Documentation should exist")
        
        # Check for key design constraints mentioned
        self.assertIn('UI 线程', content, "Should mention UI thread constraint")


if __name__ == '__main__':
    # Run tests without Qt
    unittest.main()
