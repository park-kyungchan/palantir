
"""
Orion ODA V3 - Monolithic Integration Test
=========================================
Verifies that the API properly serves both JSON endpoints and Static HTML.
"""

import sys
import pytest
from fastapi.testclient import TestClient

# Ensure path
sys.path.append("/home/palantir/orion-orchestrator-v2")

from scripts.api.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_api_health(client):
    """Verify API endpoint returns JSON."""
    response = client.get("/api/v1/proposals")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_static_root(client):
    """Verify Root URL serves Index HTML."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Orion ODA" in response.text

def test_spa_routing(client):
    """Verify Deep Link serves Index HTML (SPA Catch-All)."""
    response = client.get("/dashboard/settings/profile")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Orion ODA" in response.text
    
def test_api_not_found(client):
    """Verify API 404 is NOT swallowed by SPA Catch-All."""
    response = client.get("/api/v1/non_existent_resource")
    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"

def test_security_headers(client):
    """Verify Middleware injection."""
    response = client.get("/")
    assert "Strict-Transport-Security" in response.headers
    assert "Content-Security-Policy" in response.headers
