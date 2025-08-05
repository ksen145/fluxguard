import asyncio
import functools
import inspect
import time
from typing import Callable, Any, Dict
from .analyzer import FluxAnalyzer
from .storage import FluxStorage
from .utils import logger
import sys
if 'gevent' in sys.modules:
    from .adapters.gevent_adapter import enable_gevent_adapter
    enable_gevent_adapter()

_active_monitors: Dict[int, 'FluxMonitor'] = {}


class FluxMonitor:

    def __init__(self, task_id: int, func: Callable):
        self.task_id = task_id
        self.func = func
        self.start_time: float = None # type: ignore
        self.end_time: float = None # type: ignore
        self.data: Dict[str, Any] = {
            'calls': [],  # List of sub-calls or events
            'resources': set(),  # Tracked resources (e.g., locks)
            'duration': 0.0,
        }
        self.analyzer = FluxAnalyzer()  # Initialize analyzer
        self.storage = FluxStorage()    # For saving history

    def start(self):
        self.start_time = time.time()
        _active_monitors[self.task_id] = self
        logger.info(f"FluxGuard: Monitoring started for task {self.task_id} ({self.func.__name__})") 

    def stop_and_analyze(self):
        self.end_time = time.time()
        self.data['duration'] = self.end_time - self.start_time
        self.analyzer.analyze(self.data, self.func)
        self.storage.save(self.func.__name__, self.data)
        del _active_monitors[self.task_id]
        logger.info(f"FluxGuard: Monitoring stopped for task {self.task_id}. Duration: {self.data['duration']:.2f}s")  

    def log_event(self, event_type: str, details: Any):
        self.data['calls'].append({'type': event_type, 'details': details, 'timestamp': time.time()})


def guard_coroutine(func: Callable) -> Callable:
    if not inspect.iscoroutinefunction(func):
        raise ValueError("guard_coroutine can only be applied to async functions")

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            current_task = asyncio.current_task()
        except RuntimeError:
            raise RuntimeError("FluxGuard requires an active asyncio event loop")

        task_id = id(current_task)
        monitor = FluxMonitor(task_id, func)
        monitor.start()
        try:
            result = await func(*args, **kwargs)
        except Exception as e:
            monitor.log_event('error', str(e))
            raise
        finally:
            monitor.stop_and_analyze()
        return result

    return wrapper

def get_active_monitors() -> Dict[int, FluxMonitor]:
    return _active_monitors.copy()
