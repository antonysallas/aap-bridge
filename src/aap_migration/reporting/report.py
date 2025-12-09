"""Migration report generation.

This module provides comprehensive migration reporting with support for
multiple output formats (JSON, Markdown, HTML).
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aap_migration.utils.logging import get_logger

logger = get_logger(__name__)


class MigrationReport:
    """Generates comprehensive migration reports.

    Creates detailed reports of migration operations including statistics,
    errors, warnings, and recommendations.
    """

    def __init__(self, migration_id: str, summary: dict[str, Any]):
        """Initialize migration report.

        Args:
            migration_id: Unique migration identifier
            summary: Migration summary from coordinator
        """
        self.migration_id = migration_id
        self.summary = summary
        self.generated_at = datetime.now(UTC)

    def generate_json(self, output_path: str | None = None) -> str:
        """Generate JSON report.

        Args:
            output_path: Optional path to save report

        Returns:
            JSON report as string
        """
        report = {
            "report_version": "1.0",
            "generated_at": self.generated_at.isoformat(),
            "migration_id": self.migration_id,
            "summary": self.summary,
            "statistics": self._generate_statistics(),
            "errors": self.summary.get("errors", []),
            "skipped_items": self.summary.get("skipped_items", []),
            "recommendations": self._generate_recommendations(),
        }

        json_str = json.dumps(report, indent=2, default=str)

        if output_path:
            Path(output_path).write_text(json_str)
            logger.info("json_report_saved", path=output_path)

        return json_str

    def generate_markdown(self, output_path: str | None = None) -> str:
        """Generate Markdown report.

        Args:
            output_path: Optional path to save report

        Returns:
            Markdown report as string
        """
        lines = [
            "# AAP Migration Report",
            "",
            f"**Migration ID:** `{self.migration_id}`  ",
            f"**Generated:** {self.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
            f"**Status:** {self.summary.get('status', 'unknown')}  ",
            "",
            "## Summary",
            "",
            f"- **Start Time:** {self.summary.get('start_time', 'N/A')}",
            f"- **End Time:** {self.summary.get('end_time', 'N/A')}",
            f"- **Duration:** {self._format_duration(self.summary.get('duration_seconds'))}",
            f"- **Dry Run:** {'Yes' if self.summary.get('dry_run') else 'No'}",
            "",
            "## Phase Summary",
            "",
            f"- **Phases Completed:** {self.summary.get('phases_completed', 0)}",
            f"- **Phases Failed:** {self.summary.get('phases_failed', 0)}",
            "",
            "## Resource Statistics",
            "",
        ]

        # Add statistics table
        stats = self._generate_statistics()
        lines.extend(
            [
                "| Metric | Count |",
                "|--------|------:|",
                f"| Resources Exported | {stats['resources_exported']:,} |",
                f"| Resources Imported | {stats['resources_imported']:,} |",
                f"| Resources Failed | {stats['resources_failed']:,} |",
                f"| Resources Skipped | {stats['resources_skipped']:,} |",
                f"| Success Rate | {stats['success_rate']:.1f}% |",
                "",
            ]
        )

        # Add errors section if any
        errors = self.summary.get("errors", [])
        if errors:
            lines.extend(
                [
                    "## Errors",
                    "",
                    f"Total errors encountered: {len(errors)}",
                    "",
                ]
            )

            for idx, error in enumerate(errors[:10], 1):  # Show first 10 errors
                lines.extend(
                    [
                        f"### Error {idx}",
                        f"- **Phase:** {error.get('phase', 'unknown')}",
                        f"- **Message:** {error.get('error', 'No message')}",
                        f"- **Timestamp:** {error.get('timestamp', 'N/A')}",
                        "",
                    ]
                )

            if len(errors) > 10:
                lines.append(f"*... and {len(errors) - 10} more errors*\n")

        # Add skipped items section if any
        skipped_items = self.summary.get("skipped_items", [])
        if skipped_items:
            lines.extend(
                [
                    "## Skipped Items",
                    "",
                    f"Total items skipped: {len(skipped_items)}",
                    "",
                ]
            )

            for idx, item in enumerate(skipped_items[:10], 1):
                lines.extend(
                    [
                        f"### Skipped Item {idx}",
                        f"- **Phase:** {item.get('phase', 'unknown')}",
                        f"- **Type:** {item.get('resource_type', 'unknown')}",
                        f"- **Name:** {item.get('name', 'unknown')}",
                        f"- **Reason:** {item.get('reason', 'No reason provided')}",
                        "",
                    ]
                )

            if len(skipped_items) > 10:
                lines.append(f"*... and {len(skipped_items) - 10} more skipped items*\n")

        # Add recommendations
        recommendations = self._generate_recommendations()
        if recommendations:
            lines.extend(
                [
                    "## Recommendations",
                    "",
                ]
            )
            for rec in recommendations:
                lines.append(f"- {rec}")
            lines.append("")

        markdown = "\n".join(lines)

        if output_path:
            Path(output_path).write_text(markdown)
            logger.info("markdown_report_saved", path=output_path)

        return markdown

    def generate_html(self, output_path: str | None = None) -> str:
        """Generate HTML report.

        Args:
            output_path: Optional path to save report

        Returns:
            HTML report as string
        """
        stats = self._generate_statistics()
        errors = self.summary.get("errors", [])
        skipped_items = self.summary.get("skipped_items", [])
        recommendations = self._generate_recommendations()

        status_class = "success" if self.summary.get("status") == "completed" else "warning"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AAP Migration Report - {self.migration_id}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
        }}
        .status {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            text-transform: uppercase;
            font-size: 0.85em;
        }}
        .status.success {{
            background: #10b981;
            color: white;
        }}
        .status.warning {{
            background: #f59e0b;
            color: white;
        }}
        .section {{
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .section h2 {{
            margin-top: 0;
            color: #667eea;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .stat-card {{
            background: #f9fafb;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }}
        .stat-card .label {{
            font-size: 0.85em;
            color: #6b7280;
            margin-bottom: 5px;
        }}
        .stat-card .value {{
            font-size: 1.8em;
            font-weight: bold;
            color: #1f2937;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
        }}
        th {{
            background: #f9fafb;
            font-weight: 600;
            color: #374151;
        }}
        .error-item {{
            background: #fef2f2;
            border-left: 4px solid #ef4444;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 4px;
        }}
        .error-item h4 {{
            margin-top: 0;
            color: #dc2626;
        }}
        .skipped-item {{
            background: #fffbeb;
            border-left: 4px solid #f59e0b;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 4px;
        }}
        .skipped-item h4 {{
            margin-top: 0;
            color: #b45309;
        }}
        .recommendation {{
            background: #eff6ff;
            border-left: 4px solid #3b82f6;
            padding: 10px 15px;
            margin-bottom: 10px;
            border-radius: 4px;
        }}
        code {{
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>AAP Migration Report</h1>
        <p><strong>Migration ID:</strong> <code>{self.migration_id}</code></p>
        <p><strong>Generated:</strong> {self.generated_at.strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
        <p><span class="status {status_class}">{self.summary.get("status", "unknown")}</span></p>
    </div>

    <div class="section">
        <h2>Summary</h2>
        <table>
            <tr>
                <td><strong>Start Time</strong></td>
                <td>{self.summary.get("start_time", "N/A")}</td>
            </tr>
            <tr>
                <td><strong>End Time</strong></td>
                <td>{self.summary.get("end_time", "N/A")}</td>
            </tr>
            <tr>
                <td><strong>Duration</strong></td>
                <td>{self._format_duration(self.summary.get("duration_seconds"))}</td>
            </tr>
            <tr>
                <td><strong>Dry Run</strong></td>
                <td>{"Yes" if self.summary.get("dry_run") else "No"}</td>
            </tr>
        </table>
    </div>

    <div class="section">
        <h2>Statistics</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">Resources Exported</div>
                <div class="value">{stats["resources_exported"]:,}</div>
            </div>
            <div class="stat-card">
                <div class="label">Resources Imported</div>
                <div class="value">{stats["resources_imported"]:,}</div>
            </div>
            <div class="stat-card">
                <div class="label">Resources Failed</div>
                <div class="value">{stats["resources_failed"]:,}</div>
            </div>
            <div class="stat-card">
                <div class="label">Resources Skipped</div>
                <div class="value">{stats["resources_skipped"]:,}</div>
            </div>
            <div class="stat-card">
                <div class="label">Success Rate</div>
                <div class="value">{stats["success_rate"]:.1f}%</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Phase Summary</h2>
        <p><strong>Phases Completed:</strong> {self.summary.get("phases_completed", 0)}</p>
        <p><strong>Phases Failed:</strong> {self.summary.get("phases_failed", 0)}</p>
    </div>
"""

        # Add errors section
        if errors:
            html += f"""
    <div class="section">
        <h2>Errors ({len(errors)})</h2>
"""
            for idx, error in enumerate(errors[:10], 1):
                html += f"""
        <div class="error-item">
            <h4>Error {idx}: {error.get("phase", "unknown")}</h4>
            <p><strong>Message:</strong> {error.get("error", "No message")}</p>
            <p><strong>Timestamp:</strong> {error.get("timestamp", "N/A")}</p>
        </div>
"""
            if len(errors) > 10:
                html += f"<p><em>... and {len(errors) - 10} more errors</em></p>\n"

            html += "    </div>\n"

        # Add skipped items section
        if skipped_items:
            html += f"""
    <div class="section">
        <h2>Skipped Items ({len(skipped_items)})</h2>
"""
            for idx, item in enumerate(skipped_items[:10], 1):
                html += f"""
        <div class="skipped-item">
            <h4>Skipped Item {idx}: {item.get("resource_type", "unknown")}</h4>
            <p><strong>Name:</strong> {item.get("name", "unknown")}</p>
            <p><strong>Reason:</strong> {item.get("reason", "No reason provided")}</p>
        </div>
"""
            if len(skipped_items) > 10:
                html += f"<p><em>... and {len(skipped_items) - 10} more skipped items</em></p>\n"

            html += "    </div>\n"

        # Add recommendations
        if recommendations:
            html += """
    <div class="section">
        <h2>Recommendations</h2>
"""
            for rec in recommendations:
                html += f'        <div class="recommendation">{rec}</div>\n'
            html += "    </div>\n"

        html += """
</body>
</html>
"""

        if output_path:
            Path(output_path).write_text(html)
            logger.info("html_report_saved", path=output_path)

        return html

    def _generate_statistics(self) -> dict[str, Any]:
        """Generate detailed statistics.

        Returns:
            Dictionary with calculated statistics
        """
        exported = self.summary.get("total_resources_exported", 0)
        imported = self.summary.get("total_resources_imported", 0)
        failed = self.summary.get("total_resources_failed", 0)
        skipped = self.summary.get("total_resources_skipped", 0)

        total_processed = exported
        success_rate = (imported / total_processed * 100) if total_processed > 0 else 0

        return {
            "resources_exported": exported,
            "resources_imported": imported,
            "resources_failed": failed,
            "resources_skipped": skipped,
            "success_rate": success_rate,
            "phases_completed": self.summary.get("phases_completed", 0),
            "phases_failed": self.summary.get("phases_failed", 0),
        }

    def _generate_recommendations(self) -> list[str]:
        """Generate recommendations based on migration results.

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Check for failures
        failed = self.summary.get("total_resources_failed", 0)
        if failed > 0:
            recommendations.append(
                f"⚠️ {failed} resources failed to migrate. Review error logs for details."
            )

        # Check success rate
        stats = self._generate_statistics()
        if stats["success_rate"] < 95:
            recommendations.append(
                f"⚠️ Success rate ({stats['success_rate']:.1f}%) is below 95%. "
                "Consider investigating common failure patterns."
            )

        # Check for phase failures
        if self.summary.get("phases_failed", 0) > 0:
            recommendations.append(
                "❌ One or more phases failed. Resume from the last checkpoint after "
                "resolving issues."
            )

        # Dry run check
        if self.summary.get("dry_run"):
            recommendations.append(
                "ℹ️ This was a dry run. No actual changes were made to the target system. "
                "Run without --dry-run to perform the migration."
            )

        # Success message
        if not recommendations and stats["success_rate"] >= 95:
            recommendations.append(
                "✅ Migration completed successfully! All resources migrated with high success rate."
            )

        return recommendations

    def _format_duration(self, seconds: float | None) -> str:
        """Format duration in human-readable format.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted duration string
        """
        if seconds is None:
            return "N/A"

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"


def generate_migration_report(
    migration_id: str,
    summary: dict[str, Any],
    output_dir: str = "./reports",
    formats: list[str] | None = None,
) -> dict[str, str]:
    """Generate migration reports in multiple formats.

    Args:
        migration_id: Migration identifier
        summary: Migration summary from coordinator
        output_dir: Directory to save reports
        formats: List of formats to generate (json, markdown, html). Default: all

    Returns:
        Dictionary mapping format to file path
    """
    if formats is None:
        formats = ["json", "markdown", "html"]

    report = MigrationReport(migration_id, summary)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    generated_files = {}

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"migration_report_{migration_id}_{timestamp}"

    if "json" in formats:
        json_path = output_path / f"{base_filename}.json"
        report.generate_json(str(json_path))
        generated_files["json"] = str(json_path)

    if "markdown" in formats:
        md_path = output_path / f"{base_filename}.md"
        report.generate_markdown(str(md_path))
        generated_files["markdown"] = str(md_path)

    if "html" in formats:
        html_path = output_path / f"{base_filename}.html"
        report.generate_html(str(html_path))
        generated_files["html"] = str(html_path)

    logger.info(
        "migration_reports_generated",
        migration_id=migration_id,
        formats=formats,
        files=generated_files,
    )

    return generated_files
