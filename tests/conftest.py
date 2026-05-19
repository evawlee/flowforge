import pytest

from flowforge.cache import RunCache


@pytest.fixture(autouse=True)
def _reset_run_cache():
    RunCache.reset()
    yield
    RunCache.reset()
