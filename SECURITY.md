# Security Policy

## Supported Versions

| Version | Supported |
| --- | --- |
| 0.1.x | :white_check_mark: |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in AAP
Bridge, please report it responsibly.

### How to Report

1. **Do NOT open a public issue** for security vulnerabilities.
2. Email the maintainers directly at the email address listed in the repository.
3. Include the following information:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested fixes (optional)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your report within 48
  hours.
- **Assessment**: We will assess the vulnerability and determine its severity.
- **Fix Timeline**: Critical vulnerabilities will be addressed as quickly as
  possible. We aim to release a fix within 7-14 days for critical issues.
- **Disclosure**: We will coordinate with you on public disclosure timing.

## Security Best Practices for Users

### Credential Handling

AAP Bridge handles sensitive credentials during migration. Follow these
practices:

1. **Use Environment Variables**: Never hardcode tokens or passwords in
   configuration files.

   ```bash
   export AAP_23_TOKEN="your_source_token"
   export AAP_26_TOKEN="your_target_token"

   ```text

2. **Protect Configuration Files**: Ensure `config/config.yaml` and `.env` have

   restrictive permissions.

   ```bash
   chmod 600 .env
   chmod 600 config/config.yaml

   ```bash

3. **Secure State Database**: The migration state database may contain resource
   metadata. Protect access to the `state/` directory.

4. **Clean Up After Migration**: Remove exported data and logs after successful
   migration.

   ```bash
   aap-bridge cleanup exports
   rm -rf logs/*.log

   ```

### Network Security

1. **Use HTTPS**: Always use HTTPS URLs for AAP instances.
2. **Verify Certificates**: Do not disable SSL verification in production.
3. **Restrict Network Access**: Run migrations from a secured network with
   access only to required AAP instances.

### Logging

1. **Sensitive Data Redaction**: The tool automatically redacts sensitive fields
   (tokens, passwords, SSH keys) from logs.
2. **Log Retention**: Configure appropriate log retention and secure log file
   access.
3. **Avoid Debug in Production**: Use WARNING or higher log levels in production
   to minimize sensitive data exposure.

## Known Security Considerations

### Encrypted Credentials

AAP stores credentials in encrypted form. The AAP API returns `$encrypted$` for
secret fields, which means:

- Credentials cannot be fully extracted via API
- Secret values must be re-provisioned in the target system
- Consider using HashiCorp Vault for credential management

### Export Files

Exported data files may contain:

- Resource names and descriptions
- Inventory hostnames and variables
- Non-secret configuration data

These files should be treated as sensitive and protected accordingly.

## Security Updates

Security updates will be released as patch versions. Subscribe to repository
releases to receive notifications of security updates.
