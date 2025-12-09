"""Migration report generation for manual intervention tasks.

This module provides comprehensive reporting for migration issues that require
manual intervention, including:
- Failed imports
- Unresolved dependencies
- Encrypted credentials that need manual creation
"""

import csv
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class FailedImport:
    """Record of a failed import attempt."""

    resource_type: str
    source_id: int | str
    name: str
    error_type: str
    error_message: str
    data: dict[str, Any] | None = None


@dataclass
class UnresolvedDependency:
    """Record of an unresolved dependency."""

    resource_type: str
    resource_name: str
    source_id: int | str
    dependency_field: str
    dependency_type: str
    missing_source_id: int | str
    error: str


@dataclass
class CredentialPlaceholder:
    """Record of a credential requiring manual creation.

    This is used for both:
    - Encrypted credentials that need manual values
    - User accounts that need password resets
    """

    resource_type: str
    source_id: int | str
    name: str
    organization: int | str | None = None
    credential_type: int | str | None = None
    encrypted_fields: list[str] = field(default_factory=list)
    action_required: str = ""
    instructions: str = ""
    temp_password: str | None = None  # For user password tracking


@dataclass
class MigrationReport:
    """Complete migration report with all issues requiring attention."""

    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    source_url: str = ""
    target_url: str = ""

    # Success metrics per resource type
    successful_imports: dict[str, int] = field(default_factory=dict)

    # Issues requiring attention
    failed_imports: list[FailedImport] = field(default_factory=list)
    unresolved_dependencies: list[UnresolvedDependency] = field(default_factory=list)
    encrypted_credentials: list[CredentialPlaceholder] = field(default_factory=list)

    # Summary statistics
    total_resources_processed: int = 0
    total_successful: int = 0
    total_failed: int = 0
    total_skipped: int = 0
    requires_manual_action: int = 0

    def calculate_summary(self) -> None:
        """Calculate summary statistics from collected data."""
        self.total_successful = sum(self.successful_imports.values())
        self.total_failed = len(self.failed_imports)
        self.requires_manual_action = len(self.encrypted_credentials) + len(
            self.unresolved_dependencies
        )
        self.total_resources_processed = self.total_successful + self.total_failed

    def to_json(self) -> str:
        """Export report as JSON string."""
        self.calculate_summary()
        return json.dumps(asdict(self), indent=2, default=str)

    def save_json(self, path: Path) -> None:
        """Save report as JSON file.

        Args:
            path: Path to save the JSON report
        """
        path.write_text(self.to_json())

    def to_markdown(self) -> str:
        """Export report as Markdown for human reading."""
        self.calculate_summary()

        lines = [
            "# AAP Migration Report",
            "",
            f"**Generated**: {self.timestamp}",
            f"**Source**: {self.source_url}",
            f"**Target**: {self.target_url}",
            "",
            "---",
            "",
            "## Summary",
            "",
            f"- **Total Processed**: {self.total_resources_processed}",
            f"- **Successful**: {self.total_successful}",
            f"- **Failed**: {self.total_failed}",
            f"- **Requires Manual Action**: {self.requires_manual_action}",
            "",
        ]

        # Success breakdown
        if self.successful_imports:
            lines.extend(
                [
                    "## Successful Imports by Type",
                    "",
                    "| Resource Type | Count |",
                    "|--------------|-------|",
                ]
            )
            for rtype, count in sorted(self.successful_imports.items()):
                lines.append(f"| {rtype} | {count} |")
            lines.append("")

        # Failed imports
        if self.failed_imports:
            lines.extend(
                [
                    "## Failed Imports",
                    "",
                    "These resources failed to import and require investigation:",
                    "",
                    "| Resource Type | Name | Source ID | Error |",
                    "|--------------|------|-----------|-------|",
                ]
            )
            for fail in self.failed_imports:
                error_short = (
                    fail.error_message[:50] + "..."
                    if len(fail.error_message) > 50
                    else fail.error_message
                )
                lines.append(
                    f"| {fail.resource_type} | {fail.name} | {fail.source_id} | {error_short} |"
                )
            lines.append("")

        # Unresolved dependencies
        if self.unresolved_dependencies:
            lines.extend(
                [
                    "## Unresolved Dependencies",
                    "",
                    "These resources have missing dependencies that need to be created first:",
                    "",
                    "| Resource | Name | Missing Dependency | Type | Source ID |",
                    "|----------|------|-------------------|------|-----------|",
                ]
            )
            for dep in self.unresolved_dependencies:
                lines.append(
                    f"| {dep.resource_type} | {dep.resource_name} | "
                    f"{dep.dependency_field} | {dep.dependency_type} | {dep.missing_source_id} |"
                )
            lines.append("")

        # Encrypted credentials (CRITICAL SECTION)
        if self.encrypted_credentials:
            lines.extend(
                [
                    "## Credentials Requiring Manual Creation",
                    "",
                    "These credentials contain encrypted values that cannot be migrated via API.",
                    "You MUST recreate these credentials manually in AAP 2.6.",
                    "",
                ]
            )

            for cred in self.encrypted_credentials:
                lines.extend(
                    [
                        f"### {cred.name}",
                        "",
                        f"- **Source ID**: {cred.source_id}",
                        f"- **Organization ID**: {cred.organization}",
                        f"- **Credential Type ID**: {cred.credential_type}",
                        f"- **Encrypted Fields**: {', '.join(cred.encrypted_fields)}",
                        "",
                        cred.instructions,
                        "",
                        "---",
                        "",
                    ]
                )

        return "\n".join(lines)

    def save_markdown(self, path: Path) -> None:
        """Save report as Markdown file.

        Args:
            path: Path to save the Markdown report
        """
        path.write_text(self.to_markdown())

    def to_csv_rows(self) -> list[dict[str, str]]:
        """Export all issues as CSV rows for spreadsheet tracking.

        Returns:
            List of dictionaries representing CSV rows
        """
        rows = []

        # Failed imports
        for fail in self.failed_imports:
            rows.append(
                {
                    "category": "failed_import",
                    "resource_type": fail.resource_type,
                    "name": fail.name,
                    "source_id": str(fail.source_id),
                    "error": fail.error_message,
                    "action_required": "Investigate and retry",
                }
            )

        # Unresolved dependencies
        for dep in self.unresolved_dependencies:
            rows.append(
                {
                    "category": "unresolved_dependency",
                    "resource_type": dep.resource_type,
                    "name": dep.resource_name,
                    "source_id": str(dep.source_id),
                    "error": dep.error,
                    "action_required": f"Create {dep.dependency_type} ID {dep.missing_source_id} first",
                }
            )

        # Encrypted credentials
        for cred in self.encrypted_credentials:
            rows.append(
                {
                    "category": "encrypted_credential",
                    "resource_type": "credentials",
                    "name": cred.name,
                    "source_id": str(cred.source_id),
                    "error": f"Encrypted fields: {', '.join(cred.encrypted_fields)}",
                    "action_required": "Manual credential creation required",
                }
            )

        return rows

    def save_csv(self, path: Path) -> None:
        """Save issues as CSV file.

        Args:
            path: Path to save the CSV report
        """
        rows = self.to_csv_rows()
        if not rows:
            # Create empty CSV with headers
            rows = [
                {
                    "category": "",
                    "resource_type": "",
                    "name": "",
                    "source_id": "",
                    "error": "",
                    "action_required": "",
                }
            ]

        fieldnames = [
            "category",
            "resource_type",
            "name",
            "source_id",
            "error",
            "action_required",
        ]

        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            if rows[0]["category"]:  # Only write rows if not empty placeholder
                writer.writerows(rows)

    def add_failed_import(
        self,
        resource_type: str,
        source_id: int | str,
        name: str,
        error_type: str,
        error_message: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Add a failed import to the report.

        Args:
            resource_type: Type of resource that failed
            source_id: Source resource ID
            name: Resource name
            error_type: Type of error (exception class name)
            error_message: Detailed error message
            data: Original resource data (optional)
        """
        self.failed_imports.append(
            FailedImport(
                resource_type=resource_type,
                source_id=source_id,
                name=name,
                error_type=error_type,
                error_message=error_message,
                data=data,
            )
        )

    def add_unresolved_dependency(
        self,
        resource_type: str,
        resource_name: str,
        source_id: int | str,
        dependency_field: str,
        dependency_type: str,
        missing_source_id: int | str,
        error: str,
    ) -> None:
        """Add an unresolved dependency to the report.

        Args:
            resource_type: Type of resource with missing dependency
            resource_name: Name of the resource
            source_id: Source resource ID
            dependency_field: Field name containing the dependency
            dependency_type: Type of missing dependency
            missing_source_id: ID of the missing dependency
            error: Error description
        """
        self.unresolved_dependencies.append(
            UnresolvedDependency(
                resource_type=resource_type,
                resource_name=resource_name,
                source_id=source_id,
                dependency_field=dependency_field,
                dependency_type=dependency_type,
                missing_source_id=missing_source_id,
                error=error,
            )
        )

    def add_encrypted_credential(
        self,
        source_id: int | str,
        name: str,
        organization: int | str | None,
        credential_type: int | str | None,
        encrypted_fields: list[str],
        instructions: str,
    ) -> None:
        """Add an encrypted credential placeholder to the report.

        Args:
            source_id: Source credential ID
            name: Credential name
            organization: Organization ID
            credential_type: Credential type ID
            encrypted_fields: List of encrypted field names
            instructions: Human-readable creation instructions
        """
        self.encrypted_credentials.append(
            CredentialPlaceholder(
                resource_type="credentials",
                source_id=source_id,
                name=name,
                organization=organization,
                credential_type=credential_type,
                encrypted_fields=encrypted_fields,
                action_required="Manual credential creation required",
                instructions=instructions,
            )
        )

    def has_issues(self) -> bool:
        """Check if there are any issues requiring attention.

        Returns:
            True if there are failed imports, unresolved dependencies,
            or encrypted credentials
        """
        return bool(
            self.failed_imports or self.unresolved_dependencies or self.encrypted_credentials
        )

    def get_summary_dict(self) -> dict[str, Any]:
        """Get a summary dictionary for quick overview.

        Returns:
            Dictionary containing summary statistics
        """
        self.calculate_summary()
        return {
            "timestamp": self.timestamp,
            "total_processed": self.total_resources_processed,
            "successful": self.total_successful,
            "failed": self.total_failed,
            "requires_manual_action": self.requires_manual_action,
            "failed_imports_count": len(self.failed_imports),
            "unresolved_dependencies_count": len(self.unresolved_dependencies),
            "encrypted_credentials_count": len(self.encrypted_credentials),
        }
