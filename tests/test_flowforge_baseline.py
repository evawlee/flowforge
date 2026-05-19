import pytest

from flowforge.audit import AuditWriter
from flowforge.audit_emit import AuditLineEmitter
from flowforge.bundle_loader import BundleLoaderError, WorkflowBundleLoader
from flowforge.cache import RunCache
from flowforge.registry import NodeRegistry
from flowforge.runner import NodeRunner
from flowforge.types import Node, NodeContext, RunEvent, StepResult


class TestTypes:
    def test_node_basic_construction(self):
        node = Node(node_id="n1", node_type="http", config={"url": "https://example.com"})
        assert node.node_id == "n1"
        assert node.node_type == "http"
        assert node.config["url"] == "https://example.com"

    def test_node_context_holds_tenant(self):
        ctx = NodeContext(run_id="r1", workflow_id="w1", tenant_id="t1", invoked_by="user1")
        assert ctx.tenant_id == "t1"

    def test_run_event_default_status(self):
        ev = RunEvent(run_id="r1", step_id="s1", actor="user1")
        assert ev.status == "pending"


class TestNodeRunnerHappyPath:
    def test_execute_http_default_sandboxes(self):
        runner = NodeRunner()
        node = Node(node_id="n1", node_type="http", config={"url": "https://api.example.com"})
        ctx = NodeContext(run_id="r1", workflow_id="w1", tenant_id="t1", invoked_by="alice")
        result = runner.execute_node(node, ctx)
        assert result.status == "ok"
        assert result.output["sandboxed"] is True

    def test_execute_transform_default_sandboxes(self):
        runner = NodeRunner()
        node = Node(node_id="n2", node_type="transform", config={"expression": "x+1"})
        ctx = NodeContext(run_id="r1", workflow_id="w1", tenant_id="t1", invoked_by="alice")
        result = runner.execute_node(node, ctx)
        assert result.output["evaluated_in"] == "sandbox"

    def test_execute_unknown_type_returns_error(self):
        runner = NodeRunner()
        node = Node(node_id="n3", node_type="not_a_real_type")
        ctx = NodeContext(run_id="r1", workflow_id="w1", tenant_id="t1", invoked_by="alice")
        result = runner.execute_node(node, ctx)
        assert result.status == "error"

    def test_execute_skip_sandbox_true_runs_raw(self):
        runner = NodeRunner()
        node = Node(node_id="n4", node_type="http", config={"url": "https://api.example.com"})
        ctx = NodeContext(run_id="r1", workflow_id="w1", tenant_id="t1", invoked_by="alice")
        result = runner.execute_node(node, ctx, skip_sandbox=True)
        assert result.output["sandboxed"] is False

    def test_execute_branch_predicate_taken(self):
        runner = NodeRunner()
        node = Node(node_id="n5", node_type="branch", config={"predicate": "true"})
        ctx = NodeContext(run_id="r1", workflow_id="w1", tenant_id="t1", invoked_by="alice")
        result = runner.execute_node(node, ctx)
        assert result.output["taken"] is True


class TestBundleLoaderHappyPath:
    def test_load_accepts_serialized_dict_payload(self):
        loader = WorkflowBundleLoader()
        blob = loader.serialize({"workflow_id": "w1", "nodes": []})
        payload = loader.load(blob)
        assert payload["workflow_id"] == "w1"

    def test_load_rejects_non_bytes(self):
        loader = WorkflowBundleLoader()
        with pytest.raises(BundleLoaderError):
            loader.load("not bytes")

    def test_load_rejects_empty_blob(self):
        loader = WorkflowBundleLoader()
        with pytest.raises(BundleLoaderError):
            loader.load(b"")

    def test_load_rejects_garbage_blob(self):
        loader = WorkflowBundleLoader()
        with pytest.raises(BundleLoaderError):
            loader.load(b"this is not valid bundle payload at all\x01\x02")

    def test_registered_node_type_recognized(self):
        loader = WorkflowBundleLoader()
        assert loader.is_known_node_type("http")
        loader.register_node_type("custom_step")
        assert loader.is_known_node_type("custom_step")


class TestRunCacheHappyPath:
    def test_start_run_records_metadata(self):
        cache = RunCache()
        cache.start_run("r1", "w1", "t1")
        run = cache.get_run("r1")
        assert run["workflow_id"] == "w1"
        assert run["status"] == "running"

    def test_finish_run_updates_status(self):
        cache = RunCache()
        cache.start_run("r2", "w1", "t1")
        cache.finish_run("r2", "ok")
        assert cache.get_run("r2")["status"] == "ok"

    def test_step_results_appended(self):
        cache = RunCache()
        cache.start_run("r3", "w1", "t1")
        cache.append_step_result("r3", "s1", {"value": 42})
        results = cache.get_step_results("r3")
        assert len(results) == 1

    def test_list_active_filters_finished(self):
        cache = RunCache()
        cache.start_run("r4", "w1", "t1")
        cache.start_run("r5", "w1", "t1")
        cache.finish_run("r5", "ok")
        active = cache.list_active_runs()
        assert "r4" in active
        assert "r5" not in active


class TestNodeRegistryHappyPath:
    def test_register_and_get(self):
        reg = NodeRegistry()
        reg.register("n1", "http", "alice", '{"url":"x"}')
        row = reg.get("n1")
        assert row["node_type"] == "http"

    def test_get_unknown_returns_none(self):
        reg = NodeRegistry()
        assert reg.get("missing") is None

    def test_find_by_owner_returns_matches(self):
        reg = NodeRegistry()
        reg.register("n1", "http", "alice", "{}")
        reg.register("n2", "transform", "alice", "{}")
        reg.register("n3", "http", "bob", "{}")
        rows = reg.find_by_owner("alice")
        ids = sorted(r["node_id"] for r in rows)
        assert ids == ["n1", "n2"]

    def test_count_reflects_inserts(self):
        reg = NodeRegistry()
        for i in range(3):
            reg.register(f"n{i}", "http", "alice", "{}")
        assert reg.count() == 3

    def test_register_replaces_existing(self):
        reg = NodeRegistry()
        reg.register("n1", "http", "alice", "{}")
        reg.register("n1", "transform", "alice", "{}")
        row = reg.get("n1")
        assert row["node_type"] == "transform"


class TestAuditWriterHappyPath:
    def test_write_event_records_entry(self):
        writer = AuditWriter()
        writer.write_event("login", "alice", {"ip": "10.0.0.1"})
        assert writer.size() == 1

    def test_write_node_execution_includes_run_id(self):
        writer = AuditWriter()
        writer.write_node_execution("r1", "s1", "alice", {"input": "x"})
        entry = writer.entries()[0]
        assert entry["run_id"] == "r1"

    def test_find_by_run_filters(self):
        writer = AuditWriter()
        writer.write_node_execution("r1", "s1", "alice", {"v": 1})
        writer.write_node_execution("r2", "s1", "alice", {"v": 2})
        assert len(writer.find_by_run("r1")) == 1

    def test_find_by_actor_filters(self):
        writer = AuditWriter()
        writer.write_event("login", "alice", {})
        writer.write_event("login", "bob", {})
        assert len(writer.find_by_actor("alice")) == 1


class TestAuditLineEmitterHappyPath:
    def test_emit_appends_line(self):
        emitter = AuditLineEmitter()
        emitter.emit("tenant-a", "node-001", "alice", "deployed routing change")
        assert emitter.buffered_count() == 1

    def test_drain_returns_joined_lines(self):
        emitter = AuditLineEmitter()
        emitter.emit("tenant-a", "n1", "alice", "first note")
        emitter.emit("tenant-a", "n2", "alice", "second note")
        out = emitter.drain()
        assert "first note" in out
        assert "second note" in out

    def test_drain_clears_buffer(self):
        emitter = AuditLineEmitter()
        emitter.emit("tenant-a", "n1", "alice", "x")
        emitter.drain()
        assert emitter.buffered_count() == 0

    def test_emit_preserves_basic_text(self):
        emitter = AuditLineEmitter()
        emitter.emit("t1", "n1", "alice", "ordinary note text")
        out = emitter.drain()
        assert "ordinary note text" in out
