"""Resource importers for importing data to AAP 2.6.

This module provides a base importer class and resource-specific importers
that handle dependency resolution, bulk operations, and conflict handling.
"""

import asyncio
from collections.abc import Callable
from typing import Any

from aap_migration.client.aap_target_client import AAPTargetClient
from aap_migration.client.bulk_operations import BulkOperations
from aap_migration.client.exceptions import APIError, ConflictError
from aap_migration.config import PerformanceConfig
from aap_migration.migration.state import MigrationState
from aap_migration.utils.idempotency import compare_resources
from aap_migration.utils.logging import get_logger

logger = get_logger(__name__)


class ResourceImporter:
    """Base class for importing resources to AAP 2.6.

    Handles dependency resolution, conflict detection, and state tracking.
    """

    # Dependency mapping: field_name -> resource_type
    DEPENDENCIES = {}

    # Identifier field used for uniqueness checks (override in subclasses if different)
    IDENTIFIER_FIELD = "name"

    def __init__(
        self,
        client: AAPTargetClient,
        state: MigrationState,
        performance_config: PerformanceConfig,
        resource_mappings: dict[str, dict[str, str]] | None = None,
    ):
        """Initialize resource importer.

        Args:
            client: AAP target client instance
            state: Migration state manager
            performance_config: Performance configuration
            resource_mappings: Optional resource name mappings from config/mappings.yaml
        """
        self.client = client
        self.state = state
        self.performance_config = performance_config
        self.resource_mappings = resource_mappings or {}
        self.stats = {
            "imported_count": 0,
            "error_count": 0,
            "conflict_count": 0,
            "skipped_count": 0,
        }
        # Track issues for reporting
        self.unresolved_dependencies: list[dict[str, Any]] = []
        self.placeholder_resources: list[dict[str, Any]] = []
        self.import_errors: list[dict[str, Any]] = []

    async def import_resource(
        self,
        resource_type: str,
        source_id: int,
        data: dict[str, Any],
        resolve_dependencies: bool = True,
    ) -> dict[str, Any] | None:
        """Import a single resource to AAP 2.6.

        Args:
            resource_type: Type of resource being imported
            source_id: Source resource ID (from AAP 2.3)
            data: Transformed resource data
            resolve_dependencies: Whether to resolve foreign key dependencies

        Returns:
            Created resource data or None if skipped
        """
        # Check if already imported
        if self.state.is_migrated(resource_type, source_id):
            logger.debug(
                "resource_already_imported",
                resource_type=resource_type,
                source_id=source_id,
            )
            self.stats["skipped_count"] += 1
            return None

        # Mark as in progress
        self.state.mark_in_progress(
            resource_type=resource_type,
            source_id=source_id,
            source_name=data.get(self.IDENTIFIER_FIELD, data.get("name", "unknown")),
            phase="import",
        )

        try:
            # Resolve dependencies
            if resolve_dependencies:
                data = await self._resolve_dependencies(resource_type, data)

            # Remove None/null values from data before API call
            # AAP 2.6 API requires null-valued fields to be absent, not sent as null
            # EXCEPTION: Preserve None for credential ownership fields (organization/user/team)
            # Credentials require at least one ownership field, even if None
            ownership_fields = {"user", "team"}
            data = {k: v for k, v in data.items() if v is not None or k in ownership_fields}

            # Create resource
            result = await self.client.create_resource(
                resource_type=resource_type,
                data=data,
                check_exists=True,
            )

            # Mark as completed
            self.state.mark_completed(
                resource_type=resource_type,
                source_id=source_id,
                target_id=result["id"],
                target_name=result.get(self.IDENTIFIER_FIELD) or result.get("name"),
            )

            self.stats["imported_count"] += 1

            logger.info(
                "resource_imported",
                resource_type=resource_type,
                source_id=source_id,
                target_id=result["id"],
            )

            return result

        except ConflictError as e:
            # Handle conflict - resource already exists (409)
            logger.warning(
                "resource_conflict",
                resource_type=resource_type,
                source_id=source_id,
                error=str(e),
            )

            # Try to resolve conflict
            existing = await self._handle_conflict(resource_type, source_id, data)
            if existing:
                self.stats["conflict_count"] += 1
                return existing
            else:
                self.stats["error_count"] += 1
                self.state.mark_failed(
                    resource_type=resource_type,
                    source_id=source_id,
                    error_message=f"Conflict ({type(e).__name__}): {str(e)}",
                )
                return None

        except APIError as e:
            # Check if it's an "already exists" error (400 with specific message)
            error_str = str(e).lower()
            is_already_exists = "already exists" in error_str or (
                e.response
                and any(
                    "already exists" in str(v).lower()
                    for v in (e.response.values() if isinstance(e.response, dict) else [])
                )
            )

            if is_already_exists:
                # Treat as conflict - resource already exists (400 with "already exists")
                logger.warning(
                    "resource_already_exists",
                    resource_type=resource_type,
                    source_id=source_id,
                    error=str(e),
                )

                # Try to resolve conflict
                existing = await self._handle_conflict(resource_type, source_id, data)
                if existing:
                    self.stats["conflict_count"] += 1
                    return existing
                else:
                    self.stats["error_count"] += 1
                    self.state.mark_failed(
                        resource_type=resource_type,
                        source_id=source_id,
                        error_message=f"Already exists ({type(e).__name__}): {str(e)}",
                    )
                    return None
            else:
                # Not an "already exists" error - re-raise
                raise

        except Exception as e:
            logger.error(
                "resource_import_failed",
                resource_type=resource_type,
                source_id=source_id,
                error=str(e),
            )

            self.stats["error_count"] += 1
            self.state.mark_failed(
                resource_type=resource_type,
                source_id=source_id,
                error_message=f"{type(e).__name__}: {str(e)}",
            )

            # Track error for reporting
            self.import_errors.append(
                {
                    "resource_type": resource_type,
                    "source_id": source_id,
                    "name": data.get("name", "unknown"),
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )

            return None

    async def _resolve_dependencies(
        self, resource_type: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Resolve foreign key dependencies using ID mappings.

        Args:
            resource_type: Type of resource
            data: Resource data

        Returns:
            Data with resolved dependencies
        """
        resolved = dict(data)
        dependencies = self._get_dependencies(resource_type)
        resource_source_id = data.get("_source_id") or data.get("id")

        logger.debug(
            "dependency_resolution_start",
            resource_type=resource_type,
            source_id=resource_source_id,
            source_name=data.get("name"),
            dependencies=dependencies,
            data_fields=list(data.keys()),
        )

        for field, dep_resource_type in dependencies.items():
            if field in data and data[field]:
                dep_source_id = data[field]

                logger.debug(
                    "resolving_dependency_field",
                    resource_type=resource_type,
                    source_id=resource_source_id,
                    field=field,
                    dep_source_id=dep_source_id,
                    dep_resource_type=dep_resource_type,
                )

                # Get mapped target ID
                target_id = self.state.get_mapped_id(dep_resource_type, dep_source_id)

                logger.debug(
                    "dependency_mapping_lookup",
                    resource_type=resource_type,
                    source_id=resource_source_id,
                    field=field,
                    dep_resource_type=dep_resource_type,
                    dep_source_id=dep_source_id,
                    target_id=target_id,
                    found=target_id is not None,
                )

                if target_id:
                    resolved[field] = target_id
                    logger.debug(
                        "dependency_resolved",
                        resource_type=resource_type,
                        source_id=resource_source_id,
                        field=field,
                        dep_source_id=dep_source_id,
                        target_id=target_id,
                    )
                else:
                    # Track unresolved dependency for reporting
                    self.unresolved_dependencies.append(
                        {
                            "resource_type": resource_type,
                            "resource_name": data.get("name", "unknown"),
                            "source_id": resource_source_id,
                            "dependency_field": field,
                            "dependency_type": dep_resource_type,
                            "missing_source_id": dep_source_id,
                            "error": f"No mapping found for {dep_resource_type} ID {dep_source_id}",
                        }
                    )

                    logger.warning(
                        "unresolved_dependency",
                        resource_type=resource_type,
                        source_id=resource_source_id,
                        source_name=data.get("name"),
                        field=field,
                        dep_source_id=dep_source_id,
                        dep_resource_type=dep_resource_type,
                    )

                    # Remove the field to allow partial import
                    # (resource will be created without this dependency)
                    resolved.pop(field, None)

        return resolved

    def _get_dependencies(self, resource_type: str) -> dict[str, str]:
        """Get dependency mapping for resource type.

        Args:
            resource_type: Type of resource

        Returns:
            Dictionary mapping field names to resource types
        """
        # Use class-level DEPENDENCIES or return empty dict
        return self.DEPENDENCIES

    async def _handle_conflict(
        self, resource_type: str, source_id: int, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Handle resource conflict (already exists).

        Args:
            resource_type: Type of resource
            source_id: Source resource ID
            data: Resource data

        Returns:
            Existing resource data or None
        """
        # Try to find existing resource by name
        resource_name = data.get("name")
        if not resource_name:
            return None

        try:
            existing = await self.client.find_resource_by_name(resource_type, resource_name)

            if existing:
                # Compare resources to determine action
                resources_match = compare_resources(data, existing)

                if resources_match:
                    # Resources are identical - skip (idempotent)
                    logger.info(
                        "conflict_resolved_skip",
                        resource_type=resource_type,
                        source_id=source_id,
                        reason="Resources match",
                    )
                    self.state.mark_completed(
                        resource_type=resource_type,
                        source_id=source_id,
                        target_id=existing["id"],
                        target_name=existing.get("name"),
                    )
                    return existing
                else:
                    # Resources differ - update existing
                    logger.info(
                        "conflict_resolved_update",
                        resource_type=resource_type,
                        source_id=source_id,
                        reason="Resources differ",
                    )
                    updated = await self.client.update_resource(resource_type, existing["id"], data)
                    self.state.mark_completed(
                        resource_type=resource_type,
                        source_id=source_id,
                        target_id=updated["id"],
                        target_name=updated.get("name"),
                    )
                    return updated

            return None

        except Exception as e:
            logger.error(
                "conflict_resolution_failed",
                resource_type=resource_type,
                source_id=source_id,
                error=str(e),
            )
            return None

    async def _import_parallel(
        self,
        resource_type: str,
        resources: list[dict[str, Any]],
        progress_callback: Callable[[int, int, int], None] | None = None,
        concurrency: int | None = None,
    ) -> list[dict[str, Any]]:
        """Import resources concurrently with live progress updates.

        This method implements parallel import using asyncio.gather() with semaphore
        to limit concurrency. It provides real-time progress updates via the callback.

        Args:
            resource_type: Type of resource (users, teams, etc.)
            resources: List of resources to import
            progress_callback: Optional callback for progress updates.
                Called after each resource with (success_count, failed_count).
            concurrency: Optional override for max concurrent requests.
                Defaults to performance_config.max_concurrent if not specified.

        Returns:
            List of successfully imported resources

        Example:
            >>> def update_progress(success: int, failed: int):
            ...     progress.update_phase(phase_id, success, failed)
            >>> results = await importer._import_parallel(
            ...     "users", users, progress_callback=update_progress
            ... )
        """
        if not resources:
            return []

        # Shared counters (thread-safe with asyncio single-threaded model)
        success_count = 0
        failed_count = 0
        skipped_count = 0
        results = []

        # Semaphore limits concurrent requests (use override or default)
        max_concurrent = concurrency or self.performance_config.max_concurrent
        semaphore = asyncio.Semaphore(max_concurrent)

        async def import_with_semaphore(resource: dict[str, Any]) -> dict[str, Any] | None:
            """Import a single resource with semaphore control."""
            nonlocal success_count, failed_count, skipped_count

            async with semaphore:
                try:
                    # Extract source ID
                    source_id = resource.pop("_source_id", resource.get("id"))

                    # Import resource
                    result = await self.import_resource(
                        resource_type=resource_type,
                        source_id=source_id,
                        data=resource,
                    )

                    # Update counters
                    if result:
                        # Count managed/built-in types as success since mapping was successful
                        # (_skipped means it was mapped but not patched because it's managed)
                        success_count += 1
                        results.append(result)
                    else:
                        # Result is None if skipped (already migrated) or failed
                        # Check if it was skipped (already imported)
                        if not self.state.is_migrated(resource_type, source_id):
                            failed_count += 1
                        # Else: already migrated (skipped), count handled by pre-check logic mostly
                        # But if import_resource returns None for already migrated, we don't track it here
                        # because export_import.py handles pre-check skips.

                    # Update progress after each resource
                    if progress_callback:
                        # Callback expects: success, failed, skipped
                        progress_callback(success_count, failed_count, skipped_count)

                    return result

                except Exception as e:
                    failed_count += 1

                    # Update progress even on exception
                    if progress_callback:
                        progress_callback(success_count, failed_count, skipped_count)

                    logger.error(
                        "parallel_import_error",
                        resource_type=resource_type,
                        source_id=source_id,
                        source_name=resource.get("name", "unknown"),
                        error=str(e),
                    )

                    # Track error for reporting
                    self.import_errors.append(
                        {
                            "resource_type": resource_type,
                            "source_id": source_id,
                            "name": resource.get("name", "unknown"),
                            "error": str(e),
                            "error_type": type(e).__name__,
                        }
                    )

                    return None

        # Create tasks for all resources
        tasks = [import_with_semaphore(resource) for resource in resources]

        # Execute concurrently (limited by semaphore)
        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info(
            "parallel_import_completed",
            resource_type=resource_type,
            total=len(resources),
            success=success_count,
            failed=failed_count,
        )

        return results

    def get_stats(self) -> dict[str, int]:
        """Get import statistics.

        Returns:
            Dictionary with import statistics
        """
        return self.stats.copy()

    def reset_stats(self) -> None:
        """Reset import statistics."""
        self.stats = {
            "imported_count": 0,
            "error_count": 0,
            "conflict_count": 0,
            "skipped_count": 0,
        }

    def get_import_errors(self) -> list[dict[str, Any]]:
        """Get list of import errors for reporting.

        Returns:
            List of error dictionaries with resource details including:
            - resource_type: Type of resource that failed
            - source_id: Source resource ID
            - name: Resource name
            - error: Error message
            - error_type: Exception type name
        """
        return self.import_errors.copy()


class LabelImporter(ResourceImporter):
    """Importer for label resources."""

    DEPENDENCIES = {
        "organization": "organizations",
    }

    async def import_labels(
        self,
        labels: list[dict[str, Any]],
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> list[dict[str, Any]]:
        """Import multiple labels concurrently with live progress updates.

        Args:
            labels: List of label data
            progress_callback: Optional callback for progress updates.
                Called after each label with (success_count, failed_count).

        Returns:
            List of created label data
        """
        return await self._import_parallel("labels", labels, progress_callback)


class CredentialTypeImporter(ResourceImporter):
    """Importer for credential type resources.

    Credential types are pre-created in the target environment before migration.
    This importer PATCHes existing resources instead of POSTing new ones.
    """

    DEPENDENCIES = {
        "organization": "organizations",
    }

    async def import_resource(
        self,
        resource_type: str,
        source_id: int,
        data: dict[str, Any],
        resolve_dependencies: bool = True,
    ) -> dict[str, Any] | None:
        """Import credential_type by PATCHing existing resource in target.

        Credential types are pre-created in the target environment. This method
        finds the existing resource by name and PATCHes it with organization
        and description from the source.

        Args:
            resource_type: Type of resource being imported
            source_id: Source resource ID (from AAP 2.3)
            data: Transformed resource data
            resolve_dependencies: Whether to resolve foreign key dependencies

        Returns:
            Patched resource data or None if skipped/failed
        """
        # Check if already imported
        if self.state.is_migrated(resource_type, source_id):
            logger.debug(
                "resource_already_imported",
                resource_type=resource_type,
                source_id=source_id,
            )
            self.stats["skipped_count"] += 1
            return None

        name = data.get("name")
        if not name:
            logger.error("credential_type_missing_name", source_id=source_id)
            self.stats["error_count"] += 1
            return None

        # Mark as in progress
        self.state.mark_in_progress(
            resource_type=resource_type,
            source_id=source_id,
            source_name=name,
            phase="import",
        )

        try:
            # Find existing credential_type in target by name
            results = await self.client.get("credential_types/", params={"name": name})
            resources = results.get("results", [])

            if resources:
                # Found - PATCH existing
                target_id = resources[0]["id"]
                is_managed = resources[0].get("managed", False)

                # Skip PATCH for managed (built-in) credential types
                if is_managed:
                    logger.info(
                        "credential_type_managed_skip_patch",
                        name=name,
                        source_id=source_id,
                        target_id=target_id,
                        message="Skipping PATCH for managed credential type - saving mapping only",
                    )
                    self.state.save_id_mapping(
                        resource_type=resource_type,
                        source_id=source_id,
                        target_id=target_id,
                        source_name=name,
                        target_name=name,
                    )
                    self.state.mark_completed(
                        resource_type=resource_type,
                        source_id=source_id,
                        target_id=target_id,
                        target_name=name,
                    )
                    self.stats["skipped_count"] += 1
                    # Return skipped signal
                    return {"id": target_id, "name": name, "_skipped": True}

                # Resolve dependencies (organization)
                if resolve_dependencies:
                    data = await self._resolve_dependencies(resource_type, data)

                # Build PATCH payload (organization, description only)
                patch_data = {}
                if data.get("organization"):
                    patch_data["organization"] = data["organization"]
                if data.get("description"):
                    patch_data["description"] = data["description"]

                # PATCH the credential_type if there's data to update
                if patch_data:
                    await self.client.update_resource("credential_types", target_id, patch_data)
                    logger.info(
                        "credential_type_patched",
                        name=name,
                        source_id=source_id,
                        target_id=target_id,
                        patched_fields=list(patch_data.keys()),
                    )
                else:
                    logger.info(
                        "credential_type_mapped_no_patch",
                        name=name,
                        source_id=source_id,
                        target_id=target_id,
                        message="No fields to patch - mapping only",
                    )

                result = {"id": target_id, "name": name, "_patched": bool(patch_data)}

            else:
                # Not found - CREATE new

                # Skip creation of external credential types (they must exist in target)
                if data.get("kind") == "external":
                    logger.warning(
                        "skipping_external_credential_type_creation",
                        name=name,
                        source_id=source_id,
                        message="External credential type not found in target - skipping creation per policy",
                    )
                    self.stats["skipped_count"] += 1
                    return None

                logger.info(
                    "credential_type_creating",
                    name=name,
                    source_id=source_id,
                    message="Creating new credential type",
                )

                # Resolve dependencies (organization)
                if resolve_dependencies:
                    data = await self._resolve_dependencies(resource_type, data)

                # Create resource
                result = await self.client.create_resource(
                    resource_type="credential_types",
                    data=data,
                    check_exists=False,
                )
                target_id = result["id"]
                logger.info(
                    "credential_type_created",
                    name=name,
                    source_id=source_id,
                    target_id=target_id,
                )

            # Save mapping
            self.state.save_id_mapping(
                resource_type=resource_type,
                source_id=source_id,
                target_id=target_id,
                source_name=name,
                target_name=name,
            )
            self.state.mark_completed(
                resource_type=resource_type,
                source_id=source_id,
                target_id=target_id,
                target_name=name,
            )
            self.stats["imported_count"] += 1

            return result

        except Exception as e:
            logger.error(
                "credential_type_import_failed",
                source_id=source_id,
                name=name,
                error=str(e),
            )
            self.stats["error_count"] += 1
            self.import_errors.append(
                {
                    "resource_type": resource_type,
                    "source_id": source_id,
                    "name": name,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )
            return None

    async def import_credential_types(
        self,
        credential_types: list[dict[str, Any]],
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> list[dict[str, Any]]:
        """Import multiple credential types by PATCHing pre-existing resources.

        Credential types are pre-created in the target environment before migration.
        This method finds each credential type by name and PATCHes it with
        organization and description from the source.

        Args:
            credential_types: List of credential type data
            progress_callback: Optional callback for progress updates.
                Called after each credential type with (success_count, failed_count).

        Returns:
            List of patched credential type data
        """
        logger.info(
            "credential_types_import_starting",
            total_count=len(credential_types),
            names=[ct.get("name") for ct in credential_types],
            message="PATCHing pre-created credential types in target",
        )

        # All credential types go through the same PATCH flow via import_resource()
        results = await self._import_parallel(
            "credential_types", credential_types, progress_callback
        )

        logger.info(
            "credential_types_import_completed",
            total_input=len(credential_types),
            patched_count=len(results),
            skipped_or_failed=len(credential_types) - len(results),
        )

        return results


class UserImporter(ResourceImporter):
    """Importer for user resources."""

    DEPENDENCIES = {}  # No dependencies - users can exist independently
    IDENTIFIER_FIELD = "username"  # Users use 'username' instead of 'name'

    async def import_resource(
        self,
        resource_type: str,
        source_id: int,
        data: dict[str, Any],
        resolve_dependencies: bool = True,
    ) -> dict[str, Any] | None:
        """Import a single user with password handling.

        Overrides parent to:
        1. Use 'username' field instead of 'name' for source_name tracking
        2. Add temporary password for all users (including superusers)
        3. Track users needing password reset

        Note: AAP requires a password but we cannot extract it from the source API,
        so all users (including superusers) get temporary passwords that must be reset.
        """
        import secrets

        # Check if already imported
        if self.state.is_migrated(resource_type, source_id):
            logger.debug(
                "resource_already_imported",
                resource_type=resource_type,
                source_id=source_id,
            )
            self.stats["skipped_count"] += 1
            return None

        # Mark as in progress with correct username field (users don't have 'name')
        self.state.mark_in_progress(
            resource_type=resource_type,
            source_id=source_id,
            source_name=data.get("username", "unknown"),
            phase="import",
        )

        try:
            # Remove password-related fields (cannot be migrated)
            data.pop("password", None)
            data.pop("ldap_dn", None)

            # Generate temporary password for all users (including superusers)
            # This is required because AAP API requires a password for new users
            temp_password = secrets.token_urlsafe(16)
            data["password"] = temp_password

            # Track that user needs password reset
            self.placeholder_resources.append(
                {
                    "resource_type": "users",
                    "source_id": source_id,
                    "name": data.get("username", "unknown"),
                    "action_required": "User password reset required",
                    "temp_password": temp_password,
                    "is_superuser": data.get("is_superuser", False),
                    "instructions": self._generate_user_password_instructions(data, temp_password),
                }
            )

            logger.info(
                "user_temporary_password_set",
                username=data.get("username"),
                source_id=source_id,
                is_superuser=data.get("is_superuser", False),
            )

            # Resolve dependencies (users have none, but kept for consistency)
            if resolve_dependencies:
                data = await self._resolve_dependencies(resource_type, data)

            # Create resource
            result = await self.client.create_resource(
                resource_type=resource_type,
                data=data,
                check_exists=True,
            )

            # Mark as completed
            self.state.mark_completed(
                resource_type=resource_type,
                source_id=source_id,
                target_id=result["id"],
                target_name=result.get("username"),
            )

            self.stats["imported_count"] += 1

            logger.info(
                "resource_imported",
                resource_type=resource_type,
                source_id=source_id,
                target_id=result["id"],
            )

            return result

        except ConflictError as e:
            # Handle conflict (user already exists)
            result = await self._handle_conflict(resource_type, source_id, data, e)
            if result:
                self.stats["conflict_count"] += 1
            return result

        except Exception as e:
            # Mark as failed
            error_msg = str(e)
            self.state.mark_failed(
                resource_type=resource_type,
                source_id=source_id,
                error_message=error_msg,
            )
            self.stats["error_count"] += 1

            self.import_errors.append(
                {
                    "resource_type": resource_type,
                    "source_id": source_id,
                    "name": data.get("username", "unknown"),
                    "error": error_msg,
                }
            )

            logger.error(
                "resource_import_failed",
                resource_type=resource_type,
                source_id=source_id,
                error=error_msg,
            )

            return None

    def _generate_user_password_instructions(self, user: dict[str, Any], temp_password: str) -> str:
        """Generate instructions for user password reset.

        Args:
            user: User data
            temp_password: Temporary password set during migration

        Returns:
            Markdown-formatted instructions
        """
        return f"""
## User Password Reset Required

**Username**: {user.get("username", "Unknown")}
**Email**: {user.get("email", "Not set")}

### Temporary Password:
`{temp_password}`

### Steps:
1. Communicate temporary password to user securely (not via email if possible)
2. User should log in to AAP 2.6 and immediately change password
3. Alternatively, admin can reset password via AAP UI:
   - Navigate to Access → Users
   - Find user: {user.get("username", "Unknown")}
   - Click "Edit" and set a new password
4. If using LDAP/SSO, configure external authentication

**IMPORTANT**: This temporary password should be changed immediately after first login.
"""

    async def import_users(
        self,
        users: list[dict[str, Any]],
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> list[dict[str, Any]]:
        """Import multiple users concurrently with live progress updates.

        Uses higher concurrency than other resources since users have no
        dependencies, allowing faster import throughput.

        Note: Passwords cannot be migrated - users get temporary passwords.

        Args:
            users: List of user data
            progress_callback: Optional callback for progress updates.
                Called after each user with (success_count, failed_count).

        Returns:
            List of created user data
        """
        return await self._import_parallel(
            "users",
            users,
            progress_callback,
            concurrency=self.performance_config.user_import_max_concurrent,
        )


class TeamImporter(ResourceImporter):
    """Importer for team resources."""

    DEPENDENCIES = {
        "organization": "organizations",
    }

    async def import_teams(
        self,
        teams: list[dict[str, Any]],
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> list[dict[str, Any]]:
        """Import multiple teams concurrently with live progress updates.

        Args:
            teams: List of team data
            progress_callback: Optional callback for progress updates.
                Called after each team with (success_count, failed_count).

        Returns:
            List of created team data
        """
        return await self._import_parallel("teams", teams, progress_callback)


class OrganizationImporter(ResourceImporter):
    """Importer for organization resources."""

    DEPENDENCIES = {}  # No dependencies

    async def import_organizations(
        self,
        organizations: list[dict[str, Any]],
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> list[dict[str, Any]]:
        """Import multiple organizations concurrently with live progress updates.

        Args:
            organizations: List of organization data
            progress_callback: Optional callback for progress updates.
                Called after each organization with (success_count, failed_count).

        Returns:
            List of created organization data
        """
        return await self._import_parallel("organizations", organizations, progress_callback)


class InstanceImporter(ResourceImporter):
    """Importer for instance (AAP controller node) resources.

    Instances are infrastructure nodes that cannot be created via API.
    Instead, we match source instances to existing target instances by hostname
    and create ID mappings for instance_group references.

    Uses config/mappings.yaml to map different hostnames between environments.
    """

    DEPENDENCIES = {}  # No dependencies - instances are foundational
    IDENTIFIER_FIELD = "hostname"  # Instances use 'hostname' instead of 'name'

    async def import_instances(
        self,
        instances: list[dict[str, Any]],
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> list[dict[str, Any]]:
        """Map source instances to existing target instances via configuration.

        Instances cannot be created via API - they're infrastructure nodes.
        This method finds matching instances on target and creates ID mappings.

        Uses mappings from config/mappings.yaml to resolve different hostnames.
        Falls back to exact hostname match if no explicit mapping exists.

        Args:
            instances: List of instance data from source
            progress_callback: Optional callback for progress updates.
                Called after each instance with (success_count, failed_count, skipped_count).

        Returns:
            List of matched target instance data
        """
        results = []
        success_count = 0
        failed_count = 0
        skipped_count = 0

        # Get instance hostname mappings from config/mappings.yaml
        instance_mappings = self.resource_mappings.get("instances", {})

        # Fetch all target instances once
        target_instances = await self.client.list_resources("instances")
        target_by_hostname = {inst["hostname"]: inst for inst in target_instances}

        logger.info(
            "instance_mapping_started",
            source_count=len(instances),
            target_count=len(target_instances),
            configured_mappings=len(instance_mappings),
        )

        for instance in instances:
            source_id = instance.get("_source_id") or instance.get("id")
            source_hostname = instance.get("hostname", "unknown")

            # Check if already mapped
            if self.state.is_migrated("instances", source_id):
                skipped_count += 1
                if progress_callback:
                    progress_callback(success_count, failed_count, skipped_count)
                continue

            # Mark in progress
            self.state.mark_in_progress(
                resource_type="instances",
                source_id=source_id,
                source_name=source_hostname,
                phase="import",
            )

            # Resolve target hostname (from mapping or exact match)
            target_hostname = instance_mappings.get(source_hostname, source_hostname)
            target_instance = target_by_hostname.get(target_hostname)

            if target_instance:
                # Found match - save ID mapping
                self.state.mark_completed(
                    resource_type="instances",
                    source_id=source_id,
                    target_id=target_instance["id"],
                    target_name=target_instance["hostname"],
                )
                results.append(target_instance)
                success_count += 1
                self.stats["imported_count"] += 1
                logger.info(
                    "instance_mapped",
                    source_id=source_id,
                    target_id=target_instance["id"],
                    source_hostname=source_hostname,
                    target_hostname=target_hostname,
                )
            else:
                # No match found - log warning with hint
                error_msg = (
                    f"No target instance for '{source_hostname}'. "
                    f"Add mapping to config/mappings.yaml"
                )
                self.state.mark_failed(
                    resource_type="instances",
                    source_id=source_id,
                    error=error_msg,
                )
                failed_count += 1
                self.stats["error_count"] += 1
                logger.warning(
                    "instance_not_found_on_target",
                    source_id=source_id,
                    source_hostname=source_hostname,
                    target_hostname=target_hostname,
                    hint="Add to config/mappings.yaml: instances: { source: target }",
                )

            if progress_callback:
                progress_callback(success_count, failed_count, skipped_count)

        logger.info(
            "instance_mapping_completed",
            mapped=success_count,
            failed=failed_count,
            skipped=skipped_count,
        )

        return results


class InstanceGroupImporter(ResourceImporter):
    """Importer for instance group resources."""

    DEPENDENCIES = {
        "credential": "credentials",  # For container instance groups
    }

    async def import_instance_groups(
        self,
        instance_groups: list[dict[str, Any]],
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> list[dict[str, Any]]:
        """Import multiple instance groups concurrently with live progress updates.

        Args:
            instance_groups: List of instance group data
            progress_callback: Optional callback for progress updates.
                Called after each instance group with (success_count, failed_count).

        Returns:
            List of created instance group data
        """
        return await self._import_parallel("instance_groups", instance_groups, progress_callback)


class InventoryImporter(ResourceImporter):
    """Importer for inventory resources."""

    DEPENDENCIES = {
        "organization": "organizations",
    }

    async def import_inventories(
        self,
        inventories: list[dict[str, Any]],
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> list[dict[str, Any]]:
        """Import multiple inventories concurrently with live progress updates.

        Args:
            inventories: List of inventory data
            progress_callback: Optional callback for progress updates.
                Called after each inventory with (success_count, failed_count).

        Returns:
            List of created inventory data
        """
        return await self._import_parallel("inventories", inventories, progress_callback)


class InventoryGroupImporter(ResourceImporter):
    """Importer for inventory group resources.

    Handles nested hierarchies via topological sorting to ensure parents
    are imported before children.
    Uses optimized tier-based parallel import for performance.
    """

    DEPENDENCIES = {
        "inventory": "inventories",
        "parent": "inventory_groups",  # Link to parent group
    }

    # Override the API endpoint since "inventory_groups" maps to "groups/" in AAP API
    API_ENDPOINT = "groups"

    async def import_resource(
        self,
        resource_type: str,
        source_id: int,
        data: dict[str, Any],
        resolve_dependencies: bool = True,
    ) -> dict[str, Any] | None:
        """Import inventory group with correct API endpoint.

        Overrides parent to use 'groups' endpoint instead of 'inventory_groups'.
        """
        # Use "groups" for API call but keep "inventory_groups" for state tracking
        api_resource_type = (
            self.API_ENDPOINT if resource_type == "inventory_groups" else resource_type
        )

        # Track state with original resource_type
        if self.state.is_migrated(resource_type, source_id):
            self.stats["skipped_count"] += 1
            return None

        self.state.mark_in_progress(
            resource_type=resource_type,
            source_id=source_id,
            source_name=data.get("name", "unknown"),
            phase="import",
        )

        try:
            if resolve_dependencies:
                data = await self._resolve_dependencies(resource_type, data)

            # Use correct API endpoint
            result = await self.client.create_resource(
                resource_type=api_resource_type,
                data=data,
                check_exists=True,
            )

            target_id = result.get("id")
            self.state.mark_completed(
                resource_type=resource_type,
                source_id=source_id,
                target_id=target_id,
            )

            self.stats["imported_count"] += 1
            logger.info(
                "resource_imported",
                resource_type=resource_type,
                source_id=source_id,
                target_id=target_id,
            )

            return result

        except Exception as e:
            self.state.mark_failed(
                resource_type=resource_type,
                source_id=source_id,
                error_message=str(e),
            )
            self.stats["error_count"] += 1

            # Track error for reporting
            self.import_errors.append(
                {
                    "resource_type": resource_type,
                    "source_id": source_id,
                    "name": data.get("name", "unknown"),
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )

            raise

    async def import_inventory_groups(
        self,
        groups: list[dict[str, Any]],
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> list[dict[str, Any]]:
        """Import multiple inventory groups with topological sorting and parallel execution.

        1. Sorts groups into tiers (root, children of root, grandchildren, etc.)
        2. Imports each tier in parallel using _import_parallel
        3. Injects 'parent' field so relationships are created immediately

        Args:
            groups: List of inventory group data
            progress_callback: Optional callback for progress updates

        Returns:
            List of created inventory group data
        """
        if not groups:
            return []

        # Sort groups into tiers (list of lists)
        # Tier 0: Roots
        # Tier 1: Children of Tier 0
        # ...
        group_tiers = self._topological_sort_tiers(groups)

        all_results = []
        total_success = 0
        total_failed = 0
        total_skipped = 0

        logger.info(
            "importing_inventory_groups_tiered",
            total_groups=len(groups),
            num_tiers=len(group_tiers),
            tier_sizes=[len(tier) for tier in group_tiers],
        )

        # Create a cumulative progress callback
        def tier_progress_cb(success, failed, skipped):
            nonlocal total_success, total_failed, total_skipped
            # This callback receives totals for the CURRENT batch/tier
            # We need to accumulate them across tiers for the global progress bar
            # But _import_parallel tracks its own cumulative count from 0.
            # So we need to add the *previous* tiers' totals to the current tier's totals
            if progress_callback:
                progress_callback(
                    total_success + success,
                    total_failed + failed,
                    total_skipped + skipped,
                )

        for i, tier_groups in enumerate(group_tiers):
            logger.info("importing_group_tier", tier=i, count=len(tier_groups))

            # Import this tier in parallel
            results = await self._import_parallel(
                "inventory_groups", tier_groups, progress_callback=tier_progress_cb
            )

            # Accumulate totals for next tier's callback base
            # Count actually returned results (successes)
            tier_success = len([r for r in results if r and not r.get("_skipped")])
            tier_skipped = len([r for r in results if r and r.get("_skipped")])
            # Failed is implicit: size of tier - success - skipped
            # (Assuming _import_parallel returns failures as None)
            tier_failed = len(tier_groups) - tier_success - tier_skipped

            # Let's update the running totals based on the *final* callback values of the tier
            total_success += tier_success
            total_failed += tier_failed
            total_skipped += tier_skipped

            all_results.extend(results)

        return all_results

    def _topological_sort_tiers(self, groups: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
        """Sort groups into dependency tiers for parallel import.

        Optimized O(N) algorithm.

        1. Build adjacency map: parent_id -> [child_ids]
        2. Build parent map: child_id -> parent_id (injects 'parent' field into data)
        3. Identify roots (no parent)
        4. BFS to build tiers

        Args:
            groups: List of inventory group data

        Returns:
            List of lists (tiers), where Tier 0 is roots, Tier 1 is their children, etc.
        """
        # Index groups by ID
        group_by_id = {g.get("_source_id", g.get("id")): g for g in groups}

        # Adjacency list: parent_id -> list of child_ids
        children_map = {}
        # Parent map: child_id -> parent_id
        parent_map = {}

        # Initialize
        for gid in group_by_id:
            children_map[gid] = []

        # Build graph (O(N) - iterate once)
        for group in groups:
            parent_id = group.get("_source_id", group.get("id"))
            child_ids = group.get("children", [])

            for child_id in child_ids:
                if child_id in group_by_id:  # Only track if child is in this import set
                    children_map[parent_id].append(child_id)
                    parent_map[child_id] = parent_id

                    # INJECT PARENT FIELD!
                    # This enables the importer to link them automatically via DEPENDENCIES
                    group_by_id[child_id]["parent"] = parent_id

            # Remove children list to avoid API errors (cleaned up by importer usually, but good to be safe)
            group.pop("children", None)

        # Identify roots (groups with no parent in this set)
        roots = []
        for gid, group in group_by_id.items():
            if gid not in parent_map:
                roots.append(group)

        # BFS to build tiers
        tiers = []
        current_tier = roots

        visited = set()
        for g in roots:
            visited.add(g.get("_source_id", g.get("id")))

        while current_tier:
            tiers.append(current_tier)
            next_tier = []

            for group in current_tier:
                parent_id = group.get("_source_id", group.get("id"))
                children_ids = children_map.get(parent_id, [])

                for child_id in children_ids:
                    if child_id not in visited:
                        visited.add(child_id)
                        next_tier.append(group_by_id[child_id])

            current_tier = next_tier

        # Check for circular dependencies or orphaned loops
        if len(visited) != len(groups):
            missing_count = len(groups) - len(visited)
            logger.warning(
                "circular_dependency_detected",
                total_groups=len(groups),
                visited_groups=len(visited),
                missing=missing_count,
                message="Some groups were skipped due to circular dependencies or disconnection",
            )
            # We could raise ValueError, or just log warning and return what we have.
            # Returning what we have is safer for partial success.

        return tiers


class InventorySourceImporter(ResourceImporter):
    """Importer for inventory source resources.

    Inventory sources can have multiple dependencies:
    - inventory (required)
    - source_project (optional, for SCM sources)
    - credential (optional, for authentication)
    - execution_environment (optional, for custom execution environments)
    """

    DEPENDENCIES = {
        "inventory": "inventories",
        "source_project": "projects",
        "credential": "credentials",
        "execution_environment": "execution_environments",
    }

    async def import_inventory_sources(
        self,
        sources: list[dict[str, Any]],
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> list[dict[str, Any]]:
        """Import multiple inventory sources concurrently with live progress updates.

        Handles multiple dependencies (inventory, project, credential).
        Preserves source configuration (source_vars, update options, etc.).

        Args:
            sources: List of inventory source data
            progress_callback: Optional callback for progress updates.
                Called after each inventory source with (success_count, failed_count).

        Returns:
            List of created inventory source data
        """
        return await self._import_parallel("inventory_sources", sources, progress_callback)


class ScheduleImporter(ResourceImporter):
    """Importer for schedule resources.

    Schedules depend on unified_job_template which can reference:
    - job_templates
    - workflow_job_templates
    - inventory_sources
    """

    DEPENDENCIES = {}  # Handled manually in _resolve_dependencies

    async def _resolve_dependencies(
        self, resource_type: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Resolve dependencies with polymorphic unified_job_template handling."""
        # Call parent to handle any standard dependencies
        resolved = await super()._resolve_dependencies(resource_type, data)

        # Handle polymorphic unified_job_template
        if "unified_job_template" in data:
            ujt_id = data["unified_job_template"]
            # _ujt_resource_type is added by ScheduleTransformer
            ujt_type = data.get("_ujt_resource_type")

            # Always remove the internal metadata field from the payload
            resolved.pop("_ujt_resource_type", None)

            if ujt_id and ujt_type:
                target_id = self.state.get_mapped_id(ujt_type, ujt_id)
                if target_id:
                    resolved["unified_job_template"] = target_id
                    logger.debug(
                        "schedule_dependency_resolved",
                        source_id=data.get("id"),
                        ujt_type=ujt_type,
                        ujt_id=ujt_id,
                        target_id=target_id,
                    )
                else:
                    # Log warning but keep original ID (will likely fail)
                    logger.warning(
                        "schedule_dependency_unresolved",
                        source_id=data.get("id"),
                        ujt_type=ujt_type,
                        ujt_id=ujt_id,
                        message=f"Could not resolve {ujt_type} ID {ujt_id}",
                    )
            elif ujt_id:
                # Missing type information
                logger.warning(
                    "schedule_missing_ujt_type",
                    source_id=data.get("id"),
                    ujt_id=ujt_id,
                    message="Missing _ujt_resource_type for schedule",
                )

        return resolved

    async def import_schedules(
        self,
        schedules: list[dict[str, Any]],
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> list[dict[str, Any]]:
        """Import multiple schedules concurrently with live progress updates.

        Handles unified_job_template dependency which can point to various
        schedulable resources (job templates, workflows, inventory sources).
        Preserves RRULE format for recurrence patterns.

        Args:
            schedules: List of schedule data
            progress_callback: Optional callback for progress updates.
                Called after each schedule with (success_count, failed_count).

        Returns:
            List of created schedule data
        """
        return await self._import_parallel("schedules", schedules, progress_callback)


class WorkflowNodeImporter(ResourceImporter):
    """Importer for workflow node resources.

    Workflow nodes form a directed graph with edges. Nodes depend on:
    - workflow_job_template (required)
    - unified_job_template (optional, for non-approval nodes)

    Edge relationships (success_nodes, failure_nodes, always_nodes) are
    removed during initial import and should be handled separately.
    """

    DEPENDENCIES = {
        "workflow_job_template": "workflow_job_templates",
        "unified_job_template": "unified_job_templates",
    }

    async def import_workflow_nodes(
        self,
        nodes: list[dict[str, Any]],
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> list[dict[str, Any]]:
        """Import multiple workflow nodes.

        Handles workflow and template dependency resolution.
        Edge relationships are removed before import (handled separately).

        Args:
            nodes: List of workflow node data
            progress_callback: Optional callback for progress updates.
                Called after each node with (success_count, failed_count).

        Returns:
            List of created workflow node data
        """
        results = []
        success_count = 0
        failed_count = 0
        skipped_count = 0

        for node in nodes:
            source_id = node.pop("_source_id", node.get("id"))

            # Remove edge fields before import (will be handled separately)
            node.pop("success_nodes", None)
            node.pop("failure_nodes", None)
            node.pop("always_nodes", None)

            try:
                result = await self.import_resource(
                    resource_type="workflow_nodes",
                    source_id=source_id,
                    data=node,
                )
                if result:
                    results.append(result)
                    success_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                failed_count += 1

                # Log the error
                logger.error(
                    "workflow_node_import_failed",
                    resource_type="workflow_nodes",
                    source_id=source_id,
                    node_name=node.get("identifier", "unknown"),
                    error=str(e),
                )

                # Track error for reporting
                self.import_errors.append(
                    {
                        "resource_type": "workflow_nodes",
                        "source_id": source_id,
                        "name": node.get("identifier", "unknown"),
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                )

                raise
            finally:
                # Update progress after each node
                if progress_callback:
                    progress_callback(
                        self.stats["imported_count"],
                        self.stats["error_count"],
                        self.stats["skipped_count"],
                    )

        return results


class ExecutionEnvironmentImporter(ResourceImporter):
    """Importer for execution environment resources.

    Execution Environments are container images that provide the Ansible
    runtime environment. They depend on:
    - organization (required)
    - credential (optional, for private registries)
    """

    DEPENDENCIES = {
        "organization": "organizations",
        "credential": "credentials",
    }

    async def import_execution_environments(
        self,
        ees: list[dict[str, Any]],
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> list[dict[str, Any]]:
        """Import multiple execution environments concurrently with live progress updates.

        Handles organization and optional credential dependency resolution.

        Args:
            ees: List of execution environment data
            progress_callback: Optional callback for progress updates.
                Called after each execution environment with (success_count, failed_count).

        Returns:
            List of created execution environment data
        """
        return await self._import_parallel("execution_environments", ees, progress_callback)


class RBACImporter(ResourceImporter):
    """Importer for RBAC (Role-Based Access Control) role assignments.

    Handles granting roles to users and teams on various resource types.
    Does not have traditional dependencies as it operates on already-imported resources.
    """

    async def import_role_assignments(
        self, assignments: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Import RBAC role assignments.

        Each assignment grants a specific role to a user or team on a resource.

        Args:
            assignments: List of role assignment data with structure:
                {
                    "resource_type": "organizations",
                    "resource_id": 123,  # Source resource ID
                    "role": "admin",
                    "user": 456,  # Source user ID (mutually exclusive with team)
                    "team": 789,  # Source team ID (mutually exclusive with user)
                }

        Returns:
            List of successfully granted role assignment data
        """
        results = []

        for assignment in assignments:
            try:
                resource_type = assignment["resource_type"]
                source_resource_id = assignment["resource_id"]
                role_name = assignment["role"]
                source_user_id = assignment.get("user")
                source_team_id = assignment.get("team")

                # Resolve resource ID
                target_resource_id = self.state.get_mapped_id(resource_type, source_resource_id)
                if not target_resource_id:
                    logger.warning(
                        "rbac_resource_not_found",
                        resource_type=resource_type,
                        source_id=source_resource_id,
                    )
                    continue

                # Resolve user or team ID (prefer user if both are present)
                if source_user_id:
                    target_principal_id = self.state.get_mapped_id("users", source_user_id)
                    if not target_principal_id:
                        logger.warning(
                            "rbac_user_not_found",
                            source_user_id=source_user_id,
                        )
                        continue
                    principal_key = "user"
                    principal_id = target_principal_id
                elif source_team_id:
                    target_principal_id = self.state.get_mapped_id("teams", source_team_id)
                    if not target_principal_id:
                        logger.warning(
                            "rbac_team_not_found",
                            source_team_id=source_team_id,
                        )
                        continue
                    principal_key = "team"
                    principal_id = target_principal_id
                else:
                    logger.warning(
                        "rbac_no_principal",
                        resource_type=resource_type,
                        source_resource_id=source_resource_id,
                        assignment=assignment,
                    )
                    continue

                # Grant role via AAP API
                # Endpoint format: {resource_type}/{id}/roles/{role_name}/{principal_type}s/
                principal_type_plural = f"{principal_key}s"
                endpoint = f"{resource_type}/{target_resource_id}/roles/{role_name}/{principal_type_plural}/"
                data = {"id": principal_id}

                logger.info(
                    "granting_role",
                    resource_type=resource_type,
                    source_resource_id=source_resource_id,
                    target_resource_id=target_resource_id,
                    role=role_name,
                    principal_type=principal_key,
                    source_principal_id=source_user_id or source_team_id,
                    target_principal_id=principal_id,
                )

                result = await self.client.post(
                    endpoint=endpoint,
                    data=data,
                )

                results.append(result)
                self.stats["imported_count"] += 1

            except Exception as e:
                logger.error(
                    "rbac_import_error",
                    resource_type=resource_type,
                    source_resource_id=source_resource_id,
                    role=role_name,
                    assignment=assignment,
                    error=str(e),
                )
                self.stats["error_count"] += 1

                # Track error for reporting
                self.import_errors.append(
                    {
                        "resource_type": "rbac_assignments",
                        "source_id": source_resource_id,
                        "name": f"{resource_type}/{role_name}",
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "details": assignment,
                    }
                )

                continue

        return results


class HostImporter(ResourceImporter):
    """Importer for host resources with bulk operations support."""

    DEPENDENCIES = {
        "inventory": "inventories",
    }

    def __init__(
        self,
        client: AAPTargetClient,
        state: MigrationState,
        performance_config: PerformanceConfig,
        resource_mappings: dict[str, dict[str, str]] | None = None,
    ):
        """Initialize host importer with bulk operations.

        Args:
            client: AAP target client instance
            state: Migration state manager
            performance_config: Performance configuration
            resource_mappings: Optional resource name mappings from config/mappings.yaml
        """
        super().__init__(client, state, performance_config, resource_mappings)
        self.bulk_ops = BulkOperations(client)

    async def import_hosts_bulk(
        self,
        inventory_id: int,
        hosts: list[dict[str, Any]],
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> dict[str, Any]:
        """Import hosts using bulk API for performance.

        Args:
            inventory_id: Target inventory ID
            hosts: List of host data
            progress_callback: Optional callback for progress updates.
                Called after each batch with (total_created, total_failed, total_skipped).

        Returns:
            Bulk operation result
        """
        batch_size = self.performance_config.batch_sizes.get("hosts", 200)
        # Default to 5 if not set in config
        concurrency = getattr(self.performance_config, "host_import_concurrent_batches", 5)

        logger.info(
            "bulk_import_hosts_starting",
            inventory_id=inventory_id,
            host_count=len(hosts),
            batch_size=batch_size,
            concurrency=concurrency,
        )

        all_results = []
        total_created = 0
        total_failed = 0
        total_skipped = 0

        # Split into chunks
        chunks = [hosts[i : i + batch_size] for i in range(0, len(hosts), batch_size)]

        semaphore = asyncio.Semaphore(concurrency)

        async def process_batch(
            batch_idx: int, batch: list[dict[str, Any]]
        ) -> dict[str, Any] | None:
            nonlocal total_created, total_failed, total_skipped

            async with semaphore:
                # Prepare host data for bulk API
                prepared_hosts = []
                source_ids = []
                source_info: list[dict] = []
                source_name_by_id: dict[int, str] = {}
                batch_skipped = 0

                for host in batch:
                    source_id = host.pop("_source_id", host.get("id"))
                    source_name = host.get("name", f"host_{source_id}")
                    source_name_by_id[source_id] = source_name

                    # Skip if already migrated
                    if self.state.is_migrated("hosts", source_id):
                        self.stats["skipped_count"] += 1
                        batch_skipped += 1
                        continue

                    source_ids.append(source_id)
                    source_info.append(
                        {
                            "source_id": source_id,
                            "source_name": source_name,
                        }
                    )

                    prepared_hosts.append(
                        {
                            "name": host["name"],
                            "description": host.get("description", ""),
                            "enabled": host.get("enabled", True),
                            "variables": host.get("variables", {}),
                            "inventory": inventory_id,
                        }
                    )

                if batch_skipped > 0:
                    total_skipped += batch_skipped
                    # Callback with current cumulative stats
                    if progress_callback:
                        progress_callback(
                            self.stats["imported_count"],
                            self.stats["error_count"],
                            self.stats["skipped_count"],
                        )

                if not prepared_hosts:
                    return None

                try:
                    result = await self.bulk_ops.bulk_create_hosts(
                        inventory_id=inventory_id,
                        hosts=prepared_hosts,
                        batch_size=batch_size,
                    )

                    created_hosts = result.get("hosts", [])
                    failed_hosts = result.get("failed", [])

                    # Batch save ID mappings for all created hosts
                    if created_hosts and source_info:
                        mappings = []
                        for idx, created_host in enumerate(created_hosts):
                            if idx < len(source_info):
                                mappings.append(
                                    {
                                        "resource_type": "hosts",
                                        "source_id": source_info[idx]["source_id"],
                                        "target_id": created_host["id"],
                                        "source_name": source_info[idx]["source_name"],
                                        "target_name": created_host.get("name"),
                                    }
                                )

                        self.state.batch_create_mappings(mappings)

                    created_count = len(created_hosts)
                    failed_count = len(failed_hosts)

                    total_created += created_count
                    total_failed += failed_count

                    self.stats["imported_count"] += created_count
                    self.stats["error_count"] += failed_count

                    if progress_callback:
                        progress_callback(
                            self.stats["imported_count"],
                            self.stats["error_count"],
                            self.stats["skipped_count"],
                        )

                    return result

                except Exception as e:
                    logger.error(
                        "bulk_import_batch_failed",
                        resource_type="hosts",
                        inventory_id=inventory_id,
                        batch_idx=batch_idx,
                        error=str(e),
                    )

                    # Mark failed in state
                    for source_id in source_ids:
                        source_name = source_name_by_id.get(source_id, f"host_{source_id}")
                        if not self.state.has_source_mapping("hosts", source_id):
                            self.state.create_source_mapping(
                                "hosts", source_id, source_name=source_name
                            )
                        self.state.mark_failed("hosts", source_id, str(e))

                    self.stats["error_count"] += len(source_ids)
                    total_failed += len(source_ids)

                    self.import_errors.append(
                        {
                            "resource_type": "hosts",
                            "source_id": f"batch_{batch_idx}",
                            "name": f"batch {batch_idx} of {len(source_ids)} hosts",
                            "error": str(e),
                            "error_type": type(e).__name__,
                        }
                    )

                    if progress_callback:
                        progress_callback(
                            self.stats["imported_count"],
                            self.stats["error_count"],
                            self.stats["skipped_count"],
                        )

                    return None

        # Execute chunks in parallel
        tasks = [process_batch(i, chunk) for i, chunk in enumerate(chunks)]
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, dict):
                    all_results.append(r)
                # Note: exceptions in process_batch are caught and handled,
                # but asyncio.gather might return exceptions if something unexpected happens

        logger.info(
            "bulk_import_hosts_completed",
            inventory_id=inventory_id,
            total_hosts=len(hosts),
            created=total_created,
            failed=total_failed,
            skipped=total_skipped,
        )

        return {
            "total_requested": len(hosts),
            "total_created": total_created,
            "total_failed": total_failed,
            "total_skipped": total_skipped,
            "results": all_results,
        }


class CredentialImporter(ResourceImporter):
    """Importer for credential resources.

    Credentials are pre-created in the target environment before migration.
    This importer PATCHes existing resources instead of POSTing new ones.
    """

    DEPENDENCIES = {
        "organization": "organizations",
        "credential_type": "credential_types",
        "user": "users",
        "team": "teams",
    }

    # Built-in credential type IDs (managed by AAP, consistent across versions)
    # Built-in types are IDs 1-27 in both AAP 2.3 and AAP 2.6
    # Custom types start at ID 28+
    BUILTIN_CREDENTIAL_TYPE_MAX_ID = 27

    async def import_resource(
        self,
        resource_type: str,
        source_id: int,
        data: dict[str, Any],
        resolve_dependencies: bool = True,
    ) -> dict[str, Any] | None:
        """Import credential by PATCHing existing resource in target.

        Credentials are pre-created in the target environment. This method
        finds the existing resource by name and PATCHes it with organization
        and description from the source.

        Args:
            resource_type: Type of resource being imported
            source_id: Source resource ID (from AAP 2.3)
            data: Transformed resource data
            resolve_dependencies: Whether to resolve foreign key dependencies

        Returns:
            Patched resource data or None if skipped/failed
        """
        # Check if already imported
        if self.state.is_migrated(resource_type, source_id):
            logger.debug(
                "resource_already_imported",
                resource_type=resource_type,
                source_id=source_id,
            )
            self.stats["skipped_count"] += 1
            return None

        name = data.get("name")

        # Mark as in progress (creates MigrationProgress record for mark_completed)
        self.state.mark_in_progress(
            resource_type=resource_type,
            source_id=source_id,
            source_name=name or "unknown",
            phase="import",
        )

        if not name:
            logger.error("credential_missing_name", source_id=source_id)
            self.stats["error_count"] += 1
            return None

        # Clean up transformer markers
        temp_values = data.pop("_temp_credential_values", None)
        encrypted_fields = data.pop("_encrypted_fields", [])
        data.pop("_needs_vault_lookup", None)

        try:
            # Find existing credential in target by name
            results = await self.client.get("credentials/", params={"name": name})
            resources = results.get("results", [])

            if resources:
                # Credential exists - PATCH it
                target_id = resources[0]["id"]
                is_managed = resources[0].get("managed", False)

                # Skip PATCH for managed (built-in) credentials - AAP doesn't allow modifications
                if is_managed:
                    logger.info(
                        "credential_managed_skip_patch",
                        name=name,
                        source_id=source_id,
                        target_id=target_id,
                        message="Skipping PATCH for managed credential - saving mapping only",
                    )
                    # Save mapping without patching
                    self.state.save_id_mapping(
                        resource_type=resource_type,
                        source_id=source_id,
                        target_id=target_id,
                        source_name=name,
                        target_name=name,
                    )
                    self.state.mark_completed(
                        resource_type=resource_type,
                        source_id=source_id,
                        target_id=target_id,
                        target_name=name,
                    )
                    self.stats["skipped_count"] += 1
                    # Return skipped signal
                    return {"id": target_id, "name": name, "_skipped": True}

                # Resolve dependencies
                if resolve_dependencies:
                    data = await self._resolve_dependencies(resource_type, data)

                # Build PATCH payload (organization, description only)
                patch_data = {}
                if data.get("organization"):
                    patch_data["organization"] = data["organization"]
                if data.get("description"):
                    patch_data["description"] = data["description"]

                # PATCH the credential
                if patch_data:
                    await self.client.update_resource("credentials", target_id, patch_data)
                    logger.info(
                        "credential_patched",
                        name=name,
                        source_id=source_id,
                        target_id=target_id,
                        patched_fields=list(patch_data.keys()),
                    )
                else:
                    logger.info(
                        "credential_mapped_no_patch",
                        name=name,
                        source_id=source_id,
                        target_id=target_id,
                        message="No fields to patch - mapping only",
                    )

                result = {"id": target_id, "name": name, "_patched": bool(patch_data)}

            else:
                # Credential does not exist - CREATE it
                logger.info(
                    "credential_creating",
                    name=name,
                    source_id=source_id,
                    message="Creating new credential with temporary values",
                )

                # Resolve dependencies
                if resolve_dependencies:
                    data = await self._resolve_dependencies(resource_type, data)

                # Create resource
                result = await self.client.create_resource(
                    resource_type="credentials",
                    data=data,
                    check_exists=False,  # We already checked
                )

                target_id = result["id"]
                logger.info(
                    "credential_created",
                    name=name,
                    source_id=source_id,
                    target_id=target_id,
                )

            # Save mapping
            self.state.save_id_mapping(
                resource_type=resource_type,
                source_id=source_id,
                target_id=target_id,
                source_name=name,
                target_name=name,
            )
            self.state.mark_completed(
                resource_type=resource_type,
                source_id=source_id,
                target_id=target_id,
                target_name=name,
            )
            self.stats["imported_count"] += 1

            # Track placeholder resources if temp values were used
            if temp_values:
                self.placeholder_resources.append(
                    {
                        "resource_type": "credentials",
                        "source_id": source_id,
                        "name": name,
                        "target_id": target_id,
                        "temp_values": temp_values,
                        "action_required": "Update encrypted values",
                        "instructions": self._generate_credential_instructions(
                            {
                                "name": name,
                                "organization": data.get("organization"),
                                "credential_type": data.get("credential_type"),
                            },
                            encrypted_fields,
                            temp_values,
                        ),
                    }
                )

            return result

        except Exception as e:
            logger.error(
                "credential_import_failed",
                source_id=source_id,
                name=name,
                error=str(e),
            )
            self.stats["error_count"] += 1
            self.import_errors.append(
                {
                    "resource_type": resource_type,
                    "source_id": source_id,
                    "name": name,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )
            return None

    async def _resolve_dependencies(
        self, resource_type: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Override to handle built-in credential types.

        Built-in credential types (IDs 1-27) are managed by AAP and not exported
        because they already exist in both AAP 2.3 and AAP 2.6. We assume they
        have consistent IDs between versions.

        Custom credential types (IDs 28+) use normal ID mapping resolution.

        Args:
            resource_type: The resource type being imported
            data: The resource data with source IDs

        Returns:
            Resource data with resolved target IDs
        """
        resolved = dict(data)

        # Handle credential_type field specially
        if "credential_type" in data and data["credential_type"]:
            source_id = data["credential_type"]
            target_id = self.state.get_mapped_id("credential_types", source_id)

            if target_id:
                # Custom credential type - use mapping
                resolved["credential_type"] = target_id
                logger.debug(
                    "resolved_custom_credential_type",
                    credential_name=data.get("name"),
                    source_id=source_id,
                    target_id=target_id,
                )
            else:
                # No mapping found
                if source_id <= self.BUILTIN_CREDENTIAL_TYPE_MAX_ID:
                    # Built-in credential type - assume same ID in AAP 2.6
                    logger.debug(
                        "using_builtin_credential_type",
                        credential_name=data.get("name"),
                        credential_type_id=source_id,
                        message="Assuming consistent ID for built-in credential type",
                    )
                    # Keep original ID (assumption: built-in types have same IDs)
                    resolved["credential_type"] = source_id
                else:
                    # Custom type (ID > 27) but no mapping = ERROR
                    logger.error(
                        "missing_custom_credential_type_mapping",
                        credential_name=data.get("name"),
                        source_id=source_id,
                        message="Custom credential type not found in ID mappings",
                    )
                    # Remove field to allow partial import (existing behavior)
                    resolved.pop("credential_type", None)

        # Resolve other dependencies (organization, user, team) using base logic
        for field, dep_resource_type in self.DEPENDENCIES.items():
            # Skip credential_type - already handled above
            if field == "credential_type":
                continue

            if field in data and data[field]:
                source_id = data[field]
                target_id = self.state.get_mapped_id(dep_resource_type, source_id)
                if target_id:
                    resolved[field] = target_id
                    logger.debug(
                        f"resolved_{field}_dependency",
                        credential_name=data.get("name"),
                        source_id=source_id,
                        target_id=target_id,
                    )
                else:
                    logger.warning(
                        "unresolved_dependency",
                        resource_name=data.get("name"),
                        field=field,
                        source_id=source_id,
                        dep_resource_type=dep_resource_type,
                    )
                    # Remove field to allow partial import
                    resolved.pop(field, None)

        return resolved

    async def import_credentials(
        self,
        credentials: list[dict[str, Any]],
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> list[dict[str, Any]]:
        """Import multiple credentials by PATCHing pre-existing resources.

        Credentials are pre-created in the target environment before migration.
        This method finds each credential by name and PATCHes it with
        organization and description from the source.

        Note: Encrypted fields (secrets) are NOT patched - they are already
        set during the external credential creation process.

        Args:
            credentials: List of credential data
            progress_callback: Optional callback for progress updates.
                Called after each credential with (success_count, failed_count).

        Returns:
            List of patched credential data
        """
        logger.info(
            "credentials_import_starting",
            total_count=len(credentials),
            names=[c.get("name") for c in credentials],
            message="PATCHing pre-created credentials in target",
        )

        # Clean up transformer marker fields before import
        for credential in credentials:
            credential.pop("_encrypted_fields", None)
            credential.pop("_temp_credential_values", None)

        # All credentials go through the same PATCH flow via import_resource()
        results = await self._import_parallel("credentials", credentials, progress_callback)

        logger.info(
            "credentials_import_completed",
            total_input=len(credentials),
            patched_count=len(results),
            skipped_or_failed=len(credentials) - len(results),
        )

        return results

    def _detect_encrypted_fields(self, credential: dict[str, Any]) -> list[str]:
        """Detect fields with $encrypted$ values.

        Checks both:
        1. The _encrypted_fields marker added by transformer
        2. Current inputs dict for any remaining $encrypted$ values

        Args:
            credential: Credential data

        Returns:
            List of field names that have encrypted values
        """
        encrypted_fields = []

        # First check the transformer marker (transformer already removed $encrypted$ from inputs)
        if "_encrypted_fields" in credential:
            encrypted_fields.extend(credential["_encrypted_fields"])

        # Also check current inputs for any $encrypted$ values that weren't cleaned
        if "inputs" in credential and isinstance(credential["inputs"], dict):
            for key, value in credential["inputs"].items():
                if value == "$encrypted$" and key not in encrypted_fields:
                    encrypted_fields.append(key)

        return encrypted_fields

    def _generate_credential_instructions(
        self,
        credential: dict[str, Any],
        encrypted_fields: list[str],
        temp_values: dict[str, str] | None = None,
    ) -> str:
        """Generate human-readable instructions for credential secret value updates.

        Args:
            credential: Credential data
            encrypted_fields: List of encrypted field names
            temp_values: Dictionary of field names to temporary values

        Returns:
            Markdown-formatted instructions
        """
        temp_values = temp_values or {}
        fields_list = "\n".join(
            f"- {field}: `{temp_values.get(field, '<temp_value>')}`" for field in encrypted_fields
        )

        return f"""
## Credential Secret Values Update Required

**Name**: {credential.get("name", "Unknown")}
**Organization ID**: {credential.get("organization", "Unknown")}
**Credential Type ID**: {credential.get("credential_type", "Unknown")}

### Fields with Temporary Values:
{fields_list}

### Steps:
1. Log into AAP 2.6 web interface
2. Navigate to Resources → Credentials
3. Find credential: {credential.get("name", "Unknown")}
4. Click "Edit" to modify the credential
5. Update the secret fields listed above with real values from your authoritative source
6. Save the credential
7. Test the credential to ensure it works correctly

**IMPORTANT**: The temporary values shown above should be replaced with real secrets immediately after migration.
"""


class ProjectImporter(ResourceImporter):
    """Importer for project resources."""

    DEPENDENCIES = {
        "organization": "organizations",
        "credential": "credentials",
        "default_environment": "execution_environments",
    }

    async def import_projects(
        self,
        projects: list[dict[str, Any]],
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> list[dict[str, Any]]:
        """Import multiple projects concurrently with live progress updates.

        Args:
            projects: List of project data
            progress_callback: Optional callback for progress updates.
                Called after each project with (success_count, failed_count).

        Returns:
            List of created project data
        """
        return await self._import_parallel("projects", projects, progress_callback)


async def wait_for_project_sync(
    client: "AAPTargetClient",
    project_ids: list[int],
    timeout: int = 600,
    poll_interval: int = 10,
    progress_callback: Callable[[int, int, int], None] | None = None,
) -> tuple[int, int, list[int]]:
    """Wait for projects to complete SCM sync after import.

    After projects are imported to AAP, they automatically trigger an SCM sync.
    Job templates cannot be created until the sync completes because the playbooks
    don't exist yet. This function polls project status and waits for sync completion.

    Args:
        client: Target AAP client
        project_ids: List of target project IDs to wait for
        timeout: Maximum time to wait in seconds (default 600 = 10 minutes)
        poll_interval: Time between status checks in seconds (default 10)
        progress_callback: Optional callback for progress updates (completed, total)

    Returns:
        Tuple of (synced_count, failed_count, list_of_failed_project_ids)
    """
    import time

    if not project_ids:
        return (0, 0, [])

    logger.info(
        "waiting_for_project_sync",
        project_count=len(project_ids),
        timeout=timeout,
        poll_interval=poll_interval,
    )

    start_time = time.time()
    synced: set[int] = set()
    failed: set[int] = set()

    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout:
            # Timeout - remaining projects count as failed
            remaining = set(project_ids) - synced - failed
            logger.warning(
                "project_sync_timeout",
                synced=len(synced),
                failed=len(failed),
                timed_out=len(remaining),
                elapsed_seconds=int(elapsed),
            )
            return (len(synced), len(failed) + len(remaining), list(failed | remaining))

        # Check status of remaining projects
        pending = set(project_ids) - synced - failed

        for project_id in list(pending):
            try:
                project = await client.get(f"projects/{project_id}/")
                status = project.get("status", "unknown")
                scm_type = project.get("scm_type", "")

                # Manual projects (no SCM) - no sync needed
                if not scm_type:
                    synced.add(project_id)
                    logger.debug(
                        "project_no_scm_skip",
                        project_id=project_id,
                        name=project.get("name"),
                    )
                    continue

                # Project synced successfully
                if status == "successful":
                    synced.add(project_id)
                    logger.debug(
                        "project_sync_complete",
                        project_id=project_id,
                        name=project.get("name"),
                    )
                # Project sync failed
                elif status in ("failed", "error", "canceled"):
                    failed.add(project_id)
                    logger.warning(
                        "project_sync_failed",
                        project_id=project_id,
                        name=project.get("name"),
                        status=status,
                    )
                # Still syncing (pending, waiting, running) - continue waiting

            except Exception as e:
                logger.warning(
                    "project_status_check_error",
                    project_id=project_id,
                    error=str(e),
                )

        # Update progress
        if progress_callback:
            progress_callback(len(synced), len(failed), 0)

        # All projects done
        if len(synced) + len(failed) >= len(project_ids):
            logger.info(
                "project_sync_wait_complete",
                synced=len(synced),
                failed=len(failed),
                elapsed_seconds=int(time.time() - start_time),
            )
            return (len(synced), len(failed), list(failed))

        await asyncio.sleep(poll_interval)


class JobTemplateImporter(ResourceImporter):
    """Importer for job template resources."""

    DEPENDENCIES = {
        "organization": "organizations",
        "inventory": "inventories",
        "project": "projects",
        "credential": "credentials",
        "execution_environment": "execution_environments",
    }

    async def import_resource(
        self,
        resource_type: str,
        source_id: int | str,
        data: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Import a job template with credential association.

        Overrides base method to handle the `credentials` field after
        the job template is created.

        Args:
            resource_type: Resource type (should be "job_templates")
            source_id: Source resource ID
            data: Resource data to import

        Returns:
            Created/updated resource data, or None if failed
        """
        # Extract credentials before import (they're not valid API fields)
        credentials = data.pop("credentials", [])
        template_name = data.get("name")

        # Call base import_resource
        result = await super().import_resource(resource_type, source_id, data)

        # Associate credentials if import succeeded and we have credentials
        if result and result.get("id") and credentials:
            logger.info(
                "associating_credentials_with_job_template",
                job_template_id=result["id"],
                template_name=template_name,
                credential_count=len(credentials),
            )
            await self._associate_credentials(result["id"], credentials, template_name)

        return result

    async def import_job_templates(
        self,
        templates: list[dict[str, Any]],
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> list[dict[str, Any]]:
        """Import job templates with credential associations.

        This method imports job templates sequentially to handle post-creation
        credential associations via the `/job_templates/{id}/credentials/` endpoint.

        Args:
            templates: List of job template data
            progress_callback: Optional callback for progress updates.
                Called after each job template with (success_count, failed_count).

        Returns:
            List of created job template data
        """
        results = []
        success_count = 0
        failed_count = 0
        skipped_count = 0

        for template in templates:
            source_id = template.pop("_source_id", template.get("id"))

            # Extract credentials for post-creation association
            credentials = template.pop("credentials", [])

            # Clean up EE markers
            if template.get("_needs_execution_environment"):
                logger.warning(
                    "job_template_needs_ee_mapping",
                    resource_type="job_templates",
                    source_id=source_id,
                    source_name=template.get("name"),
                    virtualenv=template.get("_custom_virtualenv_path"),
                )
                template.pop("_needs_execution_environment", None)
                template.pop("_custom_virtualenv_path", None)

            try:
                # Create the job template
                result = await self.import_resource(
                    resource_type="job_templates",
                    source_id=source_id,
                    data=template,
                )

                if result:
                    target_id = result["id"]

                    # Associate credentials after creation
                    if credentials:
                        await self._associate_credentials(
                            target_id, credentials, template.get("name")
                        )

                    results.append(result)
                    success_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                failed_count += 1
                logger.error(
                    "job_template_import_failed",
                    source_id=source_id,
                    name=template.get("name"),
                    error=str(e),
                )

            if progress_callback:
                progress_callback(success_count, failed_count, skipped_count)

        return results

    async def _associate_credentials(
        self,
        job_template_id: int,
        credentials: list[dict[str, Any]],
        template_name: str | None = None,
    ) -> None:
        """Associate credentials with a job template via POST.

        Args:
            job_template_id: Target job template ID
            credentials: List of credential dictionaries (containing 'id') to associate
            template_name: Job template name for logging
        """
        endpoint = f"job_templates/{job_template_id}/credentials/"

        for cred_data in credentials:
            # Extract source ID from credential data
            source_cred_id = cred_data.get("id")
            if not source_cred_id:
                continue

            # Resolve Source ID to Target ID
            target_cred_id = self.state.get_mapped_id("credentials", source_cred_id)

            if not target_cred_id:
                logger.warning(
                    "credential_mapping_missing_for_association",
                    job_template_id=job_template_id,
                    source_credential_id=source_cred_id,
                    template_name=template_name,
                    message="Skipping association - credential not found in map",
                )
                continue

            try:
                await self.client.post(endpoint, json_data={"id": target_cred_id})
                logger.debug(
                    "credential_associated_with_job_template",
                    job_template_id=job_template_id,
                    credential_id=target_cred_id,
                    source_credential_id=source_cred_id,
                    template_name=template_name,
                )
            except Exception as e:
                logger.error(
                    "failed_to_associate_credential",
                    job_template_id=job_template_id,
                    credential_id=target_cred_id,
                    template_name=template_name,
                    error=str(e),
                )


class WorkflowImporter(ResourceImporter):
    """Importer for workflow job template resources."""

    DEPENDENCIES = {
        "organization": "organizations",
        "inventory": "inventories",
    }

    async def import_workflows(
        self,
        workflows: list[dict[str, Any]],
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> list[dict[str, Any]]:
        """Import multiple workflow job templates with live progress updates.

        Note: Workflow nodes must be imported separately after workflows are created.
        Workflows use sequential import (not parallel) to properly track node metadata.

        Args:
            workflows: List of workflow data
            progress_callback: Optional callback for progress updates.
                Called after each workflow with (success_count, failed_count).

        Returns:
            List of created workflow data
        """
        results = []
        success_count = 0
        failed_count = 0
        skipped_count = 0

        for workflow in workflows:
            source_id = workflow.pop("_source_id", workflow.get("id"))

            # Extract nodes for separate import
            nodes = workflow.pop("_workflow_nodes", None)

            result = await self.import_resource(
                resource_type="workflow_job_templates",
                source_id=source_id,
                data=workflow,
            )

            if result:
                if nodes:
                    # Store nodes for later import
                    result["_pending_nodes"] = nodes
                results.append(result)
                success_count += 1
            else:
                failed_count += 1

            # Update progress after each workflow
            if progress_callback:
                progress_callback(success_count, failed_count, skipped_count)

        return results


class NotificationTemplateImporter(ResourceImporter):
    """Importer for notification template resources.

    Notification templates define how AAP sends notifications about
    job status (email, Slack, webhook, etc.).
    """

    DEPENDENCIES = {
        "organization": "organizations",
    }

    async def import_notification_templates(
        self,
        notifications: list[dict[str, Any]],
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> list[dict[str, Any]]:
        """Import multiple notification templates concurrently with live progress updates.

        Args:
            notifications: List of notification template data
            progress_callback: Optional callback for progress updates.
                Called after each notification with (success_count, failed_count).

        Returns:
            List of created notification template data
        """
        return await self._import_parallel(
            "notification_templates", notifications, progress_callback
        )


class SystemJobTemplateImporter(ResourceImporter):
    """Importer for system job template resources.

    System job templates are built-in and read-only. We only map them.
    """

    DEPENDENCIES = {}

    async def import_resource(
        self,
        resource_type: str,
        source_id: int,
        data: dict[str, Any],
        resolve_dependencies: bool = True,
    ) -> dict[str, Any] | None:
        """Map system job template by name."""
        if self.state.is_migrated(resource_type, source_id):
            self.stats["skipped_count"] += 1
            return None

        name = data.get("name")
        if not name:
            return None

        self.state.mark_in_progress(resource_type, source_id, name, "import")

        try:
            # Lookup by name
            results = await self.client.get(
                "system_job_templates/",
                params={"name": name},
            )
            resources = results.get("results", [])

            if resources:
                target_id = resources[0]["id"]
                self.state.save_id_mapping(
                    resource_type=resource_type,
                    source_id=source_id,
                    target_id=target_id,
                    source_name=name,
                    target_name=name,
                )
                self.state.mark_completed(resource_type, source_id, target_id, name)
                self.stats["imported_count"] += 1
                logger.info(
                    "system_job_template_mapped",
                    source_id=source_id,
                    target_id=target_id,
                    name=name,
                )
                return {"id": target_id, "name": name}
            else:
                logger.warning(
                    "system_job_template_not_found_in_target",
                    name=name,
                    source_id=source_id,
                )
                self.state.mark_failed(resource_type, source_id, "Not found in target")
                self.stats["error_count"] += 1
                return None

        except Exception as e:
            logger.error(
                "system_job_template_import_failed",
                name=name,
                error=str(e),
            )
            self.state.mark_failed(resource_type, source_id, str(e))
            self.stats["error_count"] += 1
            return None

    async def import_system_job_templates(
        self,
        templates: list[dict[str, Any]],
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> list[dict[str, Any]]:
        """Import multiple system job templates (mapping only)."""
        return await self._import_parallel("system_job_templates", templates, progress_callback)


class CredentialInputSourceImporter(ResourceImporter):
    """Importer for credential input source resources.

    Credential input sources link credential input fields to values
    from other credentials (e.g., a Vault credential).
    """

    DEPENDENCIES = {
        "credential": "credentials",  # The credential being modified
        "source_credential": "credentials",  # The credential providing the input
    }

    async def import_credential_input_sources(
        self,
        input_sources: list[dict[str, Any]],
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> list[dict[str, Any]]:
        """Import multiple credential input sources by patching existing credentials.

        This importer does not create new resources. Instead, it modifies the `inputs`
        field of an existing credential to link it to another source credential.

        Args:
            input_sources: List of credential input source data
            progress_callback: Optional callback for progress updates.

        Returns:
            List of patched credential data
        """
        results = []
        # Removed local success_count, failed_count, skipped_count

        for input_source in input_sources:
            source_id = input_source.pop("_source_id", input_source.get("id"))
            # `credential` is the ID of the credential whose input is being sourced.
            source_target_credential_id = input_source.get(
                "credential"
            )  # Renamed for clarity to avoid confusion with the source_credential for the input value.
            source_input_field_name = input_source.get("input_field_name")
            # `source_credential` is the ID of the credential that provides the source (e.g., a HashiCorp Vault credential).
            source_source_credential_id = input_source.get("source_credential")
            source_source_credential_field_name = input_source.get("source_credential_field_name")

            if not all(
                [
                    source_target_credential_id,
                    source_input_field_name,
                    source_source_credential_id,
                    source_source_credential_field_name,
                ]
            ):
                logger.warning(
                    "credential_input_source_missing_fields",
                    source_id=source_id,
                    message="Skipping credential input source due to missing required fields",
                )
                self.stats["error_count"] += 1
                if progress_callback:
                    progress_callback(
                        self.stats["imported_count"],
                        self.stats["error_count"],
                        self.stats["skipped_count"],
                    )
                continue

            # Check if the credential associated with this input source has already been migrated.
            target_credential_id = self.state.get_mapped_id(
                "credentials", source_target_credential_id
            )
            if not target_credential_id:
                logger.warning(
                    "credential_input_source_target_credential_not_imported",
                    source_id=source_id,
                    target_credential_id=source_target_credential_id,
                    message="Skipping credential input source - target credential not found",
                )
                self.stats["error_count"] += 1
                if progress_callback:
                    progress_callback(
                        self.stats["imported_count"],
                        self.stats["error_count"],
                        self.stats["skipped_count"],
                    )
                continue

            # Resolve the source_credential to its target ID
            target_source_credential_id = self.state.get_mapped_id(
                "credentials", source_source_credential_id
            )
            if not target_source_credential_id:
                logger.warning(
                    "credential_input_source_source_credential_not_imported",
                    source_id=source_id,
                    source_credential_id=source_source_credential_id,
                    message="Skipping credential input source - source credential not found",
                )
                self.stats["error_count"] += 1
                if progress_callback:
                    progress_callback(
                        self.stats["imported_count"],
                        self.stats["error_count"],
                        self.stats["skipped_count"],
                    )
                continue

            # Construct the value to patch into the target credential's 'inputs'
            # Format: "$<target_source_credential_id>.<source_credential_field_name>$"
            new_input_value = (
                f"${target_source_credential_id}.{source_source_credential_field_name}$"
            )

            try:
                # Fetch the target credential to get its current inputs
                # This is a GET, then PATCH - ensures other inputs are preserved
                target_credential_obj = await self.client.get(
                    f"credentials/{target_credential_id}/"
                )
                current_inputs = target_credential_obj.get("inputs", {})

                # Update the specific input field
                current_inputs[source_input_field_name] = new_input_value

                # Patch the target credential with the updated inputs
                # Note: This is an important distinction: we modify an existing resource,
                # not create a new one. The target_id for the state mapping will be
                # the ID of the credential that was patched.
                await self.client.patch(
                    f"credentials/{target_credential_id}/",
                    json_data={"inputs": current_inputs},
                )

                # Mark as completed (even though it's a PATCH, not CREATE)
                self.state.mark_completed(
                    resource_type="credential_input_sources",
                    source_id=source_id,
                    target_id=target_credential_id,  # Link to the patched credential
                    source_name=input_source.get("name", f"CIS-{source_id}"),
                    target_name=target_credential_obj.get("name"),
                )
                self.stats["imported_count"] += 1
                results.append(
                    {"id": target_credential_id, "name": target_credential_obj.get("name")}
                )
                logger.info(
                    "credential_input_source_patched",
                    source_id=source_id,
                    target_credential_id=target_credential_id,
                    input_field=source_input_field_name,
                    new_input_value=new_input_value,
                )

            except Exception as e:
                self.stats["error_count"] += 1
                logger.error(
                    "credential_input_source_patch_failed",
                    source_id=source_id,
                    target_credential_id=target_credential_id,
                    error=str(e),
                    exc_info=True,
                )
                self.state.mark_failed(
                    resource_type="credential_input_sources",
                    source_id=source_id,
                    error_message=str(e),
                )

            if progress_callback:
                progress_callback(
                    self.stats["imported_count"],
                    self.stats["error_count"],
                    self.stats["skipped_count"],
                )

        return results


# Factory function for creating importers
def create_importer(
    resource_type: str,
    client: AAPTargetClient,
    state: MigrationState,
    performance_config: PerformanceConfig,
    resource_mappings: dict[str, dict[str, str]] | None = None,
) -> ResourceImporter:
    """Create appropriate importer for resource type.

    Args:
        resource_type: Type of resource to import
        client: AAP target client instance
        state: Migration state manager
        performance_config: Performance configuration
        resource_mappings: Optional resource name mappings from config/mappings.yaml

    Returns:
        Appropriate ResourceImporter subclass instance

    Raises:
        ValueError: If resource_type is not supported
    """
    importers = {
        # Foundation resources
        "organizations": OrganizationImporter,
        "labels": LabelImporter,
        "instances": InstanceImporter,
        "instance_groups": InstanceGroupImporter,
        # Identity and access
        "users": UserImporter,
        "teams": TeamImporter,
        # Credentials
        "credential_types": CredentialTypeImporter,
        "credentials": CredentialImporter,
        "credential_input_sources": CredentialInputSourceImporter,
        # Projects and execution
        "projects": ProjectImporter,
        "execution_environments": ExecutionEnvironmentImporter,
        # Inventory resources
        "inventories": InventoryImporter,
        "inventory_sources": InventorySourceImporter,
        "inventory_groups": InventoryGroupImporter,
        "hosts": HostImporter,
        # Job templates and workflows
        "job_templates": JobTemplateImporter,
        "workflow_job_templates": WorkflowImporter,
        "schedules": ScheduleImporter,
        # Notifications
        "notification_templates": NotificationTemplateImporter,
        # RBAC
        "rbac": RBACImporter,
        # System
        "system_job_templates": SystemJobTemplateImporter,
    }

    importer_class = importers.get(resource_type)
    if not importer_class:
        raise NotImplementedError(
            f"No importer implemented for resource type: {resource_type}. "
            f"Available importers: {', '.join(sorted(importers.keys()))}"
        )

    return importer_class(client, state, performance_config, resource_mappings)
