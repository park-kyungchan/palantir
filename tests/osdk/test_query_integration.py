import pytest
from unittest.mock import AsyncMock, MagicMock
from scripts.osdk.query import ObjectQuery
from scripts.osdk.sqlite_connector import SQLiteConnector
from scripts.ontology.objects.proposal import Proposal

# Mock the database connection for unit testing the Query Builder logic
# Real integration test would require setting up the full AsyncEngine which is heavy.
# For now, we verify that the Query correctly calls the Connector.

@pytest.fixture
def mock_connector():
    connector = MagicMock(spec=SQLiteConnector)
    connector.query = AsyncMock(return_value=[])
    return connector

@pytest.mark.asyncio
async def test_object_query_execute_empty(mock_connector):
    """Test standard execution with defaults."""
    query = ObjectQuery(Proposal, connector=mock_connector)
    results = await query.execute()
    
    assert results == []
    mock_connector.query.assert_called_once()
    call_kwargs = mock_connector.query.call_args.kwargs
    
    assert call_kwargs["object_type"] == Proposal
    assert call_kwargs["limit"] == 100
    assert call_kwargs["filters"] == []

@pytest.mark.asyncio
async def test_object_query_filters(mock_connector):
    """Test where clauses."""
    query = ObjectQuery(Proposal, connector=mock_connector)
    await query.where("status", "eq", "PENDING").execute()
    
    call_kwargs = mock_connector.query.call_args.kwargs
    assert len(call_kwargs["filters"]) == 1
    assert call_kwargs["filters"][0].property == "status"
    assert call_kwargs["filters"][0].value == "PENDING"

@pytest.mark.asyncio
async def test_object_query_sorting_paging(mock_connector):
    """Test limit and order_by."""
    query = ObjectQuery(Proposal, connector=mock_connector)
    await query.limit(5).order_by("created_at", False).execute()
    
    call_kwargs = mock_connector.query.call_args.kwargs
    assert call_kwargs["limit"] == 5
    assert call_kwargs["order_by"] == {"property": "created_at", "direction": "desc"}
