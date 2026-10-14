# EstimateKit docs

The Starlight (Astro) documentation site for EstimateKit, published to the central
docs portal at `docs.rb-foundry.com/apps/estimatekit` (ADR-018, ADR-023).

## Develop

```bash
npm install
npm run dev      # http://localhost:4321
```

## Build

```bash
npm run build    # astro check && astro build -> dist/
npm test         # STARLIGHT intent meta-tests (needs the @psa-* registry token)
```

## Deploy

`Dockerfile` builds the site and serves it under `DOCS_BASE` (the portal passes
`/apps/estimatekit`). Astro's output is flat, so the runtime stage copies `dist/`
to `html${DOCS_BASE}` — see the comments in `Dockerfile` and `astro.config.mjs`.

Content lives in `src/content/docs/`; every page carries CSD frontmatter
(`id`, `type`, `status`, `updated`) enforced by `src/content.config.ts` and the
STARLIGHT claims in `intent.yaml`.
