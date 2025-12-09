# Plan: Implement Instances Export/Import

## Overview

Add full export/import support for AAP Instances (controller nodes). Instances must be migrated BEFORE instance_groups since groups can reference instances.

**Current Status:** "instances" is in `READ_ONLY_ENDPOINTS` - needs to be moved to full migration support.

**Import Strategy:** Create new instances via POST (same as other resources).

---

## Background

### What are Instances?

Instances are individual AAP controller nodes in the deployment topology. They represent the actual automation controller servers that execute jobs. Instance groups are collections of these instances.

### Why Migrate Instances?

- Instance groups reference specific instances
- Custom instance configurations need to be preserved
- Capacity settings and node types should be migrated

### Migration Order

| Resource        | migration_order | cleanup_order |
|-----------------|-----------------|---------------|
| hosts           | 115             | 40            |
| **instances**   | **116**         | **88**        |
| instance_groups | 117             | 87            |
| projects        | 120             | 80            |

**Import:** hosts → instances → instance_groups → projects
**Cleanup:** instance_groups (87) → instances (88) → ...

---

## Files to Modify

### 1. `src/aap_migration/resources.py`

**A. Remove from READ_ONLY_ENDPOINTS (~line 273):**

Remove "instances" from the READ_ONLY_ENDPOINTS set.

**B. Add to RESOURCE_REGISTRY (~line 145):**

```python
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
```

---

### 2. `src/aap_migration/migration/exporter.py`

**A. Add InstanceExporter class (after HostExporter, before InstanceGroupExporter):**

```python
class InstanceExporter(ResourceExporter):
    """Exporter for instance (AAP controller node) resources.

    Instances are individual nodes in the AAP deployment topology.
    They must be exported before instance_groups.
    """

    async def export(
        self, filters: dict[str, Any] | None = None
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Export instances.

        Args:
            filters: Optional query parameters for filtering

        Yields:
            Instance dictionaries
        """
        logger.info("exporting_instances")
        async for instance in self.export_resources(
            resource_type="instances",
            endpoint="instances/",
            page_size=self.performance_config.batch_sizes.get("instances", 50),
            filters=filters,
        ):
            yield instance
```

**B. Register in factory (create_exporter function):**

Add to the exporters dict:
```python
"instances": InstanceExporter,
```

---

### 3. `src/aap_migration/migration/importer.py`

**A. Add InstanceImporter class (before InstanceGroupImporter):**

```python
class InstanceImporter(ResourceImporter):
    """Importer for instance (AAP controller node) resources.

    Instances must be imported before instance_groups since groups
    can reference specific instances.
    """

    DEPENDENCIES = {}  # No dependencies - instances are foundational

    async def import_instances(
        self,
        instances: list[dict[str, Any]],
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> list[dict[str, Any]]:
        """Import multiple instances concurrently with live progress updates."""
        return await self._import_parallel("instances", instances, progress_callback)
```

**B. Register in factory (create_importer function):**

Add to the importers dict:
```python
"instances": InstanceImporter,
```

---

### 4. `src/aap_migration/migration/transformer.py`

**Add to TRANSFORMER_CLASSES dict:**

```python
"instances": DataTransformer,  # No special transformation needed
```

---

### 5. `src/aap_migration/migration/coordinator.py`

**Add instances phase before instance_groups in MIGRATION_PHASES:**

```python
{
    "name": "instances",
    "description": "Instances (AAP Controller Nodes)",
    "resource_types": ["instances"],
    "batch_size": 50,
},
```

---

### 6. `src/aap_migration/cli/commands/migrate.py`

**Update PHASE1_RESOURCE_TYPES:**

Add "instances" before "instance_groups":

```python
PHASE1_RESOURCE_TYPES = [
    "organizations",
    "labels",
    "users",
    "teams",
    "credential_types",
    "credentials",
    "execution_environments",
    "inventories",
    "inventory_sources",
    "inventory_groups",
    "hosts",
    "instances",       # NEW - before instance_groups
    "instance_groups",
    "projects",
]
```

---

### 7. `src/aap_migration/cli/commands/cleanup.py`

**Add special handling for system instances (~line 1174):**

System instances like "localhost", "controlplane", or managed instances should be skipped during cleanup:

```python
elif resource_type == "instances" and (
    is_managed
    or resource_name in ("localhost", "controlplane")
    or resource_id == 1
):
    skip_resource = True
    skip_reason = "system/managed instance"
```

---

## Implementation Checklist

- [x] resources.py: Remove "instances" from READ_ONLY_ENDPOINTS
- [x] resources.py: Add "instances" to RESOURCE_REGISTRY
- [x] exporter.py: Add InstanceExporter class
- [x] exporter.py: Register in create_exporter factory
- [x] importer.py: Add InstanceImporter class
- [x] importer.py: Register in create_importer factory
- [x] transformer.py: Add "instances" to TRANSFORMER_CLASSES
- [x] coordinator.py: Add instances phase before instance_groups
- [x] migrate.py: Add "instances" to PHASE1_RESOURCE_TYPES
- [x] cleanup.py: Add skip logic for system instances

---

## API Reference

### Instances Endpoint

- **List:** `GET /api/controller/v2/instances/`
- **Create:** `POST /api/controller/v2/instances/`
- **Detail:** `GET /api/controller/v2/instances/{id}/`
- **Update:** `PATCH /api/controller/v2/instances/{id}/`
- **Delete:** `DELETE /api/controller/v2/instances/{id}/`

### Key Instance Fields

- `hostname` - The hostname of the instance
- `node_type` - Type of node (control, hybrid, execution, hop)
- `capacity` - Capacity for running jobs
- `enabled` - Whether the instance is enabled
- `managed` - Whether the instance is managed by AAP
