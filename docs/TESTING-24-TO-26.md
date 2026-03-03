# Testing AAP 2.4 → 2.6 Migration

This guide provides step-by-step instructions for testing the AAP Bridge migration tool with your AAP 2.4 (source) and AAP 2.6 (target) instances.

## Prerequisites Checklist

Before starting, verify you have:

- ✅ AAP 2.4 instance accessible (source)
- ✅ AAP 2.6 instance accessible (target)
- ✅ Admin access tokens for both instances
- ✅ Python 3.12+ installed
- ✅ Network connectivity from your machine to both AAP instances
- ✅ At least 8GB RAM (for large migrations)
- ✅ Sufficient disk space (~500MB for state database + exports)

## Phase 1: Environment Setup (10 minutes)

### Step 1.1: Clone and Setup Repository

```bash
# Clone the repository and checkout the 24-to-26 branch
git clone https://github.com/antonysallas/aap-bridge.git
cd aap-bridge
git checkout 24-to-26

# Create virtual environment
uv venv --seed --python 3.12
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv sync
```

### Step 1.2: Verify Installation

```bash
# Verify aap-bridge command is available
aap-bridge --help

# Should show:
# Usage: aap-bridge [OPTIONS] COMMAND [ARGS]...
# Commands:
#   migrate  Migrate resources from source to target
#   export   Export resources from source
#   import   Import resources to target
#   prep     Discover endpoints and generate schemas
#   ...
```

### Step 1.3: Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your AAP instance details
nano .env  # or vim, code, etc.
```

Update the following variables in `.env`:

```bash
# ============================================================================
# Source AAP 2.4 Configuration
# ============================================================================
SOURCE__URL=https://aap24.example.com/api/v2
SOURCE__TOKEN="your-source-token-here"
SOURCE__VERIFY_SSL=false  # Set to true if using valid SSL cert
SOURCE__TIMEOUT=30

# ============================================================================
# Target AAP 2.6 Configuration
# ============================================================================
# CRITICAL: Must include /api/controller/v2 for Platform Gateway
TARGET__URL=https://aap26.example.com/api/controller/v2
TARGET__TOKEN="your-target-token-here"
TARGET__VERIFY_SSL=false  # Set to true if using valid SSL cert
TARGET__TIMEOUT=30

# ============================================================================
# State Database (SQLite - Default)
# ============================================================================
# Uses local file - no database server required!
MIGRATION_STATE_DB_PATH=sqlite:///./migration_state.db

# ============================================================================
# HashiCorp Vault (Optional - Skip for Testing)
# ============================================================================
# Leave commented out unless you're testing credential migration
# VAULT__URL=https://vault.example.com
# VAULT__ROLE_ID=xxxxx
# VAULT__SECRET_ID=xxxxx
```

### Step 1.4: Obtain AAP Access Tokens

#### For AAP 2.4 (Source):
```bash
# Via UI:
# 1. Log in to AAP 2.4
# 2. Go to: User Icon (top right) → Tokens
# 3. Click "Add"
# 4. Scope: Write
# 5. Copy the token

# Via CLI (if awx CLI is configured):
awx login -h https://aap24.example.com
awx tokens create --scope write
```

#### For AAP 2.6 (Target):
```bash
# Via UI:
# 1. Log in to AAP 2.6
# 2. Go to: Access → Users → [Your User] → Tokens
# 3. Click "Create token"
# 4. Scope: Write
# 5. Copy the token
```

## Phase 2: Connectivity & Version Detection (5 minutes)

### Step 2.1: Test Connectivity

```bash
# Run prep command to verify connectivity and detect versions
aap-bridge prep --output test_prep/
```

**Expected Output:**
```
✓ Connecting to aap24.example.com and aap26.example.com
✓ Detecting AAP versions (Source: 2.4.x, Target: 2.6.x)
✓ Discovering endpoints
✓ Generating schemas
✓ Comparing schemas

Prep completed successfully! Results saved to: test_prep/
```

### Step 2.2: Verify Version Detection

```bash
# Check the log for version detection
grep "aap_version_detected" logs/migration.log

# Should show something like:
# aap_version_detected version=2.4.1 url=https://aap24.example.com/api/v2
# aap_version_detected version=2.6.0 url=https://aap26.example.com/api/controller/v2
```

### Step 2.3: Review Schema Comparison

```bash
# View schema differences between source and target
cat test_prep/schema_comparison.json | jq .

# This shows:
# - Fields removed in 2.6
# - Fields added in 2.6
# - Type changes
# - Required field changes
```

**Troubleshooting:**

| Error | Cause | Solution |
|-------|-------|----------|
| `Connection refused` | AAP instance not accessible | Check URL, firewall, VPN |
| `401 Unauthorized` | Invalid token | Regenerate token, check expiration |
| `SSL certificate verify failed` | Self-signed cert | Set `VERIFY_SSL=false` |
| `No route to host` | Network issue | Check connectivity, DNS |
| `Version below minimum` | Old AAP version | Upgrade source to 2.3+ |

## Phase 3: Test Migration - Small Dataset (20 minutes)

### Step 3.1: Identify Test Resources

First, check what resources exist in your source AAP 2.4:

```bash
# Count resources in source
curl -k -H "Authorization: Bearer $SOURCE__TOKEN" \
  "https://aap24.example.com/api/v2/organizations/" | jq '.count'

curl -k -H "Authorization: Bearer $SOURCE__TOKEN" \
  "https://aap24.example.com/api/v2/inventories/" | jq '.count'

curl -k -H "Authorization: Bearer $SOURCE__TOKEN" \
  "https://aap24.example.com/api/v2/hosts/" | jq '.count'
```

**For initial testing, choose a small subset:**
- 1-2 Organizations
- 2-5 Inventories
- 10-50 Hosts
- A few job templates

### Step 3.2: Create Test Filter (Optional)

To migrate only specific resources, create `config/test_filter.yaml`:

```yaml
# Only migrate specific organizations
organizations:
  - name: "Test Organization"

# Only migrate inventories from test org
inventories:
  organization: "Test Organization"
```

### Step 3.3: Run Test Migration

```bash
# Dry run first (no actual changes)
aap-bridge migrate full \
  --config config/config.yaml \
  --dry-run

# Review what would be migrated
# If looks good, run actual migration
aap-bridge migrate full \
  --config config/config.yaml

# Monitor progress - you'll see:
# [Phase 1] Migrating Organizations: 100% |████████| 1/1
# [Phase 2] Migrating Credential Types: 100% |████████| 27/27
# [Phase 3] Migrating Projects: 100% |████████| 5/5
# [Phase 4] Migrating Inventories: 100% |████████| 3/3
# [Phase 5] Migrating Hosts: 100% |████████| 25/25
# ...
```

### Step 3.4: Verify SQLite Database

```bash
# Check that SQLite database was created
ls -lh migration_state.db

# Should show something like:
# -rw-r--r--  1 user  staff   2.5M Mar  3 20:00 migration_state.db

# View database contents (requires sqlite3)
sqlite3 migration_state.db "SELECT COUNT(*) FROM id_mappings;"
# Shows number of ID mappings created

sqlite3 migration_state.db "SELECT resource_type, COUNT(*) FROM id_mappings GROUP BY resource_type;"
# Shows breakdown by resource type:
# organizations|1
# inventories|3
# hosts|25
```

### Step 3.5: Validate Migration

```bash
# Run validation to compare source and target
aap-bridge validate all --sample-size 100

# Expected output:
# Validating Organizations: ✓ 1/1 matched
# Validating Inventories: ✓ 3/3 matched
# Validating Hosts: ✓ 25/25 matched
# Validation Summary: 29/29 resources matched (100%)
```

### Step 3.6: Manual Verification

Log in to both AAP instances and verify:

**Source AAP 2.4:**
```bash
# Check organization exists
https://aap24.example.com/#/organizations

# Note the organization name, inventory names, host counts
```

**Target AAP 2.6:**
```bash
# Check organization was created
https://aap26.example.com/#/organizations

# Verify inventories exist under the organization
# Verify host counts match
# Check job templates were created
```

## Phase 4: Test Idempotency (10 minutes)

### Step 4.1: Re-run Migration

```bash
# Run migration again - should detect existing resources
aap-bridge migrate full --config config/config.yaml

# Expected output:
# [Phase 1] Migrating Organizations: Already migrated (skipped)
# [Phase 2] Migrating Inventories: Already migrated (skipped)
# [Phase 3] Migrating Hosts: Already migrated (skipped)
# Migration completed: 0 created, 29 skipped (already exist)
```

### Step 4.2: Verify No Duplicates

```bash
# Check target AAP for duplicate resources
curl -k -H "Authorization: Bearer $TARGET__TOKEN" \
  "https://aap26.example.com/api/controller/v2/organizations/" | jq '.results[] | .name'

# Should show each organization only once
```

## Phase 5: Test Resume Capability (15 minutes)

### Step 5.1: Simulate Interruption

```bash
# Start a migration and interrupt it (Ctrl+C after a few seconds)
aap-bridge migrate full --config config/config.yaml
# Press Ctrl+C after Phase 2 starts

# Check the checkpoint that was created
aap-bridge checkpoint list

# Should show something like:
# Checkpoint: phase2_credentials_batch_50
# Created: 2026-03-03 20:15:30
# Status: Valid
```

### Step 5.2: Resume Migration

```bash
# Resume from last checkpoint
aap-bridge migrate resume

# Expected output:
# Resuming from checkpoint: phase2_credentials_batch_50
# [Phase 2] Migrating Credentials: 50% |████▌    | 25/50 (resuming...)
# [Phase 3] Migrating Projects: 0% |         | 0/5
# ...
```

### Step 5.3: Verify State Persistence

```bash
# Check state database for checkpoint info
sqlite3 migration_state.db "SELECT * FROM checkpoints ORDER BY created_at DESC LIMIT 5;"

# Shows recent checkpoints with metadata
```

## Phase 6: Test Large Dataset Migration (Optional - 1-2 hours)

If your AAP 2.4 instance has a large dataset (thousands of hosts):

### Step 6.1: Configure for Large Scale

Edit `config/config.yaml`:

```yaml
performance:
  # Increase batch sizes for faster migration
  batch_sizes:
    hosts: 200  # Maximum for bulk operations
    inventories: 200
    projects: 100

  # Increase concurrency
  max_concurrent: 20
  rate_limit: 25

  # Enable parallel export (experimental)
  parallel_resource_types: true
  max_concurrent_types: 5
```

### Step 6.2: Monitor Performance

```bash
# Run migration with stats
aap-bridge migrate full \
  --config config/config.yaml \
  --show-stats

# Watch resource usage
watch -n 1 'ps aux | grep aap-bridge'
watch -n 1 'ls -lh migration_state.db'
```

### Step 6.3: Performance Metrics

Expected rates for large migrations:
- Organizations: ~100/minute
- Inventories: ~50/minute
- Hosts: ~2,000/minute (using bulk operations)
- Job Templates: ~30/minute

Example for 10,000 hosts:
- Phase 1 (Orgs, Users): ~5 minutes
- Phase 2 (Credentials): ~10 minutes
- Phase 3 (Projects): ~5 minutes
- Phase 4 (Inventories): ~2 minutes
- Phase 5 (Hosts): ~5 minutes (bulk operations)
- Phase 6 (Job Templates): ~10 minutes
- **Total: ~40 minutes**

## Phase 7: Test Error Handling

### Step 7.1: Test Network Interruption

```bash
# Start migration
aap-bridge migrate full --config config/config.yaml

# Disconnect network briefly (via UI or firewall)
# Wait 30 seconds
# Reconnect network

# Tool should:
# 1. Retry failed requests (exponential backoff)
# 2. Log warnings about retries
# 3. Eventually succeed or fail gracefully
```

### Step 7.2: Test Invalid Credentials

```bash
# Temporarily break the target token
export TARGET__TOKEN="invalid-token"

# Try to migrate
aap-bridge migrate full --config config/config.yaml

# Expected output:
# Error: Authentication failed for target AAP
# 401 Unauthorized: Invalid token
# Migration aborted.

# Fix token and retry
export TARGET__TOKEN="valid-token-here"
aap-bridge migrate full --config config/config.yaml
# Should resume and complete
```

### Step 7.3: Test Platform Gateway Overload

```bash
# Set very high concurrency to test gateway limits
aap-bridge migrate full \
  --config config/config.yaml \
  --max-concurrent 100

# Should hit Platform Gateway limits and see:
# Warning: Platform Gateway overloaded (502 Bad Gateway)
# Retrying with exponential backoff...
#
# Tool automatically reduces concurrency and retries
```

## Common Issues & Solutions

### Issue 1: "Version X.Y.Z is below minimum supported version"

**Cause:** Source AAP is older than 2.3.0 or target is older than 2.5.0

**Solution:**
```bash
# Check actual versions
curl -k https://aap24.example.com/api/v2/config/ | jq '.version'
curl -k https://aap26.example.com/api/controller/v2/config/ | jq '.version'

# Upgrade AAP instances if needed
```

### Issue 2: "Database is locked"

**Cause:** Multiple aap-bridge processes running

**Solution:**
```bash
# Kill other processes
ps aux | grep aap-bridge
kill <pid>

# Or restart from clean state
rm migration_state.db
aap-bridge migrate full --config config/config.yaml
```

### Issue 3: "Platform Gateway: no healthy upstream"

**Cause:** Target AAP 2.6 Platform Gateway overloaded

**Solution:**
```bash
# Reduce concurrency in config/config.yaml
performance:
  max_concurrent: 10  # Lower from 20
  cleanup_job_cancel_concurrency: 10  # Lower from 25
  rate_limit: 15  # Lower from 25

# Retry migration
aap-bridge migrate full --config config/config.yaml
```

### Issue 4: "Credential type not found"

**Cause:** Custom credential types don't exist in target

**Solution:**
```bash
# List custom credential types in source
curl -k -H "Authorization: Bearer $SOURCE__TOKEN" \
  "https://aap24.example.com/api/v2/credential_types/?managed=false"

# Manually create them in target AAP 2.6 first
# Then re-run migration
```

### Issue 5: SSH keys show as "$encrypted$"

**Cause:** AAP API cannot export encrypted credential fields

**Solution:**
This is expected and documented. Two options:
1. Set up HashiCorp Vault and pre-populate with credentials
2. Manually recreate credentials in target AAP after migration

## Success Criteria

Your migration is successful if:

✅ **All tests pass:**
```bash
source .venv/bin/activate
python -m pytest tests/unit/ -v
# 41 tests should pass
```

✅ **Prep succeeds:**
```bash
aap-bridge prep --output test_prep/
# Shows: ✓ Detecting AAP versions (Source: 2.4.x, Target: 2.6.x)
```

✅ **Migration completes without errors:**
```bash
aap-bridge migrate full --config config/config.yaml
# Shows: Migration completed successfully!
```

✅ **Validation passes:**
```bash
aap-bridge validate all --sample-size 100
# Shows: 100% matched
```

✅ **Idempotency works:**
```bash
# Re-run migration
aap-bridge migrate full --config config/config.yaml
# Shows: 0 created, N skipped (already exist)
```

✅ **SQLite database created:**
```bash
ls -lh migration_state.db
# File exists and has reasonable size (few MB)
```

✅ **Target AAP has resources:**
- Log in to AAP 2.6
- Verify organizations, inventories, hosts exist
- Verify job templates work
- Verify credentials exist (may need manual recreation)

## Next Steps

After successful testing:

1. **Document your findings**
   - Note any issues encountered
   - Record performance metrics
   - List any manual steps required

2. **Plan production migration**
   - Schedule maintenance window
   - Prepare rollback plan
   - Set up monitoring

3. **Create backup before production**
   ```bash
   # Backup source AAP configuration
   awx-manage dumpdata > source_aap_backup.json

   # Backup SQLite state database
   cp migration_state.db migration_state_backup.db
   ```

4. **Run production migration**
   - Follow same steps as testing
   - Monitor closely
   - Validate thoroughly

## Getting Help

If you encounter issues during testing:

1. **Check logs:**
   ```bash
   tail -f logs/migration.log
   ```

2. **Enable debug logging:**
   ```bash
   export AAP_BRIDGE_LOG_LEVEL=DEBUG
   aap-bridge migrate full --config config/config.yaml
   ```

3. **File an issue:**
   - https://github.com/antonysallas/aap-bridge/issues
   - Include: AAP versions, error messages, relevant logs

4. **Review documentation:**
   - `docs/24-to-26-migration-support.md`
   - `docs/state-storage-alternatives.md`
   - `docs/postgresql-to-sqlite-migration.md`
