"""Payload validation module for AAP import.

This module validates transformed payloads against target AAP 2.6 schema
before attempting import to catch validation errors early.
"""

import json
from pathlib import Path
from typing import Any

from aap_migration.utils.logging import get_logger

logger = get_logger(__name__)


class PayloadValidator:
    """Validates resource payloads against target schema."""

    def __init__(self, target_schema_file: Path | str | None = None):
        """Initialize payload validator.

        Args:
            target_schema_file: Path to target_schema.json from prep phase
        """
        self.target_schema: dict[str, Any] | None = None

        # Load target schema if provided
        if target_schema_file:
            schema_path = Path(target_schema_file)
            if schema_path.exists():
                with open(schema_path) as f:
                    data = json.load(f)
                    self.target_schema = data.get("schemas", {})
                logger.info(
                    "target_schema_loaded",
                    file=str(schema_path),
                    schema_count=len(self.target_schema) if self.target_schema else 0,
                )
            else:
                logger.warning(
                    "target_schema_file_not_found",
                    file=str(schema_path),
                    validation="Will skip schema-based validation",
                )

    def validate_payload(
        self,
        resource_type: str,
        payload: dict[str, Any],
    ) -> tuple[bool, list[str]]:
        """Validate a resource payload against target schema.

        Args:
            resource_type: Type of resource (e.g., "organizations")
            payload: Resource payload to validate

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        # If no schema loaded, skip validation
        if not self.target_schema:
            logger.debug(
                "validation_skipped_no_schema",
                resource_type=resource_type,
            )
            return True, []

        # Get schema for this resource type
        resource_schema = self.target_schema.get(resource_type)
        if not resource_schema:
            logger.debug(
                "validation_skipped_no_resource_schema",
                resource_type=resource_type,
            )
            return True, []

        fields_schema = resource_schema.get("fields", {})

        # Check required fields
        for field_name, field_spec in fields_schema.items():
            if field_spec.get("required") and not field_spec.get("read_only"):
                if field_name not in payload:
                    errors.append(f"Missing required field: {field_name}")

        # Check for unknown fields (fields in payload but not in schema)
        # This is informational, not an error
        for field_name in payload.keys():
            if field_name not in fields_schema and field_name not in ["_source_id"]:
                logger.debug(
                    "unknown_field_in_payload",
                    resource_type=resource_type,
                    field=field_name,
                    info="Field exists in payload but not in target schema",
                )

        # Check field types (basic validation)
        for field_name, value in payload.items():
            if field_name in fields_schema:
                field_spec = fields_schema[field_name]
                expected_type = field_spec.get("type")

                # Skip type checking for None values
                if value is None:
                    continue

                # Basic type validation
                if expected_type == "string" and not isinstance(value, str):
                    if not isinstance(value, (int, float, bool)):  # Allow type coercion
                        errors.append(
                            f"Field '{field_name}' expected string, got {type(value).__name__}"
                        )
                elif expected_type == "integer" and not isinstance(value, int):
                    if not isinstance(value, bool):  # bool is subclass of int
                        errors.append(
                            f"Field '{field_name}' expected integer, got {type(value).__name__}"
                        )
                elif expected_type == "boolean" and not isinstance(value, bool):
                    errors.append(
                        f"Field '{field_name}' expected boolean, got {type(value).__name__}"
                    )

        is_valid = len(errors) == 0

        if not is_valid:
            logger.warning(
                "payload_validation_failed",
                resource_type=resource_type,
                resource_name=payload.get("name"),
                error_count=len(errors),
                errors=errors,
            )

        return is_valid, errors

    def validate_batch(
        self,
        resource_type: str,
        payloads: list[dict[str, Any]],
        sample_size: int | None = None,
    ) -> dict[str, Any]:
        """Validate a batch of payloads, optionally sampling.

        Args:
            resource_type: Type of resource
            payloads: List of resource payloads
            sample_size: If provided, only validate this many resources

        Returns:
            Dictionary with validation results:
            - valid_count: Number of valid payloads
            - invalid_count: Number of invalid payloads
            - total_checked: Total payloads validated
            - errors: List of validation errors
        """
        # Sample if requested
        payloads_to_check = payloads
        if sample_size and len(payloads) > sample_size:
            import random

            payloads_to_check = random.sample(payloads, sample_size)
            logger.info(
                "validation_sampling",
                resource_type=resource_type,
                total=len(payloads),
                sample_size=sample_size,
            )

        valid_count = 0
        invalid_count = 0
        all_errors = []

        for payload in payloads_to_check:
            is_valid, errors = self.validate_payload(resource_type, payload)
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                all_errors.append(
                    {
                        "resource": payload.get("name", payload.get("_source_id", "unknown")),
                        "errors": errors,
                    }
                )

        result = {
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "total_checked": len(payloads_to_check),
            "total_resources": len(payloads),
            "sampled": sample_size is not None and len(payloads) > sample_size,
            "errors": all_errors,
        }

        logger.info(
            "batch_validation_complete",
            resource_type=resource_type,
            valid=valid_count,
            invalid=invalid_count,
            total=len(payloads_to_check),
        )

        return result


def create_validation_report(
    validation_results: dict[str, dict[str, Any]],
    output_file: Path,
) -> None:
    """Create a validation report JSON file.

    Args:
        validation_results: Dict of resource_type -> validation results
        output_file: Path to write report
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(validation_results, f, indent=2)

    logger.info(
        "validation_report_created",
        file=str(output_file),
        resource_types=len(validation_results),
    )
