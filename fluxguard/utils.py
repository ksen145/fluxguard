# fluxguard/utils.py
"""
Utilities module for FluxGuard.

This module provides helper functions for graph operations, logging, timing,
and other shared utilities used across the library.
"""

import logging
import time
from typing import Dict, Any, Set, Callable, List
from contextlib import contextmanager
from collections import defaultdict
import json


# Logging setup
logger = logging.getLogger('fluxguard')
logger.setLevel(logging.INFO)  # Default level; can be adjusted
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def set_log_level(level: int) -> None:
    """Set the logging level for the FluxGuard logger."""
    logger.setLevel(level)


# Graph utilities
def has_cycle(graph: Dict[str, List[str]], node: str, visited: Set[str], rec_stack: Set[str]) -> bool:
    """
    DFS-based cycle detection in a directed graph.
    Assumes graph is dict of node -> list of dependencies.
    """
    visited.add(node)
    rec_stack.add(node)
    for dep in graph.get(node, []):
        if dep not in visited:
            if has_cycle(graph, dep, visited, rec_stack):
                return True
        elif dep in rec_stack:
            return True
    rec_stack.remove(node)
    return False


def build_dependency_graph(events: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Build a simple dependency graph from a list of events.
    Assumes events have 'type' and 'details' with possible 'depends_on'.
    """
    graph = defaultdict(list)
    prev_node = None
    for event in events:
        node = event.get('type', 'unknown')
        if prev_node:
            graph[prev_node].append(node)
        prev_node = node
        # Add any explicit dependencies
        deps = event.get('details', {}).get('depends_on', [])
        graph[node].extend(deps)
    return dict(graph)


# Timing utilities
@contextmanager
def timer(label: str) -> float:
    """Context manager to time a block of code and log the duration."""
    start = time.time()
    yield
    duration = time.time() - start
    logger.info(f"Timer '{label}': {duration:.4f} seconds")
    return duration


def timed(func: Callable) -> Callable:
    """Decorator to time a function's execution."""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        logger.info(f"Function '{func.__name__}' took {duration:.4f} seconds")
        return result
    return wrapper


# Other helpers (e.g., for AST or serialization if needed)
def safe_json_dump(obj: Any) -> str:
    """Safely dump an object to JSON string, handling non-serializable types."""
    def default_handler(o):
        if isinstance(o, set):
            return list(o)
        return str(o)
    return json.dumps(obj, default=default_handler)
