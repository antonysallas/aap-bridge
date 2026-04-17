"""
Checkpoint management commands.

This module provides commands for managing migration checkpoints,
allowing users to view, inspect, and clean up checkpoint data.
"""

import click

from aap_migration.cli.context import MigrationContext
from aap_migration.cli.decorators import (
    confirm_action,
    handle_errors,
    pass_context,
    requires_config,
)
from aap_migration.cli.utils import (
    echo_error,
    echo_info,
    echo_success,
    echo_warning,
    format_timestamp,
    print_table,
)
from aap_migration.migration.checkpoint import CheckpointManager
from aap_migration.utils.logging import get_logger

logger = get_logger(__name__)


@click.group(name="checkpoint")
def checkpoint() -> None:
    """Checkpoint management commands.

    Manage migration checkpoints for resume and recovery.
    """
    pass


@checkpoint.command(name="list")
@click.option(
    "--limit",
    type=int,
    default=20,
    help="Maximum number of checkpoints to display",
)
@pass_context
@requires_config
@handle_errors
def list_checkpoints(ctx: MigrationContext, limit: int) -> None:
    """List all migration checkpoints.

    Displays a list of all saved checkpoints including:
    - Checkpoint ID
    - Phase name
    - Timestamp
    - Status

    Examples:

        # List all checkpoints
        aap-bridge checkpoint list --config config.yaml

        # Limit results
        aap-bridge checkpoint list --config config.yaml --limit 10
    """
    echo_info("Loading checkpoints...")

    try:
        checkpoint_manager = CheckpointManager(ctx.config.state)

        # Get all checkpoints
        checkpoints = checkpoint_manager.list_checkpoints(limit=limit)

        if not checkpoints:
            echo_warning("No checkpoints found")
            return

        # Display checkpoints in table
        rows = []
        for cp in checkpoints:
            rows.append(
                [
                    str(cp.get("id", "N/A")),
                    cp.get("phase", "unknown"),
                    cp.get("status", "unknown"),
                    format_timestamp(cp.get("created_at")) if cp.get("created_at") else "N/A",
                    str(cp.get("resources_processed", 0)),
                ]
            )

        print_table(
            f"Migration Checkpoints (showing {len(checkpoints)})",
            ["ID", "Phase", "Status", "Created", "Resources"],
            rows,
        )

        echo_success(f"Found {len(checkpoints)} checkpoint(s)")

    except Exception as e:
        echo_error(f"Failed to list checkpoints: {e}")
        logger.error("Checkpoint list failed", error=str(e), exc_info=True)
        raise click.ClickException(str(e)) from e


@checkpoint.command(name="show")
@click.argument("checkpoint_id", type=str)
@pass_context
@requires_config
@handle_errors
def show_checkpoint(ctx: MigrationContext, checkpoint_id: str) -> None:
    """Show detailed checkpoint information.

    Displays detailed information about a specific checkpoint including:
    - All metadata
    - Resource counts
    - Error information (if any)
    - Progress data

    Examples:

        aap-bridge checkpoint show <checkpoint-id> --config config.yaml
    """
    echo_info(f"Loading checkpoint: {checkpoint_id}")

    try:
        checkpoint_manager = CheckpointManager(ctx.config.state)

        # Get checkpoint details
        checkpoint = checkpoint_manager.get_checkpoint(checkpoint_id)

        if not checkpoint:
            echo_error(f"Checkpoint not found: {checkpoint_id}")
            raise click.ClickException(f"Checkpoint {checkpoint_id} not found")

        # Display checkpoint details
        click.echo()
        click.echo("Checkpoint Details:")
        click.echo(f"  ID: {checkpoint.get('id')}")
        click.echo(f"  Phase: {checkpoint.get('phase')}")
        click.echo(f"  Status: {checkpoint.get('status')}")
        click.echo(f"  Created: {format_timestamp(checkpoint.get('created_at'))}")

        click.echo()
        click.echo("Progress:")
        click.echo(f"  Resources Processed: {checkpoint.get('resources_processed', 0)}")
        click.echo(f"  Resources Failed: {checkpoint.get('resources_failed', 0)}")
        click.echo(f"  Resources Skipped: {checkpoint.get('resources_skipped', 0)}")

        if checkpoint.get("last_resource_id"):
            click.echo(f"  Last Resource ID: {checkpoint.get('last_resource_id')}")

        # Show error info if present
        if checkpoint.get("error"):
            click.echo()
            echo_warning("Error Information:")
            click.echo(f"  {checkpoint.get('error')}")

        # Show metadata if present
        metadata = checkpoint.get("metadata", {})
        if metadata:
            click.echo()
            click.echo("Additional Metadata:")
            for key, value in metadata.items():
                click.echo(f"  {key}: {value}")

    except Exception as e:
        echo_error(f"Failed to show checkpoint: {e}")
        logger.error("Checkpoint show failed", error=str(e), exc_info=True)
        raise click.ClickException(str(e)) from e


@checkpoint.command(name="delete")
@click.argument("checkpoint_id", type=str, required=False)
@click.option(
    "--all",
    "delete_all",
    is_flag=True,
    help="Delete all checkpoints",
)
@click.option(
    "--older-than",
    type=int,
    help="Delete checkpoints older than N days",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt",
)
@pass_context
@requires_config
@handle_errors
def delete_checkpoint(
    ctx: MigrationContext,
    checkpoint_id: str | None,
    delete_all: bool,
    older_than: int | None,
    yes: bool,
) -> None:
    """Delete migration checkpoints.

    Delete one or more checkpoints to clean up storage. Use with caution
    as deleted checkpoints cannot be recovered.

    Examples:

        # Delete specific checkpoint
        aap-bridge checkpoint delete <checkpoint-id> --config config.yaml

        # Delete all checkpoints
        aap-bridge checkpoint delete --all --config config.yaml

        # Delete old checkpoints
        aap-bridge checkpoint delete --older-than 30 --config config.yaml
    """
    if not checkpoint_id and not delete_all and not older_than:
        echo_error("Must specify checkpoint ID, --all, or --older-than")
        raise click.ClickException("No deletion criteria specified")

    try:
        checkpoint_manager = CheckpointManager(ctx.config.state)

        # Determine what to delete
        if delete_all:
            message = "Delete ALL checkpoints?"
            abort_message = "Deletion cancelled"
        elif older_than:
            message = f"Delete checkpoints older than {older_than} days?"
            abort_message = "Deletion cancelled"
        else:
            message = f"Delete checkpoint {checkpoint_id}?"
            abort_message = "Deletion cancelled"

        # Confirm deletion
        if not yes and not click.confirm(message):
            click.echo(abort_message)
            return

        # Perform deletion
        if delete_all:
            deleted_count = checkpoint_manager.delete_all_checkpoints()
            echo_success(f"Deleted {deleted_count} checkpoint(s)")

        elif older_than:
            deleted_count = checkpoint_manager.delete_old_checkpoints(days=older_than)
            echo_success(f"Deleted {deleted_count} checkpoint(s) older than {older_than} days")

        else:
            checkpoint_manager.delete_checkpoint(checkpoint_id)
            echo_success(f"Deleted checkpoint: {checkpoint_id}")

    except Exception as e:
        echo_error(f"Failed to delete checkpoint(s): {e}")
        logger.error("Checkpoint deletion failed", error=str(e), exc_info=True)
        raise click.ClickException(str(e)) from e


@checkpoint.command(name="clean")
@click.option(
    "--keep-latest",
    type=int,
    default=5,
    help="Number of latest checkpoints to keep",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt",
)
@pass_context
@requires_config
@handle_errors
@confirm_action(
    message="Clean up old checkpoints?",
    abort_message="Cleanup cancelled",
)
def clean_checkpoints(
    ctx: MigrationContext,
    keep_latest: int,
    yes: bool,
) -> None:
    """Clean up old checkpoints, keeping only recent ones.

    Removes old checkpoints to save storage space while preserving
    the most recent checkpoints for recovery.

    Examples:

        # Keep latest 5 checkpoints
        aap-bridge checkpoint clean --config config.yaml

        # Keep latest 10 checkpoints
        aap-bridge checkpoint clean --keep-latest 10 --config config.yaml
    """
    echo_info(f"Cleaning checkpoints (keeping latest {keep_latest})...")

    try:
        checkpoint_manager = CheckpointManager(ctx.config.state)

        # Get all checkpoints
        all_checkpoints = checkpoint_manager.list_checkpoints()

        if len(all_checkpoints) <= keep_latest:
            echo_info(f"Only {len(all_checkpoints)} checkpoint(s) found, nothing to clean")
            return

        # Delete old checkpoints
        deleted_count = checkpoint_manager.cleanup_checkpoints(keep_count=keep_latest)

        echo_success(f"Cleaned up {deleted_count} checkpoint(s), kept latest {keep_latest}")

    except Exception as e:
        echo_error(f"Failed to clean checkpoints: {e}")
        logger.error("Checkpoint cleanup failed", error=str(e), exc_info=True)
        raise click.ClickException(str(e)) from e
