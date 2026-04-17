"""Unit tests for Vault client."""

from unittest.mock import patch

import pytest
from hvac.exceptions import VaultError as HvacVaultError

from aap_migration.client.exceptions import VaultError
from aap_migration.client.vault_client import VaultClient
from aap_migration.config import VaultConfig


@pytest.fixture
def vault_config():
    """Mock Vault configuration."""
    return VaultConfig(
        url="https://vault.example.com:8200",
        role_id="test-role",
        secret_id="test-secret",
        mount_point="aap",
        path_prefix="migration",
        verify_ssl=False,
    )


@pytest.fixture
def mock_hvac_client():
    """Mock hvac.Client."""
    with patch("hvac.Client") as mock:
        client_instance = mock.return_value
        client_instance.auth.approle.login.return_value = {
            "auth": {
                "client_token": "test-token",
                "lease_duration": 3600,
                "renewable": True,
            }
        }
        yield client_instance


class TestVaultClient:
    """Tests for VaultClient."""

    def test_initialization(self, vault_config, mock_hvac_client):
        """Test client initialization and authentication."""
        client = VaultClient(vault_config)

        assert client.vault_url == vault_config.url
        assert client.mount_point == "aap"
        assert client.path_prefix == "migration"
        assert client._authenticated is True
        mock_hvac_client.auth.approle.login.assert_called_once_with(
            role_id=vault_config.role_id,
            secret_id=vault_config.secret_id,
        )

    def test_build_secret_path(self, vault_config, mock_hvac_client):
        """Test secret path building."""
        client = VaultClient(vault_config)

        assert client._build_secret_path("test") == "migration/test"
        assert client._build_secret_path("/test/") == "migration/test"

        client.path_prefix = ""
        assert client._build_secret_path("test") == "test"

    def test_read_secret(self, vault_config, mock_hvac_client):
        """Test reading a secret with mount_point."""
        client = VaultClient(vault_config)
        mock_hvac_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"token": "aap-token"}}
        }

        secret = client.read_secret("source")

        assert secret == {"token": "aap-token"}
        mock_hvac_client.secrets.kv.v2.read_secret_version.assert_called_once_with(
            path="migration/source",
            version=None,
            mount_point="aap",
        )

    def test_read_secret_failure(self, vault_config, mock_hvac_client):
        """Test read failure raises VaultError."""
        client = VaultClient(vault_config)
        mock_hvac_client.secrets.kv.v2.read_secret_version.side_effect = HvacVaultError(
            "Read failed"
        )

        with pytest.raises(VaultError, match="Failed to read secret"):
            client.read_secret("source")

    def test_write_secret(self, vault_config, mock_hvac_client):
        """Test writing a secret with mount_point."""
        client = VaultClient(vault_config)
        mock_hvac_client.secrets.kv.v2.create_or_update_secret.return_value = {
            "data": {"version": 1}
        }

        client.write_secret("target", {"token": "new-token"})

        mock_hvac_client.secrets.kv.v2.create_or_update_secret.assert_called_once_with(
            path="migration/target",
            secret={"token": "new-token"},
            cas=None,
            mount_point="aap",
        )

    def test_list_secrets(self, vault_config, mock_hvac_client):
        """Test listing secrets with mount_point."""
        client = VaultClient(vault_config)
        mock_hvac_client.secrets.kv.v2.list_secrets.return_value = {
            "data": {"keys": ["source", "target"]}
        }

        secrets = client.list_secrets()

        assert secrets == ["source", "target"]
        mock_hvac_client.secrets.kv.v2.list_secrets.assert_called_once_with(
            path="migration",
            mount_point="aap",
        )

    def test_validate_credential_success(self, vault_config, mock_hvac_client):
        """Test credential validation success."""
        client = VaultClient(vault_config)
        mock_hvac_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"token": "exists"}}
        }

        assert client.validate_credential("source", ["token"]) is True

    def test_validate_credential_missing_field(self, vault_config, mock_hvac_client):
        """Test credential validation failure on missing field."""
        client = VaultClient(vault_config)
        mock_hvac_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"other": "value"}}
        }

        assert client.validate_credential("source", ["token"]) is False

    def test_is_authenticated(self, vault_config, mock_hvac_client):
        """Test authentication check."""
        client = VaultClient(vault_config)
        mock_hvac_client.is_authenticated.return_value = True
        assert client.is_authenticated() is True

    def test_close(self, vault_config, mock_hvac_client):
        """Test closing the client connection."""
        client = VaultClient(vault_config)
        client.close()
        mock_hvac_client.adapter.close.assert_called_once()
