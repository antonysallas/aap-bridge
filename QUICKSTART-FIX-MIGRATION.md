# Quick Start: Fix Credentials & Projects (30-60 minutes)

**Goal:** Get your AAP migration working end-to-end with credentials and projects.

---

## TL;DR - Fastest Path

```bash
# 1. Use helper script to recreate credentials
cd /Users/arbhati/project/git/aap-bridge-fork
./scripts/recreate_credentials.sh

# 2. Follow interactive prompts to:
#    - Export source credentials
#    - Auto-create credentials without secrets (Ansible Galaxy)
#    - Manually create credentials with secrets (SSH, tokens)
#    - Associate galaxy credentials to organizations

# 3. Migrate projects and job templates
source .venv/bin/activate
aap-bridge migrate -r projects -r job_templates --config config/config.yaml

# 4. Test a job template
# (via UI or API)
```

**Time:** 30-60 minutes depending on number of credentials

---

## Option 1: Interactive Script (Recommended - Easiest)

### Step 1: Run the Helper Script

```bash
cd /Users/arbhati/project/git/aap-bridge-fork
./scripts/recreate_credentials.sh
```

### Step 2: Follow the Menu

```
AAP Credential Recreation Helper
1. Export source credentials          ← Start here
2. Show secrets needed                 ← See what you need to gather
3. Auto-create credentials (no secrets) ← Creates Ansible Galaxy automatically
4. Create credential (interactive)     ← Create SSH/token credentials one by one
5. Show credential mappings            ← View what's been created
6. Associate galaxy credentials        ← Link galaxy creds to orgs
7. Export all for manual review
8. Quit
```

### Step 3: For Each Credential with Secrets

When prompted:
```
Do you want to create this credential in target AAP? (y/n): y
Enter the credential inputs (in JSON format):
```

**Examples:**

**SSH Credential (Demo Credential):**
```json
{"username": "admin", "password": "your_password_here"}
```

**SSH with Key (test_A):**
```json
{"username": "arnav", "ssh_key_data": "-----BEGIN RSA PRIVATE KEY-----\nYour_key_here\n-----END RSA PRIVATE KEY-----"}
```

**Galaxy Token:**
```json
{"url": "https://192.168.100.26/api/galaxy/content/validated/", "token": "your_token_here"}
```

**Container Registry:**
```json
{"host": "192.168.100.26", "username": "admin", "password": "your_password_here", "verify_ssl": true}
```

### Step 4: Verify Mappings Created

Select option `5` to see:
```
Source,Target,Name
1,10,Demo Credential
2,11,Ansible Galaxy
3,12,Automation Hub Validated Repository
...
```

### Step 5: Associate Galaxy Credentials

Select option `6` to automatically associate galaxy credentials to organizations.

---

## Option 2: Manual Via Target AAP UI (Recommended - Most Reliable)

### Step 1: Export Source Credential List

```bash
curl -sk -H "Authorization: Bearer ENOBFlD2GAB2LmCD5P2RqsTEOjbrlA" \
  "https://localhost:8443/api/v2/credentials/" \
  | jq -r '.results[] | "\(.id)\t\(.name)\t\(.credential_type)\t\(.kind)"' \
  | column -t > credential_list.txt

cat credential_list.txt
```

### Step 2: For Each Credential

1. **Open target AAP:** https://localhost:10443
2. **Go to:** Resources → Credentials → Add
3. **Fill in from your list:**
   - Name: (copy from source)
   - Credential Type: (match the type)
   - Organization: (match if set)
   - **Enter the actual secrets** (passwords, tokens, keys)
4. **Save**
5. **Note the ID** from URL: `/credentials/15/details` → ID is 15

### Step 3: Create Mapping File

Create `credential_mappings.csv`:
```csv
1,10,Demo Credential
2,11,Ansible Galaxy
3,12,Automation Hub Validated Repository
4,13,Automation Hub Published Repository
5,14,Automation Hub RH Certified Repository
6,15,Automation Hub Community Repository
7,16,Automation Hub Container Registry
8,17,test_A
```

### Step 4: Update State Database

```bash
cd /Users/arbhati/project/git/aap-bridge-fork

# Load mappings into state DB
while IFS=, read -r source_id target_id name; do
  sqlite3 migration_state.db \
    "INSERT OR REPLACE INTO id_mappings (resource_type, source_id, target_id, resource_name)
     VALUES ('credentials', $source_id, $target_id, '$name');"
done < credential_mappings.csv

# Verify
sqlite3 migration_state.db \
  "SELECT source_id, target_id, resource_name FROM id_mappings WHERE resource_type='credentials';"
```

### Step 5: Associate Galaxy Credentials

**Via UI:**
1. Resources → Organizations → org_A → Edit
2. Galaxy Credentials → Add
3. Select: Ansible Galaxy
4. Save

**Via API:**
```bash
# Get Ansible Galaxy credential ID
GALAXY_ID=$(curl -sk -H "Authorization: Bearer ea023U8zsSXEBuXXZRpiLidAYMT1aT" \
  "https://localhost:10443/api/controller/v2/credentials/?name=Ansible+Galaxy" \
  | jq -r '.results[0].id')

# Associate to org_A
curl -sk -X POST \
  -H "Authorization: Bearer ea023U8zsSXEBuXXZRpiLidAYMT1aT" \
  -H "Content-Type: application/json" \
  "https://localhost:10443/api/controller/v2/organizations/2/galaxy_credentials/" \
  -d "{\"id\": $GALAXY_ID}"
```

---

## Step 6: Migrate Projects (5 minutes)

Now that credentials exist, migrate projects:

```bash
cd /Users/arbhati/project/git/aap-bridge-fork
source .venv/bin/activate

# Check what projects exist in source
curl -sk -H "Authorization: Bearer ENOBFlD2GAB2LmCD5P2RqsTEOjbrlA" \
  "https://localhost:8443/api/v2/projects/" \
  | jq -r '.results[] | {id, name, scm_type, credential}'

# Migrate projects (will use credential mappings from state DB)
aap-bridge migrate -r projects --config config/config.yaml
```

### If Projects Reference Non-Existent Credentials

**Error:** `Credential with ID X not found`

**Fix:** Check credential mapping:
```bash
# Show credential mappings
sqlite3 migration_state.db \
  "SELECT * FROM id_mappings WHERE resource_type='credentials';"

# If missing, add manually:
sqlite3 migration_state.db \
  "INSERT INTO id_mappings (resource_type, source_id, target_id, resource_name)
   VALUES ('credentials', 1, 10, 'Demo Credential');"
```

---

## Step 7: Verify Projects Work (5 minutes)

```bash
# List projects in target
curl -sk -H "Authorization: Bearer ea023U8zsSXEBuXXZRpiLidAYMT1aT" \
  "https://localhost:10443/api/controller/v2/projects/" \
  | jq -r '.results[] | "\(.id): \(.name) - Status: \(.status)"'

# Test project sync
PROJECT_ID=<id_from_above>

curl -sk -X POST \
  -H "Authorization: Bearer ea023U8zsSXEBuXXZRpiLidAYMT1aT" \
  "https://localhost:10443/api/controller/v2/projects/$PROJECT_ID/update/"

# Check result
sleep 5
curl -sk -H "Authorization: Bearer ea023U8zsSXEBuXXZRpiLidAYMT1aT" \
  "https://localhost:10443/api/controller/v2/projects/$PROJECT_ID/" \
  | jq '{name, status, scm_revision, last_job_failed}'
```

**Expected:**
```json
{
  "name": "my-project",
  "status": "successful",
  "scm_revision": "abc123...",
  "last_job_failed": false
}
```

---

## Step 8: Migrate Job Templates (10 minutes)

```bash
# Migrate job templates
aap-bridge migrate -r job_templates --config config/config.yaml

# List job templates
curl -sk -H "Authorization: Bearer ea023U8zsSXEBuXXZRpiLidAYMT1aT" \
  "https://localhost:10443/api/controller/v2/job_templates/" \
  | jq -r '.results[] | "\(.id): \(.name)"'
```

---

## Step 9: Test End-to-End (5 minutes)

```bash
# Launch a job template
TEMPLATE_ID=<id_from_above>

JOB_RESPONSE=$(curl -sk -X POST \
  -H "Authorization: Bearer ea023U8zsSXEBuXXZRpiLidAYMT1aT" \
  "https://localhost:10443/api/controller/v2/job_templates/$TEMPLATE_ID/launch/" \
  -d '{}')

JOB_ID=$(echo "$JOB_RESPONSE" | jq -r '.id')

echo "Job launched: $JOB_ID"
echo "View at: https://localhost:10443/#/jobs/$JOB_ID"

# Monitor job
while true; do
  STATUS=$(curl -sk -H "Authorization: Bearer ea023U8zsSXEBuXXZRpiLidAYMT1aT" \
    "https://localhost:10443/api/controller/v2/jobs/$JOB_ID/" \
    | jq -r '.status')

  echo "Job status: $STATUS"

  if [ "$STATUS" == "successful" ]; then
    echo "✓ Job completed successfully!"
    break
  elif [ "$STATUS" == "failed" ]; then
    echo "✗ Job failed!"
    break
  fi

  sleep 5
done
```

**Success:** Job runs without credential/project errors.

---

## Common Issues & Quick Fixes

### Issue: Script won't run

```bash
chmod +x scripts/recreate_credentials.sh
```

### Issue: "jq: command not found"

```bash
# macOS
brew install jq

# Linux
sudo apt-get install jq  # Debian/Ubuntu
sudo yum install jq      # RHEL/CentOS
```

### Issue: "Credential type X not found"

**Cause:** Credential type IDs differ between AAP versions

**Fix:** Map credential types:

```bash
# Source types
curl -sk "https://localhost:8443/api/v2/credential_types/" \
  | jq -r '.results[] | "\(.id): \(.name)"' > source_types.txt

# Target types
curl -sk "https://localhost:10443/api/controller/v2/credential_types/" \
  | jq -r '.results[] | "\(.id): \(.name)"' > target_types.txt

# Compare and update
diff source_types.txt target_types.txt
```

### Issue: "Organization galaxy credentials not showing"

**Cause:** Not associated correctly

**Fix:**
```bash
# Via UI: Organizations → org_A → Edit → Galaxy Credentials → Add
# Select the credential and save
```

### Issue: "Project sync failed: Authentication failed"

**Cause:** SCM credential is wrong or missing

**Fix:**
1. Check which credential the project uses
2. Verify that credential exists in target with correct password/key
3. Test credential independently:
   ```bash
   # Try to access the git repo with the credential
   git ls-remote https://git.example.com/repo.git
   ```

---

## Verification Checklist

- [ ] All 8 credentials recreated in target AAP
- [ ] Credential ID mappings saved to state DB
- [ ] Galaxy credentials associated with organizations
- [ ] Projects migrated successfully
- [ ] At least one project sync tested and successful
- [ ] Job templates migrated successfully
- [ ] At least one job template launched and ran successfully

---

## Time Estimates

| Task | Time |
|------|------|
| **Using Interactive Script** | **30-45 min** |
| - Export and review credentials | 5 min |
| - Auto-create no-secret credentials | 2 min |
| - Create credentials with secrets (8 total) | 15-25 min |
| - Associate galaxy credentials | 3 min |
| - Migrate projects | 5 min |
| - Migrate job templates | 5 min |
| - Test end-to-end | 5 min |
|  |  |
| **Using Manual UI Method** | **45-60 min** |
| - List source credentials | 5 min |
| - Manually create each (8 total) | 25-35 min |
| - Create mapping file | 5 min |
| - Load mappings to state DB | 5 min |
| - Associate galaxy credentials | 5 min |
| - Migrate projects | 5 min |
| - Migrate job templates | 5 min |
| - Test end-to-end | 5 min |

---

## After Completing This Guide

You should have:
- ✅ All credentials working in target AAP
- ✅ All projects syncing from SCM
- ✅ All job templates executable
- ✅ Full migration workflow validated

**Next:**
- Migrate remaining resources (workflows, schedules, notifications)
- Validate all automation
- Document any manual steps for production
- Consider HashiCorp Vault for production migrations

---

## Need Help?

See detailed guides:
- **`FIX-CREDENTIALS-GUIDE.md`** - Comprehensive step-by-step guide
- **`docs/CREDENTIAL-MIGRATION-LIMITATION.md`** - Technical details
- **`MIGRATION-ISSUES-FOUND.md`** - Issues discovered during testing

Or run:
```bash
./scripts/recreate_credentials.sh
```

And select option 7 to export everything for manual review.
