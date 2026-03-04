# RBAC Migration Guide

This guide explains how to migrate RBAC (Role-Based Access Control) role assignments from AAP 2.4 to AAP 2.6.

---

## What Was Already Fixed

✅ **System Auditor Flags** - Already restored for:
- `arnav_b` - System Auditor restored
- `kevin.audit` - System Auditor restored

---

## What Needs To Be Migrated

The RBAC migration script (`rbac_migration.py`) will migrate:

1. **Organization Roles:**
   - Organization Admin
   - Organization Member
   - Organization Auditor
   - Organization Execute
   - Organization Read

2. **Team Roles:**
   - Team Admin
   - Team Member
   - Team Read

3. **Resource-Level Roles:**
   - Project Admin/Read/Use
   - Inventory Admin/Read/Use/Adhoc
   - Job Template Admin/Read/Execute
   - Credential Admin/Read/Use
   - Workflow Admin/Read/Execute

---

## Prerequisites

1. **Python Requirements:**
   ```bash
   # Install required packages
   pip install requests
   ```

2. **Environment Variables:**
   ```bash
   # Set in your shell or add to .env
   export SOURCE__TOKEN="ENOBFlD2GAB2LmCD5P2RqsTEOjbrlA"
   export TARGET__TOKEN="ea023U8zsSXEBuXXZRpiLidAYMT1aT"
   ```

3. **Migration State Database:**
   - The script uses `migration_state.db` to map source IDs to target IDs
   - Make sure this file exists (created during main migration)

---

## How to Run

### Option 1: Automatic (Recommended)

```bash
cd /Users/arbhati/project/git/aap-bridge-fork

# Load environment variables
source .env

# Run the migration script
python rbac_migration.py
```

### Option 2: With Explicit Tokens

```bash
# Export tokens
export SOURCE__TOKEN="ENOBFlD2GAB2LmCD5P2RqsTEOjbrlA"
export TARGET__TOKEN="ea023U8zsSXEBuXXZRpiLidAYMT1aT"

# Run migration
python rbac_migration.py
```

---

## What the Script Does

### Phase 1: Initialization
1. Loads ID mappings from `migration_state.db`
2. Connects to source and target AAP instances
3. Sets up retry logic for API calls

### Phase 2: Export
1. Fetches all users from source AAP (23 users)
2. For each user, fetches their role assignments
3. Collects role details (name, resource type, resource name)

### Phase 3: ID Mapping
1. Maps source resource IDs to target IDs using state DB
2. For missing mappings, discovers target IDs by resource name
3. Validates that target resources exist

### Phase 4: Import
1. For each role assignment:
   - Finds the equivalent resource in target AAP
   - Gets the resource's available roles
   - Assigns the matching role to the user
2. Handles duplicates gracefully (skips if already assigned)

### Phase 5: Verification
1. Counts successful vs failed role assignments
2. Reports errors and missing resources
3. Provides success rate statistics

---

## Expected Output

```
======================================================================
   AAP RBAC MIGRATION
======================================================================

📊 Loading ID mappings from state database...
   - organizations: 9 mappings
   - users: 23 mappings
   - teams: 11 mappings
   - projects: 7 mappings
   - inventories: 2 mappings
✅ Loaded 52 ID mappings

📥 Fetching users from source AAP...
✅ Found 23 users

🔄 Migrating roles for 23 users...
----------------------------------------------------------------------

1/23: admin
   👤 admin: 16 roles
      - Admin on Default... ✅
      - Member on Global Engineering... ✅
      - Admin on Production Infrastructure... ✅
      ...
      Result: 15/16 roles migrated

2/23: arnav
   👤 arnav: 2 roles
      - Member on Default... ✅
      - Member on org_A... ✅
      Result: 2/2 roles migrated

3/23: arnav_b
   ℹ️  arnav_b: No roles to migrate

4/23: kevin.audit
   👤 kevin.audit: 7 roles
      - Auditor on Global Engineering... ✅
      - Read on Production Infrastructure... ✅
      ...
      Result: 6/7 roles migrated

...

======================================================================
   MIGRATION SUMMARY
======================================================================

📊 Statistics:
   Users processed:    23
   Roles found:        45
   Roles created:      38 ✅
   Roles skipped:      3 ⏭️
   Roles failed:       4 ❌

   Success Rate: 84.4%

⚠️  Errors (4):
   - amanda.pentest: Missing inventory 'Production Infrastructure' (source ID: 5)
   - charlie.devops: Missing project 'Ansible Automation' (source ID: 12)
   - diana.ops: Missing job_template 'Deploy Application' (source ID: 8)
   - bob.jenkins: Missing team 'CI/CD Team' (source ID: 9)

======================================================================
```

---

## Troubleshooting

### Issue: "User not found in target AAP"

**Solution:** The user wasn't migrated. Check the main migration log to see why.

```bash
# Manually check if user exists
curl -sk -H "Authorization: Bearer TARGET_TOKEN" \
  "https://localhost:10443/api/controller/v2/users/?username=USERNAME"
```

### Issue: "Missing resource: organization 'XYZ'"

**Solution:** The resource wasn't migrated due to timeout errors.

```bash
# Check if resource exists
curl -sk -H "Authorization: Bearer TARGET_TOKEN" \
  "https://localhost:10443/api/controller/v2/organizations/?name=XYZ"

# If missing, re-run migration for that resource type
aap-bridge migrate --skip-prep -r organizations
```

### Issue: "Role 'Admin' not found on organization"

**Solution:** AAP 2.6 may use different role names. Check available roles:

```bash
# Get organization ID
ORG_ID=6

# List available roles
curl -sk -H "Authorization: Bearer TARGET_TOKEN" \
  "https://localhost:10443/api/controller/v2/organizations/${ORG_ID}/object_roles/"
```

### Issue: "Cannot get object roles: HTTP 404"

**Solution:** The resource doesn't exist in target. Either:
1. Re-run main migration for that resource type
2. Manually create the resource in target AAP
3. Skip that role assignment

---

## Verification

After running the script, verify RBAC was migrated correctly:

### 1. Check Role Counts

```bash
# Compare role counts for a specific user
echo "=== User: amanda.pentest ==="

# Source roles
curl -sk -H "Authorization: Bearer SOURCE_TOKEN" \
  "https://localhost:8443/api/v2/users/15/roles/" | jq '.count'

# Target roles
curl -sk -H "Authorization: Bearer TARGET_TOKEN" \
  "https://localhost:10443/api/controller/v2/users/6/roles/" | jq '.count'
```

### 2. Check Specific Role

```bash
# List all roles for a user
curl -sk -H "Authorization: Bearer TARGET_TOKEN" \
  "https://localhost:10443/api/controller/v2/users/6/roles/" | \
  jq '.results[] | "\(.name) - \(.summary_fields.resource_name)"'
```

### 3. Test User Access

```bash
# Login as migrated user and verify they can access their resources
curl -sk -u "username:password" \
  "https://localhost:10443/api/controller/v2/organizations/"
```

---

## Known Limitations

1. **System Auditor Flags:** Already fixed separately (not handled by this script)

2. **Superuser Flags:** Script does NOT modify `is_superuser` - already migrated correctly

3. **Implicit Roles:** Inherited/implicit roles are skipped (they'll be recreated automatically)

4. **Custom Roles:** If you have custom role definitions, they must exist in target AAP

5. **Missing Resources:** If a resource wasn't migrated (due to timeout), its roles can't be assigned. Fix by:
   - Re-running main migration for that resource type
   - Or manually creating the resource in target

---

## Manual RBAC Operations

If the script fails for specific users, you can manually assign roles:

### Assign Organization Admin

```bash
# Get organization ID
ORG_ID=$(curl -sk -H "Authorization: Bearer $TARGET__TOKEN" \
  "https://localhost:10443/api/controller/v2/organizations/?name=Global%20Engineering" | \
  jq -r '.results[0].id')

# Get Admin role ID for that organization
ROLE_ID=$(curl -sk -H "Authorization: Bearer $TARGET__TOKEN" \
  "https://localhost:10443/api/controller/v2/organizations/${ORG_ID}/object_roles/" | \
  jq -r '.results[] | select(.name=="Admin") | .id')

# Assign user to role
curl -sk -X POST \
  -H "Authorization: Bearer $TARGET__TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": USER_ID}' \
  "https://localhost:10443/api/controller/v2/roles/${ROLE_ID}/users/"
```

### Assign Team Member

```bash
# Get team ID
TEAM_ID=$(curl -sk -H "Authorization: Bearer $TARGET__TOKEN" \
  "https://localhost:10443/api/controller/v2/teams/?name=Backend%20Development" | \
  jq -r '.results[0].id')

# Get Member role ID
ROLE_ID=$(curl -sk -H "Authorization: Bearer $TARGET__TOKEN" \
  "https://localhost:10443/api/controller/v2/teams/${TEAM_ID}/object_roles/" | \
  jq -r '.results[] | select(.name=="Member") | .id')

# Assign user
curl -sk -X POST \
  -H "Authorization: Bearer $TARGET__TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": USER_ID}' \
  "https://localhost:10443/api/controller/v2/roles/${ROLE_ID}/users/"
```

---

## Success Criteria

Migration is successful when:

- [ ] All users have same role count (source vs target) ±10%
- [ ] Critical users (admins, auditors) have correct access
- [ ] Users can login and see their resources
- [ ] No users have zero roles (unless they had zero in source)
- [ ] Success rate > 80%

---

## Next Steps After RBAC Migration

1. **Verify Access:**
   - Have each user login and verify they can access their resources
   - Check organization admins can manage their organizations
   - Verify team members can see their teams

2. **Complete Main Migration:**
   - Re-run main migration with increased timeouts
   - Migrate remaining resources (inventories, hosts, job templates)

3. **Final Validation:**
   - Run full validation: `aap-bridge validate all --sample-size 1000`
   - Compare resource counts source vs target
   - Test job template execution

---

## Support

If you encounter issues:

1. **Check Logs:** Review script output for error messages
2. **Check State DB:** Verify ID mappings exist
3. **Check Resources:** Ensure parent resources exist in target
4. **Manual Fix:** Use manual RBAC operations above
5. **Rerun:** Safe to rerun script (handles duplicates)

---

**Script Created:** 2026-03-04
**Last Updated:** 2026-03-04
