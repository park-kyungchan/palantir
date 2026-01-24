"""
Pytest configuration for E2E tests.

Schema Version: 2.0.0

Note: pytest_plugins moved to root conftest.py per pytest requirements.
"""

import pytest


def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )


@pytest.fixture(scope="session")
def event_loop_policy():
    """Use default event loop policy."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()
