---
title: EstimateKit
id: DOC-ESTIMATEKIT-001
type: Overview
status: Active
updated: "2026-10-03"
summary: What EstimateKit is and how it turns structured project data into delivery artifacts.
---

EstimateKit is a project-estimation engine, the tool of the delivery lifecycle's Scope phase: it turns an engagement brief into the priced artifacts a proposal needs. It reads structured project data (YAML + TSV), runs scheduling and costing logic, and produces a roadmap, Excel workbooks (quote, financial model, BRD), and an executive slide deck. A React workspace, a CLI, and an MCP door for agents drive the same engine through different interfaces.

## What it does

From one project folder of input data, EstimateKit generates:

- **Roadmap** — a timeline and resource plan (TSV), scheduled from phase and activity data.
- **Excel** — quoter, financial-model, and BRD workbooks (`.xlsx`).
- **Slides** — an executive presentation (Slidev Markdown, built to static HTML when the toolchain is present).

An **auditor** validates each project's data integrity before generation, and surfaces risk *suggestions* (e.g. no test lag, milestones all landing in one month) on top of hard errors.

The rules for authoring a project's data are in the **authoring guide**, which is the only reference for the data contract. It covers which files a project holds, the columns each one keeps, how streams are named, and what every audit check enforces. The workspace shows it in its Getting Started panel, agents read it with the `get_guide` MCP tool, and `GET /api/guide` serves it over HTTP. Its source is `templates/guide.yaml`.

## Shape

- **Engine** (`engine/`): a hexagonal FastAPI + CLI backend (domain / application / adapters). The same use cases are exposed over HTTP under `/api`, as a CLI, and as MCP tools under `/mcp` (the full tool list is in [Components → The MCP door](architecture/components/#the-mcp-door)).
- **Web** (`web/`): a React + Vite + Tailwind SPA — an IDE-like workspace for editing project files, running audits, and generating outputs. Served as static files by the backend in the built image.
- **Run paths**: `devops/docker-compose.yml` brings the whole solution up in one container; the native dev path (uvicorn + Vite) is documented in the repository `README.md`.

## Deployment

EstimateKit follows the Foundry app contract (the platform's repo standard): `devops/` for the image and local run, `k8s/` for the Helm chart, and this `docs/` site, published to the central docs portal. On the install that runs it, the app serves at `estimatekit.<zone>` (this install's is `estimatekit.vodafone-foundry.com`).

> **Access control:** deployed with the chart's OIDC gate (the default), oauth2-proxy fronts the SPA and `/api` against the app's own Keycloak realm, and fail-closed HTTP Basic narrows to the `/mcp` machine door (`ESTIMATEKIT_AUTH_SCOPE=mcp`); stood up alone, the Basic gate covers every route, answering 503 until credentials exist. Either way the hostname is safe to publish. See [Components → Access control](architecture/components/#access-control).
