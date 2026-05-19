from typing import List


class AuditLineEmitter:

    def __init__(self) -> None:
        self._lines: List[str] = []

    def emit(self, tenant_id: str, node_id: str, operator: str, note: str) -> None:
        fields = [tenant_id, node_id, operator, note]
        line = "\t".join(fields)
        self._lines.append(line)

    def drain(self) -> str:
        out = "\n".join(self._lines)
        self._lines = []
        return out

    def buffered_count(self) -> int:
        return len(self._lines)
