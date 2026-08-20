"""Fixtures partilhadas, cache limpo entre testes (o LocMemCache é global ao processo)."""

import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()
