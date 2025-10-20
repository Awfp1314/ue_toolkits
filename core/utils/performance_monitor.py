# -*- coding: utf-8 -*-

"""
性能监控工具 - 跟踪应用程序性能指标

提供：
1. 启动时间跟踪
2. 内存使用监控
3. 模块加载时间
4. 性能数据导出
"""

import time
import psutil
from typing import Dict, Any, Optional
from pathlib import Path
import json
from core.logger import get_logger

logger = get_logger(__name__)


class PerformanceMonitor:
    """性能监控器（单例）
    
    跟踪和记录应用程序性能指标
    
    Features:
        - 启动时间跟踪
        - 内存使用监控
        - 模块加载时间
        - CPU使用率
        - 线程数统计
        - 性能报告导出
    
    Example:
        monitor = get_performance_monitor()
        
        monitor.start_tracking('app_startup')
        # ... 启动逻辑
        monitor.end_tracking('app_startup')
        
        monitor.record_memory_usage('after_init')
        
        metrics = monitor.get_metrics()
        
        monitor.export_metrics('performance_report.json')
    """
    
    _instance: Optional['PerformanceMonitor'] = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化性能监控器"""
        # 避免重复初始化
        if hasattr(self, '_initialized'):
            return
        
        self.metrics: Dict[str, Any] = {
            'startup_time': 0,
            'module_load_times': {},
            'memory_usage': {},
            'cpu_usage': {},
            'thread_count': {},
            'tracking_start': {},
        }
        
        try:
            self.process = psutil.Process()
        except Exception as e:
            logger.warning(f"无法初始化psutil.Process: {e}")
            self.process = None
        
        self._initialized = True
        logger.info("性能监控器初始化完成")
    
    def start_tracking(self, metric_name: str):
        """开始跟踪性能指标
        
        Args:
            metric_name: 指标名称
            
        Example:
            monitor.start_tracking('module_load')
            # ... 加载模块
            monitor.end_tracking('module_load')
        """
        self.metrics['tracking_start'][metric_name] = time.time()
        logger.debug(f"开始跟踪指标: {metric_name}")
    
    def end_tracking(self, metric_name: str) -> Optional[float]:
        """结束跟踪指标并返回持续时间
        
        Args:
            metric_name: 指标名称
            
        Returns:
            Optional[float]: 持续时间（秒），如果未找到起始时间则返回None
            
        Example:
            duration = monitor.end_tracking('module_load')
            print(f"加载耗时: {duration:.3f}秒")
        """
        start_key = 'tracking_start'
        if metric_name in self.metrics[start_key]:
            start_time = self.metrics[start_key][metric_name]
            duration = time.time() - start_time
            
            # 存储到相应的指标类别
            if 'module' in metric_name.lower():
                self.metrics['module_load_times'][metric_name] = duration
            else:
                self.metrics[metric_name] = duration
            
            del self.metrics[start_key][metric_name]
            
            logger.info(f"性能指标 [{metric_name}]: {duration:.3f}秒")
            return duration
        else:
            logger.warning(f"未找到指标 {metric_name} 的起始时间")
            return None
    
    def record_memory_usage(self, checkpoint: str):
        """记录内存使用情况
        
        Args:
            checkpoint: 检查点名称
            
        Example:
            monitor.record_memory_usage('after_startup')
        """
        if not self.process:
            return
        
        try:
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()
            
            self.metrics['memory_usage'][checkpoint] = {
                'rss_mb': round(memory_info.rss / 1024 / 1024, 2),  # MB
                'vms_mb': round(memory_info.vms / 1024 / 1024, 2),  # MB
                'percent': round(memory_percent, 2)
            }
            
            logger.debug(
                f"内存使用 [{checkpoint}]: "
                f"{self.metrics['memory_usage'][checkpoint]['rss_mb']} MB "
                f"({self.metrics['memory_usage'][checkpoint]['percent']}%)"
            )
            
        except Exception as e:
            logger.error(f"记录内存使用失败: {e}")
    
    def record_cpu_usage(self, checkpoint: str, interval: float = 0.1):
        """记录CPU使用情况
        
        Args:
            checkpoint: 检查点名称
            interval: 采样间隔（秒）
            
        Example:
            monitor.record_cpu_usage('during_load')
        """
        if not self.process:
            return
        
        try:
            cpu_percent = self.process.cpu_percent(interval=interval)
            
            self.metrics['cpu_usage'][checkpoint] = {
                'percent': round(cpu_percent, 2),
                'num_threads': self.process.num_threads()
            }
            
            logger.debug(
                f"CPU使用 [{checkpoint}]: {cpu_percent:.2f}%, "
                f"线程数: {self.process.num_threads()}"
            )
            
        except Exception as e:
            logger.error(f"记录CPU使用失败: {e}")
    
    def record_thread_count(self, checkpoint: str):
        """记录线程数量
        
        Args:
            checkpoint: 检查点名称
        """
        if not self.process:
            return
        
        try:
            thread_count = self.process.num_threads()
            self.metrics['thread_count'][checkpoint] = thread_count
            logger.debug(f"线程数 [{checkpoint}]: {thread_count}")
            
        except Exception as e:
            logger.error(f"记录线程数失败: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取所有性能指标
        
        Returns:
            Dict[str, Any]: 性能指标字典
            
        Example:
            metrics = monitor.get_metrics()
            print(f"启动时间: {metrics.get('startup_time', 0):.3f}秒")
        """
        # 清理tracking_start（不包含在导出中）
        export_metrics = {k: v for k, v in self.metrics.items() if k != 'tracking_start'}
        return export_metrics
    
    def export_metrics(self, output_file: str):
        """导出性能指标到JSON文件
        
        Args:
            output_file: 输出文件路径
            
        Example:
            monitor.export_metrics('performance_report.json')
        """
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            metrics = self.get_metrics()
            
            # 添加时间戳和系统信息
            export_data = {
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                'system_info': self._get_system_info(),
                'metrics': metrics
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"性能指标已导出到: {output_path}")
            
        except Exception as e:
            logger.error(f"导出性能指标失败: {e}", exc_info=True)
    
    def _get_system_info(self) -> Dict[str, Any]:
        """获取系统信息
        
        Returns:
            Dict[str, Any]: 系统信息
        """
        import platform
        
        try:
            return {
                'platform': platform.system(),
                'platform_release': platform.release(),
                'platform_version': platform.version(),
                'architecture': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'total_memory_gb': round(psutil.virtual_memory().total / (1024**3), 2)
            }
        except Exception as e:
            logger.error(f"获取系统信息失败: {e}")
            return {}
    
    def print_summary(self):
        """打印性能摘要到日志
        
        Example:
            monitor.print_summary()
        """
        logger.info("=" * 60)
        logger.info("性能监控摘要")
        logger.info("=" * 60)
        
        metrics = self.get_metrics()
        
        # 启动时间
        if 'startup_time' in metrics and metrics['startup_time'] > 0:
            logger.info(f"启动时间: {metrics['startup_time']:.3f}秒")
        
        # 模块加载时间
        if metrics.get('module_load_times'):
            logger.info("模块加载时间:")
            for module, duration in metrics['module_load_times'].items():
                logger.info(f"  {module}: {duration:.3f}秒")
        
        # 内存使用
        if metrics.get('memory_usage'):
            logger.info("内存使用:")
            for checkpoint, mem in metrics['memory_usage'].items():
                logger.info(f"  {checkpoint}: {mem['rss_mb']} MB ({mem['percent']}%)")
        
        # CPU使用
        if metrics.get('cpu_usage'):
            logger.info("CPU使用:")
            for checkpoint, cpu in metrics['cpu_usage'].items():
                logger.info(f"  {checkpoint}: {cpu['percent']}%")
        
        logger.info("=" * 60)
    
    def reset(self):
        """重置所有指标
        
        Example:
            monitor.reset()  # 清空所有指标数据
        """
        self.metrics = {
            'startup_time': 0,
            'module_load_times': {},
            'memory_usage': {},
            'cpu_usage': {},
            'thread_count': {},
            'tracking_start': {},
        }
        logger.info("性能指标已重置")


# 全局实例
_global_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器实例
    
    Returns:
        PerformanceMonitor: 全局性能监控器
        
    Example:
        monitor = get_performance_monitor()
        monitor.start_tracking('my_task')
    """
    global _global_performance_monitor
    if _global_performance_monitor is None:
        _global_performance_monitor = PerformanceMonitor()
    return _global_performance_monitor


# 便捷函数
def track_performance(metric_name: str):
    """性能跟踪装饰器
    
    Args:
        metric_name: 指标名称
        
    Example:
        @track_performance('data_processing')
        def process_data(data):
            # ... 处理逻辑
            return result
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            monitor.start_tracking(metric_name)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                monitor.end_tracking(metric_name)
        return wrapper
    return decorator

