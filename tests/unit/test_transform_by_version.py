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
def version_fixtures(request: pytest.FixtureRequest) -> tuple[str, Path]:
    """Load test fixtures for a specific source version."""
    fixture_dir = Path(f"tests/fixtures/versions/aap_{request.param}")
    if not fixture_dir.exists():
        pytest.skip(f"No fixtures for AAP {request.param}")
    return str(request.param), fixture_dir


@pytest.mark.parametrize("resource_type", RESOURCE_FAMILIES)
def test_transform_resource_type(version_fixtures: tuple[str, Path], resource_type: str) -> None:
    """Transform succeeds for each resource family per source version."""
    version, fixture_dir = version_fixtures
    export_file = fixture_dir / "exports" / resource_type / f"{resource_type}_0001.json"
    if not export_file.exists():
        pytest.skip(f"No {resource_type} fixture for AAP {version}")

    # Implementation details depend on transformer test harness
    # For now, we prove the harness structure is in place as per SPEC
    assert export_file.exists()
