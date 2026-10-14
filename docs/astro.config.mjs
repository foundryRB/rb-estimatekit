import { defineConfig } from 'astro/config';
import mermaid from 'astro-mermaid';
import starlight from '@astrojs/starlight';
import { mermaidConfig } from '@psa-department-of-engineering/starlight-theme';

export default defineConfig({
  site: process.env.SITE_URL ?? 'http://localhost:4321',
  // The central docs portal (ADR-023) mounts this site under /apps/<app>; CI passes
  // the prefix as DOCS_BASE. Astro `base` prefixes asset + Starlight-generated link
  // URLs so they resolve under the prefix. Defaults to '/' for standalone/local.
  base: process.env.DOCS_BASE || '/',
  integrations: [
    // Must precede starlight so it transforms ```mermaid blocks before
    // expressive-code renders them as plain code. autoTheme follows dark/light.
    // mermaidConfig + the stylesheet come from the shared starlight-theme package
    // (one source of truth; REF-StarlightDocs 8.1).
    mermaid({ autoTheme: true, mermaidConfig }),
    starlight({
      title: 'EstimateKit',
      components: { SiteTitle: './src/components/SiteTitle.astro' },
      logo: { light: './src/assets/rb-lockup-light.svg', dark: './src/assets/rb-lockup-dark.svg', alt: 'Software Engineering, RB' },
      description: 'Project estimation engine — from requirements to delivery roadmaps.',
      customCss: ['@psa-department-of-engineering/starlight-theme/styles.css', './src/styles/rb.css'],
      lastUpdated: true,
      tableOfContents: {
        minHeadingLevel: 2,
        maxHeadingLevel: 3,
      },
      sidebar: [
        {
          label: 'Start Here',
          items: ['index'],
        },
        {
          label: 'Architecture',
          items: [{ autogenerate: { directory: 'architecture' } }],
        },
        {
          label: 'Decisions',
          items: [{ autogenerate: { directory: 'decisions' } }],
        },
      ],
    }),
  ],
});
