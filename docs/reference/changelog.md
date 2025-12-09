# Changelog

All notable changes to AAP Bridge are documented here.

For the complete changelog, see [CHANGELOG.md](https://github.com/antonysallas/aap-bridge/blob/main/CHANGELOG.md) in the repository.

## Version History

### v0.1.0 (Current)

Initial release of AAP Bridge.

**Features:**

- Full ETL pipeline for AAP migration
- Bulk operations support for hosts
- PostgreSQL-backed state management
- Checkpoint/resume capability
- Rich progress display
- Split-file export/import for large datasets
- Interactive CLI menu

**Supported Resources:**

- Organizations
- Labels
- Users
- Teams
- Credential Types
- Credentials
- Execution Environments
- Inventories
- Inventory Sources
- Inventory Groups
- Hosts
- Instances
- Instance Groups
- Projects
- Job Templates
- Workflow Job Templates
- Schedules

**Known Limitations:**

- Encrypted credentials cannot be migrated (API limitation)
- RBAC assignments require manual verification
- Workflow approval nodes need manual setup

---

## Versioning

AAP Bridge follows [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

## Upgrade Notes

When upgrading AAP Bridge:

1. Review the changelog for breaking changes
2. Backup your state database
3. Test in a staging environment first
4. Update configuration if needed
