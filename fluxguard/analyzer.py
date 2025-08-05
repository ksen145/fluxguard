import time
from typing import Dict, Any, List, Set, Optional, Callable
from collections import defaultdict
from .storage import FluxStorage
from .guards import apply_guard
from .reporter import generate_report, log_full_report

class FluxAnalyzer:

    def __init__(self, threshold_bottleneck: float = 1.0, threshold_race: int = 2):
        self.threshold_bottleneck = threshold_bottleneck
        self.threshold_race = threshold_race
        self.storage = FluxStorage()
        self.graph: Dict[str, Dict[str, Any]] = {}
        self.issues: List[Dict[str, Any]] = []

    def build_graph(self, data: Dict[str, Any]) -> None:
        self.graph.clear()
        prev_node = None
        for event in data.get('calls', []):
            node_id = f"event_{len(self.graph)}"
            self.graph[node_id] = {
                'depends_on': [prev_node] if prev_node else [],
                'duration': 0.0,
                'resources': set(),
                'start_time': event.get('timestamp', time.time()),
            }
            if 'resource' in event.get('details', {}):
                self.graph[node_id]['resources'].add(event['details']['resource'])
            prev_node = node_id

        nodes = sorted(self.graph.keys(), key=lambda n: self.graph[n]['start_time'])
        for i in range(1, len(nodes)):
            prev = nodes[i-1]
            curr = nodes[i]
            self.graph[curr]['duration'] = self.graph[curr]['start_time'] - self.graph[prev]['start_time']

        historical_data = self.storage.load('global')
        if historical_data:
            self._merge_historical(historical_data) # type: ignore

    def _merge_historical(self, historical_data: Dict[str, Any]) -> None:
        for node in self.graph:
            hist_duration = historical_data.get(node, {}).get('avg_duration', 0)
            if hist_duration:
                self.graph[node]['duration'] = (self.graph[node]['duration'] + hist_duration) / 2

    def detect_issues(self) -> None:
        self.issues.clear()

        for node, info in self.graph.items():
            if info['duration'] > self.threshold_bottleneck:
                self.issues.append({
                    'type': 'bottleneck',
                    'node': node,
                    'details': {'duration': info['duration']},
                    'suggestion': 'Add buffering or parallelization'
                })

        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        for node in self.graph:
            if node not in visited:
                if self._has_cycle(node, visited, rec_stack):
                    self.issues.append({
                        'type': 'deadlock',
                        'node': node,
                        'details': {'cycle': list(rec_stack)},
                        'suggestion': 'Add timeouts to locks'
                    })

        resource_access: defaultdict[str, List[str]] = defaultdict(list)
        for node, info in self.graph.items():
            for res in info['resources']:
                resource_access[res].append(node)
        for res, nodes in resource_access.items():
            if len(nodes) >= self.threshold_race:

                concurrent = any(
                    abs(self.graph[n1]['start_time'] - self.graph[n2]['start_time']) < 0.1
                    for i, n1 in enumerate(nodes)
                    for n2 in nodes[i+1:]
                )
                if concurrent:
                    self.issues.append({
                        'type': 'race_condition',
                        'node': res,  # Resource as "node"
                        'details': {'accessors': nodes},
                        'suggestion': 'Wrap with async locks'
                    })

    def _has_cycle(self, node: str, visited: Set[str], rec_stack: Set[str]) -> bool:
        visited.add(node)
        rec_stack.add(node)
        for dep in self.graph[node].get('depends_on', []):
            if dep not in visited:
                if self._has_cycle(dep, visited, rec_stack):
                    return True
            elif dep in rec_stack:
                return True
        rec_stack.remove(node)
        return False

    def suggest_fixes(self) -> Dict[str, Any]:
        fixes = {}
        for issue in self.issues:
            fix_code = apply_guard(issue)
            fixes[issue['node']] = {
                'issue': issue['type'],
                'fix': fix_code
            }
        return fixes

    def analyze(self, data: Dict[str, Any], func: Optional[Callable] = None) -> Dict[str, Any]:
        self.build_graph(data)
        self.detect_issues()
        fixes = self.suggest_fixes()

        func_name = func.__name__ if func else 'unknown'
        report = generate_report(self.graph, self.issues, fixes, func_name)
        if func:
            self.storage.save(func.__name__ + '_analysis', report)

        log_full_report(report, format='text')

        return {
            'graph': self.graph,
            'issues': self.issues,
            'fixes': fixes,
            'report': report
        }
