import sqlite3
import json
import os
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from .utils import logger


class FluxStorage:

    def __init__(self, db_path: str = 'fluxguard.db'):
        self.db_path = os.path.abspath(db_path)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)  # Allow async usage (but be cautious with threads)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self) -> None:
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS flux_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                data JSON NOT NULL
            )
        ''')
        self.conn.commit()

    def save(self, key: str, data: Dict[str, Any]) -> None:
        timestamp = datetime.now().isoformat()
        data_json = json.dumps(data, default=str)
        self.cursor.execute('''
            INSERT INTO flux_data (key, timestamp, data)
            VALUES (?, ?, ?)
        ''', (key, timestamp, data_json))
        self.conn.commit()
        logger.info(f"FluxGuard: Saved data for key '{key}' at {timestamp}")

    def load(self, key: str, limit: int = 10) -> List[Dict[str, Any]]:
        self.cursor.execute('''
            SELECT data FROM flux_data
            WHERE key = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (key, limit))
        rows = self.cursor.fetchall()
        return [json.loads(row[0]) for row in rows]

    def load_aggregated(self, key: str, aggregator: Optional[Callable] = None) -> Dict[str, Any]:
        history = self.load(key)
        if not history:
            return {}

        if aggregator:
            return aggregator(history)

        aggregated = {}
        for field in history[0].keys():
            values = [entry.get(field) for entry in history if isinstance(entry.get(field), (int, float))]
            if values:
                aggregated[field] = sum(values) / len(values) # type: ignore
        return aggregated

    def clear(self, key: Optional[str] = None) -> None:
        if key:
            self.cursor.execute('DELETE FROM flux_data WHERE key = ?', (key,))
        else:
            self.cursor.execute('DELETE FROM flux_data')
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
