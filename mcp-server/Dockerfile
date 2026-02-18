# Cyber-Lab MCP Server — project context, roadmap, devices, inventory
# Run with repo mounted at /workspace so the server can read repo files.
# Cursor: docker run --rm -i -v "$(pwd)":/workspace -e CYBER_LAB_REPO_ROOT=/workspace cyber-lab-mcp

FROM node:20-slim

WORKDIR /app

# Install deps (include dev for TypeScript) and build
COPY package.json package-lock.json* ./
RUN npm ci
COPY tsconfig.json ./
COPY src/ src/
RUN npm run build

# Server reads from REPO_ROOT (mount at runtime)
ENV CYBER_LAB_REPO_ROOT=/workspace

# Stdio transport: no port, client talks over stdin/stdout
CMD ["node", "dist/index.js"]
