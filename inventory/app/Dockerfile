# Inventory web app + AI tools (Flask, search, updates, optional OpenAI)
FROM python:3.12-slim

WORKDIR /app

# Docker CLI + OpenCV runtime libs (headless cv2 can still need libGL in some builds)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg libgl1 libglib2.0-0 libxcb1 \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc \
    && chmod 644 /etc/apt/keyrings/docker.asc \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian bookworm stable" > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# Dependencies: install CPU-only torch first so ultralytics does not pull CUDA (saves ~6GB and avoids disk full)
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code (config, routes, vision_ops, …)
COPY config.py app.py updates.py flash_ops.py project_ops.py project_templates.py map_ops.py device_ops.py debug_ops.py config_wizard_ops.py vision_ops.py device_catalog.json ./
COPY static/ static/
COPY templates/ templates/

# Default: mount repo at /workspace and set REPO_ROOT
ENV REPO_ROOT=/workspace
ENV PORT=5050
EXPOSE 5050

CMD ["python", "app.py"]
