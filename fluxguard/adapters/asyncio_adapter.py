import asyncio
import traceback
from typing import Callable, Any, Optional, Dict
from ..core import FluxMonitor, get_active_monitors  # Import from core for monitor access


class AsyncioAdapter:

    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        self.loop = loop or asyncio.get_running_loop()
        self.original_task_factory = self.loop.get_task_factory()
        self.original_exception_handler = self.loop.get_exception_handler()
        self._setup_hooks()

    def _setup_hooks(self) -> None:
        self.loop.set_debug(True)

        self.loop.set_task_factory(self._monitored_task_factory)
        self.loop.set_exception_handler(self._monitored_exception_handler)

    def _monitored_task_factory(self, loop: asyncio.AbstractEventLoop, coro: Callable) -> asyncio.Task:
        task = self.original_task_factory(loop, coro) if self.original_task_factory else asyncio.Task(coro, loop=loop)
        
        monitors = get_active_monitors()
        if monitors:
            monitor = next(iter(monitors.values()))
            task_id = id(task)
            monitor.log_event('task_created', {'task_id': task_id, 'name': task.get_name()})
            
            def done_callback(future: asyncio.Future):
                if future.exception():
                    monitor.log_event('task_exception', {'task_id': task_id, 'exception': str(future.exception())})
                else:
                    monitor.log_event('task_completed', {'task_id': task_id, 'result': future.result()})
            
            task.add_done_callback(done_callback)
        
        return task

    def _monitored_exception_handler(self, loop: asyncio.AbstractEventLoop, context: Dict[str, Any]) -> None:
        if self.original_exception_handler:
            self.original_exception_handler(loop, context)
        
        monitors = get_active_monitors()
        if monitors:
            monitor = next(iter(monitors.values()))
            exc = context.get('exception')
            msg = context.get('message', 'Unhandled exception')
            stack = traceback.format_exc() if exc else ''
            monitor.log_event('exception', {'message': msg, 'stack': stack})

    def monitor_await(self, awaitable: Any, monitor: FluxMonitor) -> Any:
        async def wrapped():
            start = asyncio.get_running_loop().time()
            result = await awaitable
            duration = asyncio.get_running_loop().time() - start
            monitor.log_event('await', {'duration': duration, 'type': type(awaitable).__name__})
            return result
        return wrapped()

    def cleanup(self) -> None:
        self.loop.set_task_factory(self.original_task_factory)
        self.loop.set_exception_handler(self.original_exception_handler)
        self.loop.set_debug(False)


def enable_asyncio_adapter(loop: Optional[asyncio.AbstractEventLoop] = None) -> AsyncioAdapter:
    return AsyncioAdapter(loop)


def log_asyncio_event(event_type: str, details: Dict[str, Any]) -> None:
    monitors = get_active_monitors()
    if monitors:
        monitor = next(iter(monitors.values()))
        monitor.log_event(event_type, details)
