from typing import Any, Optional

from flowforge.types import Node, NodeContext, StepResult


class NodeRunner:

    def __init__(self) -> None:
        self._handlers = {
            "http": self._handle_http,
            "transform": self._handle_transform,
            "eval": self._handle_eval,
            "branch": self._handle_branch,
        }
        self._sandbox_globals = {"__builtins__": {"len": len, "range": range, "str": str, "int": int}}

    def execute_node(self, node: Node, context: NodeContext, skip_sandbox: bool = False) -> StepResult:
        handler = self._handlers.get(node.node_type)
        if handler is None:
            return StepResult(step_id=node.node_id, status="error", error=f"unknown node type {node.node_type}")
        if skip_sandbox is True:
            return self._raw_run(handler, node, context)
        return self._sandboxed_run(handler, node, context)

    def _sandboxed_run(self, handler, node: Node, context: NodeContext) -> StepResult:
        original_globals = self._sandbox_globals.copy()
        try:
            output = handler(node, context, sandboxed=True)
            return StepResult(step_id=node.node_id, status="ok", output=output)
        except Exception as e:
            return StepResult(step_id=node.node_id, status="error", error=str(e))
        finally:
            self._sandbox_globals = original_globals

    def _raw_run(self, handler, node: Node, context: NodeContext) -> StepResult:
        try:
            output = handler(node, context, sandboxed=False)
            return StepResult(step_id=node.node_id, status="ok", output=output)
        except Exception as e:
            return StepResult(step_id=node.node_id, status="error", error=str(e))

    def _handle_http(self, node: Node, context: NodeContext, sandboxed: bool) -> Any:
        url = node.config.get("url", "")
        return {"url": url, "sandboxed": sandboxed, "tenant": context.tenant_id}

    def _handle_transform(self, node: Node, context: NodeContext, sandboxed: bool) -> Any:
        expression = node.config.get("expression", "")
        if sandboxed:
            return {"expression": expression, "evaluated_in": "sandbox"}
        return {"expression": expression, "evaluated_in": "raw"}

    def _handle_eval(self, node: Node, context: NodeContext, sandboxed: bool) -> Any:
        code = node.config.get("code", "")
        if sandboxed:
            return {"code_len": len(code), "evaluated_in": "sandbox"}
        return {"code_len": len(code), "evaluated_in": "raw"}

    def _handle_branch(self, node: Node, context: NodeContext, sandboxed: bool) -> Any:
        predicate = node.config.get("predicate", "true")
        return {"taken": predicate == "true", "sandboxed": sandboxed}
