# Inventory web app + AI tools (Flask, search, updates, optional OpenAI)
FROM python:3.12-slim

WORKDIR /app

# Docker CLI so the app can talk to the host daemon when socket is mounted (docker version, ps, start/stop)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc \
    && chmod 644 /etc/apt/keyrings/docker.asc \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian bookworm stable" > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code (config, routes, updates, flash_ops, project_ops, map_ops, device_ops, debug_ops, config_wizard_ops, device_catalog, static, templates)
COPY config.py app.py updates.py flash_ops.py project_ops.py map_ops.py device_ops.py debug_ops.py config_wizard_ops.py device_catalog.json ./
COPY static/ static/
COPY templates/ templates/

# Default: mount repo at /workspace and set REPO_ROOT
ENV REPO_ROOT=/workspace
ENV PORT=5050
EXPOSE 5050

CMD ["python", "app.py"]
