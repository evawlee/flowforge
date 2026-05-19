# flowforge

Internal workflow runner. Dispatches HTTP, transform, eval, and branch nodes through a per-node sandbox layer, ingests workflow bundles uploaded by tenant authors, caches in-flight run state in process, and records audit events for every node invocation.

## Install
```
pip install -e .[dev]
```

## Test
```
pytest tests/
```