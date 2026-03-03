# How AAP Bridge Actually Handles Credentials

**Discovery:** The tool DOES create credentials, but they're incomplete!

---

## What Actually Happens

### Export Phase

```python
# exporter.py lines 1074-1078
if "inputs" in credential:
    for key, value in credential["inputs"].items():
        if value == "$encrypted$":
            credential.setdefault("_encrypted_fields", []).append(key)
```

**Result:** Credentials exported with encrypted fields marked but still showing `"$encrypted$"`

Example exported credential:
```json
{
  "id": 7,
  "name": "Automation Hub Container Registry",
  "inputs": {
    "host": "192.168.100.26",
    "username": "admin",
    "password": "$encrypted$",  ← Encrypted!
    "verify_ssl": true
  },
  "_encrypted_fields": ["password"]  ← Marked
}
```

---

### Transform Phase

```python
# transformer.py lines 641-662
# Handle encrypted fields - mark them for special handling
if "inputs" in data:
    encrypted_fields = []
    for key, value in list(data["inputs"].items()):
        if value == "$encrypted$":
            encrypted_fields.append(key)

    if encrypted_fields:
        data["_needs_vault_lookup"] = True  ← Vault marker
        data["_encrypted_fields"] = encrypted_fields

    # Remove inputs with $encrypted$ values since they can't be imported
    data["inputs"] = {k: v for k, v in data["inputs"].items() if v != "$encrypted$"}
```

**Result:** Credentials transformed with encrypted fields REMOVED!

Example transformed credential:
```json
{
  "id": 7,
  "name": "Automation Hub Container Registry",
  "inputs": {
    "host": "192.168.100.26",
    "username": "admin"
    // password REMOVED!
  },
  "_needs_vault_lookup": true,
  "_encrypted_fields": ["password"]
}
```

---

### Import Phase (The Key Part!)

```python
# importer.py lines 2179-2205
else:
    # Credential does not exist - CREATE it
    logger.info(
        "credential_creating",
        name=name,
        source_id=source_id,
        message="Creating new credential with temporary values",
    )

    # Create resource
    result = await self.client.create_resource(
        resource_type="credentials",
        data=data,  ← Data WITHOUT encrypted fields!
        check_exists=False,
    )
```

**Result:** Credential IS created in target AAP, but WITHOUT secrets!

Created in target AAP:
```json
{
  "id": 16,
  "name": "Automation Hub Container Registry",
  "inputs": {
    "host": "192.168.100.26",
    "username": "admin",
    "password": ""  ← EMPTY! (or missing)
  }
}
```

---

## What You're Seeing

When you run the migration, you ARE seeing credentials created. The logs say:

```
✓ Credentials: 8/8 created
```

**BUT** - those credentials are incomplete! They have:
- ✅ Names
- ✅ Types
- ✅ Organizations
- ✅ Non-sensitive fields (usernames, URLs, hosts)
- ❌ Passwords (EMPTY)
- ❌ SSH keys (EMPTY)
- ❌ Tokens (EMPTY)
- ❌ Secrets (EMPTY)

---

## The Intended Workflow (With Vault)

The tool expects this workflow:

### Option A: Pre-created Credentials (Manual)

1. **Before migration:** Manually create ALL credentials in target AAP with actual secrets
2. **During migration:** Tool finds credentials by name and PATCHes organization/description
3. **After migration:** Credentials work immediately

### Option B: HashiCorp Vault Integration (Automated)

1. **Before migration:** Store all credential secrets in HashiCorp Vault
2. **During migration:**
   - Tool creates credentials with EMPTY secrets
   - Marks them with `"_needs_vault_lookup": true`
3. **After migration:**
   - External process OR manual step links credentials to Vault
   - AAP retrieves secrets from Vault at runtime

---

## Why Credentials Appear in Target But Don't Work

You ran:
```bash
aap-bridge migrate full
```

What happened:
1. ✅ Created credential "Demo Credential" in target
2. ✅ Created credential "test_A" in target
3. ✅ Created all 8 credentials
4. ❌ BUT all SSH keys are EMPTY
5. ❌ All passwords are EMPTY
6. ❌ All tokens are EMPTY

When you check target AAP:
```bash
curl -sk "https://localhost:10443/api/controller/v2/credentials/16/" | jq '.inputs'
```

You see:
```json
{
  "host": "192.168.100.26",
  "username": "admin",
  "password": "",  ← EMPTY!
  "verify_ssl": true
}
```

The credential EXISTS but is USELESS because the password is missing!

---

## Verification Test

Let's verify this is what happened in your migration:

```bash
# Check if credentials were created
curl -sk -H "Authorization: Bearer ea023U8zsSXEBuXXZRpiLidAYMT1aT" \
  "https://localhost:10443/api/controller/v2/credentials/" \
  | jq '.count'

# Should show: 8 (or more if pre-existing)

# Check if they have secrets
curl -sk -H "Authorization: Bearer ea023U8zsSXEBuXXZRpiLidAYMT1aT" \
  "https://localhost:10443/api/controller/v2/credentials/?name=Demo+Credential" \
  | jq '.results[0].inputs'

# Expected result:
# {
#   "username": "admin"
#   // password is MISSING or EMPTY
# }
```

---

## The Documentation Says So

From README.md line 392-394:
```
**Important**: Encrypted credentials cannot be extracted from source AAP via API.
Passwords, SSH keys, and secret fields will show as `$encrypted$`.

**Solution**: Credentials must be manually recreated in HashiCorp Vault before migration.
```

From migration-workflow.md line 229:
```
4. **Update credentials** - Encrypted values need manual setup
```

---

## Why This Is Confusing

The tool's behavior is misleading:

**What it shows:**
```
✓ Credentials imported: 8/8
✓ Projects imported: 2/2
✓ Job Templates imported: 5/5
```

**What it means:**
```
✓ Credential STRUCTURES created: 8/8 (but no secrets)
⚠ Projects created but WON'T WORK (no credential secrets)
⚠ Job Templates created but WON'T WORK (no credential secrets)
```

---

## The Real Workflow You Need

### What You Did
```bash
# Migrated everything including "credentials"
aap-bridge migrate full --config config/config.yaml
```

**Result:**
- Organizations: ✅ Working
- Users: ✅ Working
- Teams: ✅ Working
- Inventories: ✅ Working
- Credentials: ⚠️ Created but EMPTY (no secrets)
- Projects: ❌ Won't work (need credential secrets)
- Job Templates: ❌ Won't work (need credential secrets)

### What You Should Do

**Step 1: Delete incomplete credentials from target**
```bash
# List credentials
curl -sk -H "Authorization: Bearer ea023U8zsSXEBuXXZRpiLidAYMT1aT" \
  "https://localhost:10443/api/controller/v2/credentials/" \
  | jq -r '.results[] | "\(.id): \(.name)"'

# Delete each one (or via UI)
for id in 10 11 12 13 14 15 16 17; do
  curl -sk -X DELETE \
    -H "Authorization: Bearer ea023U8zsSXEBuXXZRpiLidAYMT1aT" \
    "https://localhost:10443/api/controller/v2/credentials/$id/"
done
```

**Step 2: Manually recreate credentials WITH secrets**
```bash
# Use the helper script
./scripts/recreate_credentials.sh

# OR manually via UI
# Resources → Credentials → Add
# Enter ACTUAL passwords, keys, tokens
```

**Step 3: Re-run migration for projects and templates**
```bash
# Credentials now exist with correct secrets
# Projects and templates can now reference them
aap-bridge migrate -r projects -r job_templates --config config/config.yaml
```

---

## The Code Comments Are Misleading

The importer comment says:
```python
"""Credentials are pre-created in the target environment before migration."""
```

This implies you must PRE-CREATE them. But the code actually has:
```python
else:
    # Credential does not exist - CREATE it
    result = await self.client.create_resource(...)
```

So it WILL create them if they don't exist, but without secrets!

**Better comment would be:**
```python
"""Credentials are created if they don't exist, but WITHOUT secrets.
Secrets must be added manually or via Vault integration after creation."""
```

---

## Summary

| What You Thought | What Actually Happens |
|------------------|-----------------------|
| Tool migrates credentials | Tool creates credential STRUCTURE |
| Credentials work in target | Credentials exist but are EMPTY |
| Projects/templates work | Projects/templates reference BROKEN credentials |
| Migration is complete | Migration requires MANUAL credential secrets |

**The tool DOES create credentials, but they're shells without secrets!**

---

## What to Do Now

1. **Check target credentials:**
   ```bash
   curl -sk "https://localhost:10443/api/controller/v2/credentials/" | jq '.results[] | {name, inputs}'
   ```

2. **Verify they're empty:**
   You'll see usernames/URLs but NO passwords/keys/tokens

3. **Follow the fix guide:**
   - Delete empty credentials OR
   - PATCH them with actual secrets (can't do via API - must use UI)

4. **Use helper script:**
   ```bash
   ./scripts/recreate_credentials.sh
   ```

5. **Re-migrate dependent resources:**
   After credentials have secrets, re-run projects and templates migration

---

## Recommendation for Tool Improvement

The tool should:

1. **Warn clearly** when credentials are created without secrets
2. **Mark incomplete credentials** with a flag or description
3. **Fail project/template migration** if credentials are incomplete
4. **Provide clear next steps** in migration summary

Example better output:
```
⚠ Credentials created: 8/8 (WARNING: No secrets - manual setup required)
ℹ Credentials with missing secrets:
  - Demo Credential: Missing password
  - test_A: Missing ssh_key_data
  - Automation Hub Validated: Missing token
  ...
ℹ Fix with: ./scripts/recreate_credentials.sh
❌ Skipped projects: 2 (waiting for credential secrets)
❌ Skipped job templates: 5 (waiting for credential secrets)
```

---

**Bottom Line:** The tool creates credentials, but they're useless without manual secret injection. This is an AAP API limitation, not a tool bug.
