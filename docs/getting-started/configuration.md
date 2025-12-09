# Configuration

AAP Bridge uses a combination of environment variables and YAML configuration files.

## Environment Variables

Create a `.env` file from the example:

```bash
cp .env.example .env
```

### Required Variables

```bash
# Source AAP instance
SOURCE__URL=https://source-aap.example.com/api/v2
SOURCE__TOKEN=your_source_api_token

# Target AAP instance (Platform Gateway for AAP 2.6+)
TARGET__URL=https://target-aap.example.com/api/controller/v2
TARGET__TOKEN=your_target_api_token

# PostgreSQL state database
MIGRATION_STATE_DB_PATH=postgresql://user:password@localhost:5432/aap_migration
```

### Optional Variables

```bash
# HashiCorp Vault (for credential migration)
VAULT__URL=https://vault.example.com
VAULT__ROLE_ID=your_role_id
VAULT__SECRET_ID=your_secret_id

# Logging overrides
AAP_BRIDGE__LOGGING__CONSOLE_LEVEL=WARNING
AAP_BRIDGE__LOGGING__DISABLE_PROGRESS=false
```

## Configuration File

The main configuration file is `config/config.yaml`:

### Path Configuration

```yaml
paths:
  state_db: ${MIGRATION_STATE_DB_PATH}
  export_dir: ./exports
  transform_dir: ./transformed
  log_dir: ./logs
  checkpoint_dir: ./checkpoints
```

### Performance Tuning

```yaml
performance:
  max_concurrent: 10           # Concurrent API requests
  batch_sizes:
    organizations: 50
    inventories: 100
    hosts: 200                 # Maximum for bulk API
    credentials: 50
  rate_limit:
    requests_per_second: 50
    burst_size: 100
```

### Cleanup Settings

```yaml
cleanup:
  skip_default_resources: true  # Skip Default org, admin user
  batch_size: 100
  max_concurrent: 5
```

### Logging Configuration

```yaml
logging:
  console_level: WARNING        # Console output level
  file_level: DEBUG            # File log level
  log_file: ./logs/aap-bridge.log
```

## Resource Mappings

The `config/mappings.yaml` file defines field mappings between AAP versions:

```yaml
credential_types:
  source_to_target:
    "Amazon Web Services": "Amazon Web Services"
    "VMware vCenter": "VMware vCenter"
```

## Ignored Endpoints

The `config/ignored_endpoints.yaml` file lists endpoints to skip:

```yaml
ignored_endpoints:
  global:
    - ping
    - config
    - dashboard
  source: []
  target: []
```

## Validating Configuration

Check your configuration:

```bash
# Validate all settings
aap-bridge config validate

# Show current configuration
aap-bridge config show
```

## Environment-Specific Settings

### CI/CD Pipelines

```bash
export AAP_BRIDGE__LOGGING__DISABLE_PROGRESS=true
export AAP_BRIDGE__LOGGING__CONSOLE_LEVEL=INFO
aap-bridge migrate full
```

### Large Migrations

Increase batch sizes and concurrency:

```yaml
performance:
  max_concurrent: 20
  batch_sizes:
    hosts: 200
    inventories: 200
```

### Limited Network Bandwidth

Reduce concurrent requests:

```yaml
performance:
  max_concurrent: 5
  rate_limit:
    requests_per_second: 20
```
