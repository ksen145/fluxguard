# fluxguard/__init__.py
"""
FluxGuard: A library for monitoring and adapting asynchronous Python code.

This package provides tools to create "flow guards" that analyze and protect
async functions from common issues like deadlocks, race conditions, and bottlenecks.

Main usage:
    from fluxguard import guard_coroutine

    @guard_coroutine
    async def my_async_func():
        ...

For more details, see the documentation.
"""

from .core import guard_coroutine
# Import other key components here as you add them, e.g.:
# from .analyzer import FluxAnalyzer
# from .reporter import generate_report

__version__ = '0.1.0'  # Initial version; update as needed
__all__ = ['guard_coroutine']  # Explicitly define what gets imported with 'from fluxguard import *'
