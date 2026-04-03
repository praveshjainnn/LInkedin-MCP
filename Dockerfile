# ─────────────────────────────────────────────────────────────────────────────
# Stage 1 – Base image
#   Python 3.11 slim keeps the image small while matching typical dev setups.
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim

# ─────────────────────────────────────────────────────────────────────────────
# Working directory inside the container
# ─────────────────────────────────────────────────────────────────────────────
WORKDIR /app

# ─────────────────────────────────────────────────────────────────────────────
# Copy dependency manifest first so Docker can cache the pip layer
# (only re-runs pip install when requirements.txt actually changes)
# ─────────────────────────────────────────────────────────────────────────────
COPY requirements.txt .

# ─────────────────────────────────────────────────────────────────────────────
# Install Python dependencies
#   --no-cache-dir  → keeps the image lean (no pip download cache left behind)
#   --upgrade pip   → ensures the resolver is up to date
# ─────────────────────────────────────────────────────────────────────────────
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ─────────────────────────────────────────────────────────────────────────────
# Copy the rest of the application source code into the container
# ─────────────────────────────────────────────────────────────────────────────
COPY . .

# ─────────────────────────────────────────────────────────────────────────────
# Render & other clouds set PORT at runtime; local Docker defaults to 1337.
# ─────────────────────────────────────────────────────────────────────────────
EXPOSE 1337

# ─────────────────────────────────────────────────────────────────────────────
# Runtime command
#   creator_mcp_server.py is spawned as a subprocess by server.py (stdio MCP).
#   Ollama on the host: use --add-host=host.docker.internal:host-gateway if needed.
# ─────────────────────────────────────────────────────────────────────────────
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-1337}"]
