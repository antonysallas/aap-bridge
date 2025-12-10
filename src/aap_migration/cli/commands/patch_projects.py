"""
Patch projects command (Phase 2).

This module provides the logic for Phase 2 of the migration:
Hydrating/patching projects that were imported as "Manual" with their original
SCM configuration in controlled batches to prevent controller resource exhaustion.
"""

import asyncio
import json
from contextlib import nullcontext
from pathlib import Path

import click

from aap_migration.cli.context import MigrationContext
from aap_migration.cli.decorators import handle_errors, pass_context, requires_config
from aap_migration.cli.utils import (
    echo_error,
    echo_info,
    echo_success,
    echo_warning,
    step_progress,
)
from aap_migration.migration.importer import wait_for_project_sync
from aap_migration.reporting.live_progress import MigrationProgressDisplay
from aap_migration.utils.logging import get_logger

logger = get_logger(__name__)


async def patch_project_scm_details(
    ctx: MigrationContext,
    input_dir: Path,
    batch_size: int = 100,
    interval: int = 600,
    progress_display: MigrationProgressDisplay | None = None,
) -> None:
    """Execute Phase 2: Patch projects with SCM details.

    1. Reads transformed project files.
    2. Identifies projects with _deferred_scm_details.
    3. PATCHes them in batches.
    4. Sleeps between batches to space out sync jobs.
    5. Waits for final sync completion before finishing.

    Args:
        ctx: Migration context
        input_dir: Directory containing transformed project files
        batch_size: Number of projects to patch at once (default 100)
        interval: Seconds to sleep between batches (default 600)
        progress_display: Optional existing progress display to use
    """
    projects_dir = input_dir / "projects"
    if not projects_dir.exists():
        echo_warning("No projects directory found in transformed output. Skipping Phase 2.")
        return

    # Find all project files
    json_files = sorted(projects_dir.glob("projects_*.json"))
    if not json_files:
        echo_warning("No project files found. Skipping Phase 2.")
        return

    # Load all projects with deferred details
    projects_to_patch = []

    with step_progress("Scanning projects for deferred SCM details"):
        for json_file in json_files:
            try:
                with open(json_file) as f:
                    resources = json.load(f)
                    for resource in resources:
                        if "_deferred_scm_details" in resource:
                            projects_to_patch.append(resource)
            except Exception as e:
                echo_error(f"Failed to load {json_file}: {e}")

    if not projects_to_patch:
        echo_info("No projects found with deferred SCM details. Phase 2 not required.")
        return

    total_projects = len(projects_to_patch)
    echo_info(f"Found {total_projects} projects requiring SCM activation.")
    echo_info(f"Starting Phase 2: Patching {batch_size} projects every {interval}s")

    # Initialize progress display
    phases = [
        ("patching", "Patching Projects", total_projects),
        ("syncing", "Waiting for Final Sync", total_projects),
    ]

    # Use existing display or create new one
    if progress_display:
        progress_ctx = nullcontext(progress_display)
    else:
        progress_ctx = MigrationProgressDisplay(title="🔄 Phase 2: Project Patching", enabled=True)

    with progress_ctx as progress:
        # If new display, initialize layout
        if not progress_display:
            progress.set_total_phases(2)
            progress.initialize_phases(phases)

        progress.start_phase("patching", "Patching Projects", total_projects)
        progress.start_phase("syncing", "Waiting for Final Sync", total_projects)

        patched_count = 0
        failed_patch_count = 0
        all_target_ids = []

        # Process in batches
        for i in range(0, total_projects, batch_size):
            batch = projects_to_patch[i : i + batch_size]
            batch_target_ids = []

            # Patch this batch
            for project in batch:
                source_id = project.get("_source_id")
                name = project.get("name")
                deferred = project.get("_deferred_scm_details", {})

                # Get Target ID
                target_id = ctx.migration_state.get_mapped_id("projects", source_id)

                if not target_id:
                    logger.warning(
                        "project_patch_skipped_no_mapping",
                        source_id=source_id,
                        name=name,
                        message="Project not found in map (not imported?)",
                    )
                    failed_patch_count += 1
                    progress.update_phase("patching", patched_count, failed_patch_count)
                    continue

                try:
                    # Prepare PATCH payload
                    patch_data = {
                        "scm_type": deferred.get("scm_type"),
                        "scm_url": deferred.get("scm_url"),
                        "scm_branch": deferred.get("scm_branch", ""),
                        "scm_clean": deferred.get("scm_clean", False),
                        "scm_delete_on_update": deferred.get("scm_delete_on_update", False),
                        "scm_update_on_launch": deferred.get("scm_update_on_launch", False),
                        "scm_update_cache_timeout": deferred.get("scm_update_cache_timeout", 0),
                    }

                    # Resolve credential dependency
                    source_cred_id = deferred.get("credential")
                    if source_cred_id:
                        target_cred_id = ctx.migration_state.get_mapped_id(
                            "credentials", source_cred_id
                        )
                        if target_cred_id:
                            patch_data["credential"] = target_cred_id
                        else:
                            logger.warning(
                                "project_patch_credential_missing",
                                source_id=source_id,
                                credential_id=source_cred_id,
                                message="Credential not mapped",
                            )

                    # Perform PATCH
                    await ctx.target_client.patch(f"projects/{target_id}/", json_data=patch_data)

                    patched_count += 1
                    batch_target_ids.append(target_id)
                    all_target_ids.append(target_id)

                    logger.info(
                        "project_patched_scm",
                        source_id=source_id,
                        target_id=target_id,
                        name=name,
                    )

                except Exception as e:
                    failed_patch_count += 1
                    logger.error(
                        "project_patch_failed",
                        source_id=source_id,
                        target_id=target_id,
                        error=str(e),
                    )

                progress.update_phase("patching", patched_count, failed_patch_count)

            # After batch is done, sleep if there are more batches
            if i + batch_size < total_projects:
                logger.info(
                    "phase2_batch_sleep",
                    seconds=interval,
                    message=f"Batch complete. Sleeping {interval}s.",
                )
                # Show sleeping status?
                # Using asyncio.sleep prevents progress updates during sleep unless we run a background task,
                # but for now a simple sleep is fine.
                await asyncio.sleep(interval)

        progress.complete_phase("patching")

        # Wait for ALL patched projects to sync
        # This ensures Phase 3 (Job Templates) starts with clean state
        if all_target_ids:
            logger.info(
                "phase2_final_wait",
                count=len(all_target_ids),
                message="Waiting for all projects to sync",
            )

            def wait_progress_callback(synced, failed, _):
                progress.update_phase("syncing", synced, failed)

            # Set a generous timeout: 10 minutes base + 1 minute per project
            # For 1000 projects, this is huge, but necessary if they are all queuing
            timeout = 600 + (len(all_target_ids) * 60)

            synced, failed, failed_ids = await wait_for_project_sync(
                client=ctx.target_client,
                project_ids=all_target_ids,
                timeout=timeout,
                progress_callback=wait_progress_callback,
            )

            progress.update_phase("syncing", synced, failed)
            progress.complete_phase("syncing")

            if failed_ids:
                echo_warning(f"Phase 2 completed with {failed} sync failures.")
                logger.warning("phase2_sync_failures", failed_ids=failed_ids)
            else:
                echo_success(f"Phase 2 Complete: All {synced} projects patched and synced.")
        else:
            progress.complete_phase("syncing")
            echo_warning("Phase 2 completed but no projects were patched.")


@click.command(name="patch-projects")
@click.option(
    "--input",
    "-i",
    "input_dir",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Input directory with transformed projects (default: xformed/)",
)
@click.option(
    "--batch-size",
    type=int,
    default=None,
    help="Number of projects to patch at once (default: from config)",
)
@click.option(
    "--interval",
    type=int,
    default=None,
    help="Seconds to wait between batches (default: from config)",
)
@pass_context
@requires_config
@handle_errors
def patch_projects(
    ctx: MigrationContext,
    input_dir: Path | None,
    batch_size: int | None,
    interval: int | None,
) -> None:
    """Execute Phase 2: Patch projects with SCM details.

    Hydrates projects that were imported as 'Manual' with their original
    SCM configuration. Runs in controlled batches to prevent controller overload.
    """
    if input_dir is None:
        input_dir = Path(ctx.config.paths.transform_dir)
    else:
        input_dir = Path(input_dir)

    # Use config values if not specified via CLI
    if batch_size is None:
        batch_size = ctx.config.performance.project_patch_batch_size
    if interval is None:
        interval = ctx.config.performance.project_patch_batch_interval

    async def run():
        await patch_project_scm_details(ctx, input_dir, batch_size, interval)

    try:
        asyncio.run(run())
    except RuntimeError:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run())
