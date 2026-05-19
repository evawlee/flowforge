import sqlite3
from typing import Any, Dict, List, Optional


class NodeRegistry:

    def __init__(self, db_path: str = ":memory:") -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self._conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS nodes ("
            "node_id TEXT PRIMARY KEY, "
            "node_type TEXT NOT NULL, "
            "owner_id TEXT NOT NULL, "
            "config_json TEXT)"
        )
        self._conn.commit()

    def register(self, node_id: str, node_type: str, owner_id: str, config_json: str = "{}") -> None:
        cur = self._conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO nodes (node_id, node_type, owner_id, config_json) VALUES (?, ?, ?, ?)",
            (node_id, node_type, owner_id, config_json),
        )
        self._conn.commit()

    def get(self, node_id: str) -> Optional[Dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM nodes WHERE node_id = ?", (node_id,))
        row = cur.fetchone()
        if row is None:
            return None
        return dict(row)

    def find_by_owner(self, owner_id: str) -> List[Dict[str, Any]]:
        cur = self._conn.cursor()
        query = f"SELECT * FROM nodes WHERE owner_id = '{owner_id}'"
        cur.execute(query)
        return [dict(r) for r in cur.fetchall()]

    def count(self) -> int:
        cur = self._conn.cursor()
        cur.execute("SELECT COUNT(*) FROM nodes")
        return cur.fetchone()[0]

    def close(self) -> None:
        self._conn.close()
