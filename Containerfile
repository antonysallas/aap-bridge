# AAP Bridge - Multi-stage Container Build
# Base: Python 3.12 slim (Debian-based)

# =============================================================================
# Stage 1: Builder
# =============================================================================
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (better layer caching)
COPY pyproject.toml ./
COPY src/ ./src/

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# =============================================================================
# Stage 2: Runtime
# =============================================================================
FROM python:3.12-slim AS runtime

# Labels (OCI standard)
LABEL org.opencontainers.image.title="aap-bridge" \
      org.opencontainers.image.version="0.1.0" \
      org.opencontainers.image.description="Production-grade migration tool for Ansible Automation Platform" \
      org.opencontainers.image.source="https://github.com/antonysallas/aap-bridge" \
      org.opencontainers.image.licenses="GPL-3.0-or-later" \
      org.opencontainers.image.vendor="Antony Sallas"

# Install runtime dependencies only (libpq for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1001 appuser

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create runtime directories
RUN mkdir -p /app/config /app/logs /app/exports /app/xformed /app/reports /app/schemas /app/backups && \
    chown -R appuser:appuser /app

# Copy configuration files (defaults, can be overridden via volume mount)
COPY --chown=appuser:appuser config/ /app/config/
COPY --chown=appuser:appuser .env.example /app/

# Switch to non-root user
USER appuser

# Environment variables (defaults)
ENV AAP_BRIDGE_CONFIG=/app/config/config.yaml \
    AAP_BRIDGE_LOG_LEVEL=INFO \
    LOG_FILE=/app/logs/migration.log \
    PATHS__BASE_DIR=/app \
    PATHS__EXPORT_DIR=/app/exports \
    PATHS__TRANSFORM_DIR=/app/xformed \
    PATHS__SCHEMA_DIR=/app/schemas \
    PATHS__REPORT_DIR=/app/reports \
    PATHS__BACKUP_DIR=/app/backups \
    PATHS__MAPPINGS_FILE=/app/config/mappings.yaml

# Entrypoint - no args launches interactive menu
ENTRYPOINT ["aap-bridge"]
CMD []
