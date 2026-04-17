import json
from pathlib import Path

import pytest

SOURCE_VERSIONS = ["2.3", "2.4", "2.5"]
RESOURCE_FAMILIES = [
    "organizations",
    "inventories",
    "hosts",
    "credentials",
    "credential_types",
    "projects",
    "job_templates",
    "workflow_job_templates",
    "schedules",
]


@pytest.fixture(params=SOURCE_VERSIONS)
def version_exports(request: pytest.FixtureRequest) -> tuple[str, Path]:
    fixture_dir = Path(f"tests/fixtures/versions/aap_{request.param}/exports")
    if not fixture_dir.exists():
        pytest.skip(f"No export fixtures for AAP {request.param}")
    return str(request.param), fixture_dir


def test_export_metadata_has_version_provenance(version_exports: tuple[str, Path]) -> None:
    """Export metadata records source and target version."""
    version, export_dir = version_exports
    metadata_file = export_dir / "metadata.json"
    if not metadata_file.exists():
        pytest.skip(f"No metadata.json for AAP {version}")

    metadata = json.loads(metadata_file.read_text())
    assert "source_version" in metadata, "Missing source_version in export metadata"
    assert "target_version" in metadata, "Missing target_version in export metadata"
    assert metadata["source_version"].startswith(version)


@pytest.mark.parametrize("resource_type", RESOURCE_FAMILIES)
def test_export_produces_valid_records(
    version_exports: tuple[str, Path], resource_type: str
) -> None:
    """Exported records for each version have the expected structure."""
    version, export_dir = version_exports
    type_dir = export_dir / resource_type
    if not type_dir.exists():
        pytest.skip(f"No {resource_type} export fixture for AAP {version}")

    files = list(type_dir.glob("*.json"))
    assert len(files) > 0, f"Empty export directory for {resource_type} on AAP {version}"
    for f in files:
        records = json.loads(f.read_text())
        assert isinstance(records, list), f"{f.name} should contain a list of records"
        for record in records:
            assert "id" in record, f"Record in {f.name} missing 'id' field"
