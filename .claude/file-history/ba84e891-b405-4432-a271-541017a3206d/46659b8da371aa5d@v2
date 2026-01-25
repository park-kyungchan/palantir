"""
Writeback Types for Ontology Definition.

Writeback is the mechanism for synchronizing Ontology changes (user edits via Actions)
back to writeback datasets and external systems via Webhooks, Exports, or External Functions.

This module provides:
    - WritebackDatasetConfig: Internal writeback dataset configuration
    - WritebackWebhook: Writeback webhook (BEFORE_OTHER_RULES, blocking)
    - SideEffectWebhook: Side effect webhook (AFTER_OTHER_RULES, best-effort)
    - FileExportConfig: File export to cloud storage (S3, GCS, Azure Blob)
    - StreamingExportConfig: Streaming export (Kafka, Kinesis, PubSub)
    - TableExportConfig: JDBC table export with write modes
    - WritebackConfig: Complete writeback configuration

Aligned with Ontology.md Section 10.
"""

from __future__ import annotations

from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ontology_definition.core.enums import (
    ConflictResolutionStrategy,
    ExportMode,
    ExportTargetType,
    TableExportMode,
    WebhookExecutionOrder,
    WebhookFailureHandling,
    WebhookType,
    WritebackStatus,
)


class WritebackDatasetConfig(BaseModel):
    """
    Internal writeback dataset configuration.

    Stores user-modified version of source data with conflict resolution.
    The writeback dataset merges edits with the source dataset.

    Example:
        config = WritebackDatasetConfig(
            dataset_rid="ri.foundry.main.dataset.xxx",
            source_dataset_rid="ri.foundry.main.dataset.yyy",
            conflict_resolution=ConflictResolutionStrategy.TIMESTAMP_WINS
        )
    """

    dataset_rid: str = Field(
        ...,
        description="Resource Identifier of the writeback dataset.",
        alias="datasetRid",
        pattern=r"^ri\.foundry\.[^.]+\.dataset\.[a-f0-9-]+$",
    )

    source_dataset_rid: Optional[str] = Field(
        default=None,
        description="Resource Identifier of the source dataset (unchanged data).",
        alias="sourceDatasetRid",
        pattern=r"^ri\.foundry\.[^.]+\.dataset\.[a-f0-9-]+$",
    )

    conflict_resolution: ConflictResolutionStrategy = Field(
        default=ConflictResolutionStrategy.TIMESTAMP_WINS,
        description="Strategy for resolving conflicts between source and edits.",
        alias="conflictResolution",
    )

    enabled: bool = Field(
        default=True,
        description="Whether writeback to this dataset is enabled.",
    )

    description: Optional[str] = Field(
        default=None,
        description="Human-readable description of this writeback configuration.",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "datasetRid": self.dataset_rid,
            "conflictResolution": self.conflict_resolution.value,
        }

        if self.source_dataset_rid:
            result["sourceDatasetRid"] = self.source_dataset_rid

        if not self.enabled:
            result["enabled"] = False

        if self.description:
            result["description"] = self.description

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "WritebackDatasetConfig":
        """Create from Foundry JSON format."""
        return cls(
            dataset_rid=data["datasetRid"],
            source_dataset_rid=data.get("sourceDatasetRid"),
            conflict_resolution=ConflictResolutionStrategy(
                data.get("conflictResolution", "TIMESTAMP_WINS")
            ),
            enabled=data.get("enabled", True),
            description=data.get("description"),
        )


class WebhookEndpoint(BaseModel):
    """
    Webhook endpoint configuration.

    Defines the HTTP endpoint for webhook delivery.
    """

    url: str = Field(
        ...,
        description="Webhook endpoint URL.",
        pattern=r"^https://",
    )

    method: str = Field(
        default="POST",
        description="HTTP method (typically POST).",
        pattern=r"^(POST|PUT|PATCH)$",
    )

    headers: Optional[dict[str, str]] = Field(
        default=None,
        description="Custom HTTP headers to include in webhook requests.",
    )

    timeout_seconds: int = Field(
        default=30,
        description="Request timeout in seconds.",
        ge=1,
        le=300,
        alias="timeoutSeconds",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "url": self.url,
            "method": self.method,
            "timeoutSeconds": self.timeout_seconds,
        }

        if self.headers:
            result["headers"] = self.headers

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "WebhookEndpoint":
        """Create from Foundry JSON format."""
        return cls(
            url=data["url"],
            method=data.get("method", "POST"),
            headers=data.get("headers"),
            timeout_seconds=data.get("timeoutSeconds", 30),
        )


class WritebackWebhook(BaseModel):
    """
    Writeback webhook configuration.

    Writeback webhooks execute BEFORE other rules and block all changes on failure.
    Only ONE writeback webhook is allowed per Action.

    Use case: Saga/Compensation pattern - fail-safe external call first.

    Example:
        webhook = WritebackWebhook(
            name="externalSystemSync",
            endpoint=WebhookEndpoint(url="https://api.example.com/sync"),
            output_parameters=["transactionId", "status"]
        )
    """

    name: str = Field(
        ...,
        description="Unique name for this webhook.",
        min_length=1,
        max_length=255,
    )

    endpoint: WebhookEndpoint = Field(
        ...,
        description="Webhook endpoint configuration.",
    )

    description: Optional[str] = Field(
        default=None,
        description="Human-readable description of this webhook.",
    )

    output_parameters: Optional[list[str]] = Field(
        default=None,
        description="Parameters from webhook response available for subsequent rules.",
        alias="outputParameters",
    )

    retry_count: int = Field(
        default=3,
        description="Number of retry attempts on failure.",
        ge=0,
        le=10,
        alias="retryCount",
    )

    enabled: bool = Field(
        default=True,
        description="Whether this webhook is enabled.",
    )

    # Fixed values for writeback webhooks
    webhook_type: WebhookType = Field(
        default=WebhookType.WRITEBACK,
        description="Type of webhook (always WRITEBACK for this class).",
        alias="webhookType",
    )

    execution_order: WebhookExecutionOrder = Field(
        default=WebhookExecutionOrder.BEFORE_OTHER_RULES,
        description="When to execute (always BEFORE_OTHER_RULES for writeback).",
        alias="executionOrder",
    )

    failure_handling: WebhookFailureHandling = Field(
        default=WebhookFailureHandling.BLOCKING,
        description="How to handle failures (always BLOCKING for writeback).",
        alias="failureHandling",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def validate_writeback_settings(self) -> "WritebackWebhook":
        """Ensure writeback webhook has correct fixed settings."""
        if self.webhook_type != WebhookType.WRITEBACK:
            raise ValueError("WritebackWebhook must have webhookType=WRITEBACK")
        if self.execution_order != WebhookExecutionOrder.BEFORE_OTHER_RULES:
            raise ValueError(
                "WritebackWebhook must have executionOrder=BEFORE_OTHER_RULES"
            )
        if self.failure_handling != WebhookFailureHandling.BLOCKING:
            raise ValueError(
                "WritebackWebhook must have failureHandling=BLOCKING"
            )
        return self

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "name": self.name,
            "endpoint": self.endpoint.to_foundry_dict(),
            "webhookType": self.webhook_type.value,
            "executionOrder": self.execution_order.value,
            "failureHandling": self.failure_handling.value,
            "retryCount": self.retry_count,
        }

        if self.description:
            result["description"] = self.description

        if self.output_parameters:
            result["outputParameters"] = self.output_parameters

        if not self.enabled:
            result["enabled"] = False

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "WritebackWebhook":
        """Create from Foundry JSON format."""
        return cls(
            name=data["name"],
            endpoint=WebhookEndpoint.from_foundry_dict(data["endpoint"]),
            description=data.get("description"),
            output_parameters=data.get("outputParameters"),
            retry_count=data.get("retryCount", 3),
            enabled=data.get("enabled", True),
        )


class SideEffectWebhook(BaseModel):
    """
    Side effect webhook configuration.

    Side effect webhooks execute AFTER other rules with best-effort delivery.
    Multiple side effect webhooks are allowed per Action.

    Use case: Event publication, external notifications.

    Example:
        webhook = SideEffectWebhook(
            name="notifyExternalSystem",
            endpoint=WebhookEndpoint(url="https://api.example.com/notify")
        )
    """

    name: str = Field(
        ...,
        description="Unique name for this webhook.",
        min_length=1,
        max_length=255,
    )

    endpoint: WebhookEndpoint = Field(
        ...,
        description="Webhook endpoint configuration.",
    )

    description: Optional[str] = Field(
        default=None,
        description="Human-readable description of this webhook.",
    )

    retry_count: int = Field(
        default=3,
        description="Number of retry attempts on failure.",
        ge=0,
        le=10,
        alias="retryCount",
    )

    enabled: bool = Field(
        default=True,
        description="Whether this webhook is enabled.",
    )

    # Fixed values for side effect webhooks
    webhook_type: WebhookType = Field(
        default=WebhookType.SIDE_EFFECT,
        description="Type of webhook (always SIDE_EFFECT for this class).",
        alias="webhookType",
    )

    execution_order: WebhookExecutionOrder = Field(
        default=WebhookExecutionOrder.AFTER_OTHER_RULES,
        description="When to execute (always AFTER_OTHER_RULES for side effect).",
        alias="executionOrder",
    )

    failure_handling: WebhookFailureHandling = Field(
        default=WebhookFailureHandling.BEST_EFFORT,
        description="How to handle failures (always BEST_EFFORT for side effect).",
        alias="failureHandling",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def validate_side_effect_settings(self) -> "SideEffectWebhook":
        """Ensure side effect webhook has correct fixed settings."""
        if self.webhook_type != WebhookType.SIDE_EFFECT:
            raise ValueError("SideEffectWebhook must have webhookType=SIDE_EFFECT")
        if self.execution_order != WebhookExecutionOrder.AFTER_OTHER_RULES:
            raise ValueError(
                "SideEffectWebhook must have executionOrder=AFTER_OTHER_RULES"
            )
        if self.failure_handling != WebhookFailureHandling.BEST_EFFORT:
            raise ValueError(
                "SideEffectWebhook must have failureHandling=BEST_EFFORT"
            )
        return self

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "name": self.name,
            "endpoint": self.endpoint.to_foundry_dict(),
            "webhookType": self.webhook_type.value,
            "executionOrder": self.execution_order.value,
            "failureHandling": self.failure_handling.value,
            "retryCount": self.retry_count,
        }

        if self.description:
            result["description"] = self.description

        if not self.enabled:
            result["enabled"] = False

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "SideEffectWebhook":
        """Create from Foundry JSON format."""
        return cls(
            name=data["name"],
            endpoint=WebhookEndpoint.from_foundry_dict(data["endpoint"]),
            description=data.get("description"),
            retry_count=data.get("retryCount", 3),
            enabled=data.get("enabled", True),
        )


class FileExportConfig(BaseModel):
    """
    File export configuration for cloud storage.

    Supports batch export to S3, GCS, or Azure Blob Storage.

    Example:
        export = FileExportConfig(
            name="s3Export",
            target=ExportTargetType.S3,
            bucket="my-bucket",
            path_prefix="ontology-exports/",
            format="parquet"
        )
    """

    name: str = Field(
        ...,
        description="Unique name for this export configuration.",
        min_length=1,
        max_length=255,
    )

    target: ExportTargetType = Field(
        ...,
        description="Target storage type (S3, GCS, AZURE_BLOB).",
    )

    bucket: str = Field(
        ...,
        description="Bucket or container name.",
        min_length=1,
    )

    path_prefix: Optional[str] = Field(
        default=None,
        description="Path prefix within the bucket.",
        alias="pathPrefix",
    )

    format: str = Field(
        default="parquet",
        description="Export file format (parquet, csv, json).",
        pattern=r"^(parquet|csv|json|avro)$",
    )

    compression: Optional[str] = Field(
        default=None,
        description="Compression algorithm (gzip, snappy, zstd).",
        pattern=r"^(gzip|snappy|zstd|none)$",
    )

    connection_name: Optional[str] = Field(
        default=None,
        description="Name of the connection configuration in Foundry.",
        alias="connectionName",
    )

    enabled: bool = Field(
        default=True,
        description="Whether this export is enabled.",
    )

    # Fixed mode for file exports
    mode: ExportMode = Field(
        default=ExportMode.BATCH,
        description="Export mode (always BATCH for file exports).",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def validate_file_export(self) -> "FileExportConfig":
        """Validate file export configuration."""
        if self.target not in ExportTargetType.batch_targets():
            raise ValueError(
                f"FileExportConfig target must be one of {ExportTargetType.batch_targets()}"
            )
        return self

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "name": self.name,
            "target": self.target.value,
            "bucket": self.bucket,
            "mode": self.mode.value,
            "format": self.format,
        }

        if self.path_prefix:
            result["pathPrefix"] = self.path_prefix

        if self.compression:
            result["compression"] = self.compression

        if self.connection_name:
            result["connectionName"] = self.connection_name

        if not self.enabled:
            result["enabled"] = False

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "FileExportConfig":
        """Create from Foundry JSON format."""
        return cls(
            name=data["name"],
            target=ExportTargetType(data["target"]),
            bucket=data["bucket"],
            path_prefix=data.get("pathPrefix"),
            format=data.get("format", "parquet"),
            compression=data.get("compression"),
            connection_name=data.get("connectionName"),
            enabled=data.get("enabled", True),
        )


class StreamingExportConfig(BaseModel):
    """
    Streaming export configuration for real-time data sync.

    Supports streaming to Kafka, Kinesis, or Pub/Sub.

    Example:
        export = StreamingExportConfig(
            name="kafkaExport",
            target=ExportTargetType.KAFKA,
            topic="ontology-events",
            bootstrap_servers="kafka.example.com:9092"
        )
    """

    name: str = Field(
        ...,
        description="Unique name for this export configuration.",
        min_length=1,
        max_length=255,
    )

    target: ExportTargetType = Field(
        ...,
        description="Target streaming platform (KAFKA, KINESIS, PUBSUB).",
    )

    topic: str = Field(
        ...,
        description="Topic name for message delivery.",
        min_length=1,
    )

    bootstrap_servers: Optional[str] = Field(
        default=None,
        description="Bootstrap servers for Kafka.",
        alias="bootstrapServers",
    )

    stream_name: Optional[str] = Field(
        default=None,
        description="Stream name for Kinesis.",
        alias="streamName",
    )

    project_id: Optional[str] = Field(
        default=None,
        description="GCP project ID for Pub/Sub.",
        alias="projectId",
    )

    format: str = Field(
        default="json",
        description="Message format (json, avro).",
        pattern=r"^(json|avro)$",
    )

    connection_name: Optional[str] = Field(
        default=None,
        description="Name of the connection configuration in Foundry.",
        alias="connectionName",
    )

    enabled: bool = Field(
        default=True,
        description="Whether this export is enabled.",
    )

    # Fixed mode for streaming exports
    mode: ExportMode = Field(
        default=ExportMode.REALTIME,
        description="Export mode (always REALTIME for streaming exports).",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def validate_streaming_export(self) -> "StreamingExportConfig":
        """Validate streaming export configuration."""
        if self.target not in ExportTargetType.streaming_targets():
            raise ValueError(
                f"StreamingExportConfig target must be one of "
                f"{ExportTargetType.streaming_targets()}"
            )

        # Validate target-specific requirements
        if self.target == ExportTargetType.KAFKA and not self.bootstrap_servers:
            raise ValueError("Kafka export requires bootstrap_servers")
        if self.target == ExportTargetType.KINESIS and not self.stream_name:
            raise ValueError("Kinesis export requires stream_name")
        if self.target == ExportTargetType.PUBSUB and not self.project_id:
            raise ValueError("Pub/Sub export requires project_id")

        return self

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "name": self.name,
            "target": self.target.value,
            "topic": self.topic,
            "mode": self.mode.value,
            "format": self.format,
        }

        if self.bootstrap_servers:
            result["bootstrapServers"] = self.bootstrap_servers

        if self.stream_name:
            result["streamName"] = self.stream_name

        if self.project_id:
            result["projectId"] = self.project_id

        if self.connection_name:
            result["connectionName"] = self.connection_name

        if not self.enabled:
            result["enabled"] = False

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "StreamingExportConfig":
        """Create from Foundry JSON format."""
        return cls(
            name=data["name"],
            target=ExportTargetType(data["target"]),
            topic=data["topic"],
            bootstrap_servers=data.get("bootstrapServers"),
            stream_name=data.get("streamName"),
            project_id=data.get("projectId"),
            format=data.get("format", "json"),
            connection_name=data.get("connectionName"),
            enabled=data.get("enabled", True),
        )


class TableExportConfig(BaseModel):
    """
    Table export configuration for JDBC databases.

    Supports various write modes for database synchronization.

    Example:
        export = TableExportConfig(
            name="postgresExport",
            connection_name="production-db",
            table_name="ontology_objects",
            write_mode=TableExportMode.UPSERT,
            primary_keys=["object_id"]
        )
    """

    name: str = Field(
        ...,
        description="Unique name for this export configuration.",
        min_length=1,
        max_length=255,
    )

    connection_name: str = Field(
        ...,
        description="Name of the JDBC connection configuration in Foundry.",
        alias="connectionName",
    )

    table_name: str = Field(
        ...,
        description="Target table name in the database.",
        alias="tableName",
        min_length=1,
    )

    schema_name: Optional[str] = Field(
        default=None,
        description="Database schema name.",
        alias="schemaName",
    )

    write_mode: TableExportMode = Field(
        default=TableExportMode.APPEND,
        description="Write mode (TRUNCATE_INSERT, APPEND, UPSERT).",
        alias="writeMode",
    )

    primary_keys: Optional[list[str]] = Field(
        default=None,
        description="Primary key columns for UPSERT mode.",
        alias="primaryKeys",
    )

    batch_size: int = Field(
        default=1000,
        description="Batch size for inserts.",
        ge=1,
        le=100000,
        alias="batchSize",
    )

    enabled: bool = Field(
        default=True,
        description="Whether this export is enabled.",
    )

    # Fixed target for table exports
    target: ExportTargetType = Field(
        default=ExportTargetType.JDBC,
        description="Target type (always JDBC for table exports).",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def validate_table_export(self) -> "TableExportConfig":
        """Validate table export configuration."""
        if self.write_mode == TableExportMode.UPSERT and not self.primary_keys:
            raise ValueError("UPSERT mode requires primary_keys to be specified")
        return self

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "name": self.name,
            "target": self.target.value,
            "connectionName": self.connection_name,
            "tableName": self.table_name,
            "writeMode": self.write_mode.value,
            "batchSize": self.batch_size,
        }

        if self.schema_name:
            result["schemaName"] = self.schema_name

        if self.primary_keys:
            result["primaryKeys"] = self.primary_keys

        if not self.enabled:
            result["enabled"] = False

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "TableExportConfig":
        """Create from Foundry JSON format."""
        return cls(
            name=data["name"],
            connection_name=data["connectionName"],
            table_name=data["tableName"],
            schema_name=data.get("schemaName"),
            write_mode=TableExportMode(data.get("writeMode", "APPEND")),
            primary_keys=data.get("primaryKeys"),
            batch_size=data.get("batchSize", 1000),
            enabled=data.get("enabled", True),
        )


# Type alias for any export configuration
ExportConfig = Union[FileExportConfig, StreamingExportConfig, TableExportConfig]


class WritebackConfig(BaseModel):
    """
    Complete writeback configuration for an ObjectType or Action.

    Combines internal writeback dataset with external webhooks and exports.

    Example:
        config = WritebackConfig(
            internal_dataset=WritebackDatasetConfig(
                dataset_rid="ri.foundry.main.dataset.xxx"
            ),
            writeback_webhook=WritebackWebhook(
                name="syncExternal",
                endpoint=WebhookEndpoint(url="https://api.example.com/sync")
            ),
            exports=[
                FileExportConfig(name="s3Backup", target=ExportTargetType.S3, bucket="backup"),
                StreamingExportConfig(
                    name="kafkaStream",
                    target=ExportTargetType.KAFKA,
                    topic="changes",
                    bootstrap_servers="kafka:9092"
                )
            ]
        )
    """

    internal_dataset: Optional[WritebackDatasetConfig] = Field(
        default=None,
        description="Internal writeback dataset configuration.",
        alias="internalDataset",
    )

    writeback_webhook: Optional[WritebackWebhook] = Field(
        default=None,
        description="Writeback webhook (ONE per Action, executes first).",
        alias="writebackWebhook",
    )

    side_effect_webhooks: Optional[list[SideEffectWebhook]] = Field(
        default=None,
        description="Side effect webhooks (multiple allowed).",
        alias="sideEffectWebhooks",
    )

    file_exports: Optional[list[FileExportConfig]] = Field(
        default=None,
        description="File export configurations.",
        alias="fileExports",
    )

    streaming_exports: Optional[list[StreamingExportConfig]] = Field(
        default=None,
        description="Streaming export configurations.",
        alias="streamingExports",
    )

    table_exports: Optional[list[TableExportConfig]] = Field(
        default=None,
        description="Table export configurations.",
        alias="tableExports",
    )

    status: WritebackStatus = Field(
        default=WritebackStatus.ACTIVE,
        description="Status of this writeback configuration.",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @property
    def has_internal_writeback(self) -> bool:
        """Return True if internal writeback is configured."""
        return self.internal_dataset is not None

    @property
    def has_external_writeback(self) -> bool:
        """Return True if any external writeback is configured."""
        return any([
            self.writeback_webhook,
            self.side_effect_webhooks,
            self.file_exports,
            self.streaming_exports,
            self.table_exports,
        ])

    @property
    def all_exports(self) -> list[ExportConfig]:
        """Return all export configurations."""
        exports: list[ExportConfig] = []
        if self.file_exports:
            exports.extend(self.file_exports)
        if self.streaming_exports:
            exports.extend(self.streaming_exports)
        if self.table_exports:
            exports.extend(self.table_exports)
        return exports

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "status": self.status.value,
        }

        if self.internal_dataset:
            result["internalDataset"] = self.internal_dataset.to_foundry_dict()

        if self.writeback_webhook:
            result["writebackWebhook"] = self.writeback_webhook.to_foundry_dict()

        if self.side_effect_webhooks:
            result["sideEffectWebhooks"] = [
                w.to_foundry_dict() for w in self.side_effect_webhooks
            ]

        if self.file_exports:
            result["fileExports"] = [e.to_foundry_dict() for e in self.file_exports]

        if self.streaming_exports:
            result["streamingExports"] = [
                e.to_foundry_dict() for e in self.streaming_exports
            ]

        if self.table_exports:
            result["tableExports"] = [e.to_foundry_dict() for e in self.table_exports]

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "WritebackConfig":
        """Create from Foundry JSON format."""
        internal_dataset = None
        if data.get("internalDataset"):
            internal_dataset = WritebackDatasetConfig.from_foundry_dict(
                data["internalDataset"]
            )

        writeback_webhook = None
        if data.get("writebackWebhook"):
            writeback_webhook = WritebackWebhook.from_foundry_dict(
                data["writebackWebhook"]
            )

        side_effect_webhooks = None
        if data.get("sideEffectWebhooks"):
            side_effect_webhooks = [
                SideEffectWebhook.from_foundry_dict(w)
                for w in data["sideEffectWebhooks"]
            ]

        file_exports = None
        if data.get("fileExports"):
            file_exports = [
                FileExportConfig.from_foundry_dict(e) for e in data["fileExports"]
            ]

        streaming_exports = None
        if data.get("streamingExports"):
            streaming_exports = [
                StreamingExportConfig.from_foundry_dict(e)
                for e in data["streamingExports"]
            ]

        table_exports = None
        if data.get("tableExports"):
            table_exports = [
                TableExportConfig.from_foundry_dict(e) for e in data["tableExports"]
            ]

        return cls(
            internal_dataset=internal_dataset,
            writeback_webhook=writeback_webhook,
            side_effect_webhooks=side_effect_webhooks,
            file_exports=file_exports,
            streaming_exports=streaming_exports,
            table_exports=table_exports,
            status=WritebackStatus(data.get("status", "ACTIVE")),
        )
