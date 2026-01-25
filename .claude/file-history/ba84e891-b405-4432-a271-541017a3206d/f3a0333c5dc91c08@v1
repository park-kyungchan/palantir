"""
Unit tests for Writeback type definitions.

Tests cover:
- Internal writeback dataset configuration
- Writeback webhooks (BEFORE_OTHER_RULES, blocking)
- Side effect webhooks (AFTER_OTHER_RULES, best-effort)
- File, Streaming, and Table export configurations
- Serialization (to_foundry_dict / from_foundry_dict roundtrip)
"""

import pytest
from pydantic import ValidationError

from ontology_definition.types import (
    WritebackConfig,
    WritebackDatasetConfig,
    WritebackWebhook,
    SideEffectWebhook,
    WebhookEndpoint,
    FileExportConfig,
    StreamingExportConfig,
    TableExportConfig,
)
from ontology_definition.core.enums import (
    ConflictResolutionStrategy,
    ExportTargetType,
    TableExportMode,
    WebhookExecutionOrder,
    WebhookFailureHandling,
    WritebackStatus,
)


class TestWritebackDatasetConfig:
    """Tests for WritebackDatasetConfig - internal writeback dataset."""

    def test_basic_config(self):
        """Basic writeback dataset configuration."""
        config = WritebackDatasetConfig(
            dataset_rid="ri.foundry.main.dataset.12345678-1234-1234-1234-123456789012"
        )
        assert config.dataset_rid.startswith("ri.foundry")
        assert config.conflict_resolution == ConflictResolutionStrategy.TIMESTAMP_WINS

    def test_with_source_dataset(self):
        """Configuration with source dataset reference."""
        config = WritebackDatasetConfig(
            dataset_rid="ri.foundry.main.dataset.12345678-1234-1234-1234-123456789012",
            source_dataset_rid="ri.foundry.main.dataset.87654321-4321-4321-4321-210987654321",
            conflict_resolution=ConflictResolutionStrategy.PRIORITY_WINS
        )
        assert config.source_dataset_rid is not None
        assert config.conflict_resolution == ConflictResolutionStrategy.PRIORITY_WINS

    def test_invalid_rid_pattern(self):
        """Invalid RID pattern should fail."""
        with pytest.raises(ValidationError) as exc_info:
            WritebackDatasetConfig(dataset_rid="invalid-rid")
        assert "pattern" in str(exc_info.value).lower() or "dataset_rid" in str(exc_info.value).lower()


class TestWebhookEndpoint:
    """Tests for WebhookEndpoint configuration."""

    def test_basic_endpoint(self):
        """Basic webhook endpoint."""
        endpoint = WebhookEndpoint(url="https://api.example.com/webhook")
        assert endpoint.url == "https://api.example.com/webhook"
        assert endpoint.method == "POST"

    def test_with_custom_headers(self):
        """Endpoint with custom headers."""
        endpoint = WebhookEndpoint(
            url="https://api.example.com/webhook",
            headers={"Authorization": "Bearer token123", "X-Custom": "value"}
        )
        assert endpoint.headers["Authorization"] == "Bearer token123"

    def test_https_required(self):
        """URL must use HTTPS."""
        with pytest.raises(ValidationError) as exc_info:
            WebhookEndpoint(url="http://api.example.com/webhook")
        assert "pattern" in str(exc_info.value).lower()


class TestWritebackWebhook:
    """Tests for WritebackWebhook - executes before rules, blocking."""

    def test_basic_writeback_webhook(self):
        """Basic writeback webhook configuration."""
        webhook = WritebackWebhook(
            name="syncExternal",
            endpoint=WebhookEndpoint(url="https://api.example.com/sync")
        )
        assert webhook.name == "syncExternal"
        assert webhook.execution_order == WebhookExecutionOrder.BEFORE_OTHER_RULES
        assert webhook.failure_handling == WebhookFailureHandling.BLOCKING

    def test_with_output_parameters(self):
        """Writeback webhook with output parameters."""
        webhook = WritebackWebhook(
            name="transactionSync",
            endpoint=WebhookEndpoint(url="https://api.example.com/sync"),
            output_parameters=["transactionId", "status", "timestamp"]
        )
        assert webhook.output_parameters == ["transactionId", "status", "timestamp"]

    def test_cannot_change_execution_order(self):
        """Writeback webhook must have BEFORE_OTHER_RULES."""
        with pytest.raises(ValidationError) as exc_info:
            WritebackWebhook(
                name="test",
                endpoint=WebhookEndpoint(url="https://example.com"),
                execution_order=WebhookExecutionOrder.AFTER_OTHER_RULES  # Invalid!
            )
        assert "BEFORE_OTHER_RULES" in str(exc_info.value)

    def test_cannot_change_failure_handling(self):
        """Writeback webhook must have BLOCKING failure handling."""
        with pytest.raises(ValidationError) as exc_info:
            WritebackWebhook(
                name="test",
                endpoint=WebhookEndpoint(url="https://example.com"),
                failure_handling=WebhookFailureHandling.BEST_EFFORT  # Invalid!
            )
        assert "BLOCKING" in str(exc_info.value)


class TestSideEffectWebhook:
    """Tests for SideEffectWebhook - executes after rules, best-effort."""

    def test_basic_side_effect_webhook(self):
        """Basic side effect webhook configuration."""
        webhook = SideEffectWebhook(
            name="notifySlack",
            endpoint=WebhookEndpoint(url="https://hooks.slack.com/services/xxx")
        )
        assert webhook.name == "notifySlack"
        assert webhook.execution_order == WebhookExecutionOrder.AFTER_OTHER_RULES
        assert webhook.failure_handling == WebhookFailureHandling.BEST_EFFORT

    def test_cannot_change_execution_order(self):
        """Side effect webhook must have AFTER_OTHER_RULES."""
        with pytest.raises(ValidationError) as exc_info:
            SideEffectWebhook(
                name="test",
                endpoint=WebhookEndpoint(url="https://example.com"),
                execution_order=WebhookExecutionOrder.BEFORE_OTHER_RULES  # Invalid!
            )
        assert "AFTER_OTHER_RULES" in str(exc_info.value)


class TestFileExportConfig:
    """Tests for FileExportConfig - batch export to cloud storage."""

    def test_s3_export(self):
        """S3 file export configuration."""
        export = FileExportConfig(
            name="s3Backup",
            target=ExportTargetType.S3,
            bucket="my-backup-bucket",
            path_prefix="ontology-exports/",
            format="parquet"
        )
        assert export.target == ExportTargetType.S3
        assert export.format == "parquet"

    def test_gcs_export(self):
        """GCS file export configuration."""
        export = FileExportConfig(
            name="gcsBackup",
            target=ExportTargetType.GCS,
            bucket="my-gcs-bucket"
        )
        assert export.target == ExportTargetType.GCS

    def test_with_compression(self):
        """File export with compression."""
        export = FileExportConfig(
            name="compressedExport",
            target=ExportTargetType.S3,
            bucket="my-bucket",
            compression="snappy"
        )
        assert export.compression == "snappy"

    def test_invalid_target_type(self):
        """File export must use batch-compatible target."""
        with pytest.raises(ValidationError) as exc_info:
            FileExportConfig(
                name="invalidExport",
                target=ExportTargetType.KAFKA,  # Streaming target, not batch!
                bucket="my-bucket"
            )
        assert "batch_targets" in str(exc_info.value).lower() or "target" in str(exc_info.value).lower()


class TestStreamingExportConfig:
    """Tests for StreamingExportConfig - real-time streaming export."""

    def test_kafka_export(self):
        """Kafka streaming export configuration."""
        export = StreamingExportConfig(
            name="kafkaStream",
            target=ExportTargetType.KAFKA,
            topic="ontology-changes",
            bootstrap_servers="kafka.example.com:9092"
        )
        assert export.target == ExportTargetType.KAFKA
        assert export.topic == "ontology-changes"

    def test_kinesis_export(self):
        """Kinesis streaming export configuration."""
        export = StreamingExportConfig(
            name="kinesisStream",
            target=ExportTargetType.KINESIS,
            topic="ontology-stream",
            stream_name="my-kinesis-stream"
        )
        assert export.target == ExportTargetType.KINESIS

    def test_pubsub_export(self):
        """Pub/Sub streaming export configuration."""
        export = StreamingExportConfig(
            name="pubsubStream",
            target=ExportTargetType.PUBSUB,
            topic="ontology-topic",
            project_id="my-gcp-project"
        )
        assert export.target == ExportTargetType.PUBSUB

    def test_kafka_requires_bootstrap_servers(self):
        """Kafka export requires bootstrap_servers."""
        with pytest.raises(ValidationError) as exc_info:
            StreamingExportConfig(
                name="kafkaExport",
                target=ExportTargetType.KAFKA,
                topic="my-topic"
                # Missing bootstrap_servers!
            )
        assert "bootstrap_servers" in str(exc_info.value)

    def test_kinesis_requires_stream_name(self):
        """Kinesis export requires stream_name."""
        with pytest.raises(ValidationError) as exc_info:
            StreamingExportConfig(
                name="kinesisExport",
                target=ExportTargetType.KINESIS,
                topic="my-topic"
                # Missing stream_name!
            )
        assert "stream_name" in str(exc_info.value)


class TestTableExportConfig:
    """Tests for TableExportConfig - JDBC database export."""

    def test_basic_table_export(self):
        """Basic JDBC table export configuration."""
        export = TableExportConfig(
            name="postgresSync",
            connection_name="prod-postgres",
            table_name="ontology_objects"
        )
        assert export.connection_name == "prod-postgres"
        assert export.write_mode == TableExportMode.APPEND  # Default

    def test_upsert_mode(self):
        """UPSERT mode with primary keys."""
        export = TableExportConfig(
            name="upsertExport",
            connection_name="prod-db",
            table_name="employees",
            write_mode=TableExportMode.UPSERT,
            primary_keys=["employee_id"]
        )
        assert export.write_mode == TableExportMode.UPSERT
        assert export.primary_keys == ["employee_id"]

    def test_upsert_requires_primary_keys(self):
        """UPSERT mode requires primary_keys."""
        with pytest.raises(ValidationError) as exc_info:
            TableExportConfig(
                name="invalidUpsert",
                connection_name="prod-db",
                table_name="employees",
                write_mode=TableExportMode.UPSERT
                # Missing primary_keys!
            )
        assert "primary_keys" in str(exc_info.value)

    def test_truncate_insert_mode(self):
        """TRUNCATE_INSERT mode."""
        export = TableExportConfig(
            name="fullReplace",
            connection_name="prod-db",
            table_name="lookup_table",
            write_mode=TableExportMode.TRUNCATE_INSERT
        )
        assert export.write_mode == TableExportMode.TRUNCATE_INSERT


class TestWritebackConfig:
    """Tests for WritebackConfig - complete writeback configuration."""

    def test_internal_only(self):
        """Internal writeback only configuration."""
        config = WritebackConfig(
            internal_dataset=WritebackDatasetConfig(
                dataset_rid="ri.foundry.main.dataset.12345678-1234-1234-1234-123456789012"
            )
        )
        assert config.has_internal_writeback is True
        assert config.has_external_writeback is False

    def test_external_only(self):
        """External writeback only configuration."""
        config = WritebackConfig(
            writeback_webhook=WritebackWebhook(
                name="syncExternal",
                endpoint=WebhookEndpoint(url="https://api.example.com/sync")
            )
        )
        assert config.has_internal_writeback is False
        assert config.has_external_writeback is True

    def test_complete_configuration(self):
        """Complete writeback configuration with all components."""
        config = WritebackConfig(
            internal_dataset=WritebackDatasetConfig(
                dataset_rid="ri.foundry.main.dataset.12345678-1234-1234-1234-123456789012"
            ),
            writeback_webhook=WritebackWebhook(
                name="syncExternal",
                endpoint=WebhookEndpoint(url="https://api.example.com/sync"),
                output_parameters=["transactionId"]
            ),
            side_effect_webhooks=[
                SideEffectWebhook(
                    name="notifySlack",
                    endpoint=WebhookEndpoint(url="https://hooks.slack.com/xxx")
                )
            ],
            file_exports=[
                FileExportConfig(
                    name="s3Backup",
                    target=ExportTargetType.S3,
                    bucket="backup-bucket"
                )
            ],
            streaming_exports=[
                StreamingExportConfig(
                    name="kafkaStream",
                    target=ExportTargetType.KAFKA,
                    topic="changes",
                    bootstrap_servers="kafka:9092"
                )
            ],
            table_exports=[
                TableExportConfig(
                    name="postgresSync",
                    connection_name="prod-db",
                    table_name="objects"
                )
            ]
        )
        assert config.has_internal_writeback is True
        assert config.has_external_writeback is True
        assert len(config.all_exports) == 3

    def test_to_foundry_dict_roundtrip(self):
        """to_foundry_dict / from_foundry_dict should roundtrip."""
        original = WritebackConfig(
            internal_dataset=WritebackDatasetConfig(
                dataset_rid="ri.foundry.main.dataset.12345678-1234-1234-1234-123456789012",
                conflict_resolution=ConflictResolutionStrategy.TIMESTAMP_WINS
            ),
            writeback_webhook=WritebackWebhook(
                name="syncExternal",
                endpoint=WebhookEndpoint(url="https://api.example.com/sync"),
                output_parameters=["transactionId", "status"]
            ),
            side_effect_webhooks=[
                SideEffectWebhook(
                    name="notifySlack",
                    endpoint=WebhookEndpoint(url="https://hooks.slack.com/xxx")
                )
            ],
            file_exports=[
                FileExportConfig(
                    name="s3Backup",
                    target=ExportTargetType.S3,
                    bucket="backup-bucket",
                    format="parquet"
                )
            ],
            status=WritebackStatus.ACTIVE
        )

        dict_form = original.to_foundry_dict()
        restored = WritebackConfig.from_foundry_dict(dict_form)

        assert restored.internal_dataset.dataset_rid == original.internal_dataset.dataset_rid
        assert restored.writeback_webhook.name == original.writeback_webhook.name
        assert len(restored.side_effect_webhooks) == len(original.side_effect_webhooks)
        assert len(restored.file_exports) == len(original.file_exports)
        assert restored.status == original.status
