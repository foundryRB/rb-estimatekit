# EstimateKit

> From customer requirements to delivery roadmaps, Excel workbooks, and slide decks.

EstimateKit is a project-estimation engine. It reads structured project data
(YAML + TSV), runs scheduling and costing logic, and produces the artifacts a
proposal needs — a roadmap, Excel workbooks (quote, financial model, BRD), and an
executive Slidev deck. A hexagonal FastAPI + CLI engine drives it; a React + Vite
workspace and a PowerShell CLI are two faces onto the same use cases. A standalone
auditor validates each project's data and raises delivery-risk suggestions.

## Run with Docker

The web SPA build and the Python runtime are produced inside the image, so Docker is
the only prerequisite — every configuration value has a sensible default and there
are no secrets.

```bash
docker compose -f devops/docker-compose.yml up --build
```

The app listens on http://localhost:8000 (the React workspace at `/`, the API under
`/api`). Generated projects persist in the `estimatekit-data` named volume. To explore
the repo's bundled example projects instead of an empty volume, see the commented bind
mount in `devops/docker-compose.yml`. `.env.example` documents the (optional)
environment variables.

> **Auth:** the app fails closed on HTTP Basic auth. `devops/docker-compose.yml` sets
> demo credentials (`ops` / `change-me`) — change them before exposing the instance,
> or set `ESTIMATEKIT_AUTH_DISABLED=true` for an unauthenticated local run. See
> [Access control](#access-control).

## Develop without Docker

The backend (FastAPI, port 8000) and the frontend (Vite, port 3000) run as two
processes; Vite proxies `/api` to the backend.

```bash
# Backend — FastAPI on :8000
pip install -e ".[http,dev]"
python -m uvicorn engine.adapters.inbound.http.app:create_app --factory --port 8000 --reload

# Frontend — Vite dev server on :3000 (proxies /api -> :8000)
cd web && npm install && npm run dev
```

On Windows, `devops/start.ps1` (or double-clicking `devops/start.bat`) launches both
in their own windows and opens the browser.

The same engine is also a CLI, and there is a PowerShell front-end under `cli/`:

```bash
estimatekit --help                 # discover / scaffold / scaffold-phase / generate / summary
estimatekit discover projects/     # find projects under a root
estimatekit scaffold-phase projects/<slug> P3   # mint a phase: its files arrive sentinel-marked
estimatekit generate projects/<slug> --phase P3 # the deck sells one phase; a single-phase project needs no --phase
estimatekit audit projects/<slug> --phase P3    # one phase plus shared integrity; omit --phase for all
```

Test and lint:

```bash
python -m pytest                   # engine + integration tests
ruff check .
cd web && npm test                 # frontend unit tests
```

## Access control

EstimateKit gates every route — the SPA, all of `/api/*`, and `/mcp` — with HTTP Basic auth and
**fails closed**: it refuses to serve protected routes unless credentials are
configured, so a misconfigured instance is never silently exposed. The health endpoint
(`/api/health`) stays open so probes work. This is what makes it safe to publish at
`estimatekit.rb-foundry.com` through the shared Cloudflare tunnel.

- Production: set `ESTIMATEKIT_AUTH_USER` and `ESTIMATEKIT_AUTH_PASSWORD` (injected as a
  Kubernetes Secret by the chart; see `k8s/values.yaml` `auth.existingSecret`). With no
  Secret provisioned the app answers 503 on every protected route.
- Local dev and tests: set `ESTIMATEKIT_AUTH_DISABLED=true` to run without a prompt.

Edge SSO (e.g. Cloudflare Access) can still be layered on top; the app does not depend
on it. See `.env.example` for the variables.

## Agents (MCP)

The engine serves the Model Context Protocol at `/mcp` on the same app: tools mirror
the inbound ports (scaffold, read/write data files, audit, generate, list outputs), so
an agent drives the same estimation loop the SPA and CLI do. Connect with:

```bash
claude mcp add --scope user --transport http estimatekit https://estimatekit.rb-foundry.com/mcp \
  --header "Authorization: Basic <base64 user:password>"
```

The same fail-closed HTTP Basic gate covers `/mcp`. Deployments must allow their public
hostname through the transport's DNS-rebinding guard via `ESTIMATEKIT_MCP_ALLOWED_HOSTS`
(the chart sets it; see `k8s/values.yaml`). The `estimate-project` MCP prompt carries
the full estimation runbook for a given project slug.

## Data

Projects are folders of plain files (one per engagement). Natively they live under
`projects/` in the repo; in the container they live on the `/data` volume, overridable
with `ESTIMATEKIT_PROJECTS_ROOT`. Back them up by snapshotting that volume. Generated
`output/` is regenerated from inputs and is gitignored.

## Layout

- `engine/domain` — entities, value objects, scheduling services, constants (no outward imports)
- `engine/application` — inbound/outbound ports and the use cases (generate, scaffold, audit, file I/O, import/export)
- `engine/adapters/inbound` — CLI (argparse) and HTTP (FastAPI) adapters; the HTTP app serves the built SPA at `/`
- `engine/adapters/outbound` — persistence, roadmap (TSV), excel (openpyxl), slidev, and the pytest-backed auditor adapter
- `engine/container.py` — composition root (the single place all layers meet)
- `web/` — React + Vite + Tailwind SPA (MVVM), served as static files by the backend in the built image
- `auditor/` — standalone pytest data-integrity checks, run by the engine
- `templates/` — scaffolding templates (TSV, YAML, PlantUML); `projects/` — example engagements
- `devops/` — multi-stage Dockerfile and docker-compose
- `k8s/` — Helm chart for the rb-foundry.com install
- `docs/` — Starlight documentation site (published to the central docs portal)
- `intent.yaml` — CSD-INTENT-01 claims for the app

## Learn more

Architecture and conventions follow the shared `REF-CleanArchitecture`, `REF-FastAPI`,
`REF-Frontend`, and `REF-Python` references. Deployment follows the platform's repo
standard (`REF-Foundry`, ADR-018); the rendered docs live at
`docs.rb-foundry.com/apps/estimatekit`.

## Commits

Every commit follows the platform's commit convention: a Conventional Commit
subject and no co-author trailer. CI derives the version from the type and
blocks release otherwise. The convention is documented on the platform
portal's GitOps delivery page, under "Commit convention"; the committed
`.pre-commit-config.yaml` checks it locally once installed (`pre-commit install`).
