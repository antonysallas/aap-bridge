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
def version_expected(request: pytest.FixtureRequest) -> tuple[str, Path]:
    fixture_dir = Path(f"tests/fixtures/versions/aap_{request.param}/expected")
    if not fixture_dir.exists():
        pytest.skip(f"No expected fixtures for AAP {request.param}")
    return str(request.param), fixture_dir


@pytest.mark.parametrize("resource_type", RESOURCE_FAMILIES)
def test_transformed_output_is_importable(
    version_expected: tuple[str, Path], resource_type: str
) -> None:
    """Transformed output from each version conforms to import contract."""
    version, expected_dir = version_expected
    files = list(expected_dir.glob(f"{resource_type}_*.json"))
    if not files:
        pytest.skip(f"No expected {resource_type} fixture for AAP {version}")

    for f in files:
        records = json.loads(f.read_text())
        assert isinstance(records, list)
        for record in records:
            # Import contract: each record must have 'name' or 'id' for
            # the importer to create/match on the target
            assert "name" in record or "id" in record, (
                f"Record in {f.name} missing both 'name' and 'id' — "
                f"importer cannot create or match on target"
            )


def test_import_metadata_has_version_provenance(
    version_expected: tuple[str, Path],
) -> None:
    """Import metadata (when generated) records version lineage."""
    version, expected_dir = version_expected
    # The import_metadata.json is generated at runtime, but the fixture
    # should include a reference import_metadata to validate schema
    meta_file = expected_dir.parent / "import_metadata.json"
    if not meta_file.exists():
        pytest.skip(f"No import_metadata fixture for AAP {version}")

    metadata = json.loads(meta_file.read_text())
    assert "source_version" in metadata
    assert "target_version" in metadata
    assert "source_run_fingerprint" in metadata
