"""Metadata management commands.

This module provides commands for generating and validating metadata.json files
for export directories.
"""

import json
from datetime import datetime
from pathlib import Path

import click

from aap_migration.cli.decorators import handle_errors
from aap_migration.cli.utils import echo_error, echo_info, echo_success, echo_warning, format_count
from aap_migration.utils.logging import get_logger

logger = get_logger(__name__)


@click.group(name="metadata")
def metadata():
    """Manage metadata.json for export directories.

    Commands for generating, validating, and inspecting metadata.json files
    that describe the structure and contents of export directories.
    """
    pass


@metadata.command(name="generate")
@click.option(
    "--input",
    "-i",
    "input_dir",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Export directory path",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Overwrite existing metadata.json",
)
@handle_errors
def generate(input_dir: Path, force: bool) -> None:
    """Generate metadata.json from export directory structure.

    Scans the export directory, counts resources and files, and generates
    a complete metadata.json file in the correct format for import.

    Examples:

        # Generate metadata.json from export directory
        aap-bridge metadata generate --input exports/

        # Force overwrite existing metadata
        aap-bridge metadata generate --input exports/ --force

    """
    input_dir = Path(input_dir)
    metadata_file = input_dir / "metadata.json"

    # Check if metadata already exists
    if metadata_file.exists() and not force:
        if not click.confirm(f"Metadata file {metadata_file} exists. Overwrite?"):
            raise click.exceptions.Exit(0)

    echo_info(f"Scanning export directory: {input_dir}")

    # Scan directory structure
    resource_types = {}
    total_resources = 0

    for resource_dir in sorted(input_dir.iterdir()):
        if not resource_dir.is_dir():
            continue

        resource_type = resource_dir.name
        json_files = list(resource_dir.glob(f"{resource_type}_*.json"))

        if not json_files:
            echo_warning(f"No JSON files found for {resource_type}, skipping")
            continue

        # Count resources across all files
        resource_count = 0
        for json_file in json_files:
            try:
                with open(json_file) as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        resource_count += len(data)
                    else:
                        resource_count += 1
            except Exception as e:
                echo_warning(f"Failed to read {json_file}: {e}")
                continue

        resource_types[resource_type] = {
            "count": resource_count,
            "files": len(json_files),
        }
        total_resources += resource_count

        click.echo(
            f"  {resource_type}: {format_count(resource_count)} resources in {len(json_files)} file(s)"
        )

    if not resource_types:
        echo_error(f"No valid resource directories found in {input_dir}")
        raise click.ClickException("No resources found")

    # Check for existing metadata to extract source/target URLs
    source_url = None
    target_url = None
    if metadata_file.exists():
        try:
            with open(metadata_file) as f:
                old_metadata = json.load(f)
                source_url = old_metadata.get("source_url")
                target_url = old_metadata.get("target_url")
        except Exception:
            pass

    # Prompt for source URL if not found
    if not source_url:
        source_url = click.prompt(
            "Source AAP URL",
            default="https://aap23.example.com/api/v2",
            show_default=True,
        )

    # Build metadata
    metadata = {
        "export_timestamp": datetime.utcnow().isoformat(),
        "source_url": source_url,
        "total_resources": total_resources,
        "records_per_file": 1000,  # Standard default
        "resource_types": resource_types,
    }

    # Add target_url if available
    if target_url:
        metadata["target_url"] = target_url

    # Write metadata file
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)

    click.echo()
    echo_success(f"Generated metadata.json: {metadata_file}")
    echo_info(f"Total resources: {format_count(total_resources)}")
    echo_info(f"Resource types: {len(resource_types)}")


@metadata.command(name="validate")
@click.option(
    "--input",
    "-i",
    "input_dir",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Export directory path",
)
@handle_errors
def validate(input_dir: Path) -> None:
    """Validate metadata.json against export directory.

    Checks that metadata.json accurately describes the export directory
    structure and resource counts.

    Examples:

        # Validate metadata.json
        aap-bridge metadata validate --input exports/

    """
    input_dir = Path(input_dir)
    metadata_file = input_dir / "metadata.json"

    if not metadata_file.exists():
        echo_error(f"Metadata file not found: {metadata_file}")
        raise click.ClickException("Metadata file missing")

    echo_info(f"Validating metadata: {metadata_file}")

    # Load metadata
    try:
        with open(metadata_file) as f:
            metadata = json.load(f)
    except Exception as e:
        echo_error(f"Failed to load metadata: {e}")
        raise click.ClickException(str(e)) from e

    # Check format
    resource_types_data = metadata.get("resource_types")
    if not resource_types_data:
        echo_error("Metadata missing 'resource_types' field")
        raise click.ClickException("Invalid metadata format")

    # Check if old format (list)
    if isinstance(resource_types_data, list):
        echo_warning("Metadata is in OLD format (list of resource types)")
        echo_info("Run 'aap-bridge metadata generate --force' to update")
        raise click.ClickException("Metadata needs regeneration")

    # Validate each resource type
    errors = []
    warnings = []

    for resource_type, stats in resource_types_data.items():
        resource_dir = input_dir / resource_type

        # Check directory exists
        if not resource_dir.exists():
            errors.append(f"{resource_type}: directory not found")
            continue

        # Count actual files
        json_files = list(resource_dir.glob(f"{resource_type}_*.json"))
        actual_file_count = len(json_files)
        expected_file_count = stats.get("files", 0)

        if actual_file_count != expected_file_count:
            warnings.append(
                f"{resource_type}: file count mismatch "
                f"(expected: {expected_file_count}, actual: {actual_file_count})"
            )

        # Count actual resources
        actual_resource_count = 0
        for json_file in json_files:
            try:
                with open(json_file) as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        actual_resource_count += len(data)
                    else:
                        actual_resource_count += 1
            except Exception as e:
                errors.append(f"{resource_type}/{json_file.name}: failed to read - {e}")

        expected_resource_count = stats.get("count", 0)
        if actual_resource_count != expected_resource_count:
            warnings.append(
                f"{resource_type}: resource count mismatch "
                f"(expected: {expected_resource_count}, actual: {actual_resource_count})"
            )

    # Report results
    click.echo()
    if errors:
        echo_error(f"Found {len(errors)} error(s):")
        for error in errors:
            click.echo(f"  ✗ {error}")

    if warnings:
        echo_warning(f"Found {len(warnings)} warning(s):")
        for warning in warnings:
            click.echo(f"  ⚠ {warning}")

    if not errors and not warnings:
        echo_success("Metadata is valid!")
        click.echo(f"  ✓ {len(resource_types_data)} resource types")
        click.echo(f"  ✓ {metadata.get('total_resources', 0):,} total resources")
    elif errors:
        raise click.ClickException("Metadata validation failed")
    else:
        echo_warning("Metadata has warnings but is usable")


@metadata.command(name="show")
@click.option(
    "--input",
    "-i",
    "input_dir",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Export directory path",
)
@handle_errors
def show(input_dir: Path) -> None:
    """Display metadata.json contents.

    Shows the contents of metadata.json in a readable format.

    Examples:

        # Show metadata contents
        aap-bridge metadata show --input exports/

    """
    input_dir = Path(input_dir)
    metadata_file = input_dir / "metadata.json"

    if not metadata_file.exists():
        echo_error(f"Metadata file not found: {metadata_file}")
        raise click.ClickException("Metadata file missing")

    # Load and display metadata
    try:
        with open(metadata_file) as f:
            metadata = json.load(f)
    except Exception as e:
        echo_error(f"Failed to load metadata: {e}")
        raise click.ClickException(str(e)) from e

    echo_info("Metadata Contents:")
    click.echo()
    click.echo(f"  Export Timestamp: {metadata.get('export_timestamp', 'N/A')}")
    click.echo(f"  Source URL: {metadata.get('source_url', 'N/A')}")
    if "target_url" in metadata:
        click.echo(f"  Target URL: {metadata.get('target_url')}")
    click.echo(f"  Total Resources: {format_count(metadata.get('total_resources', 0))}")
    click.echo(f"  Records Per File: {metadata.get('records_per_file', 'N/A')}")

    click.echo()
    echo_info("Resource Types:")

    resource_types_data = metadata.get("resource_types", {})
    if isinstance(resource_types_data, list):
        click.echo("  Format: LIST (old format)")
        for rtype in resource_types_data:
            click.echo(f"    - {rtype}")
    else:
        click.echo("  Format: DICT (current format)")
        for rtype, stats in resource_types_data.items():
            count = stats.get("count", 0) if isinstance(stats, dict) else 0
            files = stats.get("files", 0) if isinstance(stats, dict) else 0
            click.echo(f"    {rtype}: {format_count(count)} resources in {files} file(s)")
