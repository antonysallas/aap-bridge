"""Regression: Phase 2 patching must report patched counts (#116)."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aap_migration.cli.commands.patch_projects import _empty_patch_stats, patch_project_scm_details

_SYNC_COMPLETE = (1, 0, [], [])


def test_empty_patch_stats_shape() -> None:
    assert _empty_patch_stats() == {
        "imported": 0,
        "skipped": 0,
        "failed": 0,
        "total": 0,
    }


@pytest.mark.asyncio
async def test_patch_returns_zeros_when_no_projects_dir(tmp_path: Path) -> None:
    ctx = MagicMock()
    stats = await patch_project_scm_details(ctx, tmp_path, batch_size=1, interval=0)
    assert stats == _empty_patch_stats()


@pytest.mark.asyncio
async def test_patch_returns_patched_count(tmp_path: Path) -> None:
    """Successful patches must populate run_stats-compatible imported count."""
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()
    (projects_dir / "projects_001.json").write_text(
        """[
          {
            "name": "demo",
            "_source_id": 10,
            "_deferred_scm_details": {
              "scm_type": "git",
              "scm_url": "https://example.com/repo.git",
              "scm_branch": "main"
            }
          }
        ]"""
    )

    ctx = _make_patch_test_ctx()
    ctx.migration_state.get_mapped_id = MagicMock(return_value=99)

    with (
        patch(
            "aap_migration.cli.commands.patch_projects.wait_for_project_sync",
            new_callable=AsyncMock,
            return_value=_SYNC_COMPLETE,
        ),
        patch("aap_migration.cli.commands.patch_projects.asyncio.sleep", new_callable=AsyncMock),
        patch("aap_migration.cli.commands.patch_projects.MigrationProgressDisplay"),
    ):
        stats = await patch_project_scm_details(ctx, tmp_path, batch_size=1, interval=0)

    assert stats["imported"] == 1
    assert stats["failed"] == 0
    assert stats["skipped"] == 0
    assert stats["total"] == 1
    ctx.target_client.patch.assert_awaited_once()


def _make_patch_test_project_file(tmp_path: Path) -> None:
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()
    (projects_dir / "projects_001.json").write_text(
        """[
          {
            "name": "demo",
            "_source_id": 10,
            "_deferred_scm_details": {
              "scm_type": "git",
              "scm_url": "https://example.com/repo.git",
              "scm_branch": "main"
            }
          }
        ]"""
    )


def _make_patch_test_ctx(*, mapped_id: int | None = 99) -> MagicMock:
    ctx = MagicMock()
    ctx.migration_state.get_mapped_id = MagicMock(return_value=mapped_id)
    ctx.target_client = AsyncMock()
    ctx.target_client.patch = AsyncMock(return_value={})
    ctx.target_client.get = AsyncMock(return_value={"scm_type": "", "status": "never updated"})
    ctx.config.performance.project_sync_max_retries = 0
    ctx.config.performance.project_sync_fail_on_sync_failure = False
    ctx.config.performance.project_sync_poll_interval = 0
    ctx.config.performance.project_sync_timeout = 1
    return ctx


@pytest.mark.asyncio
async def test_patch_returns_failed_count_on_patch_error(tmp_path: Path) -> None:
    """PATCH exceptions must populate stats['failed']."""
    _make_patch_test_project_file(tmp_path)
    ctx = _make_patch_test_ctx()
    ctx.target_client.patch = AsyncMock(side_effect=RuntimeError("API error"))

    with (
        patch(
            "aap_migration.cli.commands.patch_projects.wait_for_project_sync",
            new_callable=AsyncMock,
            return_value=_SYNC_COMPLETE,
        ),
        patch("aap_migration.cli.commands.patch_projects.asyncio.sleep", new_callable=AsyncMock),
        patch("aap_migration.cli.commands.patch_projects.MigrationProgressDisplay"),
    ):
        stats = await patch_project_scm_details(ctx, tmp_path, batch_size=1, interval=0)

    assert stats["imported"] == 0
    assert stats["failed"] == 1
    assert stats["skipped"] == 0
    assert stats["total"] == 1
    ctx.target_client.patch.assert_awaited_once()


@pytest.mark.asyncio
async def test_patch_returns_skipped_count_when_all_already_configured(tmp_path: Path) -> None:
    """Re-run must report already-configured projects as skipped."""
    _make_patch_test_project_file(tmp_path)
    ctx = _make_patch_test_ctx()

    with (
        patch(
            "aap_migration.cli.commands.patch_projects.classify_project_patch_action",
            new_callable=AsyncMock,
            return_value="skip",
        ),
        patch("aap_migration.cli.commands.patch_projects.MigrationProgressDisplay"),
    ):
        stats = await patch_project_scm_details(ctx, tmp_path, batch_size=1, interval=0)

    assert stats["imported"] == 0
    assert stats["failed"] == 0
    assert stats["skipped"] == 1
    assert stats["total"] == 1
    ctx.target_client.patch.assert_not_awaited()


@pytest.mark.asyncio
async def test_patch_reports_skipped_in_progress_when_all_already_configured(
    tmp_path: Path,
) -> None:
    """Import progress must show patching phase even when all projects are skipped."""
    _make_patch_test_project_file(tmp_path)
    ctx = _make_patch_test_ctx()
    progress = MagicMock()

    with patch(
        "aap_migration.cli.commands.patch_projects.classify_project_patch_action",
        new_callable=AsyncMock,
        return_value="skip",
    ):
        stats = await patch_project_scm_details(
            ctx, tmp_path, batch_size=1, interval=0, progress_display=progress
        )

    assert stats["skipped"] == 1
    progress.start_phase.assert_called_once_with("patching", "Patching Projects", 1)
    progress.update_phase.assert_called_once_with("patching", 0, 0, 1)
    progress.complete_phase.assert_called_once_with("patching")


@pytest.mark.asyncio
async def test_patch_returns_skipped_count_when_no_mapping(tmp_path: Path) -> None:
    """Projects without a target ID mapping must be counted as skipped."""
    _make_patch_test_project_file(tmp_path)
    ctx = _make_patch_test_ctx(mapped_id=None)

    with (
        patch(
            "aap_migration.cli.commands.patch_projects.wait_for_project_sync",
            new_callable=AsyncMock,
            return_value=_SYNC_COMPLETE,
        ),
        patch("aap_migration.cli.commands.patch_projects.asyncio.sleep", new_callable=AsyncMock),
        patch("aap_migration.cli.commands.patch_projects.MigrationProgressDisplay"),
    ):
        stats = await patch_project_scm_details(ctx, tmp_path, batch_size=1, interval=0)

    assert stats["imported"] == 0
    assert stats["failed"] == 0
    assert stats["skipped"] == 1
    assert stats["total"] == 1
    ctx.target_client.patch.assert_not_awaited()
