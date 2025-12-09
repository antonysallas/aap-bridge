"""
SQLAlchemy models for AAP migration state tracking.

This module defines the database schema for tracking migration progress,
checkpoints, ID mappings, metadata, and performance metrics.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class MigrationProgress(Base):
    """
    Tracks the migration status of individual resources.

    Each row represents a single resource (organization, inventory, host, etc.)
    and tracks its migration state through the pipeline.
    """

    __tablename__ = "migration_progress"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Resource identification
    resource_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Type of resource (e.g., inventory, host, credential)",
    )
    source_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, index=True, comment="ID in source AAP 2.3 system"
    )
    source_name: Mapped[str] = mapped_column(
        String(512), nullable=False, comment="Name of resource in source system"
    )
    target_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        index=True,
        comment="ID in target AAP 2.6 system (null if not yet migrated)",
    )

    # Migration state
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
        comment="Migration status: pending, in_progress, completed, failed, skipped",
    )
    phase: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Migration phase (e.g., export, transform, import)",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), comment="When record was created"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="When record was last updated",
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="When migration started for this resource"
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="When migration completed for this resource"
    )

    # Error tracking
    error_message: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Error message if migration failed"
    )
    retry_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Number of retry attempts"
    )

    # Relationships
    id_mappings: Mapped[list["IDMapping"]] = relationship(
        "IDMapping", back_populates="migration_progress", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("resource_type", "source_id", name="uq_resource_type_source_id"),
        CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed', 'failed', 'skipped')",
            name="ck_migration_progress_status",
        ),
        Index("idx_resource_type_status", "resource_type", "status"),
        Index("idx_status_phase", "status", "phase"),
        Index("idx_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<MigrationProgress(id={self.id}, resource_type='{self.resource_type}', "
            f"source_id={self.source_id}, status='{self.status}')>"
        )


class Checkpoint(Base):
    """
    Stores migration checkpoints for resume functionality.

    Checkpoints capture the state of a migration at a specific point in time,
    allowing migrations to be resumed after interruption.
    """

    __tablename__ = "checkpoints"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Checkpoint identification
    checkpoint_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique name for this checkpoint",
    )
    migration_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Migration run identifier (UUID or timestamp)",
    )

    # Checkpoint data
    phase: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Migration phase at checkpoint (e.g., inventories, hosts)",
    )
    progress_stats: Mapped[dict] = mapped_column(
        JSON, nullable=False, comment="Progress statistics (total, completed, failed counts)"
    )
    checkpoint_data: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="Additional checkpoint data (last processed ID, batch info, etc.)",
    )

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="When checkpoint was created",
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Human-readable description of checkpoint"
    )

    # Validation
    checksum: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="SHA-256 checksum for integrity validation"
    )
    is_valid: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether checkpoint is valid and can be restored",
    )

    # Constraints
    __table_args__ = (
        Index("idx_migration_id_phase", "migration_id", "phase"),
        Index("idx_created_at_desc", "created_at", postgresql_using="btree"),
    )

    def __repr__(self) -> str:
        return (
            f"<Checkpoint(id={self.id}, name='{self.checkpoint_name}', "
            f"phase='{self.phase}', created_at={self.created_at})>"
        )


class IDMapping(Base):
    """
    Maps source resource IDs to target resource IDs.

    This is critical for resolving dependencies between resources
    (e.g., hosts reference inventories, job templates reference projects).
    """

    __tablename__ = "id_mappings"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Resource identification
    resource_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="Type of resource"
    )
    source_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, index=True, comment="ID in source AAP 2.3 system"
    )
    target_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, index=True, comment="ID in target AAP 2.6 system (null if not yet imported)"
    )

    # Additional mapping data
    source_name: Mapped[str | None] = mapped_column(
        String(512), nullable=True, comment="Name of resource in source system"
    )
    target_name: Mapped[str | None] = mapped_column(
        String(512), nullable=True, comment="Name of resource in target system"
    )

    # Foreign key to migration progress
    migration_progress_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("migration_progress.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), comment="When mapping was created"
    )

    # Additional metadata
    mapping_metadata: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="Additional metadata about the mapping"
    )

    # Relationships
    migration_progress: Mapped[Optional["MigrationProgress"]] = relationship(
        "MigrationProgress", back_populates="id_mappings"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("resource_type", "source_id", name="uq_resource_type_source_id_mapping"),
        Index("idx_resource_type_target_id", "resource_type", "target_id"),
        Index("idx_source_id_target_id", "source_id", "target_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<IDMapping(id={self.id}, resource_type='{self.resource_type}', "
            f"source_id={self.source_id}, target_id={self.target_id})>"
        )


class MigrationMetadata(Base):
    """
    Stores metadata about the overall migration run.

    One record per migration run, tracking configuration, environment,
    and overall status.
    """

    __tablename__ = "migration_metadata"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Migration identification
    migration_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique migration run identifier (UUID)",
    )
    migration_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Human-readable migration name"
    )

    # Migration status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="in_progress",
        index=True,
        comment="Overall migration status: in_progress, completed, failed, paused",
    )

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="When migration started",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="When migration completed or failed"
    )
    last_checkpoint_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="When last checkpoint was created"
    )

    # Configuration
    config_snapshot: Mapped[dict] = mapped_column(
        JSON, nullable=False, comment="Configuration snapshot (sanitized, no secrets)"
    )
    source_url: Mapped[str] = mapped_column(
        String(512), nullable=False, comment="Source AAP 2.3 URL"
    )
    target_url: Mapped[str] = mapped_column(
        String(512), nullable=False, comment="Target AAP 2.6 URL"
    )

    # Statistics
    total_resources: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Total number of resources to migrate"
    )
    completed_resources: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Number of successfully migrated resources"
    )
    failed_resources: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Number of failed resources"
    )
    skipped_resources: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Number of skipped resources"
    )

    # Additional metadata
    environment: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="Environment information (Python version, OS, etc.)"
    )
    notes: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Additional notes about the migration"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('in_progress', 'completed', 'failed', 'paused')",
            name="ck_migration_metadata_status",
        ),
        Index("idx_started_at_desc", "started_at", postgresql_using="btree"),
    )

    def __repr__(self) -> str:
        return (
            f"<MigrationMetadata(id={self.id}, migration_id='{self.migration_id}', "
            f"status='{self.status}', started_at={self.started_at})>"
        )


class PerformanceMetric(Base):
    """
    Tracks performance metrics during migration.

    Records timing, throughput, and resource utilization data
    for performance analysis and optimization.
    """

    __tablename__ = "performance_metrics"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Metric identification
    migration_id: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True, comment="Migration run identifier"
    )
    metric_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Type of metric (e.g., api_call, batch_processing, checkpoint)",
    )
    resource_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Resource type being measured (if applicable)",
    )

    # Timestamp
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="When metric was recorded",
    )

    # Performance data
    duration_ms: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Duration in milliseconds"
    )
    throughput: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Throughput (resources per second)"
    )
    batch_size: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Batch size used (if applicable)"
    )
    success_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Number of successful operations"
    )
    failure_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Number of failed operations"
    )

    # Additional metric data
    metric_data: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="Additional metric data (memory usage, API calls, etc.)"
    )

    # Constraints
    __table_args__ = (
        Index("idx_migration_id_metric_type", "migration_id", "metric_type"),
        Index("idx_metric_type_recorded_at", "metric_type", "recorded_at"),
        Index("idx_recorded_at_desc", "recorded_at", postgresql_using="btree"),
    )

    def __repr__(self) -> str:
        return (
            f"<PerformanceMetric(id={self.id}, metric_type='{self.metric_type}', "
            f"duration_ms={self.duration_ms}, recorded_at={self.recorded_at})>"
        )
