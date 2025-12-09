# Quick Start

Get AAP Bridge running in 5 minutes.

## 1. Set Up Environment

Copy the example environment file:

```bash
cp .env.example .env
```text

Edit `.env` with your AAP credentials:

```bash
# Source AAP instance (AAP 2.3/2.4)
SOURCE__URL=https://source-aap.example.com/api/v2
SOURCE__TOKEN=your_source_token

# Target AAP instance (AAP 2.6+ via Platform Gateway)
TARGET__URL=https://target-aap.example.com/api/controller/v2
TARGET__TOKEN=your_target_token

# PostgreSQL state database
MIGRATION_STATE_DB_PATH=postgresql://user:password@localhost:5432/aap_migration
```markdown

!!! warning "Platform Gateway URL"
    For AAP 2.6+, the target URL must use `/api/controller/v2` (Platform
    Gateway), not the direct controller API.

## 2. Validate Configuration

```bash
aap-bridge config validate
```markdown

This checks connectivity to both AAP instances and the database.

## 3. Run Preparation Phase

```bash
aap-bridge prep
```yaml

This:

- Fetches schemas from both AAP instances
- Compares field differences
- Generates transformation rules

## 4. Export from Source

```bash
aap-bridge export
```markdown

Exports all resources from the source AAP to the `exports/` directory.

## 5. Transform Data

```bash
aap-bridge transform
```markdown

Applies schema transformations for the target AAP version.

## 6. Import to Target

```bash
aap-bridge import
```markdown

Imports transformed data to the target AAP.

## 7. Validate Migration

```bash
aap-bridge validate
```markdown

Compares source and target to verify migration success.

## One-Command Migration

For a complete migration in one command:

```bash
aap-bridge migrate full
```dockerfile

This runs all phases sequentially with progress tracking.

## Interactive Mode

Run without arguments for an interactive menu:

```bash
aap-bridge
```markdown

## Next Steps

- [Configuration](configuration.md) - Fine-tune settings for your environment
- [CLI Reference](../user-guide/cli-reference.md) - Explore all available commands
- [Migration Workflow](../user-guide/migration-workflow.md) - Understand the full process
