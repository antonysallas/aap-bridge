"""
Migration module for AAP Bridge.

This module provides state management, checkpoints, and migration coordination
for migrating from source AAP to target AAP.
"""

# Database models
# Checkpoint management
from aap_migration.migration.checkpoint import AutoCheckpointer, CheckpointManager

# Database utilities
from aap_migration.migration.database import (
    create_database_engine,
    get_database_size,
    get_engine,
    get_session,
    get_session_factory,
    init_database,
    reset_database,
    validate_database_connection,
)
from aap_migration.migration.models import (
    Base,
    Checkpoint,
    IDMapping,
    MigrationMetadata,
    MigrationProgress,
    PerformanceMetric,
)

# State management
from aap_migration.migration.state import MigrationState

__all__ = [
    # Models
    "Base",
    "MigrationProgress",
    "Checkpoint",
    "IDMapping",
    "MigrationMetadata",
    "PerformanceMetric",
    # Database utilities
    "init_database",
    "get_engine",
    "get_session",
    "get_session_factory",
    "create_database_engine",
    "reset_database",
    "validate_database_connection",
    "get_database_size",
    # State management
    "MigrationState",
    # Checkpoint management
    "CheckpointManager",
    "AutoCheckpointer",
]
