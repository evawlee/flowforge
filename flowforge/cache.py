from typing import Any, Dict, List, Optional


class RunCache:

    _active_runs: Dict[str, Dict[str, Any]] = {}
    _step_results: Dict[str, List[Dict[str, Any]]] = {}

    def start_run(self, run_id: str, workflow_id: str, tenant_id: str) -> None:
        self._active_runs[run_id] = {
            "workflow_id": workflow_id,
            "tenant_id": tenant_id,
            "status": "running",
        }
        self._step_results[run_id] = []

    def finish_run(self, run_id: str, status: str) -> None:
        if run_id in self._active_runs:
            self._active_runs[run_id]["status"] = status

    def append_step_result(self, run_id: str, step_id: str, output: Any) -> None:
        if run_id not in self._step_results:
            self._step_results[run_id] = []
        self._step_results[run_id].append({"step_id": step_id, "output": output})

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        return self._active_runs.get(run_id)

    def get_step_results(self, run_id: str) -> List[Dict[str, Any]]:
        return list(self._step_results.get(run_id, []))

    def list_active_runs(self) -> List[str]:
        return [k for k, v in self._active_runs.items() if v.get("status") == "running"]

    @classmethod
    def reset(cls) -> None:
        cls._active_runs.clear()
        cls._step_results.clear()
