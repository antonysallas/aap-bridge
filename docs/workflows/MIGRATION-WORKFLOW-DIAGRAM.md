# AAP Bridge Migration Workflow - Visual Guide

This document provides visual diagrams explaining the AAP Bridge migration workflow with the credential-first approach.

---

## 🎯 High-Level Migration Flow

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        AAP BRIDGE MIGRATION WORKFLOW                       │
│                                                                            │
│  Source AAP 2.4                                                Target AAP 2.6 │
│  (localhost:8443)                                            (localhost:10443) │
└────────────────────────────────────────────────────────────────────────────┘

   ┌─────────────┐
   │   START     │
   └──────┬──────┘
          │
          ▼
   ┌─────────────────────────────────────────────┐
   │  STEP 1: PRE-FLIGHT CREDENTIAL CHECK        │
   │  ─────────────────────────────────────      │
   │  • Fetch all credentials from source        │
   │  • Fetch all credentials from target        │
   │  • Compare by (name, type, organization)    │
   │  • Generate diff report                     │
   │  • Display summary in console               │
   │                                             │
   │  Output: credential-comparison.md           │
   └──────────────────┬──────────────────────────┘
                      │
                      ▼
   ┌─────────────────────────────────────────────┐
   │  STEP 2: PHASE 1 - ORGANIZATIONS            │
   │  ────────────────────────────────           │
   │  • Migrate organizations                    │
   │  • Store ID mappings in database            │
   │  • Create checkpoint                        │
   │                                             │
   │  Status: ✅ 9/9 organizations migrated      │
   └──────────────────┬──────────────────────────┘
                      │
                      ▼
   ┌─────────────────────────────────────────────┐
   │  STEP 3: PHASE 2 - CREDENTIALS ⚠️ CRITICAL │
   │  ──────────────────────────────────────     │
   │  • Migrate credential types                 │
   │  • Migrate ALL credentials                  │
   │  • Verify 100% success before proceeding    │
   │  • Store ID mappings                        │
   │  • Create checkpoint                        │
   │                                             │
   │  Status: ✅ 39/39 credentials migrated      │
   │  Note: MUST complete before Phase 3+        │
   └──────────────────┬──────────────────────────┘
                      │
                      ▼
   ┌─────────────────────────────────────────────┐
   │  STEP 4: PHASES 3-15 - ALL OTHER RESOURCES  │
   │  ────────────────────────────────────────   │
   │  Phase 3:  Credential Input Sources         │
   │  Phase 4:  Identity (Users, Teams, Labels)  │
   │  Phase 5:  Execution Environments           │
   │  Phase 6:  Inventories                      │
   │  Phase 7:  Hosts (bulk operations)          │
   │  Phase 8:  Instances & Instance Groups      │
   │  Phase 9:  Projects                         │
   │  Phase 10: Inventory Configuration          │
   │  Phase 11: Notification Templates           │
   │  Phase 12: Job Templates                    │
   │  Phase 13: Workflows                        │
   │  Phase 14: System Job Templates             │
   │  Phase 15: Schedules                        │
   │                                             │
   │  All phases can safely use credentials      │
   └──────────────────┬──────────────────────────┘
                      │
                      ▼
   ┌─────────────────────────────────────────────┐
   │  STEP 5: POST-MIGRATION VALIDATION          │
   │  ────────────────────────────────────       │
   │  • Validate resource counts                 │
   │  • Check ID mappings                        │
   │  • Verify data integrity                    │
   │  • Generate migration reports               │
   └──────────────────┬──────────────────────────┘
                      │
                      ▼
   ┌─────────────────────────────────────────────┐
   │  STEP 6: RBAC MIGRATION (SEPARATE SCRIPT)   │
   │  ──────────────────────────────────────     │
   │  • Export role assignments from source      │
   │  • Map roles to target resources            │
   │  • Import role assignments to target        │
   │                                             │
   │  Run: python rbac_migration.py              │
   └──────────────────┬──────────────────────────┘
                      │
                      ▼
   ┌─────────────────────────────────────────────┐
   │  COMPLETE ✅                                │
   │  ────────────                               │
   │  All resources migrated                     │
   │  Reports generated                          │
   │  System ready for production                │
   └─────────────────────────────────────────────┘
```

---

## 🔐 Credential-First Workflow Detail

```
┌────────────────────────────────────────────────────────────────────────────┐
│                     CREDENTIAL COMPARISON & MIGRATION                      │
└────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐         ┌─────────────────┐
│  Source AAP     │         │  Target AAP     │
│  (2.4)          │         │  (2.6)          │
└────────┬────────┘         └────────┬────────┘
         │                           │
         ├──── Fetch Credentials ────┤
         │                           │
         ▼                           ▼
   [53 credentials]           [48 credentials]
         │                           │
         └────────┬──────────────────┘
                  │
                  ▼
         ┌────────────────────┐
         │  COMPARISON ENGINE │
         │  ─────────────────  │
         │  Match by:          │
         │  • Name             │
         │  • Type             │
         │  • Organization     │
         └────────┬───────────┘
                  │
                  ├──────────────────┬──────────────────┐
                  ▼                  ▼                  ▼
          ┌──────────────┐   ┌──────────────┐  ┌──────────────┐
          │   MATCHED    │   │   MISSING    │  │   SKIPPED    │
          │   13 creds   │   │   39 creds   │  │   1 managed  │
          │              │   │              │  │              │
          │ Store ID     │   │ Need to      │  │ System       │
          │ mappings     │   │ migrate      │  │ credentials  │
          └──────────────┘   └──────┬───────┘  └──────────────┘
                                    │
                                    ▼
                          ┌─────────────────────┐
                          │  GENERATE REPORT    │
                          │  ──────────────────  │
                          │  • credential-      │
                          │    comparison.md    │
                          │  • Console summary  │
                          │  • Missing cred     │
                          │    details          │
                          └─────────┬───────────┘
                                    │
                                    ▼
                          ┌─────────────────────┐
                          │  USER REVIEW        │
                          │  ──────────────      │
                          │  Review report and  │
                          │  proceed with       │
                          │  migration          │
                          └─────────┬───────────┘
                                    │
                                    ▼
                          ┌─────────────────────┐
                          │  MIGRATE PHASE 2    │
                          │  ───────────────     │
                          │  1. Organizations   │
                          │  2. Credential Types│
                          │  3. Credentials     │
                          │     (39 missing)    │
                          │                     │
                          │  Result: 39/39 ✅   │
                          └─────────┬───────────┘
                                    │
                                    ▼
                          ┌─────────────────────┐
                          │  VERIFY SUCCESS     │
                          │  ──────────────      │
                          │  • All creds        │
                          │    migrated         │
                          │  • ID mappings      │
                          │    stored           │
                          │  • 0 failures       │
                          └─────────┬───────────┘
                                    │
                                    ▼
                          ┌─────────────────────┐
                          │  PROCEED TO         │
                          │  PHASES 3+          │
                          │                     │
                          │  Credentials ready! │
                          └─────────────────────┘
```

---

## 📊 Migration Phase Timeline

```
Timeline View - Shows when each phase executes
═══════════════════════════════════════════════════════════════════════════

Time 0s ──────────────────────────────────────────────────────────── Start
  │
  ├─ [Pre-Flight Check] Credential Comparison (2 seconds)
  │   └─ Output: credential-comparison.md
  │
Time 2s
  │
  ├─ [Phase 1] Organizations (7.5 seconds)
  │   • 9 organizations
  │   • Rate: 1.2/sec
  │   • Checkpoint created
  │
Time 10s
  │
  ├─ [Phase 2] Credentials ⚠️ CRITICAL (36 seconds)
  │   • 39 credentials
  │   • Rate: 1.1/sec
  │   • 100% success required
  │   • Checkpoint created
  │   └─ BLOCK: Must complete before proceeding
  │
Time 46s ──── CREDENTIAL GATE ────────────────────────────────────────
  │            ✅ All credentials ready
  │            ✅ Dependent resources can proceed
  │
  ├─ [Phase 3] Credential Input Sources (2 seconds)
  │   • 4 credential input sources
  │   • Rate: 1.8/sec
  │
Time 48s
  │
  ├─ [Phase 4] Identity - Users, Teams, Labels (variable)
  │   • Users: 23
  │   • Teams: 11
  │   • Labels: variable
  │
  ├─ [Phase 5] Execution Environments (variable)
  │
  ├─ [Phase 6] Inventories (variable)
  │   • Uses bulk operations
  │   • Batch size: 200
  │
  ├─ [Phase 7] Hosts (variable)
  │   • Uses bulk operations
  │   • Batch size: 200 (API maximum)
  │   • Can handle 80,000+ hosts
  │
  ├─ [Phases 8-15] Remaining Resources
  │   • Instances & Instance Groups
  │   • Projects
  │   • Inventory Configuration
  │   • Notification Templates
  │   • Job Templates
  │   • Workflows
  │   • System Job Templates
  │   • Schedules
  │
Time Varies ───────────────────────────────────────────────────── Complete
```

---

## 🔄 State Management & ID Mapping Flow

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         ID MAPPING & STATE TRACKING                        │
└────────────────────────────────────────────────────────────────────────────┘

Source AAP                Migration State DB              Target AAP
─────────                 ──────────────────              ──────────

┌─────────────┐          ┌──────────────────┐          ┌─────────────┐
│ Credential  │          │                  │          │ Credential  │
│ ID: 51      │──export─▶│  Store Mapping   │◀─import──│ ID: 75      │
│ Name: Test  │          │  ──────────────   │          │ Name: Test  │
│ Type: SSH   │          │  source_id: 51   │          │ Type: SSH   │
│ Org: Eng    │          │  target_id: 75   │          │ Org: Eng    │
└─────────────┘          │  name: Test      │          └─────────────┘
                         │  type: creds     │
                         │                  │
                         │  Database Tables:│
                         │  ───────────────  │
                         │  • id_mappings   │
                         │  • checkpoints   │
                         │  • metadata      │
                         │  • progress      │
                         └──────────────────┘

Flow:
─────
1. Export: Read credential from source (ID: 51)
2. Transform: Prepare for target (map dependencies)
3. Import: Create in target (receives ID: 75)
4. Store: Save mapping (51 → 75) in database
5. Reuse: Later resources use mapping to reference credential

Example Dependency Resolution:
────────────────────────────
Project needs Credential ID 51 (from source)
  ↓
Migration tool queries: SELECT target_id FROM id_mappings
                       WHERE resource_type='credentials' AND source_id=51
  ↓
Returns: target_id = 75
  ↓
Project migrated with credential_id: 75 (target)
```

---

## 🎨 Credential Comparison Report Structure

```
┌────────────────────────────────────────────────────────────────────────────┐
│                   CREDENTIAL COMPARISON REPORT                             │
│                   credential-comparison.md                                 │
└────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ SUMMARY SECTION                                                          │
├──────────────────────────────────────────────────────────────────────────┤
│ Total Source Credentials: 53                                             │
│ Total Target Credentials: 48                                             │
│ Matching Credentials: 13                                                 │
│ Missing in Target: 39                                                    │
│ Managed Credentials (Skipped): 1                                         │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ MISSING CREDENTIALS TABLE                                                │
├────────┬──────────────────────┬─────────────────┬──────────────┬─────────┤
│ Src ID │ Name                 │ Type            │ Organization │ Desc    │
├────────┼──────────────────────┼─────────────────┼──────────────┼─────────┤
│   51   │ REGRESSION_TEST_...  │ Machine         │ Engineering  │ Test... │
│   52   │ REGRESSION_TEST_...  │ Source Control  │ Global Eng   │ Test... │
│   53   │ REGRESSION_TEST_...  │ AWS             │ Default      │ Test... │
│  ...   │ ...                  │ ...             │ ...          │ ...     │
└────────┴──────────────────────┴─────────────────┴──────────────┴─────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ DETAILED CREDENTIAL INFORMATION                                          │
├──────────────────────────────────────────────────────────────────────────┤
│ 1. REGRESSION_TEST_Machine_Cred_001                                      │
│    • Source ID: 51                                                       │
│    • Type: Machine (ID: 1)                                               │
│    • Organization: Engineering (ID: 4)                                   │
│    • Inputs: ['username', 'password', 'become_method']                   │
│    • Note: Secret values will show as $encrypted$ after migration        │
│                                                                          │
│ 2. REGRESSION_TEST_Git_Cred_002                                          │
│    • Source ID: 52                                                       │
│    • Type: Source Control (ID: 2)                                        │
│    • Organization: Global Engineering (ID: 5)                            │
│    • Inputs: ['username', 'password']                                    │
│    • Note: Secret values will show as $encrypted$ after migration        │
│                                                                          │
│ [... continues for all missing credentials ...]                         │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ NEXT STEPS                                                               │
├──────────────────────────────────────────────────────────────────────────┤
│ 1. Review missing credentials above                                      │
│ 2. Run migration to create missing credentials                           │
│ 3. Note: Secret values will need manual entry (API returns $encrypted$) │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Command Workflow Examples

### Example 1: First-Time Migration

```bash
# Step 1: Compare credentials first
$ aap-bridge credentials compare

Output:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CREDENTIAL COMPARISON RESULTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Source Credentials: 53
Target Credentials: 48
Missing in Target: 39

Detailed report: ./reports/credential-comparison.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Step 2: Review the report
$ cat ./reports/credential-comparison.md

# Step 3: Run full migration (credentials will be migrated first)
$ aap-bridge migrate full

Output:
┌─ Phase 1: Organizations ─────────────────────┐
│ 9/9    1.2/s    Err:0    Skip:0    7.5s     │
└──────────────────────────────────────────────┘
┌─ Phase 2: Credentials (CRITICAL) ────────────┐
│ 39/39  1.1/s    Err:0    Skip:0    36.3s    │
└──────────────────────────────────────────────┘
┌─ Phase 3: Credential Input Sources ──────────┐
│ 4/4    1.8/s    Err:0    Skip:0    2.2s     │
└──────────────────────────────────────────────┘
[... continues ...]
```

### Example 2: Credentials Only Migration

```bash
# Migrate just credentials (useful for troubleshooting)
$ aap-bridge credentials migrate

Output:
Phase 1: Comparing credentials...
Found 39 missing credentials

Phase 2: Migrating credentials...
✓ Migrated organizations (dependency)
✓ Migrated credential types (dependency)
✓ Migrated credentials (39/39)

Credential Migration Complete!
Resources Exported: 18
Resources Imported: 18
Resources Failed: 0
```

### Example 3: Dry Run

```bash
# Test migration without making changes
$ aap-bridge credentials migrate --dry-run

Output:
DRY RUN MODE - No changes will be made

Found 39 missing credentials
Would migrate:
  • 9 organizations
  • 35 credential types
  • 39 credentials

No resources actually created (dry run)
```

---

## 📈 Success Metrics Dashboard

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        MIGRATION HEALTH DASHBOARD                          │
└────────────────────────────────────────────────────────────────────────────┘

Phase Completion Status:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 1: Organizations              [████████████████████] 100% (9/9)
Phase 2: Credentials ⚠️ CRITICAL    [████████████████████] 100% (39/39)
Phase 3: Credential Input Sources   [████████████████████] 100% (4/4)
Phase 4: Identity                   [████████████████████] 100% (34/34)
Phase 5: Execution Environments     [████████████████████] 100% (15/15)
Phase 6: Inventories                [████████████████████] 100% (10/10)
Phase 7: Hosts                      [████████████████████] 100% (21/21)
...

Resource Migration Statistics:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Resources Exported:    234
Total Resources Imported:    234
Total Resources Failed:      0
Total Resources Skipped:     0
Success Rate:                100%

Credential-Specific Metrics:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Credentials in Source:       53
Credentials in Target:       53 (after migration)
Credentials Missing:         0
Credentials Migrated:        39 (structure only)
Success Rate:                Structure migrated successfully
Migration Time:              36.3 seconds
Processing Rate:             1.1 creds/second

⚠️ Note: Secret values require manual update in target AAP

ID Mapping Statistics:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Organizations:               9 mappings
Credentials:                 53 mappings
Users:                       23 mappings
Teams:                       11 mappings
Inventories:                 10 mappings
Projects:                    7 mappings
Job Templates:               15 mappings
Total Mappings:              234
```

---

## 🔧 Troubleshooting Flow

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         TROUBLESHOOTING GUIDE                              │
└────────────────────────────────────────────────────────────────────────────┘

Issue: All credentials show as missing
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ↓
Check: State database empty?
   ├─ Yes → Run: aap-bridge credentials compare
   │         (This will populate ID mappings)
   └─ No  → Check credential matching logic

Issue: Credential migration fails
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ↓
Check error type:
   ├─ Dependency error → Ensure organizations migrated first
   ├─ Type mismatch   → Check credential type mappings
   └─ API error       → Check logs: logs/migration.log

Issue: Secrets don't work after migration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ↓
Expected behavior! AAP API returns $encrypted$ for secrets
   ↓
Solution:
   1. Go to target AAP Web UI
   2. Edit credential
   3. Enter actual secret values
   4. Save

Issue: Migration stuck on credentials phase
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ↓
Check:
   1. API timeout settings (.env: TARGET__TIMEOUT)
   2. Network connectivity
   3. Target AAP performance (check logs)
   4. Reduce batch size (config.yaml)

Need Help?
━━━━━━━━━
   • Check: CREDENTIAL-FIRST-WORKFLOW.md
   • Review: logs/migration.log
   • Check: ./reports/credential-comparison.md
   • Run: aap-bridge credentials report
```

---

## 📚 Related Documentation

- **[CREDENTIAL-FIRST-WORKFLOW.md](CREDENTIAL-FIRST-WORKFLOW.md)** - Complete user guide
- **[QUICK-START.md](../../QUICK-START.md)** - Quick reference
- **[IMPLEMENTATION-COMPLETE.md](../development/implementation/IMPLEMENTATION-COMPLETE.md)** - Technical details
- **[REGRESSION-TEST-RESULTS.md](../development/test-results/REGRESSION-TEST-RESULTS.md)** - Test validation
- **[FULL-MIGRATION-TEST-RESULTS.md](../development/test-results/FULL-MIGRATION-TEST-RESULTS.md)** - Full workflow test

---

**Last Updated:** 2026-03-23
**Version:** 0.2.0
**Status:** Production Ready ✅
