"""Prep command for endpoint discovery and schema generation.

This module provides the `aap-bridge prep` command that discovers
all available endpoints from source and target AAP instances and
generates schemas for transformation.
"""

import asyncio
import logging
from pathlib import Path

import click
from rich.logging import RichHandler

from aap_migration.cli.context import MigrationContext
from aap_migration.cli.decorators import (
    handle_errors,
    pass_context,
    requires_config,
)
from aap_migration.cli.utils import (
    echo_success,
    step_progress,
)
from aap_migration.prep import (
    compare_schemas,
    discover_endpoints,
    generate_schema,
    save_comparison,
    save_endpoints,
    save_schema,
)
from aap_migration.utils.logging import get_logger

logger = get_logger(__name__)


@click.command(name="prep")
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=Path("schemas"),
    help="Output directory for schema files (default: schemas/)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Force re-discovery even if schemas exist",
)
@pass_context
@requires_config
@handle_errors
def prep(ctx: MigrationContext, output_dir: Path, force: bool) -> None:
    """Discover endpoints and generate schemas from AAP instances.

    This command:
    1. Connects to source AAP 2.3 and target AAP 2.6
    2. Discovers all available endpoints
    3. Generates schemas for each endpoint
    4. Compares schemas and generates transformation rules

    Outputs:
        schemas/source_endpoints.json - Source endpoints
        schemas/target_endpoints.json - Target endpoints
        schemas/source_schema.json - Source schema
        schemas/target_schema.json - Target schema
        schemas/schema_comparison.json - Transformation rules

    Examples:

        \\b
        # Discover and generate schemas
        aap-bridge prep --config config.yaml

        \\b
        # Force re-discovery
        aap-bridge prep --config config.yaml --force

        \\b
        # Custom output directory
        aap-bridge prep --config config.yaml --output-dir my_schemas/
    """
    # Force console logging to WARNING to hide verbose API logs during prep
    # unless user explicitly requested DEBUG
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if isinstance(handler, RichHandler):
            # Only override if current level is INFO (20) or NOTSET (0)
            # Leave DEBUG (10) alone so explicit debug works
            if handler.level == logging.INFO or handler.level == logging.NOTSET:
                handler.setLevel(logging.WARNING)

    # Check if schemas already exist
    source_endpoints_file = output_dir / "source_endpoints.json"
    target_endpoints_file = output_dir / "target_endpoints.json"

    if not force and source_endpoints_file.exists() and target_endpoints_file.exists():
        if not click.confirm("Schema files already exist. Overwrite?", default=False):
            click.echo("Cancelled.")
            return

    # Extract hostnames for cleaner output
    source_host = ctx.config.source.url.split("//")[-1].split("/")[0]
    target_host = ctx.config.target.url.split("//")[-1].split("/")[0]

    async def run_prep() -> None:
        """Async function to run prep workflow."""
        try:
            # ============================================
            # 1. TEST CONNECTIVITY (combined into one step)
            # ============================================
            with step_progress(f"Connecting to {source_host} and {target_host}"):
                await ctx.source_client.get("ping/")
                await ctx.target_client.get("ping/")

            # ============================================
            # 2. DISCOVER ENDPOINTS (combined output)
            # ============================================
            common_ignored = ctx.config.ignored_endpoints.get("common", [])
            source_ignored = common_ignored + ctx.config.ignored_endpoints.get("source", [])
            target_ignored = common_ignored + ctx.config.ignored_endpoints.get("target", [])

            with step_progress("Discovering endpoints"):
                source_endpoints = await discover_endpoints(
                    ctx.source_client,
                    api_version="2.3.0",
                    ignored_endpoints=source_ignored,
                )
                target_endpoints = await discover_endpoints(
                    ctx.target_client,
                    api_version="2.6.0",
                    ignored_endpoints=target_ignored,
                )
            # Log details to file only
            logger.info(
                "endpoints_discovered",
                source_count=len(source_endpoints["endpoints"]),
                target_count=len(target_endpoints["endpoints"]),
            )

            save_endpoints(source_endpoints, source_endpoints_file)
            save_endpoints(target_endpoints, target_endpoints_file)

            # ============================================
            # 3. GENERATE SCHEMAS
            # ============================================
            with step_progress("Generating schemas"):
                source_schema = await generate_schema(ctx.source_client, source_endpoints)
                target_schema = await generate_schema(ctx.target_client, target_endpoints)
            # Log details to file only
            logger.info(
                "schemas_generated",
                source_count=len(source_schema["schemas"]),
                target_count=len(target_schema["schemas"]),
            )

            source_schema_file = output_dir / "source_schema.json"
            target_schema_file = output_dir / "target_schema.json"
            save_schema(source_schema, source_schema_file)
            save_schema(target_schema, target_schema_file)

            # ============================================
            # 4. COMPARE SCHEMAS
            # ============================================
            with step_progress("Comparing schemas"):
                comparison = compare_schemas(source_schema, target_schema)

            # Count changes and log to file
            total_removed = 0
            total_added = 0
            for transformation in comparison["transformations"].values():
                total_removed += len(transformation.get("fields_removed", []))
                total_added += len(transformation.get("fields_added", []))

            # Check for resources using source schema fallback
            fallback_resources = [
                rtype
                for rtype, data in comparison["transformations"].items()
                if data.get("requires_manual_verification")
            ]

            # Log all details to file only
            logger.info(
                "schemas_compared",
                fields_added=total_added,
                fields_removed=total_removed,
                fallback_resources=fallback_resources if fallback_resources else None,
            )

            comparison_file = output_dir / "schema_comparison.json"
            save_comparison(comparison, comparison_file)

            # ============================================
            # SUMMARY (compact)
            # ============================================
            click.echo()
            echo_success(f"Prep complete! Output: {output_dir}/")

        except Exception as e:
            logger.error(
                "prep_failed",
                error=str(e),
                exc_info=True,
            )
            raise

    # Run async workflow
    try:
        asyncio.run(run_prep())
    except RuntimeError:
        # Already in event loop
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_prep())
