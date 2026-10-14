# syntax=docker/dockerfile:1

# Stage 1: build the React SPA (the project workspace + generation UI).
# The frontend's OpenAPI types are committed (web/src/api/generated/), so the
# build needs no running backend — unlike a spec-export step.
FROM node:22-slim AS web
WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web ./
RUN npm run build

# Stage 2: install the shared Slidev toolchain the engine shells out to when
# building decks (SlidevBuilder expects it at /app/slidev). Pinned to bookworm
# so the node binary copied into the runtime stage never links a newer glibc
# than the python:3.12-slim runtime provides.
FROM node:22-bookworm-slim AS slidev
WORKDIR /app/slidev
COPY slidev/package.json slidev/package-lock.json ./
# The decks build to static HTML; no browser is involved, so skip Playwright's
# postinstall browser download entirely.
RUN PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm ci

# Stage 3: runtime. One Python image serves the API and the built SPA.
# pytest is a runtime dependency, not just a dev tool: engine.container imports
# the pytest-backed auditor adapter at module load (the "Run audit" feature shells
# pytest.main over auditor/), so the app will not even import without it.
FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    ESTIMATEKIT_PROJECTS_ROOT=/data/projects
# Architecture diagrams render to SVG inside this image: a headless JRE runs a
# pinned plantuml.jar with the built-in smetana layout engine (no graphviz), so
# a client's architecture never round-trips a third-party PlantUML server.
# fontconfig + DejaVu + harfbuzz give headless AWT the font machinery SVG text
# needs (the JRE's libfontmanager dlopens libharfbuzz at first font access).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        default-jre-headless fontconfig fonts-dejavu-core libharfbuzz0b \
    && rm -rf /var/lib/apt/lists/*
# Pinned by version and checksum; PlantUmlRenderer expects it at /app/plantuml.jar.
ADD --checksum=sha256:89948f14c93756c7a3fb7b69078ff37e8489fd79dd430c582b931e2f65358690 \
    https://github.com/plantuml/plantuml/releases/download/v1.2026.6/plantuml-1.2026.6.jar \
    /app/plantuml.jar
COPY pyproject.toml ./
COPY engine ./engine
COPY templates ./templates
COPY auditor ./auditor
RUN pip install --no-cache-dir -e ".[http]" pytest
COPY --from=web /app/web/dist ./web/dist
# Deck building shells out to the Slidev CLI: node on PATH and the toolchain at
# /app/slidev. The decks build to static HTML, so no browser is bundled.
COPY --from=slidev /usr/local/bin/node /usr/local/bin/node
COPY --from=slidev /app/slidev ./slidev
RUN mkdir -p /data/projects
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health').read()" || exit 1
CMD ["python", "-m", "uvicorn", \
     "engine.adapters.inbound.http.app:create_app", \
     "--factory", "--host", "0.0.0.0", "--port", "8000"]
