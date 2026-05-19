from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Node:
    node_id: str
    node_type: str
    config: Dict[str, Any] = field(default_factory=dict)
    owner_id: Optional[str] = None


@dataclass
class NodeContext:
    run_id: str
    workflow_id: str
    tenant_id: str
    invoked_by: str
    inputs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RunEvent:
    run_id: str
    step_id: str
    actor: str
    payload: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"


@dataclass
class StepResult:
    step_id: str
    status: str
    output: Any = None
    error: Optional[str] = None
