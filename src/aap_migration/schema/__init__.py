"""Schema comparison and analysis for AAP migration.

This module provides tools for comparing AAP 2.3 and AAP 2.6 API schemas
to identify migration requirements and potential issues.
"""

from aap_migration.schema.comparator import SchemaComparator
from aap_migration.schema.models import ComparisonResult, FieldDiff, FieldRename, SchemaChange

__all__ = [
    "SchemaComparator",
    "ComparisonResult",
    "FieldDiff",
    "FieldRename",
    "SchemaChange",
]
