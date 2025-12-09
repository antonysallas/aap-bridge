"""Endpoint discovery module for AAP instances.

This module discovers all available API endpoints from AAP 2.3 (source)
and AAP 2.6 (target) instances by fetching the API root.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aap_migration.client.aap_source_client import AAPSourceClient
from aap_migration.client.aap_target_client import AAPTargetClient
from aap_migration.utils.logging import get_logger

logger = get_logger(__name__)


async def discover_endpoints(
    client: AAPSourceClient | AAPTargetClient,
    api_version: str,
    ignored_endpoints: list[str] | None = None,
) -> dict[str, Any]:
    """Discover all available endpoints from AAP API root.

    Args:
        client: AAP client (source or target)
        api_version: API version string (e.g., "2.3.0" or "2.6.0")
        ignored_endpoints: List of endpoint paths to ignore (e.g., ["mesh_visualizer/", "metrics/"])

    Returns:
        Dictionary containing:
        - api_version: AAP version
        - discovered_at: ISO timestamp
        - base_url: Base URL of the API
        - endpoints: Dict of endpoint_name -> endpoint_details

    Raises:
        HTTPError: If API is unreachable or returns error
    """
    ignored_endpoints = ignored_endpoints or []

    logger.info(
        "discovering_endpoints",
        api_version=api_version,
        base_url=client.base_url,
        ignored_count=len(ignored_endpoints),
    )

    try:
        # Fetch API root - this returns all available endpoints
        response = await client.get("")

        # Extract endpoint listing from response
        # The API root returns a dict like:
        # {
        #   "organizations": "/api/v2/organizations/",
        #   "users": "/api/v2/users/",
        #   ...
        # }
        endpoints_data = {}
        endpoint_count = 0
        ignored_count = 0

        for endpoint_name, endpoint_url in response.items():
            # Skip metadata fields
            if endpoint_name in ["description", "current_version", "available_versions"]:
                continue

            # Extract only the relative endpoint path
            # AAP API returns absolute paths like "/api/v2/ping/" or "/api/controller/v2/organizations/"
            # but base_url already contains the API prefix (e.g., "https://aap.example.com/api/v2")
            # We only want the relative path (e.g., "ping/" or "organizations/")
            # Split by '/' and take the last non-empty part
            endpoint_path = endpoint_url.rstrip("/").split("/")[-1] + "/"

            # Skip ignored endpoints
            if endpoint_path in ignored_endpoints:
                logger.debug(
                    "endpoint_ignored",
                    endpoint_name=endpoint_name,
                    endpoint_path=endpoint_path,
                )
                ignored_count += 1
                continue

            # Store endpoint information
            endpoints_data[endpoint_name] = {
                "url": endpoint_path,  # Just "ping/" or "organizations/", not "/api/v2/ping/"
                "methods": None,  # Will be populated by schema generator
                "supports_filtering": None,
                "supports_pagination": None,
            }
            endpoint_count += 1

        logger.info(
            "endpoints_discovered",
            api_version=api_version,
            endpoint_count=endpoint_count,
            ignored_count=ignored_count,
        )

        # Build result
        result = {
            "api_version": api_version,
            "discovered_at": datetime.now(UTC).isoformat(),
            "base_url": str(client.base_url),
            "endpoints": endpoints_data,
        }

        return result

    except Exception as e:
        logger.error(
            "endpoint_discovery_failed",
            api_version=api_version,
            error=str(e),
            exc_info=True,
        )
        raise


def save_endpoints(
    endpoints_data: dict[str, Any],
    output_file: Path,
) -> None:
    """Save discovered endpoints to JSON file.

    Args:
        endpoints_data: Endpoints data from discover_endpoints()
        output_file: Path to output JSON file
    """
    logger.info(
        "saving_endpoints",
        output_file=str(output_file),
        endpoint_count=len(endpoints_data.get("endpoints", {})),
    )

    # Create parent directory if it doesn't exist
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON file
    with open(output_file, "w") as f:
        json.dump(endpoints_data, f, indent=2)

    logger.info(
        "endpoints_saved",
        output_file=str(output_file),
        file_size=output_file.stat().st_size,
    )


def load_endpoints(endpoints_file: Path) -> dict[str, Any]:
    """Load endpoints from JSON file.

    Args:
        endpoints_file: Path to endpoints JSON file

    Returns:
        Endpoints data

    Raises:
        FileNotFoundError: If file doesn't exist
        JSONDecodeError: If file is not valid JSON
    """
    logger.debug("loading_endpoints", file=str(endpoints_file))

    with open(endpoints_file) as f:
        data = json.load(f)

    logger.debug(
        "endpoints_loaded",
        file=str(endpoints_file),
        endpoint_count=len(data.get("endpoints", {})),
    )

    return data
