# How to Fix Credentials and Projects Migration

**Goal:** Get your credentials and projects working in target AAP 2.6

**Time Required:** 45-90 minutes for 8 credentials + projects

---

## Step 1: Export Source Credential Details (5 minutes)

First, let's get all the information about your source credentials:

```bash
# Export credential metadata
curl -sk -H "Authorization: Bearer ENOBFlD2GAB2LmCD5P2RqsTEOjbrlA" \
  "https://localhost:8443/api/v2/credentials/" \
  | jq -r '.results[] | {
      id: .id,
      name: .name,
      type: .credential_type,
      kind: .kind,
      organization: .organization,
      inputs: .inputs
    }' > source_credentials.json

cat source_credentials.json
```

This will show you all 8 credentials with their structure (but encrypted secrets).

---

## Step 2: Gather Actual Secrets (15-30 minutes)

For each credential, you need to find the actual passwords/keys/tokens. Here's where to look:

### 2.1 SSH Credentials (Demo Credential, test_A)

**Option A: Check AAP filesystem (if you have SSH access to source AAP)**
```bash
# SSH to source AAP server
ssh admin@source-aap-server

# Check for SSH keys
sudo ls -la /var/lib/awx/.ssh/
sudo cat /var/lib/awx/.ssh/id_rsa  # Private key
sudo cat /var/lib/awx/.ssh/id_rsa.pub  # Public key

# Check AWX database for password hints (won't show actual passwords)
sudo awx-manage shell
>>> from awx.main.models import Credential
>>> for c in Credential.objects.filter(credential_type__kind='ssh'):
...     print(f"{c.name}: {c.inputs}")
```

**Option B: Check your password manager or documentation**
- Look for "AAP Demo Credential password"
- Look for "test_A SSH key"

**Option C: Ask team members who created them**

**For testing:** If you don't have the actual secrets, you can:
- Generate new SSH keys
- Use test passwords
- Skip these credentials temporarily

### 2.2 Galaxy/Automation Hub Tokens

**Where to find:**
1. Log in to Automation Hub: https://192.168.100.26
2. Go to: Collections → API Token (or User → Token)
3. Copy the token

**Your Automation Hub URLs:**
- Validated: https://192.168.100.26/api/galaxy/content/validated/
- Published: https://192.168.100.26/api/galaxy/content/published/
- RH Certified: https://192.168.100.26/api/galaxy/content/rh-certified/
- Community: https://192.168.100.26/api/galaxy/content/community/

### 2.3 Container Registry Credentials

**Where to find:**
- Host: 192.168.100.26
- Username: admin
- Password: (check documentation or ask admin)

---

## Step 3: Create Credential Mapping Spreadsheet (5 minutes)

Create a file `credential_mapping.csv`:

```csv
Source_ID,Source_Name,Type,Organization,Status,Target_ID,Notes
1,Demo Credential,SSH,1,TODO,,Need password/key
2,Ansible Galaxy,Galaxy,NULL,READY,,No secrets needed
3,Automation Hub Validated,Galaxy,NULL,TODO,,Need token
4,Automation Hub Published,Galaxy,NULL,TODO,,Need token
5,Automation Hub RH Certified,Galaxy,NULL,TODO,,Need token
6,Automation Hub Community,Galaxy,NULL,TODO,,Need token
7,Automation Hub Container Registry,Registry,NULL,TODO,,Need password
8,test_A,SSH,NULL,TODO,,Need SSH key
```

---

## Step 4: Recreate Credentials in Target AAP (20-40 minutes)

### Option A: Via Target AAP Web UI (Recommended)

**For each credential:**

1. **Log in to target AAP:** https://localhost:10443
2. **Go to:** Resources → Credentials
3. **Click:** Add
4. **Fill in:**
   - Name: (exact name from source)
   - Credential Type: (match the type)
   - Organization: (match the org)
   - **Input fields:** Enter actual passwords/tokens/keys
5. **Save**
6. **Note the new ID** from the URL (e.g., `/credentials/15/details` → ID is 15)

**Example: Recreating "Automation Hub Validated Repository"**

```
Name: Automation Hub Validated Repository
Credential Type: Ansible Galaxy/Automation Hub API Token
Organization: (leave blank)
Galaxy Server URL: https://192.168.100.26/api/galaxy/content/validated/
Auth Server URL: (leave blank)
Token: [PASTE YOUR ACTUAL TOKEN HERE]
```

### Option B: Via API/CLI (Faster if you have the secrets)

Create a script `recreate_credentials.sh`:

```bash
#!/bin/bash

TARGET_URL="https://localhost:10443/api/controller/v2"
TARGET_TOKEN="ea023U8zsSXEBuXXZRpiLidAYMT1aT"

# Function to create credential
create_credential() {
    local name="$1"
    local type="$2"
    local inputs="$3"
    local org="$4"

    curl -sk -X POST \
      -H "Authorization: Bearer $TARGET_TOKEN" \
      -H "Content-Type: application/json" \
      "$TARGET_URL/credentials/" \
      -d "{
        \"name\": \"$name\",
        \"credential_type\": $type,
        \"organization\": $org,
        \"inputs\": $inputs
      }"
}

# Example: Create Ansible Galaxy credential (no secrets)
create_credential \
  "Ansible Galaxy" \
  19 \
  '{"url": "https://galaxy.ansible.com/"}' \
  "null"

# Example: Create Automation Hub Validated (with token)
create_credential \
  "Automation Hub Validated Repository" \
  19 \
  '{"url": "https://192.168.100.26/api/galaxy/content/validated/", "token": "YOUR_ACTUAL_TOKEN_HERE"}' \
  "null"

# Example: Create SSH credential (with key)
create_credential \
  "Demo Credential" \
  1 \
  '{"username": "admin", "ssh_key_data": "-----BEGIN RSA PRIVATE KEY-----\nYOUR_KEY_HERE\n-----END RSA PRIVATE KEY-----"}' \
  1

# Repeat for all 8 credentials...
```

**Run it:**
```bash
chmod +x recreate_credentials.sh
./recreate_credentials.sh
```

---

## Step 5: Verify Credentials Created (2 minutes)

```bash
# List all credentials in target
curl -sk -H "Authorization: Bearer ea023U8zsSXEBuXXZRpiLidAYMT1aT" \
  "https://localhost:10443/api/controller/v2/credentials/" \
  | jq -r '.results[] | "\(.id): \(.name) - Type: \(.credential_type)"'

# Should show all 8 credentials with new IDs
```

**Update your credential_mapping.csv with new IDs:**
```csv
Source_ID,Source_Name,Type,Organization,Status,Target_ID,Notes
1,Demo Credential,SSH,1,DONE,10,Recreated via UI
2,Ansible Galaxy,Galaxy,NULL,DONE,11,Recreated via API
3,Automation Hub Validated,Galaxy,NULL,DONE,12,Recreated via UI
...
```

---

## Step 6: Associate Galaxy Credentials to Organizations (5 minutes)

Your source org_A has "Ansible Galaxy" credential. Need to add it to target org_A.

### Via UI:
1. Go to: Resources → Organizations → org_A
2. Click: Edit
3. Scroll to: Galaxy Credentials
4. Click: Add
5. Select: Ansible Galaxy
6. Save

### Via API:
```bash
# Get Ansible Galaxy credential ID in target
GALAXY_CRED_ID=$(curl -sk -H "Authorization: Bearer ea023U8zsSXEBuXXZRpiLidAYMT1aT" \
  "https://localhost:10443/api/controller/v2/credentials/?name=Ansible+Galaxy" \
  | jq -r '.results[0].id')

# Associate to org_A (ID 2)
curl -sk -X POST \
  -H "Authorization: Bearer ea023U8zsSXEBuXXZRpiLidAYMT1aT" \
  -H "Content-Type: application/json" \
  "https://localhost:10443/api/controller/v2/organizations/2/galaxy_credentials/" \
  -d "{\"id\": $GALAXY_CRED_ID}"
```

**Verify:**
```bash
curl -sk -H "Authorization: Bearer ea023U8zsSXEBuXXZRpiLidAYMT1aT" \
  "https://localhost:10443/api/controller/v2/organizations/2/galaxy_credentials/" \
  | jq -r '.results[] | "\(.id): \(.name)"'

# Should show: Ansible Galaxy
```

---

## Step 7: Export Projects from Source (2 minutes)

```bash
# Check what projects exist in source
curl -sk -H "Authorization: Bearer ENOBFlD2GAB2LmCD5P2RqsTEOjbrlA" \
  "https://localhost:8443/api/v2/projects/" \
  | jq -r '.results[] | {
      id: .id,
      name: .name,
      scm_type: .scm_type,
      scm_url: .scm_url,
      credential: .credential,
      organization: .organization
    }'

# Export projects
source .venv/bin/activate
aap-bridge export -r projects --output projects_export
```

---

## Step 8: Update Project Credential References (CRITICAL)

**Problem:** Projects exported from source reference credential IDs that don't exist in target.

**Solution:** Create a credential ID mapping file.

Create `config/credential_mappings.yaml`:

```yaml
# Source Credential ID → Target Credential ID mappings
credential_id_mappings:
  1: 10  # Demo Credential: source ID 1 → target ID 10
  2: 11  # Ansible Galaxy: source ID 2 → target ID 11
  3: 12  # Automation Hub Validated: source ID 3 → target ID 12
  4: 13  # Automation Hub Published: source ID 4 → target ID 13
  5: 14  # Automation Hub RH Certified: source ID 5 → target ID 14
  6: 15  # Automation Hub Community: source ID 6 → target ID 15
  7: 16  # Automation Hub Container Registry: source ID 7 → target ID 16
  8: 17  # test_A: source ID 8 → target ID 17
```

**Or:** If using the migration tool's state database:

```bash
# Manually insert credential mappings into SQLite
sqlite3 migration_state.db <<EOF
INSERT OR REPLACE INTO id_mappings (resource_type, source_id, target_id, resource_name)
VALUES
  ('credentials', 1, 10, 'Demo Credential'),
  ('credentials', 2, 11, 'Ansible Galaxy'),
  ('credentials', 3, 12, 'Automation Hub Validated Repository'),
  ('credentials', 4, 13, 'Automation Hub Published Repository'),
  ('credentials', 5, 14, 'Automation Hub RH Certified Repository'),
  ('credentials', 6, 15, 'Automation Hub Community Repository'),
  ('credentials', 7, 16, 'Automation Hub Container Registry'),
  ('credentials', 8, 17, 'test_A');
EOF

# Verify
sqlite3 migration_state.db "SELECT * FROM id_mappings WHERE resource_type='credentials';"
```

---

## Step 9: Transform and Import Projects (5 minutes)

```bash
# Transform projects (will use credential mappings from state DB)
aap-bridge transform -r projects --input projects_export --output projects_xformed

# Import projects to target
aap-bridge import -r projects --input projects_xformed --yes
```

**If projects reference credentials that don't exist:**

Manually edit the transformed files:

```bash
# Check what credential IDs are referenced
cat projects_xformed/projects/*.json | jq -r '.[] | select(.credential != null) | {name, credential}'

# Edit each file to update credential IDs
nano projects_xformed/projects/projects_0001.json

# Change:
#   "credential": 1
# To:
#   "credential": 10

# Then import
aap-bridge import -r projects --input projects_xformed --yes
```

---

## Step 10: Verify Projects Work (5 minutes)

### Check projects exist:
```bash
curl -sk -H "Authorization: Bearer ea023U8zsSXEBuXXZRpiLidAYMT1aT" \
  "https://localhost:10443/api/controller/v2/projects/" \
  | jq -r '.results[] | "\(.id): \(.name) - Org: \(.organization)"'
```

### Test project sync:
```bash
# Get project ID
PROJECT_ID=<id_from_above>

# Trigger sync
curl -sk -X POST \
  -H "Authorization: Bearer ea023U8zsSXEBuXXZRpiLidAYMT1aT" \
  "https://localhost:10443/api/controller/v2/projects/$PROJECT_ID/update/"

# Check sync status
curl -sk -H "Authorization: Bearer ea023U8zsSXEBuXXZRpiLidAYMT1aT" \
  "https://localhost:10443/api/controller/v2/projects/$PROJECT_ID/" \
  | jq '{name, status, scm_revision}'
```

**Expected:** Project should sync successfully, pulling code from SCM.

---

## Step 11: Migrate Job Templates (10 minutes)

Once projects work, migrate job templates:

```bash
# Export job templates from source
aap-bridge export -r job_templates --output templates_export

# Insert job template credential mappings if needed
# (same process as projects)

# Transform
aap-bridge transform -r job_templates --input templates_export --output templates_xformed

# Import
aap-bridge import -r job_templates --input templates_xformed --yes
```

---

## Step 12: Test End-to-End (5 minutes)

**Test a job template:**

```bash
# Get job template ID
curl -sk -H "Authorization: Bearer ea023U8zsSXEBuXXZRpiLidAYMT1aT" \
  "https://localhost:10443/api/controller/v2/job_templates/" \
  | jq -r '.results[] | "\(.id): \(.name)"'

# Launch a job
JOB_TEMPLATE_ID=<id_from_above>

curl -sk -X POST \
  -H "Authorization: Bearer ea023U8zsSXEBuXXZRpiLidAYMT1aT" \
  "https://localhost:10443/api/controller/v2/job_templates/$JOB_TEMPLATE_ID/launch/" \
  -d '{}'

# Check job status
JOB_ID=<id_from_launch_response>

curl -sk -H "Authorization: Bearer ea023U8zsSXEBuXXZRpiLidAYMT1aT" \
  "https://localhost:10443/api/controller/v2/jobs/$JOB_ID/" \
  | jq '{status, name, playbook, inventory, credentials}'
```

**Expected:** Job should run successfully using migrated credentials, projects, and inventories.

---

## Troubleshooting

### Issue: "Credential not found"
**Cause:** Project/template references old credential ID
**Fix:** Update credential ID mapping in state DB or manually edit transformed files

### Issue: "Project sync failed: Authentication failed"
**Cause:** SCM credential is wrong or missing
**Fix:** Recreate the SCM credential with correct password/key

### Issue: "Credential type mismatch"
**Cause:** Credential type ID differs between AAP versions
**Fix:** Check credential type IDs in both systems:

```bash
# Source credential types
curl -sk "https://localhost:8443/api/v2/credential_types/" | jq -r '.results[] | "\(.id): \(.name)"'

# Target credential types
curl -sk "https://localhost:10443/api/controller/v2/credential_types/" | jq -r '.results[] | "\(.id): \(.name)"'
```

### Issue: "Galaxy credential not working"
**Cause:** Not associated with organization
**Fix:** Follow Step 6 to associate galaxy credentials

---

## Quick Checklist

- [ ] Export credential metadata from source
- [ ] Gather actual passwords/tokens/keys for all 8 credentials
- [ ] Recreate 8 credentials in target AAP (via UI or API)
- [ ] Note new credential IDs
- [ ] Associate galaxy credentials to organizations
- [ ] Update credential ID mappings in state DB or config file
- [ ] Export projects from source
- [ ] Transform projects with credential mappings
- [ ] Import projects to target
- [ ] Verify project sync works
- [ ] Export job templates from source
- [ ] Transform job templates with credential mappings
- [ ] Import job templates to target
- [ ] Test job template execution end-to-end

---

## Time Breakdown

| Task | Time |
|------|------|
| Export credential metadata | 5 min |
| Gather actual secrets | 15-30 min |
| Recreate credentials in target | 20-40 min |
| Associate galaxy creds to orgs | 5 min |
| Update credential ID mappings | 5 min |
| Migrate projects | 5 min |
| Verify project sync | 5 min |
| Migrate job templates | 10 min |
| Test end-to-end | 5 min |
| **TOTAL** | **45-90 min** |

---

## Next Steps

After completing this guide:
1. Document your credential mapping for future reference
2. Update migration runbook with lessons learned
3. Consider HashiCorp Vault for production
4. Test full workflow (create job, run job, verify results)
