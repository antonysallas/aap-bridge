#!/usr/bin/env python3
"""
Interactive helper to fill in credential secrets.

Walks through each credential and prompts for secrets.
Much safer than editing YAML directly.
"""

import getpass
import sys
from pathlib import Path

import yaml


def load_secrets_template(file_path):
    """Load the secrets template."""
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
    return data.get("credentials", [])


def prompt_for_secrets(credentials):
    """Interactively prompt for each secret."""
    print("🔐 Interactive Credential Secrets Input")
    print("=" * 60)
    print("Press Enter to skip optional fields")
    print("Type 'quit' to exit\n")

    filled_credentials = []

    for idx, cred in enumerate(credentials, 1):
        print(f"\n[{idx}/{len(credentials)}] {cred['credential_name']}")
        print(f"   Type: {cred['credential_type']}")
        print(f"   Source ID: {cred['source_id']}")
        print("-" * 60)

        filled_secrets = {}
        for secret_field, placeholder in cred['secrets'].items():
            # Provide helpful prompts based on field name
            if 'password' in secret_field.lower():
                prompt = f"   Enter {secret_field} (hidden): "
                value = getpass.getpass(prompt)
            elif 'key' in secret_field.lower() and 'ssh' in secret_field.lower():
                print(f"   Enter {secret_field} (multi-line SSH key):")
                print("   Paste key and press Ctrl+D when done:")
                lines = []
                try:
                    while True:
                        line = input()
                        lines.append(line)
                except EOFError:
                    value = '\n'.join(lines)
            elif 'token' in secret_field.lower():
                value = getpass.getpass(f"   Enter {secret_field} (hidden): ")
            else:
                value = input(f"   Enter {secret_field}: ")

            if value.lower() == 'quit':
                print("\n⚠️  Exiting... Partial data saved.")
                return filled_credentials

            if value:  # Only add non-empty values
                filled_secrets[secret_field] = value

        if filled_secrets:
            filled_credentials.append({
                "credential_name": cred["credential_name"],
                "credential_type": cred["credential_type"],
                "source_id": cred["source_id"],
                "secrets": filled_secrets
            })
            print(f"   ✅ Saved {len(filled_secrets)} secrets")
        else:
            print(f"   ⚠️  No secrets provided - skipped")

    return filled_credentials


def save_filled_secrets(credentials, output_file):
    """Save filled secrets to file."""
    with open(output_file, 'w') as f:
        f.write("# FILLED CREDENTIAL SECRETS\n")
        f.write("# ⚠️  KEEP THIS FILE SECURE - Contains plaintext secrets!\n")
        f.write("# Delete after migration completes\n\n")
        yaml.dump({"credentials": credentials}, f, default_flow_style=False)


def update_playbook_with_secrets(playbook_file, secrets_data):
    """Update the playbook with actual secrets."""
    print(f"\n📝 Updating playbook with secrets...")

    with open(playbook_file, 'r') as f:
        playbook = yaml.safe_load(f)

    # Create lookup map
    secrets_map = {}
    for cred in secrets_data:
        secrets_map[cred["credential_name"]] = cred["secrets"]

    # Update playbook tasks
    updated_count = 0
    for play in playbook:
        for task in play.get("tasks", []):
            task_name = task.get("name", "")
            if "Create credential:" in task_name:
                cred_name = task_name.replace("Create credential:", "").strip()

                if cred_name in secrets_map:
                    inputs = task.get("awx.awx.credential", {}).get("inputs", {})

                    for field, value in inputs.items():
                        if value.startswith("REPLACE_WITH_ACTUAL_"):
                            actual_field = field
                            if actual_field in secrets_map[cred_name]:
                                inputs[field] = secrets_map[cred_name][actual_field]
                                updated_count += 1

    # Save updated playbook
    with open(playbook_file, 'w') as f:
        f.write("---\n")
        f.write("# CREDENTIAL MIGRATION PLAYBOOK\n")
        f.write("# Secrets filled - Ready to run!\n\n")
        yaml.dump(playbook, f, default_flow_style=False, sort_keys=False)

    print(f"✅ Updated {updated_count} secret fields in playbook")


def main():
    migration_dir = Path("credential_migration")

    if not migration_dir.exists():
        print("❌ ERROR: credential_migration/ directory not found")
        print("   Run export_credentials_for_migration.py first")
        sys.exit(1)

    secrets_template = migration_dir / "secrets_template.yml"
    playbook_file = migration_dir / "migrate_credentials.yml"

    if not secrets_template.exists():
        print(f"❌ ERROR: {secrets_template} not found")
        print("   Run export_credentials_for_migration.py first")
        sys.exit(1)

    try:
        # Load template
        credentials = load_secrets_template(secrets_template)

        if not credentials:
            print("✅ No credentials need secrets - all non-secret fields only!")
            sys.exit(0)

        print(f"Found {len(credentials)} credentials needing secrets\n")

        # Prompt for secrets
        filled = prompt_for_secrets(credentials)

        if not filled:
            print("\n⚠️  No secrets filled - exiting")
            sys.exit(0)

        # Save filled secrets
        filled_secrets_file = migration_dir / "filled_secrets.yml"
        save_filled_secrets(filled, filled_secrets_file)
        print(f"\n💾 Saved filled secrets to: {filled_secrets_file}")

        # Update playbook
        update_playbook_with_secrets(playbook_file, filled)

        print(f"\n✅ SUCCESS!")
        print(f"\n🚀 Ready to migrate!")
        print(f"   Run: ansible-playbook {playbook_file}")

        print(f"\n⚠️  SECURITY REMINDER:")
        print(f"   - {filled_secrets_file} contains plaintext secrets")
        print(f"   - Delete after migration: rm {filled_secrets_file}")

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
