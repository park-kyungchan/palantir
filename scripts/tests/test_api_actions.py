
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import status

from scripts.api.routes import router
from scripts.api.dtos import ActionResultResponse, ExecuteActionRequest
from scripts.ontology.actions import ActionResult

# We need a dummy FastAPI app to mount the router
from fastapi import FastAPI
app = FastAPI()
app.include_router(router)

client = TestClient(app)

@pytest.fixture
def mock_registry():
    with patch("scripts.ontology.actions.action_registry") as mock:
        yield mock

@pytest.fixture
def mock_marshaler():
    with patch("scripts.runtime.marshaler.ToolMarshaler") as mock_cls:
        instance = mock_cls.return_value
        instance.execute_action = AsyncMock()
        yield instance

def test_execute_action_success(mock_registry, mock_marshaler):
    # Setup Governance: Safe Action
    mock_meta = MagicMock()
    mock_meta.requires_proposal = False
    mock_registry.get_metadata.return_value = mock_meta
    
    # Setup Marshaler Success
    mock_marshaler.execute_action.return_value = ActionResult(
        action_type="safe_action",
        success=True,
        data={"result": "ok"}
    )
    
    payload = {
        "action_type": "safe_action",
        "params": {"foo": "bar"}
    }
    
    response = client.post("/api/v1/proposals/execute", json=payload)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert data["action_type"] == "safe_action"
    assert data["result"] == {"value": {"result": "ok"}} or data["result"] == {"result": "ok"}
    
    # Verify Metadata Check
    mock_registry.get_metadata.assert_called_with("safe_action")
    # Verify Execution
    mock_marshaler.execute_action.assert_called_once()


def test_execute_action_hazardous_forbidden(mock_registry, mock_marshaler):
    # Setup Governance: Hazardous Action
    mock_meta = MagicMock()
    mock_meta.requires_proposal = True # Requires Proposal!
    mock_registry.get_metadata.return_value = mock_meta
    
    payload = {
        "action_type": "dangerous_action",
        "params": {}
    }
    
    response = client.post("/api/v1/proposals/execute", json=payload)
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "requires a Proposal" in response.json()["detail"]
    
    # Verify Marshaler NOT called
    mock_marshaler.execute_action.assert_not_called()


def test_execute_action_not_found(mock_registry, mock_marshaler):
    # Setup Governance: Unknown Action
    mock_registry.get_metadata.return_value = None
    
    payload = {
        "action_type": "unknown_action",
        "params": {}
    }
    
    response = client.post("/api/v1/proposals/execute", json=payload)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_execute_action_marshaler_failure(mock_registry, mock_marshaler):
    # Safe action, but execution fails
    mock_meta = MagicMock()
    mock_meta.requires_proposal = False
    mock_registry.get_metadata.return_value = mock_meta
    
    mock_marshaler.execute_action.return_value = ActionResult(
        action_type="safe_action",
        success=False,
        error="Execution blew up"
    )
    
    payload = {
        "action_type": "safe_action",
        "params": {}
    }
    
    response = client.post("/api/v1/proposals/execute", json=payload)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Execution blew up" in response.json()["detail"]
