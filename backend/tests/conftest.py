import pytest

from app.services import edgar_client


@pytest.fixture(autouse=True)
def _clear_ticker_cache():
    """Ensures the lru_cache'd ticker lookup table doesn't leak between tests."""
    edgar_client._ticker_to_cik_map.cache_clear()
    yield
    edgar_client._ticker_to_cik_map.cache_clear()
