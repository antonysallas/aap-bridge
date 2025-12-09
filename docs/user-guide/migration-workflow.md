# Migration Workflow

This guide explains the complete AAP migration process.

## Overview

AAP Bridge follows an ETL (Export, Transform, Load) pattern:

```text
┌──────────┐    ┌───────────┐    ┌──────────┐    ┌────────┐    ┌──────────┐
│   Prep   │───▶│  Export   │───▶│Transform │───▶│ Import │───▶│ Validate │
└──────────┘    └───────────┘    └──────────┘    └────────┘    └──────────┘

```markdown

## Phase 1: Preparation

```bash
aap-bridge prep

```text

**Purpose:** Analyze both AAP instances and prepare for migration.

**What happens:**

1. Connects to source AAP and fetches API schema
2. Connects to target AAP and fetches API schema
3. Compares schemas to identify field differences
4. Generates transformation rules
5. Saves prep data for subsequent phases

**Output:**

- `prep/source_schema.json` - Source AAP schema
- `prep/target_schema.json` - Target AAP schema
- `prep/schema_comparison.json` - Field differences and transformations

## Phase 2: Export

```bash
aap-bridge export

```text

**Purpose:** Extract all resources from source AAP.

**What happens:**

1. Exports resources in dependency order
2. Handles pagination automatically
3. Splits large datasets into multiple files
4. Tracks export progress in state database

**Export Order:**

| Order | Resources |
| --- | --- |
| 1 | Organizations |
| 2 | Labels |
| 3 | Users, Teams |
| 4 | Credential Types, Credentials |
| 5 | Execution Environments |
| 6 | Inventories |
| 7 | Inventory Sources, Inventory Groups |
| 8 | Hosts |
| 9 | Instances, Instance Groups |
| 10 | Projects |
| 11 | Job Templates |
| 12 | Workflow Job Templates |
| 13 | Schedules |

**Output Structure:**

```text
exports/
├── metadata.json
├── organizations/
│   └── organizations_0001.json
├── inventories/
│   ├── inventories_0001.json
│   └── inventories_0002.json
└── hosts/
    ├── hosts_0001.json
    ├── hosts_0002.json
    └── hosts_0003.json

```markdown

## Phase 3: Transform

```bash
aap-bridge transform

```text

**Purpose:** Apply schema transformations for target AAP version.

**What happens:**

1. Reads exported data
2. Applies field mappings from schema comparison
3. Removes deprecated fields
4. Adds new required fields with defaults
5. Validates transformed data

**Transformations applied:**

- Field renames (e.g., API changes between versions)
- Type conversions
- Default value injection for new required fields
- Removal of read-only fields

## Phase 4: Import

```bash
aap-bridge import

```text

**Purpose:** Load transformed data into target AAP.

**What happens:**

1. Creates resources in dependency order
2. Resolves foreign key references using ID mappings
3. Uses bulk APIs where available (hosts)
4. Handles conflicts (already exists)
5. Tracks progress and creates checkpoints

**Import Features:**

- **Bulk Operations**: Hosts imported 200 at a time
- **Idempotency**: Skips already-migrated resources
- **Conflict Resolution**: Updates or skips existing resources
- **Checkpointing**: Can resume from any failure point

## Phase 5: Validation

```bash
aap-bridge validate

```markdown

**Purpose:** Verify migration success.

**What happens:**

1. Compares resource counts between source and target
2. Validates field values match
3. Checks relationship integrity
4. Generates validation report

## Checkpoint and Resume

### Automatic Checkpoints

Checkpoints are created automatically during import:

- After each resource type completes
- At configurable intervals within large batches

### Viewing Checkpoints

```bash
aap-bridge checkpoint list

```markdown

### Resuming from Failure

```bash
# Resume from last checkpoint
aap-bridge migrate resume

# Resume from specific checkpoint
aap-bridge migrate resume --checkpoint inventories_batch_50

```markdown

## Resource Dependencies

Understanding dependencies is crucial for migration:

```text
Organizations
    ├── Users (member of)
    ├── Teams (belongs to)
    ├── Credentials (owned by)
    ├── Projects (belongs to)
    └── Inventories (belongs to)
            ├── Inventory Sources
            ├── Inventory Groups
            └── Hosts

Credential Types (standalone)
    └── Credentials (uses)

Execution Environments (standalone)

Job Templates
    ├── Project (uses)
    ├── Inventory (uses)
    ├── Credentials (uses)
    └── Execution Environment (uses)

```markdown

## Best Practices

### Before Migration

1. **Backup target AAP** - Always have a rollback plan
2. **Test in staging** - Run migration in a test environment first
3. **Check disk space** - Exports can be large
4. **Verify credentials** - Ensure API tokens have admin access

### During Migration

1. **Monitor progress** - Watch for errors in logs
2. **Don't interrupt bulk operations** - Wait for completion
3. **Use checkpoints** - Resume rather than restart on failure

### After Migration

1. **Validate thoroughly** - Run validation phase
2. **Test functionality** - Run sample job templates
3. **Check RBAC** - Verify user permissions
4. **Update credentials** - Encrypted values need manual setup

## Troubleshooting

See [Troubleshooting Guide](troubleshooting.md) for common issues and solutions.
