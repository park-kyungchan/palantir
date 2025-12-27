import pytest
import asyncio
import csv
from typing import List, Dict, Any, Type
from unittest.mock import MagicMock, patch

# --- ODA Imports ---
from scripts.ontology.storage.database import Database, initialize_database
from scripts.ontology.storage.proposal_repository import ProposalRepository
from scripts.ontology.objects.proposal import Proposal, ProposalStatus
from scripts.ontology.storage.models import ProposalModel, TaskModel
from scripts.ontology.actions import (
    ActionRegistry, 
    ActionContext, 
    ActionType, 
    ActionResult, 
    EditOperation,
    EditType,
    register_action, 
    action_registry,
    GovernanceEngine
)
from scripts.osdk import ObjectQuery
from scripts.osdk.connector import DataConnector
from scripts.data import DataPipeline, CSVDataSource, SQLAlchemyDataSource
from scripts.aip_logic import LogicFunction, LogicEngine, LogicContext # Assuming these exist or will use ABC

# --- Mock Domain Objects ---
from scripts.ontology.storage.orm import AsyncOntologyObject
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer


# Define OSDK Domain Object
from pydantic import BaseModel, Field
class Task(BaseModel):
    id: str
    title: str
    priority: str
    task_status: str

# Define Action
@register_action
class ArchiveTaskAction(ActionType):
    api_name = "archive_task"
    object_type = Task
    
    async def apply_edits(self, params: Dict[str, Any], context: ActionContext):
        # Mocking the object return for marshaler to pick up ID
        mock_obj = MagicMock()
        mock_obj.id = params['task_id']
        
        edits = [
            EditOperation(
                edit_type=EditType.MODIFY,
                object_type="Task",
                object_id=params['task_id'],
                changes={"task_status": "Archived"}
            )
        ]
        return mock_obj, edits

# --- E2E Test Case ---

@pytest.mark.asyncio
async def test_golden_path_data_to_action(tmp_path):
    """
    Golden Path Scenario:
    1. Ingest Data (CSV -> DB)
    2. Read Data (OSDK Query)
    3. Analyze (AIP Logic)
    4. Propose Action (Governance)
    5. Execute Action (Kernel)
    """
    
    # 0. Setup Infrastructure
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    
    # Initialize DB with Schema
    # We need to manually add TaskModel to Base.metadata or ensure it is imported
    from scripts.ontology.storage.models import Base
    # TaskModel is already defined above, ensuring it's in Base.registry
    
    # Setup Data Source File
    csv_file = tmp_path / "tasks.csv"
    with open(csv_file, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "title", "description", "priority", "task_status", "status", "tags", "version", "created_at", "updated_at", "created_by"])
        writer.writerow(["t1", "Fix Bug", "Desc 1", "High", "Completed", "active", "[]", 1, "2024-01-01T00:00:00", "2024-01-01T00:00:00", "system"])
        writer.writerow(["t2", "Feature X", "Desc 2", "Low", "In Progress", "active", "[]", 1, "2024-01-01T00:00:00", "2024-01-01T00:00:00", "system"])
        writer.writerow(["t3", "Critical Fix", "Desc 3", "High", "Completed", "active", "[]", 1, "2024-01-01T00:00:00", "2024-01-01T00:00:00", "system"])

    # 1. DATA INGESTION (ETL)
    # -------------------------------------------------------------------------
    db = Database(db_url)
    await db.initialize()
    
    # Create tables including 'tasks'
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    pipeline = DataPipeline("task_ingest") \
        .extract(CSVDataSource(str(csv_file))) \
        .load(SQLAlchemyDataSource(db, table="tasks"))
        
    await pipeline.execute()
    
    # Verify Ingestion
    repo = SQLAlchemyDataSource(db, query="SELECT * FROM tasks")
    rows = await repo.read()
    assert len(rows) == 3
    
    # 2. OSDK READ (Query)
    # -------------------------------------------------------------------------
    # Configure OSDK to use our Test DB
    from scripts.osdk.sqlite_connector import SQLiteConnector
    connector = SQLiteConnector(db)
    
    # We need to register TaskModel to Connector for this ad-hoc test
    # Connector usually finds models via registry. 
    # Let's ensure SQLiteConnector functionality works with custom models if dynamic
    # OR we assume the connector handles Mapping.
    # For now, we manually inject or mock the resolution if needed.
    # SQLiteConnector uses _get_model_class which iterates subclasses of AsyncOntologyObject.
    # So it should find TaskModel automatically.
    
    # Query: Find High Priority + Completed Tasks
    # Note: OSDK filters need to match model fields.
    query = ObjectQuery(Task) \
        .where("priority", "eq", "High") \
        .where("task_status", "eq", "Completed")
        
    # Inject connector (usually done globally or via factory)
    connector._model_map["Task"] = TaskModel
    query.connector = connector
    
    results = await query.execute()
    
    assert len(results) == 2
    assert "t1" in [t.id for t in results]
    assert "t3" in [t.id for t in results]

    # 3. AIP LOGIC (Analyze)
    # -------------------------------------------------------------------------
    # Define Logic Function
    class ArchiveCandidateAnalysis(LogicFunction[List[Task], List[str]]):
        @property
        def name(self): return "analyze_archive_candidates"
        @property
        def input_type(self): return List[Task]
        @property
        def output_type(self): return List[str] # Returns list of IDs
        
        async def run(self, tasks: List[Task], context: LogicContext) -> List[str]:
            # Mock LLM Logic: "If Completed and High Priority, Archive it"
            # In real life, we would prompt LLM. Here we simulate the logic.
            return [t.id for t in tasks]

    logic_engine = LogicEngine(MagicMock()) # Mock LLM Client
    candidates = await logic_engine.execute(ArchiveCandidateAnalysis, results)
    
    assert len(candidates) == 2
    
    # 4. GOVERNANCE & PROPOSAL
    # -------------------------------------------------------------------------
    # Governance Engine Check
    gov_engine = GovernanceEngine(action_registry)
    # We marked params as optional in base but for registry we need checking.
    # Our simple ArchiveTaskAction didn't define strict metadata in this test file
    # But let's assume policy requires proposal for "archive_task".
    
    # Manually forcing policy for test if metadata defaults to ALLOW
    # Or we construct Proposal directly as the Kernel would.
    
    proposal_repo = ProposalRepository(db)
    
    # Create Proposals for each candidate
    for task_id in candidates:
        proposal = Proposal(
            action_type="archive_task",
            payload={"task_id": task_id},
            created_by="ai_logic",
            priority="medium" 
        )
        proposal.submit()
        await proposal_repo.save(proposal)
        
    # Verify Pending Proposals
    pending = await proposal_repo.find_by_status(ProposalStatus.PENDING)
    assert len(pending) == 2
    
    # 5. EXECUTION (Approve & Run)
    # -------------------------------------------------------------------------
    # Simulate Human Approval
    p1 = pending[0]
    await proposal_repo.approve(p1.id, reviewer_id="admin")
    
    # Kernel Execution Simulation
    from scripts.runtime.marshaler import ToolMarshaler
    marshaler = ToolMarshaler(action_registry)
    
    # Execute the action
    # (In real Kernel, this loop runs continuously)
    result = await marshaler.execute_action(
        action_name=p1.action_type,
        params=p1.payload,
        context=ActionContext(actor_id="admin")
    )
    
    assert result.success is True
    assert p1.payload["task_id"] in result.modified_ids
    
    # Mark Executed in Repo
    await proposal_repo.execute(p1.id, executor_id="kernel", result=result.to_dict())
    
    # Final State Check
    users_proposal_state = await proposal_repo.find_by_id(p1.id)
    assert users_proposal_state.status == ProposalStatus.EXECUTED

    print("\n✅ GOLDEN PATH E2E SUCCESS")
