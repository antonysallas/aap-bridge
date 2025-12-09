# Guide: Adding a New Resource Type to AAP Bridge

This document provides a comprehensive guide for adding export/import support for a new AAP resource type. Use this as a reference checklist when implementing support for any new resource.

---

## Overview

Adding a new resource type requires modifications to **8 files**:

| File | Purpose |
|------|---------|
| `resources.py` | Central registry - migration order, cleanup order, metadata |
| `exporter.py` | Export class + factory registration |
| `importer.py` | Import class + factory registration |
| `transformer.py` | Transformation class registration |
| `coordinator.py` | Migration phase definition |
| `migrate.py` | Phase 1/2/3 resource type list |
| `export_import.py` | Import method mapping (critical!) |
| `cleanup.py` | Skip logic for system/managed resources |

---

## Step-by-Step Implementation

### Step 1: `src/aap_migration/resources.py`

#### A. Remove from READ_ONLY_ENDPOINTS (if present)

If the resource type is currently in `READ_ONLY_ENDPOINTS`, remove it:

```python
READ_ONLY_ENDPOINTS = {
    "ping",
    "config",
    # ... remove your resource type from here
}
```

#### B. Add to RESOURCE_REGISTRY

Add the new resource type with appropriate migration/cleanup order:

```python
"your_resource": ResourceTypeInfo(
    name="your_resource",
    endpoint="your_resource/",
    description="Your Resource Description",
    migration_order=XXX,  # See Migration Order section below
    cleanup_order=YYY,    # See Cleanup Order section below
    has_exporter=True,
    has_importer=True,
    has_transformer=False,  # True if needs custom transformation
    batch_size=50,          # Adjust based on resource size
    use_bulk_api=False,     # True only for hosts
),
```

**Migration Order Guidelines:**
- Lower numbers = migrated earlier (dependencies first)
- Organizations: 20, Users: 40, Credentials: 70, Inventories: 100, Hosts: 115
- Place your resource after its dependencies

**Cleanup Order Guidelines:**
- Lower numbers = deleted earlier (dependents first)
- Reverse of migration order conceptually
- Resources that reference others should be deleted first

---

### Step 2: `src/aap_migration/migration/exporter.py`

#### A. Add Exporter Class

```python
class YourResourceExporter(ResourceExporter):
    """Exporter for your_resource resources.

    Add description of what this resource is and any special considerations.
    """

    async def export(
        self, filters: dict[str, Any] | None = None
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Export your_resource items.

        Args:
            filters: Optional query parameters for filtering

        Yields:
            Resource dictionaries
        """
        logger.info("exporting_your_resource")
        async for resource in self.export_resources(
            resource_type="your_resource",
            endpoint="your_resource/",
            page_size=self.performance_config.batch_sizes.get("your_resource", 50),
            filters=filters,
        ):
            yield resource
```

#### B. Register in Factory

Add to the `exporters` dict in `create_exporter()`:

```python
exporters = {
    # ... existing exporters
    "your_resource": YourResourceExporter,
}
```

---

### Step 3: `src/aap_migration/migration/importer.py`

#### A. Add Importer Class

```python
class YourResourceImporter(ResourceImporter):
    """Importer for your_resource resources."""

    # Define foreign key dependencies (field_name -> resource_type)
    DEPENDENCIES = {
        "organization": "organizations",  # Example
        # Add other FK dependencies
    }

    async def import_your_resource(
        self,
        resources: list[dict[str, Any]],
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> list[dict[str, Any]]:
        """Import multiple resources concurrently with live progress updates.

        Args:
            resources: List of resource data
            progress_callback: Optional callback for progress updates.

        Returns:
            List of created resource data
        """
        return await self._import_parallel("your_resource", resources, progress_callback)
```

**Important:** The method name MUST follow the pattern `import_{resource_type}` (e.g., `import_instances`, `import_organizations`).

#### B. Register in Factory

Add to the `importers` dict in `create_importer()`:

```python
importers = {
    # ... existing importers
    "your_resource": YourResourceImporter,
}
```

---

### Step 4: `src/aap_migration/migration/transformer.py`

Add to `TRANSFORMER_CLASSES` dict:

```python
TRANSFORMER_CLASSES: dict[str, type[DataTransformer]] = {
    # ... existing transformers
    "your_resource": DataTransformer,  # Use base class if no special transformation
    # OR create a custom transformer class if needed:
    # "your_resource": YourResourceTransformer,
}
```

If custom transformation is needed, create a transformer class:

```python
class YourResourceTransformer(DataTransformer):
    """Transformer for your_resource resources."""

    DEPENDENCIES = {
        "organization": "organizations",
    }
    REQUIRED_DEPENDENCIES = {"organization"}  # Dependencies that must exist
```

---

### Step 5: `src/aap_migration/migration/coordinator.py`

Add a phase to `MIGRATION_PHASES` list in the correct position:

```python
MIGRATION_PHASES = [
    # ... earlier phases
    {
        "name": "your_resource",
        "description": "Your Resource Description",
        "resource_types": ["your_resource"],
        "batch_size": 50,
    },
    # ... later phases
]
```

---

### Step 6: `src/aap_migration/cli/commands/migrate.py`

Add to the appropriate phase list:

```python
# Phase 1: Infrastructure & Projects
PHASE1_RESOURCE_TYPES = [
    # ... existing types
    "your_resource",  # Add in correct dependency order
]

# Phase 3: Automation Definitions (if applicable)
PHASE3_RESOURCE_TYPES = [
    # ... existing types
]
```

---

### Step 7: `src/aap_migration/cli/commands/export_import.py` ⚠️ CRITICAL

**This step is often missed!** Add to the `method_map` dict inside the import function:

```python
method_map = {
    # Foundation resources
    "organizations": "import_organizations",
    "your_resource": "import_your_resource",  # ADD THIS
    # ... other mappings
}
```

**The method name must match exactly** the method you defined in the importer class (Step 3A).

Without this mapping, the resource will be skipped during import with:
```
⚠️ SKIPPED - no importer
```

---

### Step 8: `src/aap_migration/cli/commands/cleanup.py`

Add skip logic for system/managed resources (if applicable):

```python
# Skip managed/system resources
elif resource_type == "your_resource" and (
    is_managed
    or resource_name in ("system_name_1", "system_name_2")
    or resource_id == 1
):
    skip_resource = True
    skip_reason = "managed/system resource"
```

---

## Implementation Checklist

Use this checklist when adding a new resource type:

- [ ] `resources.py`: Remove from READ_ONLY_ENDPOINTS (if present)
- [ ] `resources.py`: Add to RESOURCE_REGISTRY with correct migration/cleanup order
- [ ] `exporter.py`: Add Exporter class
- [ ] `exporter.py`: Register in create_exporter factory
- [ ] `importer.py`: Add Importer class with `import_{resource_type}` method
- [ ] `importer.py`: Register in create_importer factory
- [ ] `transformer.py`: Add to TRANSFORMER_CLASSES
- [ ] `coordinator.py`: Add phase to MIGRATION_PHASES
- [ ] `migrate.py`: Add to PHASE1/PHASE3_RESOURCE_TYPES
- [ ] `export_import.py`: Add to method_map ⚠️ **DON'T FORGET!**
- [ ] `cleanup.py`: Add skip logic for system/managed resources
- [ ] Verify code compiles: `uv run python -m py_compile <files>`
- [ ] Run tests: `uv run pytest tests/`

---

## Example: Adding "instances" Resource Type

Below is the complete implementation for the "instances" resource type as a reference.

### Background

Instances are AAP controller nodes in the deployment topology. They must be migrated BEFORE instance_groups since groups can reference instances.

### Migration Order

| Resource        | migration_order | cleanup_order |
|-----------------|-----------------|---------------|
| hosts           | 115             | 40            |
| **instances**   | **116**         | **88**        |
| instance_groups | 117             | 87            |
| projects        | 120             | 80            |

### Implementation Details

#### resources.py
```python
"instances": ResourceTypeInfo(
    name="instances",
    endpoint="instances/",
    description="Instances (AAP Controller Nodes)",
    migration_order=116,
    cleanup_order=88,
    has_exporter=True,
    has_importer=True,
    has_transformer=False,
    batch_size=50,
),
```

#### exporter.py
```python
class InstanceExporter(ResourceExporter):
    """Exporter for instance (AAP controller node) resources."""

    async def export(
        self, filters: dict[str, Any] | None = None
    ) -> AsyncGenerator[dict[str, Any], None]:
        logger.info("exporting_instances")
        async for instance in self.export_resources(
            resource_type="instances",
            endpoint="instances/",
            page_size=self.performance_config.batch_sizes.get("instances", 50),
            filters=filters,
        ):
            yield instance

# In create_exporter():
"instances": InstanceExporter,
```

#### importer.py
```python
class InstanceImporter(ResourceImporter):
    """Importer for instance (AAP controller node) resources."""

    DEPENDENCIES = {}  # No dependencies - instances are foundational

    async def import_instances(
        self,
        instances: list[dict[str, Any]],
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> list[dict[str, Any]]:
        return await self._import_parallel("instances", instances, progress_callback)

# In create_importer():
"instances": InstanceImporter,
```

#### transformer.py
```python
"instances": DataTransformer,  # No special transformation needed
```

#### coordinator.py
```python
{
    "name": "instances",
    "description": "Instances (AAP Controller Nodes)",
    "resource_types": ["instances"],
    "batch_size": 50,
},
```

#### migrate.py
```python
PHASE1_RESOURCE_TYPES = [
    # ...
    "hosts",
    "instances",       # After hosts, before instance_groups
    "instance_groups",
    "projects",
]
```

#### export_import.py
```python
method_map = {
    # Foundation resources
    "organizations": "import_organizations",
    "instances": "import_instances",  # Must match importer method name!
    "instance_groups": "import_instance_groups",
    # ...
}
```

#### cleanup.py
```python
elif resource_type == "instances" and (
    is_managed
    or resource_name in ("localhost", "controlplane")
    or resource_id == 1
):
    skip_resource = True
    skip_reason = "managed/system instance"
```

---

## API Reference

When adding a new resource, document its API endpoints:

### Instances Endpoint Example

- **List:** `GET /api/controller/v2/instances/`
- **Create:** `POST /api/controller/v2/instances/`
- **Detail:** `GET /api/controller/v2/instances/{id}/`
- **Update:** `PATCH /api/controller/v2/instances/{id}/`
- **Delete:** `DELETE /api/controller/v2/instances/{id}/`

### Key Fields

Document important fields for the resource:

- `hostname` - The hostname of the instance
- `node_type` - Type of node (control, hybrid, execution, hop)
- `capacity` - Capacity for running jobs
- `enabled` - Whether the instance is enabled
- `managed` - Whether the instance is managed by AAP

---

## Troubleshooting

### "SKIPPED - no importer" Warning

**Cause:** Missing entry in `export_import.py` method_map.

**Fix:** Add `"your_resource": "import_your_resource"` to method_map.

### "No exporter implemented for resource type" Error

**Cause:** Missing exporter class or factory registration.

**Fix:** Add exporter class and register in `create_exporter()`.

### Resources imported in wrong order

**Cause:** Incorrect `migration_order` value in resources.py.

**Fix:** Adjust migration_order to ensure dependencies are imported first.

### Cleanup deletes resources in wrong order (FK errors)

**Cause:** Incorrect `cleanup_order` value in resources.py.

**Fix:** Ensure dependents have lower cleanup_order (deleted first).
