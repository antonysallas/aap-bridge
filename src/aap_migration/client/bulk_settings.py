"""Target AAP bulk-operation settings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aap_migration.utils.logging import get_logger

if TYPE_CHECKING:
    from aap_migration.client.base_client import BaseAPIClient

logger = get_logger(__name__)

# Hard ceiling for a single bulk/host_create request (API design limit).
HOST_BULK_API_MAX = 200

# Stock AWX/AAP default for the controller setting BULK_HOST_MAX_CREATE.
BULK_HOST_MAX_CREATE_DEFAULT = 100


async def fetch_bulk_host_max_create(client: BaseAPIClient) -> int | None:
    """Return the target's BULK_HOST_MAX_CREATE setting.

    Returns None if the setting cannot be read (caller should fall back to config only).
    """
    try:
        response = await client.get("settings/bulk/")
        value = response.get("BULK_HOST_MAX_CREATE")
        if value is None:
            logger.warning(
                "bulk_host_max_create_missing",
                message="BULK_HOST_MAX_CREATE not present in settings/bulk/ response",
            )
            return BULK_HOST_MAX_CREATE_DEFAULT
        return int(value)
    except Exception as e:
        logger.warning("bulk_host_max_create_fetch_failed", error=str(e))
        return None


def effective_host_batch_size(
    configured: int,
    *,
    target_bulk_max: int | None = None,
) -> int:
    """Compute a host import batch size safe for the target controller."""
    size = min(configured, HOST_BULK_API_MAX)
    if target_bulk_max is not None:
        size = min(size, target_bulk_max)
    return max(1, size)
