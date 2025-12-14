"""Data models for schema comparison results."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ChangeType(Enum):
    """Types of schema changes."""

    FIELD_ADDED = "field_added"
    FIELD_REMOVED = "field_removed"
    FIELD_RENAMED = "field_renamed"
    TYPE_CHANGED = "type_changed"
    REQUIRED_CHANGED = "required_changed"
    VALIDATION_CHANGED = "validation_changed"
    DEFAULT_CHANGED = "default_changed"


class Severity(Enum):
    """Severity levels for schema changes."""

    INFO = "info"  # Informational, no action needed
    LOW = "low"  # Minor, can be auto-handled
    MEDIUM = "medium"  # Needs attention, might need manual fix
    HIGH = "high"  # Breaking change, requires manual intervention
    CRITICAL = "critical"  # Blocks migration, must be fixed


@dataclass
class FieldDiff:
    """Difference between source and target field definitions."""

    field_name: str
    change_type: ChangeType
    severity: Severity
    source_value: Any = None
    target_value: Any = None
    description: str = ""
    recommendation: str = ""

    @property
    def is_breaking(self) -> bool:
        """Check if this is a breaking change."""
        return self.severity in (Severity.HIGH, Severity.CRITICAL)


@dataclass
class FieldRename:
    """Detected field rename between source and target."""

    old_name: str
    new_name: str
    confidence: str  # "high", "medium", "low"
    reason: str
    auto_fixable: bool
    manual_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "new_name": self.new_name,
            "confidence": self.confidence,
            "reason": self.reason,
            "auto_fixable": self.auto_fixable,
            "manual_action": self.manual_action if self.manual_action else None,
        }


@dataclass
class SchemaChange:
    """High-level schema change for a resource type."""

    resource_type: str
    change_type: ChangeType
    severity: Severity
    description: str
    fields_affected: list[str] = field(default_factory=list)
    recommendation: str = ""

    @property
    def is_breaking(self) -> bool:
        """Check if this is a breaking change."""
        return self.severity in (Severity.HIGH, Severity.CRITICAL)


@dataclass
class ComparisonResult:
    """Result of comparing source and target schemas for a resource type."""

    resource_type: str
    source_schema: dict[str, Any]
    target_schema: dict[str, Any]
    field_diffs: list[FieldDiff] = field(default_factory=list)
    schema_changes: list[SchemaChange] = field(default_factory=list)
    field_renames: dict[str, FieldRename] = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        """Check if there are any changes."""
        return bool(self.field_diffs or self.schema_changes)

    @property
    def has_breaking_changes(self) -> bool:
        """Check if there are any breaking changes."""
        return any(diff.is_breaking for diff in self.field_diffs) or any(
            change.is_breaking for change in self.schema_changes
        )

    @property
    def deprecated_fields(self) -> list[str]:
        """Get list of fields deprecated in target."""
        return [
            diff.field_name
            for diff in self.field_diffs
            if diff.change_type == ChangeType.FIELD_REMOVED
        ]

    @property
    def new_required_fields(self) -> dict[str, Any]:
        """Get dict of new required fields with their defaults."""
        result = {}
        for diff in self.field_diffs:
            if (
                diff.change_type == ChangeType.FIELD_ADDED
                and diff.target_value
                and diff.target_value.get("required")
            ):
                # Try to get default value
                default = diff.target_value.get("default")
                result[diff.field_name] = default
        return result

    @property
    def type_changes(self) -> dict[str, tuple[str, str]]:
        """Get dict of fields with type changes (old_type, new_type)."""
        result = {}
        for diff in self.field_diffs:
            if diff.change_type == ChangeType.TYPE_CHANGED:
                result[diff.field_name] = (diff.source_value, diff.target_value)
        return result

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dictionary for schema_comparison.json.

        Returns:
            Dict suitable for saving to schema_comparison.json
        """
        # Determine severity
        max_severity = Severity.INFO
        for diff in self.field_diffs:
            if diff.severity.value > max_severity.value:
                max_severity = diff.severity
        for change in self.schema_changes:
            if change.severity.value > max_severity.value:
                max_severity = change.severity

        # Determine if auto-fixable
        auto_fixable = not self.has_breaking_changes or all(
            rename.auto_fixable for rename in self.field_renames.values()
        )

        validation_changes = [
            change.description
            for change in self.schema_changes
            if change.change_type == ChangeType.VALIDATION_CHANGED
        ]

        return {
            "deprecated_fields": self.deprecated_fields,
            "new_fields": [
                diff.field_name
                for diff in self.field_diffs
                if diff.change_type == ChangeType.FIELD_ADDED
            ],
            "new_required_fields": self.new_required_fields,
            "type_changes": {
                field: {"from": old, "to": new} for field, (old, new) in self.type_changes.items()
            },
            "field_renames": {
                old_name: rename.to_dict() for old_name, rename in self.field_renames.items()
            },
            "validation_changes": validation_changes,
            "severity": max_severity.name,
            "auto_fixable": auto_fixable,
        }

    def get_summary(self) -> dict[str, Any]:
        """Get summary of comparison results."""
        return {
            "resource_type": self.resource_type,
            "has_changes": self.has_changes,
            "has_breaking_changes": self.has_breaking_changes,
            "total_diffs": len(self.field_diffs),
            "deprecated_fields_count": len(self.deprecated_fields),
            "new_required_fields_count": len(self.new_required_fields),
            "type_changes_count": len(self.type_changes),
            "field_renames_count": len(self.field_renames),
            "critical_changes": sum(
                1 for diff in self.field_diffs if diff.severity == Severity.CRITICAL
            ),
            "high_severity_changes": sum(
                1 for diff in self.field_diffs if diff.severity == Severity.HIGH
            ),
        }
