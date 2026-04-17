# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic
Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-12-05

### Added

- Initial release of AAP Bridge
- **Migration Framework**
  - ETL pipeline for source-to-target AAP migrations
  - Support for all major AAP resource types: organizations, users, teams,
    credentials, credential types, execution environments, projects,
    inventories, hosts, job templates, workflow job templates, and schedules
  - RBAC role assignment migration
  - Bulk API operations for high-performance host and inventory imports
- **State Management**
  - PostgreSQL-backed state tracking with checkpoint/resume capability
  - ID mapping persistence for cross-system resource references
  - Idempotent operations to prevent duplicate creation
- **Export/Import Operations**
  - Split-file export for large datasets (configurable records per file)
  - Automatic file discovery and ordered import
  - Metadata tracking for export sessions
- **Validation**
  - Statistical sampling validation (configurable confidence level and margin of
    error)
  - Count reconciliation between source and target
  - Phase-by-phase validation support
- **CLI Interface**
  - `aap-bridge` - Single command with a menu-driven interface
  - `aap-bridge migrate` - Full migration with phase control
  - `aap-bridge export` - Export resources from source AAP
  - `aap-bridge import` - Import resources to target AAP
  - `aap-bridge validate` - Validate migration completeness
  - `aap-bridge state` - View and manage migration state
  - `aap-bridge cleanup` - Clean up target resources or local data
- **Progress Display**
  - Rich-based live progress display with real-time metrics
  - Multiple output modes: normal, quiet, CI/CD, and detailed
  - Rate tracking, success/failure counts, and timing information
- **Logging**
  - Structured logging with structlog
  - Separate console (human-readable) and file (JSON) output
  - Automatic sensitive data redaction
  - Configurable log levels for console and file
- **Configuration**
  - YAML-based configuration with environment variable substitution
  - Resource renaming via mappings.yaml (e.g., credential type name changes
    between versions)
  - Endpoint filtering via ignored_endpoints.yaml
  - Extensive performance tuning options

### Security

- Automatic redaction of sensitive fields in logs (tokens, passwords, SSH keys)
- Environment variable support for all credentials
- No hardcoded secrets in configuration files

[Unreleased]: https://github.com/antonysallas/aap-bridge/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/antonysallas/aap-bridge/releases/tag/v0.1.0
