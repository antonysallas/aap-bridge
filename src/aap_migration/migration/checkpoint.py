"""
Checkpoint and resume management for migrations.

This module provides the CheckpointManager class for creating, restoring,
and managing migration checkpoints. Checkpoints allow migrations to be
resumed after interruption.
"""

import hashlib
import json
from datetime import UTC, datetime

from sqlalchemy import desc

from aap_migration.client.exceptions import CheckpointError
from aap_migration.migration.database import get_session
from aap_migration.migration.models import Checkpoint
from aap_migration.migration.state import MigrationState
from aap_migration.utils.logging import get_logger

logger = get_logger(__name__)


class CheckpointManager:
    """
    Manages migration checkpoints for resume functionality.

    Checkpoints capture the state of a migration at a specific point,
    allowing migrations to resume after interruption. The manager handles
    automatic checkpoint creation, validation, and restoration.

    Usage:
        manager = CheckpointManager(state)

        # Create checkpoint
        checkpoint_id = manager.create_checkpoint(
            phase="inventories",
            progress_stats={"completed": 500, "total": 1000}
        )

        # Restore from checkpoint
        manager.restore_checkpoint(checkpoint_id)

        # Resume from latest
        if manager.has_checkpoints():
            latest = manager.get_latest_checkpoint()
            manager.restore_checkpoint(latest['id'])
    """

    def __init__(self, state: MigrationState):
        """
        Initialize checkpoint manager.

        Args:
            state: MigrationState instance to manage checkpoints for
        """
        self.state = state
        self.database_url = state.database_url
        self._checkpoint_counter = 0

    def create_checkpoint(
        self,
        phase: str,
        progress_stats: dict[str, int] | None = None,
        checkpoint_data: dict | None = None,
        description: str | None = None,
        checkpoint_name: str | None = None,
    ) -> int:
        """
        Create a new checkpoint.

        Args:
            phase: Current migration phase (e.g., 'inventories', 'hosts')
            progress_stats: Progress statistics (total, completed, failed counts)
            checkpoint_data: Additional checkpoint data (last_processed_id, batch_info, etc.)
            description: Human-readable description
            checkpoint_name: Optional custom name (auto-generated if None)

        Returns:
            Checkpoint ID

        Raises:
            CheckpointError: If checkpoint creation fails
        """
        try:
            # Get current stats if not provided
            if progress_stats is None:
                progress_stats = self.state.get_migration_stats()

            # Generate checkpoint name if not provided
            if checkpoint_name is None:
                self._checkpoint_counter += 1
                timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")
                checkpoint_name = (
                    f"{self.state.migration_id}_{phase}_{timestamp}_{self._checkpoint_counter:04d}"
                )

            # Default checkpoint data
            if checkpoint_data is None:
                checkpoint_data = {}

            # Add migration metadata to checkpoint data
            checkpoint_data.update(
                {
                    "migration_id": self.state.migration_id,
                    "migration_name": self.state.migration_name,
                    "created_at": datetime.now(UTC).isoformat(),
                    "phase": phase,
                }
            )

            # Calculate checksum for integrity validation
            checksum = self._calculate_checksum(
                {
                    "checkpoint_name": checkpoint_name,
                    "phase": phase,
                    "progress_stats": progress_stats,
                    "checkpoint_data": checkpoint_data,
                }
            )

            # Create checkpoint record
            with get_session(self.database_url) as session:
                checkpoint = Checkpoint(
                    checkpoint_name=checkpoint_name,
                    migration_id=self.state.migration_id,
                    phase=phase,
                    progress_stats=progress_stats,
                    checkpoint_data=checkpoint_data,
                    description=description,
                    checksum=checksum,
                    is_valid=True,
                )
                session.add(checkpoint)
                session.commit()

                checkpoint_id = checkpoint.id

                logger.info(
                    "Created checkpoint",
                    checkpoint_id=checkpoint_id,
                    checkpoint_name=checkpoint_name,
                    phase=phase,
                    progress_stats=progress_stats,
                )

                return checkpoint_id

        except Exception as e:
            logger.error("Failed to create checkpoint", phase=phase, error=str(e))
            raise CheckpointError(f"Failed to create checkpoint: {e}") from e

    def restore_checkpoint(
        self,
        checkpoint_id: int,
        validate_integrity: bool = True,
    ) -> dict:
        """
        Restore migration state from a checkpoint.

        This loads the checkpoint data and returns it for the caller to use.
        It does NOT automatically reset the migration state - the caller
        should decide how to handle the restored data.

        Args:
            checkpoint_id: ID of checkpoint to restore
            validate_integrity: Whether to validate checksum

        Returns:
            Dictionary with checkpoint data:
            {
                'checkpoint_id': int,
                'checkpoint_name': str,
                'phase': str,
                'progress_stats': dict,
                'checkpoint_data': dict,
                'created_at': datetime,
                'description': str
            }

        Raises:
            CheckpointError: If checkpoint not found or validation fails
        """
        try:
            with get_session(self.database_url) as session:
                checkpoint = session.query(Checkpoint).filter_by(id=checkpoint_id).first()

                if checkpoint is None:
                    raise CheckpointError(f"Checkpoint not found: {checkpoint_id}")

                if not checkpoint.is_valid:
                    raise CheckpointError(
                        f"Checkpoint is marked as invalid: {checkpoint.checkpoint_name}"
                    )

                # Validate integrity
                if validate_integrity:
                    self._validate_checkpoint(checkpoint)

                # Prepare restored data
                restored_data = {
                    "checkpoint_id": checkpoint.id,
                    "checkpoint_name": checkpoint.checkpoint_name,
                    "phase": checkpoint.phase,
                    "progress_stats": checkpoint.progress_stats,
                    "checkpoint_data": checkpoint.checkpoint_data,
                    "created_at": checkpoint.created_at,
                    "description": checkpoint.description,
                }

                logger.info(
                    "Restored checkpoint",
                    checkpoint_id=checkpoint_id,
                    checkpoint_name=checkpoint.checkpoint_name,
                    phase=checkpoint.phase,
                )

                return restored_data

        except CheckpointError:
            raise
        except Exception as e:
            logger.error("Failed to restore checkpoint", checkpoint_id=checkpoint_id, error=str(e))
            raise CheckpointError(f"Failed to restore checkpoint: {e}") from e

    def list_checkpoints(
        self,
        migration_id: str | None = None,
        phase: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """
        List available checkpoints.

        Args:
            migration_id: Filter by migration ID (uses current if None)
            phase: Filter by phase
            limit: Maximum number of checkpoints to return

        Returns:
            List of checkpoint dictionaries (most recent first)
        """
        try:
            if migration_id is None:
                migration_id = self.state.migration_id

            with get_session(self.database_url) as session:
                query = session.query(Checkpoint).filter_by(migration_id=migration_id)

                if phase:
                    query = query.filter_by(phase=phase)

                checkpoints = (
                    query.order_by(desc(Checkpoint.created_at), desc(Checkpoint.id))
                    .limit(limit)
                    .all()
                )

                result = [
                    {
                        "id": cp.id,
                        "checkpoint_name": cp.checkpoint_name,
                        "phase": cp.phase,
                        "progress_stats": cp.progress_stats,
                        "created_at": cp.created_at,
                        "description": cp.description,
                        "is_valid": cp.is_valid,
                    }
                    for cp in checkpoints
                ]

                logger.debug(
                    "Listed checkpoints",
                    migration_id=migration_id,
                    phase=phase,
                    count=len(result),
                )

                return result

        except Exception as e:
            logger.error("Failed to list checkpoints", error=str(e))
            raise CheckpointError(f"Failed to list checkpoints: {e}") from e

    def get_latest_checkpoint(
        self,
        phase: str | None = None,
    ) -> dict | None:
        """
        Get the most recent checkpoint.

        Args:
            phase: Filter by phase (optional)

        Returns:
            Checkpoint dictionary or None if no checkpoints exist
        """
        checkpoints = self.list_checkpoints(phase=phase, limit=1)
        return checkpoints[0] if checkpoints else None

    def delete_checkpoint(self, checkpoint_id: int) -> None:
        """
        Delete a checkpoint.

        Args:
            checkpoint_id: ID of checkpoint to delete

        Raises:
            CheckpointError: If deletion fails
        """
        try:
            with get_session(self.database_url) as session:
                checkpoint = session.query(Checkpoint).filter_by(id=checkpoint_id).first()

                if checkpoint is None:
                    raise CheckpointError(f"Checkpoint not found: {checkpoint_id}")

                checkpoint_name = checkpoint.checkpoint_name
                session.delete(checkpoint)
                session.commit()

                logger.info(
                    "Deleted checkpoint",
                    checkpoint_id=checkpoint_id,
                    checkpoint_name=checkpoint_name,
                )

        except CheckpointError:
            raise
        except Exception as e:
            logger.error("Failed to delete checkpoint", checkpoint_id=checkpoint_id, error=str(e))
            raise CheckpointError(f"Failed to delete checkpoint: {e}") from e

    def delete_old_checkpoints(
        self,
        keep_count: int = 5,
        phase: str | None = None,
    ) -> int:
        """
        Delete old checkpoints, keeping only the most recent N.

        Args:
            keep_count: Number of recent checkpoints to keep
            phase: Filter by phase (optional)

        Returns:
            Number of checkpoints deleted

        Raises:
            CheckpointError: If deletion fails
        """
        try:
            with get_session(self.database_url) as session:
                query = session.query(Checkpoint).filter_by(migration_id=self.state.migration_id)

                if phase:
                    query = query.filter_by(phase=phase)

                # Get all checkpoints ordered by creation time (and ID as tiebreaker)
                all_checkpoints = query.order_by(
                    desc(Checkpoint.created_at), desc(Checkpoint.id)
                ).all()

                # Delete old checkpoints
                deleted_count = 0
                for checkpoint in all_checkpoints[keep_count:]:
                    session.delete(checkpoint)
                    deleted_count += 1

                session.commit()

                logger.info(
                    "Deleted old checkpoints",
                    keep_count=keep_count,
                    deleted_count=deleted_count,
                    phase=phase,
                )

                return deleted_count

        except Exception as e:
            logger.error("Failed to delete old checkpoints", error=str(e))
            raise CheckpointError(f"Failed to delete old checkpoints: {e}") from e

    def has_checkpoints(self, phase: str | None = None) -> bool:
        """
        Check if any checkpoints exist.

        Args:
            phase: Filter by phase (optional)

        Returns:
            True if checkpoints exist, False otherwise
        """
        checkpoints = self.list_checkpoints(phase=phase, limit=1)
        return len(checkpoints) > 0

    def should_create_checkpoint(
        self,
        completed_since_last: int,
        checkpoint_frequency: int,
    ) -> bool:
        """
        Determine if a checkpoint should be created based on frequency.

        Args:
            completed_since_last: Number of resources completed since last checkpoint
            checkpoint_frequency: Create checkpoint every N resources

        Returns:
            True if checkpoint should be created
        """
        return completed_since_last >= checkpoint_frequency

    def get_resume_info(self) -> dict | None:
        """
        Get information for resuming an interrupted migration.

        Returns:
            Dictionary with resume information or None if no checkpoints:
            {
                'checkpoint_id': int,
                'checkpoint_name': str,
                'phase': str,
                'progress_stats': dict,
                'completed': int,
                'total': int,
                'percentage': float
            }
        """
        latest = self.get_latest_checkpoint()

        if latest is None:
            return None

        progress_stats = latest["progress_stats"]
        completed = progress_stats.get("completed", 0)
        total = progress_stats.get("total", 0)
        percentage = (completed / total * 100) if total > 0 else 0

        # Get full checkpoint details including checkpoint_data
        restored = self.restore_checkpoint(latest["id"], validate_integrity=False)

        return {
            "checkpoint_id": latest["id"],
            "checkpoint_name": latest["checkpoint_name"],
            "phase": latest["phase"],
            "progress_stats": progress_stats,
            "checkpoint_data": restored["checkpoint_data"],
            "completed": completed,
            "total": total,
            "percentage": percentage,
            "created_at": latest["created_at"],
        }

    def invalidate_checkpoint(self, checkpoint_id: int, reason: str) -> None:
        """
        Mark a checkpoint as invalid.

        Args:
            checkpoint_id: ID of checkpoint to invalidate
            reason: Reason for invalidation

        Raises:
            CheckpointError: If operation fails
        """
        try:
            with get_session(self.database_url) as session:
                checkpoint = session.query(Checkpoint).filter_by(id=checkpoint_id).first()

                if checkpoint is None:
                    raise CheckpointError(f"Checkpoint not found: {checkpoint_id}")

                checkpoint.is_valid = False
                checkpoint.description = f"INVALID: {reason}"
                session.commit()

                logger.warning(
                    "Invalidated checkpoint",
                    checkpoint_id=checkpoint_id,
                    checkpoint_name=checkpoint.checkpoint_name,
                    reason=reason,
                )

        except CheckpointError:
            raise
        except Exception as e:
            logger.error(
                "Failed to invalidate checkpoint", checkpoint_id=checkpoint_id, error=str(e)
            )
            raise CheckpointError(f"Failed to invalidate checkpoint: {e}") from e

    def _calculate_checksum(self, data: dict) -> str:
        """
        Calculate SHA-256 checksum for checkpoint data.

        Args:
            data: Checkpoint data dictionary

        Returns:
            Hex string of checksum
        """
        # Serialize data to JSON (sorted keys for consistency)
        json_data = json.dumps(data, sort_keys=True, default=str)
        # Calculate SHA-256
        checksum = hashlib.sha256(json_data.encode()).hexdigest()
        return checksum

    def _validate_checkpoint(self, checkpoint: Checkpoint) -> None:
        """
        Validate checkpoint integrity.

        Args:
            checkpoint: Checkpoint model instance

        Raises:
            CheckpointError: If validation fails
        """
        if checkpoint.checksum is None:
            logger.warning(
                "Checkpoint has no checksum, skipping validation",
                checkpoint_id=checkpoint.id,
            )
            return

        # Recalculate checksum
        data = {
            "checkpoint_name": checkpoint.checkpoint_name,
            "phase": checkpoint.phase,
            "progress_stats": checkpoint.progress_stats,
            "checkpoint_data": checkpoint.checkpoint_data,
        }
        calculated_checksum = self._calculate_checksum(data)

        # Compare
        if calculated_checksum != checkpoint.checksum:
            raise CheckpointError(
                f"Checkpoint integrity check failed: {checkpoint.checkpoint_name}. "
                f"Expected {checkpoint.checksum}, got {calculated_checksum}"
            )

        logger.debug(
            "Checkpoint integrity validated",
            checkpoint_id=checkpoint.id,
            checkpoint_name=checkpoint.checkpoint_name,
        )


class AutoCheckpointer:
    """
    Automatic checkpoint creation helper.

    Tracks progress and automatically creates checkpoints at
    specified intervals.

    Usage:
        auto_cp = AutoCheckpointer(checkpoint_manager, frequency=100)

        for item in items:
            # ... process item ...

            # Track progress and create checkpoint if needed
            if auto_cp.track_completion("inventories"):
                print(f"Created checkpoint at {auto_cp.completed_count} items")
    """

    def __init__(
        self,
        checkpoint_manager: CheckpointManager,
        frequency: int = 100,
    ):
        """
        Initialize auto-checkpointer.

        Args:
            checkpoint_manager: CheckpointManager instance
            frequency: Create checkpoint every N completed resources
        """
        self.checkpoint_manager = checkpoint_manager
        self.frequency = frequency
        self.completed_count = 0
        self.last_checkpoint_at = 0

    def track_completion(
        self,
        phase: str,
        increment: int = 1,
        checkpoint_data: dict | None = None,
    ) -> bool:
        """
        Track resource completion and create checkpoint if needed.

        Args:
            phase: Current migration phase
            increment: Number of resources completed (default: 1)
            checkpoint_data: Additional checkpoint data

        Returns:
            True if checkpoint was created, False otherwise
        """
        self.completed_count += increment
        completed_since_last = self.completed_count - self.last_checkpoint_at

        if self.checkpoint_manager.should_create_checkpoint(completed_since_last, self.frequency):
            # Create checkpoint
            stats = self.checkpoint_manager.state.get_migration_stats()

            if checkpoint_data is None:
                checkpoint_data = {}

            checkpoint_data.update(
                {
                    "completed_count": self.completed_count,
                    "last_checkpoint_at": self.last_checkpoint_at,
                }
            )

            self.checkpoint_manager.create_checkpoint(
                phase=phase,
                progress_stats=stats,
                checkpoint_data=checkpoint_data,
                description=f"Auto-checkpoint at {self.completed_count} completed resources",
            )

            self.last_checkpoint_at = self.completed_count
            return True

        return False

    def reset(self) -> None:
        """Reset counters."""
        self.completed_count = 0
        self.last_checkpoint_at = 0
