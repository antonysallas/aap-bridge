"""Central resource type definitions - single source of truth.

This module provides the definitive registry of all supported resource types
in the AAP migration tool. All other modules should import from here rather
than defining their own hardcoded lists.

This ensures consistency across:
- CLI commands (export, import, migrate, cleanup)
- Migration phases
- Exporter/Importer factories
- API endpoint mappings

DYNAMIC DISCOVERY (NEW):
If `schemas/source_endpoints.json` exists (created by `aap-bridge prep`),
functions will use discovered endpoints dynamically. Otherwise, falls back
to the hardcoded RESOURCE_REGISTRY below.
"""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ResourceTypeInfo:
    """Metadata for a resource type."""

    name: str
    endpoint: str
    description: str
    migration_order: int  # Lower = earlier in migration (dependency order)
    cleanup_order: int  # Lower = earlier in cleanup (reverse dependency)
    has_exporter: bool = True
    has_importer: bool = False
    has_transformer: bool = False
    batch_size: int = 100
    use_bulk_api: bool = False


# Complete registry of all supported resource types
# This is the SINGLE SOURCE OF TRUTH for the entire application
RESOURCE_REGISTRY: dict[str, ResourceTypeInfo] = {
    # Foundation resources (migrate first, delete last)
    "organizations": ResourceTypeInfo(
        name="organizations",
        endpoint="organizations/",
        description="Organizations",
        migration_order=20,  # CHANGED: Was 10, now after instance_groups
        cleanup_order=140,
        has_exporter=True,
        has_importer=True,
        has_transformer=False,
        batch_size=50,
    ),
    "labels": ResourceTypeInfo(
        name="labels",
        endpoint="labels/",
        description="Labels",
        migration_order=30,  # CHANGED: Was 20, now after organizations
        cleanup_order=130,  # Delete after users but before organizations
        has_exporter=True,
        has_importer=True,
        has_transformer=False,
    ),
    # Identity and access
    # NOTE: Cleanup deletes in ascending order of cleanup_order (lower = deleted first)
    # Users own: credentials, inventories, job_templates, projects, etc.
    # Those resources must be deleted FIRST (lower number), then users AFTER (higher number)
    # Current order is correct: credentials(90) < users(120) means credentials deleted before users
    "users": ResourceTypeInfo(
        name="users",
        endpoint="users/",
        description="Users",
        migration_order=40,  # CHANGED: Was 30, now after labels
        cleanup_order=120,  # Delete AFTER resources that reference users (credentials=90, etc.)
        has_exporter=True,
        has_importer=True,
        has_transformer=False,
    ),
    "teams": ResourceTypeInfo(
        name="teams",
        endpoint="teams/",
        description="Teams",
        migration_order=50,  # CHANGED: Was 40, now after users
        cleanup_order=110,  # Delete after most resources but before users
        has_exporter=True,
        has_importer=True,
        has_transformer=False,
    ),
    # Credentials
    "credential_types": ResourceTypeInfo(
        name="credential_types",
        endpoint="credential_types/",
        description="Credential Types",
        migration_order=60,  # CHANGED: Was 50, now after teams
        cleanup_order=100,
        has_exporter=True,
        has_importer=True,
        has_transformer=False,
        batch_size=50,
    ),
    "credentials": ResourceTypeInfo(
        name="credentials",
        endpoint="credentials/",
        description="Credentials",
        migration_order=70,  # CHANGED: Was 60, now after credential_types
        cleanup_order=90,
        has_exporter=True,
        has_importer=True,
        has_transformer=True,
        batch_size=50,
    ),
    "credential_input_sources": ResourceTypeInfo(
        name="credential_input_sources",
        endpoint="credential_input_sources/",
        description="Credential Input Sources",
        migration_order=80,  # CHANGED: Was 65, now after credentials
        cleanup_order=85,
        has_exporter=True,
        has_importer=True,
        has_transformer=True,
        batch_size=100,
    ),
    # Shared infrastructure (created early, deleted late)
    "execution_environments": ResourceTypeInfo(
        name="execution_environments",
        endpoint="execution_environments/",
        description="Execution Environments",
        migration_order=90,  # CHANGED: Was 65, now after credential_input_sources
        cleanup_order=135,   # Delete AFTER projects (before orgs)
        has_exporter=True,
        has_importer=True,
        has_transformer=True,  # Extracts organization, credential
    ),
    "instance_groups": ResourceTypeInfo(
        name="instance_groups",
        endpoint="instance_groups/",
        description="Instance Groups",
        migration_order=117,  # After hosts (115), before projects (120)
        cleanup_order=87,    # Delete before EEs
        has_exporter=True,
        has_importer=True,
        has_transformer=False,
        batch_size=50,
    ),
    # Projects and configuration
    "projects": ResourceTypeInfo(
        name="projects",
        endpoint="projects/",
        description="Projects",
        migration_order=120,  # CHANGED: Was 75, now after hosts
        cleanup_order=80,     # Delete before EEs
        has_exporter=True,
        has_importer=True,
        has_transformer=True,  # Extracts organization, default_environment, credential
    ),
    # Inventory resources
    "inventories": ResourceTypeInfo(
        name="inventories",
        endpoint="inventories/",
        description="Inventories",
        migration_order=100,  # CHANGED: Was 85, now after execution_environments
        cleanup_order=60,
        has_exporter=True,
        has_importer=True,
        has_transformer=True,
    ),
    "inventory_sources": ResourceTypeInfo(
        name="inventory_sources",
        endpoint="inventory_sources/",
        description="Inventory Sources",
        migration_order=105,  # After inventories (100), before inventory_groups
        cleanup_order=70,
        has_exporter=True,
        has_importer=True,
        has_transformer=True,  # Extracts inventory, source_project, credential, execution_environment
    ),
    "inventory_groups": ResourceTypeInfo(
        name="inventory_groups",
        endpoint="groups/",
        description="Inventory Groups",
        migration_order=110,  # After inventory_sources (105), before hosts
        cleanup_order=50,
        has_exporter=True,  # InventoryGroupExporter
        has_importer=True,
        has_transformer=True,  # Extracts inventory (added in commit d42ba2b)
    ),
    "hosts": ResourceTypeInfo(
        name="hosts",
        endpoint="hosts/",
        description="Hosts",
        migration_order=115,  # After inventory_groups (110), before instances
        cleanup_order=40,
        has_exporter=True,
        has_importer=True,
        has_transformer=False,
        batch_size=200,
        use_bulk_api=True,
    ),
    "instances": ResourceTypeInfo(
        name="instances",
        endpoint="instances/",
        description="Instances (AAP Controller Nodes)",
        migration_order=116,  # After hosts (115), before instance_groups (117)
        cleanup_order=88,     # After instance_groups (87) - delete dependents first
        has_exporter=True,
        has_importer=True,
        has_transformer=False,
        batch_size=50,
    ),
    # Job templates and workflows
    "job_templates": ResourceTypeInfo(
        name="job_templates",
        endpoint="job_templates/",
        description="Job Templates",
        migration_order=150,  # CHANGED: Was 115, now after inventory_groups
        cleanup_order=20,
        has_exporter=True,
        has_importer=True,
        has_transformer=True,
    ),
    "workflow_job_templates": ResourceTypeInfo(
        name="workflow_job_templates",
        endpoint="workflow_job_templates/",
        description="Workflow Job Templates",
        migration_order=160,  # CHANGED: Was 125, now after job_templates
        cleanup_order=10,
        has_exporter=True,
        has_importer=True,
        has_transformer=True,
        batch_size=50,
    ),
    "system_job_templates": ResourceTypeInfo(
        name="system_job_templates",
        endpoint="system_job_templates/",
        description="System Job Templates",
        migration_order=165,  # Before schedules (170)
        cleanup_order=15,     # Not deleted, but order needed
        has_exporter=True,
        has_importer=True,    # Mapping only
        has_transformer=True, # Mapping logic
        batch_size=50,
    ),
    "schedules": ResourceTypeInfo(
        name="schedules",
        endpoint="schedules/",
        description="Schedules",
        migration_order=170,  # CHANGED: Was 135, now after workflow_job_templates
        cleanup_order=30,
        has_exporter=True,
        has_importer=True,
        has_transformer=False,
    ),
    "notification_templates": ResourceTypeInfo(
        name="notification_templates",
        endpoint="notification_templates/",
        description="Notification Templates",
        migration_order=140,  # Before job_templates (150)
        cleanup_order=25,     # Delete before schedules
        has_exporter=True,
        has_importer=True,
        has_transformer=False,
        batch_size=100,
    ),
}


# ============================================
# Read-Only Endpoints (Never Exported)
# ============================================

# Endpoints that are read-only and should never be exported/migrated
# These are informational, meta, or auto-discovered endpoints
READ_ONLY_ENDPOINTS = {
    "ping",                    # Health check endpoint
    "config",                  # System configuration (read-only)
    "dashboard",               # Dashboard data (read-only)
    "metrics",                 # Metrics endpoint (read-only)
    "mesh_visualizer",         # Visualization data (read-only)
    "me",                      # Current user info (read-only)
    "activity_stream",         # Audit log (historical)
    "unified_job_templates",   # Meta-endpoint (virtual)
    "unified_jobs",            # Meta-endpoint (virtual)
}


# ============================================
# Endpoint Name Mapping
# ============================================

# Maps discovered endpoint names to internal resource type names
# Used when endpoint discovery returns different names than our exporters expect
ENDPOINT_TO_RESOURCE_TYPE = {
    # Endpoint name → Resource type name
    "groups": "inventory_groups",  # Exporter expects inventory_groups, API uses groups
    "inventory": "inventories",  # Handle singular form from API discovery
    "workflow_job_template_nodes": "workflow_nodes",  # Exporter expects workflow_nodes
}


# ============================================
# Runtime Data Endpoints (Never Exported)
# ============================================

# Endpoints that contain runtime/historical data that should NOT be migrated
# These are job execution logs, ad-hoc command history, inventory updates, etc.
RUNTIME_DATA_ENDPOINTS = {
    # Job execution data (historical logs, never migrated)
    "jobs",                      # Job execution records (historical)
    "workflow_jobs",             # Workflow execution records (historical)
    "project_updates",           # Project sync job logs (historical)
    "inventory_updates",         # Inventory sync job logs (historical)
    "ad_hoc_commands",           # Ad-hoc command execution records (historical)
    "system_jobs",               # System job execution records (historical)
    "workflow_job_nodes",        # Workflow execution node logs (historical - NOT workflow_job_template_nodes)

    # Runtime notifications (not migrated)
    "notifications",             # Runtime notification instances (historical)

    # System metrics (auto-generated, ephemeral)
    "host_metric_summary_monthly",  # Host usage metrics (auto-expires, ephemeral)

    # System job templates (auto-created, not migrated)
}


# ============================================
# Manual Migration Endpoints
# ============================================

# Endpoints that require manual migration or special handling
# These cannot be automatically migrated due to security or architectural constraints
MANUAL_MIGRATION_ENDPOINTS = {
    "settings",                  # Global system settings (manual review/config required)
    "roles",                     # RBAC role assignments (handled separately via RBAC import)
    "applications",              # OAuth applications (manual recreation recommended)
    "tokens",                    # OAuth tokens (short-lived, manual recreation)
    "inventory_sources",         # Inventory sources (manual recreation - tied to dynamic inventories)
}


# ============================================
# Job Status Constants
# ============================================

# Job status states based on AAP API and AWX implementation
# See: docs/JOB_CANCEL_503_FIX_PLAN.md for detailed explanations

# Active job statuses that can be cancelled
JOB_ACTIVE_STATUSES = ["new", "pending", "waiting", "running"]

# Terminal job statuses (job completed, cannot be cancelled)
JOB_TERMINAL_STATUSES = ["successful", "failed", "error", "canceled"]

# Transient statuses (cancellation in progress)
JOB_TRANSIENT_STATUSES = ["canceling"]

# All valid job statuses
JOB_ALL_STATUSES = JOB_ACTIVE_STATUSES + JOB_TERMINAL_STATUSES + JOB_TRANSIENT_STATUSES

# Job types that CAN be deleted during clean wipe scenarios
# These are runtime/historical data - safe to delete when doing a full cleanup
# See: docs/JOB_CLEANUP_BEFORE_IMPORT.md for detailed explanations
JOB_DELETABLE_TYPES = [
    "jobs",                # Job template execution records
    "workflow_jobs",       # Workflow execution records
    "project_updates",     # Project SCM sync jobs
    "inventory_updates",   # Inventory source sync jobs
    "system_jobs",         # System cleanup/management jobs
    "ad_hoc_commands",     # Ad-hoc command execution records
]


# ============================================
# Resource Uniqueness Scope
# ============================================

# Organization-scoped resources: unique per (name, organization)
# These resources can have the same name in different organizations
ORGANIZATION_SCOPED_RESOURCES = {
    "projects",
    "inventories",
    "credentials",
    "job_templates",
    "workflow_job_templates",
    "teams",
}

# Parent-scoped resources: unique within parent resource
# Format: {resource_type: parent_field_name}
PARENT_SCOPED_RESOURCES = {
    "hosts": "inventory",
    "groups": "inventory",
    "inventory_sources": "inventory",
}

# All other resources are globally unique by name (organizations, users, labels, etc.)


# ============================================
# Dynamic Endpoint Discovery (NEW)
# ============================================


def _load_discovered_endpoints() -> dict[str, str] | None:
    """Load discovered endpoints from prep output.

    Returns:
        Dict mapping resource_type -> endpoint_url, or None if not available
    """
    endpoints_file = Path("schemas/source_endpoints.json")
    if not endpoints_file.exists():
        return None

    try:
        with open(endpoints_file) as f:
            data = json.load(f)
        return {name: info["url"] for name, info in data.get("endpoints", {}).items()}
    except Exception:
        return None


def has_discovered_endpoints() -> bool:
    """Check if discovered endpoints are available.

    Returns:
        True if schemas/source_endpoints.json exists
    """
    return Path("schemas/source_endpoints.json").exists()


def get_discovered_types() -> list[str]:
    """Get all resource types discovered by prep phase.

    Returns:
        List of discovered resource type names, or empty list if prep not run
    """
    endpoints = _load_discovered_endpoints()
    return list(endpoints.keys()) if endpoints else []


# ============================================
# Helper Functions - Derived from Registry
# ============================================


def get_all_types() -> list[str]:
    """Get all supported resource types.

    Returns:
        List of all resource type names
    """
    return list(RESOURCE_REGISTRY.keys())


def get_migration_order() -> list[str]:
    """Get resource types in migration dependency order.

    Resources are ordered so dependencies are migrated first.

    Returns:
        List of resource type names in migration order
    """
    return sorted(
        RESOURCE_REGISTRY.keys(),
        key=lambda x: RESOURCE_REGISTRY[x].migration_order,
    )


def get_cleanup_order() -> list[str]:
    """Get resource types in cleanup/deletion order.

    Resources are ordered in reverse dependency order to avoid FK conflicts.

    Returns:
        List of resource type names in cleanup order
    """
    return sorted(
        RESOURCE_REGISTRY.keys(),
        key=lambda x: RESOURCE_REGISTRY[x].cleanup_order,
    )


def get_exportable_types(use_discovered: bool = False) -> list[str]:
    """Get resource types that can be exported.

    Args:
        use_discovered: If True and discovered endpoints exist, return ALL
                       discovered types (not just those with exporters).
                       If False, return only types from registry with has_exporter=True.

    Returns:
        List of resource type names available for export
    """
    if use_discovered:
        discovered = get_discovered_types()
        if discovered:
            return discovered

    # Fall back to hardcoded registry
    return [name for name, info in RESOURCE_REGISTRY.items() if info.has_exporter]


def get_importable_types(use_discovered: bool = False) -> list[str]:
    """Get resource types that can be imported.

    Args:
        use_discovered: If True and discovered endpoints exist, return ALL
                       discovered types from target (not just those with importers).
                       If False, return only types from registry with has_importer=True.

    Returns:
        List of resource type names available for import
    """
    if use_discovered:
        # Load target endpoints (for import)
        target_file = Path("schemas/target_endpoints.json")
        if target_file.exists():
            try:
                with open(target_file) as f:
                    data = json.load(f)
                return list(data.get("endpoints", {}).keys())
            except Exception:
                pass

    # Fall back to hardcoded registry
    return [name for name, info in RESOURCE_REGISTRY.items() if info.has_importer]


def get_transformable_types() -> list[str]:
    """Get resource types that have specialized transformers.

    Returns:
        List of resource type names with transformers
    """
    return [name for name, info in RESOURCE_REGISTRY.items() if info.has_transformer]


def get_fully_supported_types() -> list[str]:
    """Get resource types that support full migration (export + import).

    These are the types that can be used in migrate all command.

    Returns:
        List of resource type names with both exporter and importer
    """
    types = [
        name for name, info in RESOURCE_REGISTRY.items() if info.has_exporter and info.has_importer
    ]
    # Return in migration order
    return sorted(types, key=lambda x: RESOURCE_REGISTRY[x].migration_order)


def get_endpoint(resource_type: str) -> str:
    """Get API endpoint for a resource type.

    If discovered endpoints exist (from `aap-bridge prep`), uses those.
    Otherwise, falls back to hardcoded RESOURCE_REGISTRY.

    Args:
        resource_type: Name of the resource type

    Returns:
        API endpoint path (e.g., "organizations/" or "/api/v2/organizations/")

    Raises:
        KeyError: If resource type is not in registry or discovered endpoints
    """
    # Try discovered endpoints first
    discovered = _load_discovered_endpoints()
    if discovered and resource_type in discovered:
        return discovered[resource_type]

    # Fall back to hardcoded registry
    if resource_type in RESOURCE_REGISTRY:
        return RESOURCE_REGISTRY[resource_type].endpoint

    # Not found in either
    raise KeyError(f"Unknown resource type: {resource_type}")


def get_info(resource_type: str) -> ResourceTypeInfo:
    """Get full metadata for a resource type.

    Args:
        resource_type: Name of the resource type

    Returns:
        ResourceTypeInfo object with all metadata

    Raises:
        KeyError: If resource type is not in registry
    """
    return RESOURCE_REGISTRY[resource_type]


def normalize_resource_type(endpoint_name: str) -> str:
    """Normalize discovered endpoint name to internal resource type name.

    Some AAP API endpoints have different names than our internal resource types.
    For example, the API uses "groups" but we use "inventory_groups" internally.

    Args:
        endpoint_name: Name discovered from AAP API (e.g., "groups", "organizations")

    Returns:
        Internal resource type name (e.g., "inventory_groups", "organizations")

    Example:
        >>> normalize_resource_type("groups")
        "inventory_groups"
        >>> normalize_resource_type("organizations")
        "organizations"
    """
    return ENDPOINT_TO_RESOURCE_TYPE.get(endpoint_name, endpoint_name)


def get_batch_size(resource_type: str) -> int:
    """Get recommended batch size for a resource type.

    Args:
        resource_type: Name of the resource type

    Returns:
        Recommended batch size for the resource type

    Raises:
        KeyError: If resource type is not in registry
    """
    return RESOURCE_REGISTRY[resource_type].batch_size


def is_valid_type(resource_type: str) -> bool:
    """Check if a resource type is valid.

    Args:
        resource_type: Name of the resource type

    Returns:
        True if resource type is in registry
    """
    return resource_type in RESOURCE_REGISTRY


def get_description(resource_type: str) -> str:
    """Get human-readable description of a resource type.

    Args:
        resource_type: Name of the resource type

    Returns:
        Description string

    Raises:
        KeyError: If resource type is not in registry
    """
    return RESOURCE_REGISTRY[resource_type].description


# ============================================
# Convenience Constants (derived from registry)
# ============================================

# All types in migration order
ALL_RESOURCE_TYPES = get_migration_order()

# Types that support full export->transform->import cycle
FULLY_SUPPORTED_TYPES = get_fully_supported_types()

# Types that can be exported
EXPORTABLE_TYPES = get_exportable_types()

# Types that can be imported
IMPORTABLE_TYPES = get_importable_types()

# Types in cleanup order (reverse dependency)
CLEANUP_ORDER = get_cleanup_order()
