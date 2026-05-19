from typing import Any, Dict, List


class AuditWriter:

    def __init__(self) -> None:
        self._entries: List[Dict[str, Any]] = []

    def write_event(self, event_kind: str, actor: str, payload: Dict[str, Any]) -> None:
        entry = {
            "kind": event_kind,
            "actor": actor,
            "payload": dict(payload),
        }
        self._entries.append(entry)

    def write_node_execution(self, run_id: str, step_id: str, actor: str, payload: Dict[str, Any]) -> None:
        entry = {
            "kind": "node_execution",
            "run_id": run_id,
            "step_id": step_id,
            "actor": actor,
            "payload": dict(payload),
        }
        self._entries.append(entry)

    def find_by_run(self, run_id: str) -> List[Dict[str, Any]]:
        return [e for e in self._entries if e.get("run_id") == run_id]

    def find_by_actor(self, actor: str) -> List[Dict[str, Any]]:
        return [e for e in self._entries if e.get("actor") == actor]

    def entries(self) -> List[Dict[str, Any]]:
        return list(self._entries)

    def size(self) -> int:
        return len(self._entries)
