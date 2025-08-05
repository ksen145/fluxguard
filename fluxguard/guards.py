# fluxguard/guards.py
"""
Guards module for FluxGuard.

This module defines "guard" classes that provide auto-fixes or code suggestions
for detected issues in async code. Guards can modify AST or generate wrapper code
to prevent problems like deadlocks, race conditions, and bottlenecks.

Main usage: The apply_guard function dispatches to the appropriate guard based on issue type.
"""

import ast
from typing import Dict, Any, Optional

# Registry of guards by issue type
_guard_registry: Dict[str, 'BaseGuard'] = {}


class BaseGuard:
    """Base class for all guards. Subclasses implement specific fixes."""

    def __init__(self):
        pass

    def apply(self, issue: Dict[str, Any]) -> Optional[str]:
        """
        Apply the guard to the issue and return suggested fix code (as string).
        Returns None if no fix is applicable.
        """
        raise NotImplementedError("Subclasses must implement apply()")

    @staticmethod
    def register(issue_type: str):
        """Decorator to register a guard class in the registry."""
        def decorator(cls):
            _guard_registry[issue_type] = cls()
            return cls
        return decorator

    def generate_ast_fix(self, original_code: str, modification: ast.AST) -> str:
        """
        Helper to modify original code's AST and return the unparsed string.
        Note: Requires Python 3.9+ for ast.unparse; fallback to manual if needed.
        """
        tree = ast.parse(original_code)
        # Simplified: Append modification to body (e.g., add a wrapper)
        if isinstance(tree.body[0], ast.FunctionDef) and isinstance(modification, ast.stmt):
            tree.body[0].body.insert(0, modification)
        return ast.unparse(tree)  # Generate fixed code string


@BaseGuard.register('bottleneck')
class BottleneckGuard(BaseGuard):
    """Guard for bottlenecks: Suggests adding buffering or parallelization."""

    def apply(self, issue: Dict[str, Any]) -> Optional[str]:
        node = issue.get('node')
        details = issue.get('details', {})
        duration = details.get('duration', 0)

        # Generate simple fix: Wrap with asyncio.gather for parallelization (placeholder)
        fix_code = f"""
# FluxGuard Fix: Add buffering for bottleneck at {node} (duration: {duration:.2f}s)
import asyncio

async def buffered_{node}(*args, **kwargs):
    queue = asyncio.Queue(maxsize=10)  # Buffer tasks
    async def worker():
        while True:
            task = await queue.get()
            await task  # Execute buffered task
            queue.task_done()

    # Start worker
    asyncio.create_task(worker())
    # Original code here...
    await queue.put(original_task)  # Enqueue original
    await queue.join()
"""
        return fix_code


@BaseGuard.register('deadlock')
class DeadlockGuard(BaseGuard):
    """Guard for deadlocks: Adds timeouts to locks."""

    def apply(self, issue: Dict[str, Any]) -> Optional[str]:
        node = issue.get('node')
        details = issue.get('details', {})
        cycle = details.get('cycle', [])

        # Generate fix: Add asyncio.wait_for with timeout
        fix_code = f"""
# FluxGuard Fix: Add timeout to prevent deadlock at {node} (cycle: {cycle})
import asyncio

async def timeout_{node}(*args, **kwargs):
    try:
        return await asyncio.wait_for(original_coroutine(*args, **kwargs), timeout=5.0)
    except asyncio.TimeoutError:
        print("Deadlock timeout at {node}")
        raise
"""
        return fix_code


@BaseGuard.register('race_condition')
class RaceGuard(BaseGuard):
    """Guard for race conditions: Wraps shared resources with async locks."""

    def apply(self, issue: Dict[str, Any]) -> Optional[str]:
        resource = issue.get('node')  # Resource name
        details = issue.get('details', {})
        accessors = details.get('accessors', [])

        # Generate fix: Use asyncio.Lock around accesses
        fix_code = f"""
# FluxGuard Fix: Add lock for race condition on resource '{resource}' (accessors: {accessors})
import asyncio

lock = asyncio.Lock()

async def locked_access(*args, **kwargs):
    async with lock:
        # Original access to {resource} here...
        return await original_function(*args, **kwargs)
"""
        return fix_code


def apply_guard(issue: Dict[str, Any]) -> Optional[str]:
    """
    Dispatch to the appropriate guard based on issue type and apply it.
    Returns the suggested fix code or None if no guard matches.
    """
    issue_type = issue.get('type')
    guard = _guard_registry.get(issue_type) # type: ignore
    if guard:
        return guard.apply(issue)
    return None
