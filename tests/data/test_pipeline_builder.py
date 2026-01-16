"""
Tests for PipelineBuilder DSL and Pipeline ObjectTypes (Phase 4.3)

Tests cover:
- PipelineBuilder fluent API
- Pipeline validation
- Stage dependency resolution
- Pipeline ObjectTypes
- Pipeline Actions
"""

import pytest
import uuid
from datetime import datetime, timezone

from lib.oda.data.pipeline_builder import (
    PipelineBuilder,
    Pipeline,
    PipelineStage,
    PipelineRun,
    StageType,
    PipelineStatus,
    RunStatus,
)
from lib.oda.ontology.objects.pipeline import (
    PipelineObject,
    PipelineRunObject,
    PipelineStageObject,
    PipelineObjectStatus,
    PipelineRunStatus,
    StageTypeEnum,
)
from lib.oda.ontology.actions.pipeline_actions import (
    PipelineValidateAction,
    PipelineExecuteAction,
    PipelineScheduleAction,
    PipelinePauseAction,
    PipelineStatusAction,
    ValidPipelineStages,
    ValidScheduleCron,
)
from lib.oda.ontology.actions import ActionContext


# =============================================================================
# PIPELINE BUILDER TESTS
# =============================================================================


class TestPipelineBuilder:
    """Tests for PipelineBuilder fluent API."""

    def test_basic_pipeline_creation(self):
        """Test creating a basic pipeline with source and output."""
        pipeline = (
            PipelineBuilder("test_pipeline", owner="test_user")
            .source("database", {"table": "users"})
            .output("output_sink", "parquet", {"path": "/data/output"})
            .build()
        )

        assert pipeline.pipeline_id == "test_pipeline"
        assert pipeline.name == "test_pipeline"
        assert pipeline.owner == "test_user"
        assert len(pipeline.stages) == 2
        assert pipeline.stages[0].stage_type == StageType.SOURCE
        assert pipeline.stages[1].stage_type == StageType.OUTPUT

    def test_full_etl_pipeline(self):
        """Test creating a full ETL pipeline with all stage types."""
        pipeline = (
            PipelineBuilder("etl_tasks", owner="data_team")
            .with_description("ETL pipeline for task processing")
            .source("database", {"table": "raw_tasks"})
            .filter("active_only", "status != 'deleted'")
            .transform("enrich", "add_metadata", {"fields": ["created_at"]})
            .aggregate("daily_counts", ["date"], {"count": "task_id"})
            .output("warehouse", "parquet", {"path": "/data/tasks"})
            .build()
        )

        assert pipeline.pipeline_id == "etl_tasks"
        assert pipeline.description == "ETL pipeline for task processing"
        assert len(pipeline.stages) == 5

        # Verify stage types
        stage_types = [s.stage_type for s in pipeline.stages]
        assert StageType.SOURCE in stage_types
        assert StageType.FILTER in stage_types
        assert StageType.TRANSFORM in stage_types
        assert StageType.AGGREGATE in stage_types
        assert StageType.OUTPUT in stage_types

    def test_pipeline_with_schedule(self):
        """Test adding schedule to pipeline."""
        pipeline = (
            PipelineBuilder("scheduled_pipeline", owner="system")
            .source("api", {"endpoint": "/data"})
            .output("storage", "json", {"path": "/output"})
            .with_schedule("0 0 * * *")
            .build()
        )

        assert pipeline.schedule == "0 0 * * *"

    def test_pipeline_with_tags(self):
        """Test adding tags to pipeline."""
        pipeline = (
            PipelineBuilder("tagged_pipeline", owner="system")
            .source("api", {"endpoint": "/data"})
            .output("storage", "json", {"path": "/output"})
            .with_tags("etl", "production", "critical")
            .build()
        )

        assert "etl" in pipeline.tags
        assert "production" in pipeline.tags
        assert "critical" in pipeline.tags

    def test_pipeline_with_join(self):
        """Test pipeline with join stage."""
        pipeline = (
            PipelineBuilder("join_pipeline", owner="analyst")
            .source("database", {"table": "orders"})
            .join("with_users", "user_pipeline", "user_id", join_type="left")
            .output("report", "csv", {"path": "/reports/orders"})
            .build()
        )

        join_stage = next(s for s in pipeline.stages if s.stage_type == StageType.JOIN)
        assert join_stage.config["other_pipeline"] == "user_pipeline"
        assert join_stage.config["join_key"] == "user_id"
        assert join_stage.config["join_type"] == "left"

    def test_auto_dependency_chain(self):
        """Test that stages automatically depend on previous stage."""
        pipeline = (
            PipelineBuilder("chain_test", owner="test")
            .source("db", {"table": "t1"})
            .filter("f1", "x > 0")
            .transform("t1", "fn1")
            .output("out", "json", {"path": "/"})
            .build()
        )

        # Source has no dependencies
        assert pipeline.stages[0].dependencies == []

        # Each subsequent stage depends on the previous
        for i in range(1, len(pipeline.stages)):
            assert len(pipeline.stages[i].dependencies) == 1
            assert pipeline.stages[i].dependencies[0] == pipeline.stages[i-1].stage_id

    def test_explicit_dependencies(self):
        """Test explicit dependency specification."""
        builder = PipelineBuilder("explicit_deps", owner="test")
        builder.source("db1", {"table": "t1"}, name="source1")
        source1_id = builder._stages[0].stage_id

        builder.source("db2", {"table": "t2"}, name="source2")
        source2_id = builder._stages[1].stage_id

        # Transform depends on both sources
        builder.transform(
            "merge",
            "combine",
            depends_on=[source1_id, source2_id]
        )
        builder.output("final", "parquet", {"path": "/"})

        pipeline = builder.build()

        merge_stage = next(s for s in pipeline.stages if s.name == "merge")
        assert source1_id in merge_stage.dependencies
        assert source2_id in merge_stage.dependencies


class TestPipelineBuilderValidation:
    """Tests for PipelineBuilder validation."""

    def test_missing_source_raises_error(self):
        """Test that pipeline without source fails validation."""
        builder = (
            PipelineBuilder("no_source", owner="test")
            .transform("t1", "fn1")
            .output("out", "json", {"path": "/"})
        )

        errors = builder.validate()
        assert len(errors) > 0
        assert any("source" in e.lower() for e in errors)

    def test_missing_output_raises_error(self):
        """Test that pipeline without output fails validation."""
        builder = (
            PipelineBuilder("no_output", owner="test")
            .source("db", {"table": "t1"})
            .transform("t1", "fn1")
        )

        errors = builder.validate()
        assert len(errors) > 0
        assert any("output" in e.lower() for e in errors)

    def test_duplicate_stage_name_raises_error(self):
        """Test that duplicate stage names raise error."""
        builder = PipelineBuilder("dup_names", owner="test")
        builder.source("db", {"table": "t1"}, name="stage1")

        with pytest.raises(ValueError, match="Duplicate stage name"):
            builder.source("db2", {"table": "t2"}, name="stage1")

    def test_invalid_dependency_detected(self):
        """Test that invalid dependencies are detected."""
        builder = (
            PipelineBuilder("bad_deps", owner="test")
            .source("db", {"table": "t1"})
        )
        # Manually add a stage with invalid dependency
        builder._stages.append(PipelineStage(
            name="bad_stage",
            stage_type=StageType.TRANSFORM,
            config={},
            dependencies=["nonexistent_stage_id"]
        ))
        builder._stage_names.add("bad_stage")
        builder.output("out", "json", {"path": "/"})

        errors = builder.validate()
        assert len(errors) > 0
        assert any("non-existent" in e.lower() or "references" in e.lower() for e in errors)

    def test_build_fails_on_validation_error(self):
        """Test that build() raises ValueError on validation failure."""
        builder = PipelineBuilder("invalid", owner="test")
        # No stages at all

        with pytest.raises(ValueError, match="validation failed"):
            builder.build()


class TestPipelineExecutionOrder:
    """Tests for pipeline execution order (topological sort)."""

    def test_simple_linear_order(self):
        """Test execution order for linear pipeline."""
        pipeline = (
            PipelineBuilder("linear", owner="test")
            .source("db", {"table": "t1"})
            .filter("f1", "x > 0")
            .transform("t1", "fn1")
            .output("out", "json", {"path": "/"})
            .build()
        )

        order = pipeline.get_execution_order()
        assert len(order) == 4

        # First should be source (no deps)
        source_id = pipeline.stages[0].stage_id
        assert order[0] == source_id

    def test_diamond_dependency(self):
        """Test execution order for diamond-shaped dependency graph."""
        builder = PipelineBuilder("diamond", owner="test")
        builder.source("db", {"table": "t1"}, name="source")
        source_id = builder._stages[0].stage_id

        builder.transform("branch1", "fn1", depends_on=[source_id])
        branch1_id = builder._stages[1].stage_id

        builder.transform("branch2", "fn2", depends_on=[source_id])
        branch2_id = builder._stages[2].stage_id

        # Merge depends on both branches
        builder.transform("merge", "combine", depends_on=[branch1_id, branch2_id])
        builder.output("out", "json", {"path": "/"})

        pipeline = builder.build()
        order = pipeline.get_execution_order()

        # Source must come first
        assert order.index(source_id) == 0

        # Both branches must come before merge
        merge_idx = order.index(builder._stages[3].stage_id)
        assert order.index(branch1_id) < merge_idx
        assert order.index(branch2_id) < merge_idx

    def test_circular_dependency_detected(self):
        """Test that circular dependencies are detected."""
        pipeline = Pipeline(
            pipeline_id="circular",
            name="circular",
            owner="test",
            stages=[
                PipelineStage(
                    stage_id="a",
                    name="stage_a",
                    stage_type=StageType.SOURCE,
                    dependencies=["c"]  # Circular: a -> c -> b -> a
                ),
                PipelineStage(
                    stage_id="b",
                    name="stage_b",
                    stage_type=StageType.TRANSFORM,
                    dependencies=["a"]
                ),
                PipelineStage(
                    stage_id="c",
                    name="stage_c",
                    stage_type=StageType.OUTPUT,
                    dependencies=["b"]
                ),
            ]
        )

        with pytest.raises(ValueError, match="[Cc]ircular"):
            pipeline.get_execution_order()


# =============================================================================
# PIPELINE RUN TESTS
# =============================================================================


class TestPipelineRun:
    """Tests for PipelineRun model."""

    def test_run_status_transitions(self):
        """Test run status transitions."""
        run = PipelineRun(pipeline_id="test_pipeline")

        assert run.status == RunStatus.PENDING

        run.mark_running()
        assert run.status == RunStatus.RUNNING

        run.mark_completed()
        assert run.status == RunStatus.COMPLETED
        assert run.completed_at is not None

    def test_run_failure(self):
        """Test marking run as failed."""
        run = PipelineRun(pipeline_id="test_pipeline")
        run.mark_running()
        run.mark_failed("Stage failed: database connection error")

        assert run.status == RunStatus.FAILED
        assert run.error == "Stage failed: database connection error"
        assert run.completed_at is not None

    def test_stage_results(self):
        """Test recording stage results."""
        run = PipelineRun(pipeline_id="test_pipeline")
        run.mark_running()

        run.set_stage_result("stage_1", {"rows_processed": 1000})
        run.set_stage_result("stage_2", {"rows_processed": 950})

        assert run.stage_results["stage_1"]["rows_processed"] == 1000
        assert run.stage_results["stage_2"]["rows_processed"] == 950

    def test_duration_calculation(self):
        """Test duration calculation."""
        run = PipelineRun(pipeline_id="test_pipeline")

        # Not completed yet
        assert run.duration_seconds is None

        run.mark_running()
        run.mark_completed()

        # Should have duration now
        assert run.duration_seconds is not None
        assert run.duration_seconds >= 0


# =============================================================================
# PIPELINE OBJECT TYPE TESTS
# =============================================================================


class TestPipelineObjectTypes:
    """Tests for Pipeline OntologyObjects."""

    def test_pipeline_object_creation(self):
        """Test PipelineObject creation."""
        pipeline = PipelineObject(
            pipeline_id="test_pipeline",
            name="Test Pipeline",
            owner="test_user",
            description="A test pipeline",
        )

        assert pipeline.pipeline_id == "test_pipeline"
        assert pipeline.name == "Test Pipeline"
        assert pipeline.owner == "test_user"
        assert pipeline.pipeline_status == PipelineObjectStatus.DRAFT
        assert pipeline.pipeline_version == 1

    def test_pipeline_object_lifecycle(self):
        """Test PipelineObject lifecycle methods."""
        pipeline = PipelineObject(
            pipeline_id="lifecycle_test",
            name="Lifecycle Test",
            owner="test",
        )

        # Activate
        pipeline.activate()
        assert pipeline.pipeline_status == PipelineObjectStatus.ACTIVE
        assert pipeline.is_active

        # Pause
        pipeline.pause()
        assert pipeline.pipeline_status == PipelineObjectStatus.PAUSED

        # Archive
        pipeline.archive()
        assert pipeline.pipeline_status == PipelineObjectStatus.ARCHIVED

    def test_pipeline_run_object(self):
        """Test PipelineRunObject."""
        run = PipelineRunObject(
            run_id=str(uuid.uuid4()),
            pipeline_id="test_pipeline",
            pipeline_object_id="obj_123",
            created_by="test_user",
        )

        assert run.run_status == PipelineRunStatus.PENDING

        run.mark_running()
        assert run.run_status == PipelineRunStatus.RUNNING

        run.set_stage_result("stage_1", {"count": 100}, {"duration_ms": 500})
        assert "stage_1" in run.stage_results

        run.mark_completed()
        assert run.is_success
        assert run.is_terminal

    def test_pipeline_stage_object(self):
        """Test PipelineStageObject."""
        stage = PipelineStageObject(
            stage_id="stage_1",
            name="Source Stage",
            stage_type=StageTypeEnum.SOURCE,
            pipeline_id="test_pipeline",
            config={"table": "users"},
        )

        assert stage.is_source
        assert not stage.is_output
        assert not stage.has_dependencies

        config = stage.to_execution_config()
        assert config["stage_id"] == "stage_1"
        assert config["config"]["table"] == "users"


# =============================================================================
# PIPELINE ACTION TESTS
# =============================================================================


class TestPipelineActions:
    """Tests for Pipeline Actions."""

    @pytest.fixture
    def context(self):
        """Create action context for tests."""
        return ActionContext(actor_id="test_user")

    @pytest.fixture
    def valid_stages(self):
        """Create valid pipeline stages."""
        return [
            {
                "stage_id": "s1",
                "name": "source",
                "stage_type": "source",
                "config": {"table": "users"},
                "dependencies": [],
            },
            {
                "stage_id": "s2",
                "name": "transform",
                "stage_type": "transform",
                "config": {},
                "dependencies": ["s1"],
            },
            {
                "stage_id": "s3",
                "name": "output",
                "stage_type": "output",
                "config": {"path": "/data"},
                "dependencies": ["s2"],
            },
        ]

    @pytest.mark.asyncio
    async def test_validate_action_success(self, context, valid_stages):
        """Test successful pipeline validation."""
        action = PipelineValidateAction()
        result = await action.execute(
            params={"stages": valid_stages},
            context=context,
        )

        assert result.success
        assert result.data["is_valid"]
        assert len(result.data["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_action_missing_source(self, context):
        """Test validation with missing source."""
        action = PipelineValidateAction()
        result = await action.execute(
            params={
                "stages": [
                    {
                        "stage_id": "s1",
                        "name": "output",
                        "stage_type": "output",
                        "config": {},
                        "dependencies": [],
                    }
                ]
            },
            context=context,
        )

        assert result.success  # Action ran successfully
        assert not result.data["is_valid"]  # But validation failed
        assert any("source" in e.lower() for e in result.data["errors"])

    @pytest.mark.asyncio
    async def test_validate_action_circular_deps(self, context):
        """Test validation detects circular dependencies."""
        action = PipelineValidateAction()
        result = await action.execute(
            params={
                "stages": [
                    {"stage_id": "a", "name": "a", "stage_type": "source", "dependencies": ["c"]},
                    {"stage_id": "b", "name": "b", "stage_type": "transform", "dependencies": ["a"]},
                    {"stage_id": "c", "name": "c", "stage_type": "output", "dependencies": ["b"]},
                ]
            },
            context=context,
        )

        assert result.success
        assert not result.data["is_valid"]
        assert any("circular" in e.lower() for e in result.data["errors"])

    @pytest.mark.asyncio
    async def test_execute_action_requires_proposal(self):
        """Test that execute action requires proposal."""
        action = PipelineExecuteAction()
        assert action.requires_proposal is True

    @pytest.mark.asyncio
    async def test_execute_action_creates_run(self, context):
        """Test execute action creates a run object."""
        action = PipelineExecuteAction()
        result = await action.execute(
            params={
                "pipeline_id": "test_pipeline",
                "triggered_by": "test",
            },
            context=context,
        )

        assert result.success
        run = result.data
        assert run is not None
        assert run.pipeline_id == "test_pipeline"
        assert run.run_status == PipelineRunStatus.RUNNING

    @pytest.mark.asyncio
    async def test_schedule_action(self, context):
        """Test pipeline schedule action."""
        action = PipelineScheduleAction()
        result = await action.execute(
            params={
                "pipeline_id": "test_pipeline",
                "schedule": "0 0 * * *",
            },
            context=context,
        )

        assert result.success
        assert result.data["schedule"] == "0 0 * * *"
        assert result.data["status"] == PipelineObjectStatus.ACTIVE.value

    @pytest.mark.asyncio
    async def test_pause_action(self, context):
        """Test pipeline pause action."""
        action = PipelinePauseAction()
        result = await action.execute(
            params={"pipeline_id": "test_pipeline"},
            context=context,
        )

        assert result.success
        assert result.data["status"] == PipelineObjectStatus.PAUSED.value

    @pytest.mark.asyncio
    async def test_status_action(self, context):
        """Test pipeline status action."""
        action = PipelineStatusAction()
        result = await action.execute(
            params={"pipeline_id": "test_pipeline"},
            context=context,
        )

        assert result.success
        assert "pipeline_id" in result.data


class TestPipelineValidators:
    """Tests for pipeline validation criteria."""

    @pytest.fixture
    def context(self):
        return ActionContext(actor_id="test")

    def test_valid_pipeline_stages(self, context):
        """Test ValidPipelineStages validator."""
        validator = ValidPipelineStages()

        valid_params = {
            "stages": [
                {"stage_id": "s1", "stage_type": "source"},
                {"stage_id": "s2", "stage_type": "output"},
            ]
        }

        assert validator.validate(valid_params, context)

    def test_missing_source_stage(self, context):
        """Test validation fails without source."""
        validator = ValidPipelineStages()

        invalid_params = {
            "stages": [
                {"stage_id": "s1", "stage_type": "transform"},
                {"stage_id": "s2", "stage_type": "output"},
            ]
        }

        with pytest.raises(Exception):  # ValidationError
            validator.validate(invalid_params, context)

    def test_valid_schedule_cron(self, context):
        """Test ValidScheduleCron validator."""
        validator = ValidScheduleCron()

        # Valid 5-part cron
        assert validator.validate({"schedule": "0 0 * * *"}, context)

        # Valid 6-part cron
        assert validator.validate({"schedule": "0 0 0 * * *"}, context)

        # None schedule is valid
        assert validator.validate({"schedule": None}, context)

    def test_invalid_schedule_cron(self, context):
        """Test invalid cron expressions."""
        validator = ValidScheduleCron()

        with pytest.raises(Exception):
            validator.validate({"schedule": "invalid cron"}, context)


# =============================================================================
# ACTION REGISTRATION TESTS
# =============================================================================


class TestActionRegistration:
    """Tests for action registration."""

    def test_actions_registered(self):
        """Test that pipeline actions are registered."""
        from lib.oda.ontology.actions import action_registry

        # Import to ensure registration
        import lib.oda.ontology.actions.pipeline_actions  # noqa: F401

        registered = action_registry.list_actions()

        # Check actions are registered
        assert "pipeline.validate" in registered
        assert "pipeline.execute" in registered
        assert "pipeline.schedule" in registered
        assert "pipeline.pause" in registered
        assert "pipeline.status" in registered

    def test_hazardous_actions_marked(self):
        """Test that hazardous actions are properly marked."""
        from lib.oda.ontology.actions import action_registry

        # Import to ensure registration
        import lib.oda.ontology.actions.pipeline_actions  # noqa: F401

        hazardous = action_registry.get_hazardous_actions()

        # These should be hazardous
        assert "pipeline.execute" in hazardous
        assert "pipeline.schedule" in hazardous
        assert "pipeline.pause" in hazardous

        # These should NOT be hazardous
        assert "pipeline.validate" not in hazardous
        assert "pipeline.status" not in hazardous
