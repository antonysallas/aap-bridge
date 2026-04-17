# Source-Version Compatibility Matrix (AAP 2.3, 2.4, 2.5 → 2.6)

This document defines the supported source-to-target migration paths for the AAP Bridge tool and documents known version-specific exceptions.

## Support Status Key

| Status | Description |
|:---|:---|
| **Supported** | Fully tested migration path. Core resource families and dependency chains are verified. |
| **Partial** | Core resources tested, but some version-specific features or complex configurations may require manual steps. |
| **Unsupported** | Migration path not yet tested or verified. Use with caution. |

## Compatibility Matrix

| Source Version | Target Version | Status | Evidence Date | Notes |
|:---|:---|:---|:---|:---|
| AAP 2.3 | AAP 2.6 | **Supported** | 2026-03-24 | Primary migration path. Fully tested across all resource types. |
| AAP 2.4 | AAP 2.6 | **Partial** | 2026-03-24 | Core resource families verified. Inventory plugin changes may require review. |
| AAP 2.5 | AAP 2.6 | **Partial** | 2026-03-24 | Schema differences are minimal. RBAC model changes require manual review. |

## Known Version-Specific Exceptions

### All Source Versions → AAP 2.6

- **Encrypted Credentials**: Encrypted field values (passwords, SSH keys) cannot be extracted via the source AAP API. These must be migrated using HashiCorp Vault or re-entered manually on the target.
- **Platform Gateway**: All API calls to the target AAP 2.6 instance must be routed through the Platform Gateway.

### AAP 2.3 → AAP 2.6

- **Custom Credential Types**: May require manual pre-creation on the target if they use complex schema features not fully handled by the automated transformation.

### AAP 2.4 → AAP 2.6

- **Inventory Plugins**: Configuration format for certain inventory plugins changed between 2.4 and 2.6. Review imported inventories that use SCM or cloud-based sources.

### AAP 2.5 → AAP 2.6

- **RBAC Model**: The RBAC model was significantly restructured in AAP 2.6. While basic user and team assignments are migrated, complex custom role definitions should be manually reviewed on the target.

## Verifying Your Migration Path

The `aap-bridge prep` command automatically discovers the versions of your source and target instances and validates them against this matrix.

```bash
aap-bridge prep --config config.yaml
```

If your version pair is not fully supported, the tool will issue a warning and list known exceptions for that path. You can override an "Unsupported" status using the `--force` flag, but this is recommended for experimental use only.
