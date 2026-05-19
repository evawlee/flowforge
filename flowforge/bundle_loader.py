import json
from typing import Any, Dict


class BundleLoaderError(Exception):
    pass


_ALLOWED_BUNDLE_KEYS = frozenset({"workflow_id", "nodes", "edges", "metadata", "version"})


class WorkflowBundleLoader:

    def __init__(self) -> None:
        self._known_node_types = {"http", "transform", "eval", "branch"}

    def load(self, blob: bytes) -> Dict[str, Any]:
        if not isinstance(blob, (bytes, bytearray)):
            raise BundleLoaderError("bundle blob must be bytes")
        if len(blob) == 0:
            raise BundleLoaderError("bundle blob is empty")
        try:
            text = bytes(blob).decode("utf-8")
        except UnicodeDecodeError as e:
            raise BundleLoaderError(f"bundle blob is not valid utf-8: {e}")
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as e:
            raise BundleLoaderError(f"failed to decode bundle: {e}")
        if not isinstance(payload, dict):
            raise BundleLoaderError("bundle payload must be a dict")
        unknown_keys = set(payload.keys()) - _ALLOWED_BUNDLE_KEYS
        if unknown_keys:
            raise BundleLoaderError(f"bundle contains unknown keys: {sorted(unknown_keys)}")
        return payload

    def serialize(self, payload: Dict[str, Any]) -> bytes:
        if not isinstance(payload, dict):
            raise BundleLoaderError("payload must be a dict")
        unknown_keys = set(payload.keys()) - _ALLOWED_BUNDLE_KEYS
        if unknown_keys:
            raise BundleLoaderError(f"payload contains unknown keys: {sorted(unknown_keys)}")
        return json.dumps(payload).encode("utf-8")

    def is_known_node_type(self, name: str) -> bool:
        return name in self._known_node_types

    def register_node_type(self, name: str) -> None:
        self._known_node_types.add(name)
