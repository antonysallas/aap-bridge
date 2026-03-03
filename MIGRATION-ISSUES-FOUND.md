# Critical Migration Issues Discovered

**Date:** 2026-03-03
**Testing:** Live AAP 2.4 → 2.6 migration

---

## ❌ Issue #1: Credentials Cannot Be Migrated

### Root Cause
AAP API returns `"$encrypted$"` for all sensitive credential fields instead of actual values.

### Impact on Your Environment

**Source AAP has 8 credentials:**
1. Demo Credential (SSH) - ❌ Cannot migrate (password/key encrypted)
2. test_A (SSH) - ⚠️ Partial (uses "ASK" prompts)
3. Ansible Galaxy - ✅ Can migrate (no secrets)
4. Automation Hub Validated - ❌ Cannot migrate (token encrypted)
5. Automation Hub Published - ❌ Cannot migrate (token encrypted)
6. Automation Hub RH Certified - ❌ Cannot migrate (token encrypted)
7. Automation Hub Community - ❌ Cannot migrate (token encrypted)
8. Automation Hub Container Registry - ❌ Cannot migrate (password encrypted)

**Result:** 6-7 credentials CANNOT be migrated automatically

### Evidence

```bash
# Exported credential shows encrypted values:
{
  "name": "Automation Hub Container Registry",
  "inputs": {
    "host": "192.168.100.26",
    "username": "admin",
    "password": "$encrypted$",  ← CANNOT RETRIEVE
    "verify_ssl": true
  }
}
```

### Solutions

See: [`docs/CREDENTIAL-MIGRATION-LIMITATION.md`](docs/CREDENTIAL-MIGRATION-LIMITATION.md)

**Quick Options:**
1. **HashiCorp Vault** (recommended for production) - Pre-populate Vault, let AAP retrieve at runtime
2. **Manual Recreation** (recommended for testing) - Recreate 8 credentials by hand (~30-60 minutes)

---

## ❌ Issue #2: Organization Associations Not Migrated

### Root Cause
Organizations migrate, but their **associated credentials** and other relationships do not.

### Impact on Your Environment

**Organization: org_A**

Source AAP:
```
Name: org_A ✅
Description: (empty) ✅
Max Hosts: 0 ✅
Galaxy Credentials: [Ansible Galaxy] ← HAS ASSOCIATION
Default Environment: null ✅
```

Target AAP:
```
Name: org_A ✅
Description: (empty) ✅
Max Hosts: 0 ✅
Galaxy Credentials: [] ← MISSING! ❌
Default Environment: null ✅
```

### Evidence

```bash
# Source org_A has galaxy credential
GET /api/v2/organizations/2/galaxy_credentials/
Result: [{"id": 2, "name": "Ansible Galaxy"}]

# Target org_A has NO galaxy credentials
GET /api/controller/v2/organizations/2/galaxy_credentials/
Result: []  ← MISSING
```

### Why This Happens

1. Migration creates organization ✅
2. Migration does NOT migrate credentials (Issue #1) ❌
3. Organization→Credential association cannot be created because credential doesn't exist ❌

### Cascading Impact

This affects:
- ❌ Galaxy/Automation Hub integration (org can't pull collections)
- ❌ Projects that rely on organization galaxy credentials
- ❌ Job templates that use projects requiring galaxy credentials

---

## ❌ Issue #3: Other Missing Associations (To Be Verified)

### Potentially Affected

Organizations may be missing:
- [ ] Instance Group associations
- [ ] Notification templates
- [ ] Execution environment defaults
- [ ] Custom resource permissions

### Verification Needed

```bash
# Check instance groups
curl -sk "https://localhost:8443/api/v2/organizations/2/instance_groups/"

# Check notification templates
curl -sk "https://localhost:8443/api/v2/organizations/2/notification_templates/"
```

---

## Impact Summary

### What DID Migrate Successfully ✅

| Resource | Status | Notes |
|----------|--------|-------|
| Organizations (structure) | ✅ | Names, descriptions, max_hosts |
| Users (structure) | ✅ | Usernames, emails, roles |
| Teams (structure) | ✅ | Names, organizations |
| Inventories (structure) | ✅ | Names, descriptions |
| Hosts | ⚠️ | Failed due to duplicates (separate issue) |

### What Did NOT Migrate ❌

| Resource | Status | Impact |
|----------|--------|--------|
| Credentials | ❌ CRITICAL | All sensitive fields lost |
| Organization→Credential associations | ❌ CRITICAL | Galaxy/Hub integration broken |
| Credential→Template associations | ❌ CRITICAL | Job templates won't work |
| Project SCM credentials | ❌ HIGH | Projects can't sync |
| Inventory source credentials | ❌ MEDIUM | Dynamic inventories broken |

---

## Real-World Impact

### Before Migration
```
org_A
  ├── Galaxy Credential: "Ansible Galaxy" ✅
  ├── Project: my-playbooks (pulls from git) ✅
  │   └── Uses SSH credential for git access ✅
  └── Job Template: deploy-app ✅
      ├── Uses project: my-playbooks ✅
      ├── Uses credential: test_A (SSH) ✅
      └── Uses inventory: inv_a ✅
```

### After Migration (Current State)
```
org_A
  ├── Galaxy Credential: NONE ❌
  ├── Project: my-playbooks (NOT MIGRATED - depends on credentials) ❌
  └── Job Template: deploy-app (NOT MIGRATED - depends on credentials) ❌
      └── Inventory: inv_a ✅
```

**Result:** Migrated infrastructure is **non-functional** without credentials.

---

## Recommended Fix

### Phase 1: Manual Credential Recreation (REQUIRED)

**Step 1:** Export credential list for reference
```bash
aap-bridge export -r credentials --output creds_backup
cat creds_backup/credentials/*.json | jq -r '.[] | "\(.name) - Type: \(.kind)"' > credential_inventory.txt
```

**Step 2:** Manually recreate each credential in target AAP

Via UI:
1. Log in to https://localhost:10443
2. Resources → Credentials → Add
3. For each of 8 credentials:
   - Enter name, type, organization
   - **Manually enter passwords/tokens/keys** from source
   - Save

**Step 3:** Document new credential IDs
```bash
# After recreation, get new IDs
curl -sk -H "Authorization: Bearer ea023U8zsSXEBuXXZRpiLidAYMT1aT" \
  "https://localhost:10443/api/controller/v2/credentials/" \
  | jq -r '.results[] | "\(.id): \(.name)"' > new_credential_ids.txt
```

**Estimated Time:** 30-60 minutes for 8 credentials

### Phase 2: Associate Credentials to Organizations

**Step 1:** Add galaxy credentials to organizations
```bash
# Associate Ansible Galaxy credential to org_A
curl -sk -X POST \
  -H "Authorization: Bearer ea023U8zsSXEBuXXZRpiLidAYMT1aT" \
  -H "Content-Type: application/json" \
  "https://localhost:10443/api/controller/v2/organizations/2/galaxy_credentials/" \
  -d '{"id": <ansible_galaxy_credential_id>}'
```

**Estimated Time:** 5-10 minutes

### Phase 3: Migrate Remaining Resources

After credentials exist, migrate:
- Projects (will now work with credentials)
- Job Templates (will reference migrated credentials)
- Workflows (will reference migrated templates)

```bash
# Continue migration with remaining resources
aap-bridge migrate -r projects -r job_templates -r workflows
```

**Estimated Time:** 10-30 minutes depending on complexity

---

## Long-Term Solution: HashiCorp Vault

For production environments, implement HashiCorp Vault:

### Benefits
- ✅ Automated credential migration
- ✅ Centralized secret management
- ✅ Audit trail for credential access
- ✅ Rotation without AAP updates
- ✅ Multi-environment support

### Setup
1. Deploy HashiCorp Vault
2. Configure AAP external credential plugin
3. Pre-populate Vault with credentials
4. Update `.env`:
   ```bash
   VAULT__URL=https://vault.example.com
   VAULT__ROLE_ID=xxxxx
   VAULT__SECRET_ID=xxxxx
   ```
5. Run migration with `--use-vault`

**Estimated Setup Time:** 2-4 hours (one-time)

---

## Updated Migration Workflow

### Old (Incorrect) Workflow
1. Export all resources
2. Transform all resources
3. Import all resources
4. ✅ Done

### New (Correct) Workflow
1. Export non-credential resources
2. Transform non-credential resources
3. Import non-credential resources (orgs, users, teams, inventories, hosts)
4. **MANUALLY** recreate all credentials in target AAP
5. **MANUALLY** associate credentials to organizations
6. Export credential-dependent resources (projects, job templates)
7. Transform with updated credential ID mappings
8. Import credential-dependent resources
9. **MANUALLY** verify and test all job templates
10. ✅ Done

**Estimated Total Time:** 2-4 hours for test environment

---

## Action Items

### Immediate (Today)

- [ ] Read [`docs/CREDENTIAL-MIGRATION-LIMITATION.md`](docs/CREDENTIAL-MIGRATION-LIMITATION.md)
- [ ] Decide on credential migration approach (Manual vs Vault)
- [ ] Document where to find original passwords/tokens/keys
- [ ] Create credential inventory spreadsheet

### Before Next Migration Run

- [ ] Manually recreate 8 credentials in target AAP
- [ ] Verify credentials work (test each one)
- [ ] Associate galaxy credentials to organizations
- [ ] Document new credential ID mappings (source_id → target_id)

### During Next Migration

- [ ] Skip credential export (already handled manually)
- [ ] Migrate remaining resources (projects, templates, workflows)
- [ ] Verify credential references in job templates

### After Migration

- [ ] Test job template execution
- [ ] Verify galaxy collection downloads work
- [ ] Test project syncs from SCM
- [ ] Validate dynamic inventory sources

---

## Test Environment Recommendation

**For testing purposes, recommend:**

1. **Clean target AAP completely** (delete all resources including demo data)
2. **Manually create 8 credentials first** (30-60 min)
3. **Run full migration** including credentials in config
4. **Test end-to-end** (project sync → job template run)

This validates the full workflow before production migration.

---

## Production Migration Recommendation

**For production, recommend:**

1. **Deploy HashiCorp Vault** (2-4 hours setup)
2. **Pre-populate Vault with credentials** (1-2 hours)
3. **Configure AAP external credential plugin** (30 min)
4. **Run migration with Vault integration** (2-4 hours)
5. **Verify and test** (1-2 hours)

**Total Production Migration Time:** 1-2 days

---

## Questions to Answer

1. **How many total credentials exist in production?**
   - Test env: 8
   - Production: ???

2. **What credential types are most common?**
   - SSH: 2
   - Galaxy/Hub: 6
   - Other: ???

3. **Is HashiCorp Vault available?**
   - Yes → Use Vault integration
   - No → Manual recreation required

4. **What is acceptable downtime?**
   - Manual: 2-4 hours minimum
   - Vault: Can be near-zero with proper planning

---

## Status: Migration Blocked

**Current State:**
- ✅ Organizations migrated (structure only)
- ✅ Users migrated
- ✅ Teams migrated
- ✅ Inventories migrated (partial - duplicate host issue)
- ❌ Credentials NOT migrated ← BLOCKING
- ❌ Organization associations NOT migrated ← BLOCKING
- ❌ Projects NOT migrated (depend on credentials)
- ❌ Job Templates NOT migrated (depend on credentials)
- ❌ Workflows NOT migrated (depend on templates)

**Next Steps:**
1. Manually recreate credentials
2. Associate credentials to organizations
3. Continue migration for remaining resources

**Estimated Time to Unblock:** 1-2 hours manual work
