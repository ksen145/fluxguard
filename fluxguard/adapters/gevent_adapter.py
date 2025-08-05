import gevent
from gevent import Greenlet
import time
from typing import Callable
from ..core import get_active_monitors

class GeventAdapter:
    def __init__(self):
        self.original_spawn = gevent.spawn

    def monitored_spawn(self, func: Callable, *args, **kwargs) -> Greenlet:
        def wrapped(*args, **kwargs):
            monitors = get_active_monitors()
            if monitors:
                monitor = next(iter(monitors.values()))
                start_time = time.time()
                monitor.log_event('gevent_start', {'func': func.__name__, 'timestamp': start_time, 'resources': set(['greenlet'])})

                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    monitor.log_event('gevent_end', {'duration': duration, 'result': result, 'timestamp': time.time()})
                    return result
                except Exception as e:
                    monitor.log_event('gevent_error', {'error': str(e), 'timestamp': time.time()})
                    raise

        return self.original_spawn(wrapped, *args, **kwargs)

    def enable(self):
        gevent.spawn = self.monitored_spawn

def enable_gevent_adapter():
    adapter = GeventAdapter()
    adapter.enable()
    return adapter
