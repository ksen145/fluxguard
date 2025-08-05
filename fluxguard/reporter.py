import json
from typing import Dict, Any, List
from pprint import pformat
import logging
from .utils import logger


file_handler = logging.FileHandler('fluxguard.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

def generate_report(graph: Dict[str, Dict[str, Any]], issues: List[Dict[str, Any]], fixes: Dict[str, Any], func_name: str = 'unknown') -> Dict[str, Any]:
    report = {
        'endpoint': func_name,
        'summary': {
            'node_count': len(graph),
            'issue_count': len(issues),
            'fix_count': len(fixes),
        },
        'graph': _summarize_graph(graph),
        'issues': issues,
        'fixes': fixes,
    }
    return report


def _summarize_graph(graph: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    summary = []
    for node, info in graph.items():
        summary.append({
            'node': node,
            'duration': info.get('duration', 0.0),
            'depends_on': info.get('depends_on', []),
            'resources': list(info.get('resources', set())),
        })
    return summary


def text_report(report: Dict[str, Any]) -> str:
    lines = []
    lines.append(f"FluxGuard Analysis Report for endpoint: {report['endpoint']}") 
    lines.append("FluxGuard Analysis Report")
    lines.append("=========================")
    lines.append("\nSummary:")
    lines.append(pformat(report['summary']))
    lines.append("\nGraph Summary:")
    lines.append(pformat(report['graph']))
    lines.append("\nDetected Issues:")
    lines.append(pformat(report['issues']))
    lines.append("\nSuggested Fixes:")
    lines.append(pformat(report['fixes']))
    return "\n".join(lines)


def json_report(report: Dict[str, Any]) -> str:
    return json.dumps(report, indent=4, default=str)


def print_report(report: Dict[str, Any], format: str = 'text') -> None:
    if format == 'text':
        print(text_report(report))
    elif format == 'json':
        print(json_report(report))
    else:
        raise ValueError(f"Unsupported report format: {format}")


def log_full_report(report: Dict[str, Any], format: str = 'text', level: int = logging.INFO, func_name: str = 'unknown') -> None:
    if format == 'text':
        report_str = text_report(report)
    elif format == 'json':
        report_str = json_report(report)
    else:
        raise ValueError("Unsupported format")

    logger.log(level, func_name, "Full FluxGuard Report:\n%s", report_str)