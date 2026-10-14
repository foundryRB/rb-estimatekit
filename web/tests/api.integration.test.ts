// @vitest-environment node
/**
 * Integration tests — exercises the real frontend API clients against
 * a running backend at http://localhost:8000.
 *
 * Prerequisites:
 *   cd modern/
 *   pip install -e ".[http,dev]"
 *   python -m uvicorn engine.adapters.inbound.http.app:create_app --factory --port 8000
 *
 * Run:
 *   npx vitest run tests/api.integration.test.ts
 *
 * If the backend isn't running, every test fails — that's the point.
 */

import { describe, it, expect, afterAll } from 'vitest';

// Set the base URL BEFORE importing clients (module-level const is evaluated on import)
// Use 127.0.0.1 (not localhost) — Node.js resolves localhost to IPv6 ::1
// but uvicorn binds to 127.0.0.1 by default
process.env.VITE_API_BASE_URL = 'http://127.0.0.1:8000/api';

// Dynamic imports so BASE_URL picks up the env var above
const { checkHealth, discoverProjects, scaffoldProject, getProjectSummary } =
    await import('@/api/clients/projectClient');
const { listFiles, readFile, saveFile } = await import('@/api/clients/fileClient');
const { ApiError } = await import('@/api/client');

/* ── Constants ───────────────────────────────────────────── */

/**
 * Slug used for scaffold / write / read tests.
 * Cleaned up in the test suite itself (scaffold with force=true overwrites).
 */
const TEST_SLUG = `_test-integration-${Date.now()}`;

/* ── Connectivity ────────────────────────────────────────── */

describe('health', () => {
    it('GET /health returns status ok', async () => {
        const result = await checkHealth();
        expect(result).toHaveProperty('status', 'ok');
        expect(result).toHaveProperty('service', 'estimatekit-engine');
    });
});

/* ── Discovery ───────────────────────────────────────────── */

describe('discoverProjects', () => {
    it('returns active and archived project slugs', async () => {
        const listing = await discoverProjects();
        expect(Array.isArray(listing.projects)).toBe(true);
        expect(Array.isArray(listing.archived)).toBe(true);
        // demo-acme should already exist in projects/
        expect(listing.projects).toContain('demo-acme');
    });
});

/* ── Scaffold ────────────────────────────────────────────── */

describe('scaffoldProject', () => {
    it('creates a new project and returns its path', async () => {
        const path = await scaffoldProject(TEST_SLUG, true);
        expect(typeof path).toBe('string');
        expect(path).toContain(TEST_SLUG);
    });

    it('returns 409 when project already exists (force=false)', async () => {
        await expect(scaffoldProject(TEST_SLUG, false)).rejects.toThrow(ApiError);
        try {
            await scaffoldProject(TEST_SLUG, false);
        } catch (err) {
            expect((err as InstanceType<typeof ApiError>).status).toBe(409);
        }
    });
});

/* ── Project Summary ─────────────────────────────────────── */

describe('getProjectSummary', () => {
    it('returns mapped summary for a scaffolded project', async () => {
        const summary = await getProjectSummary(TEST_SLUG);
        expect(summary).toHaveProperty('name');
        expect(summary).toHaveProperty('phaseCount');
        expect(summary).toHaveProperty('requirementCount');
        expect(summary).toHaveProperty('assumptionCount');
    });

    it('throws 404 for a non-existent project', async () => {
        await expect(getProjectSummary('does-not-exist-ever')).rejects.toThrow();
    });
});

/* ── File Listing ────────────────────────────────────────── */

describe('listFiles', () => {
    it('returns files for the scaffolded project', async () => {
        const files = await listFiles(TEST_SLUG);
        expect(Array.isArray(files)).toBe(true);
        expect(files.length).toBeGreaterThan(0);

        // Every file has the expected shape
        for (const f of files) {
            expect(f).toHaveProperty('path');
            expect(f).toHaveProperty('name');
            expect(f).toHaveProperty('kind');
            expect(f).toHaveProperty('directory');
        }
    });
});

/* ── File Read ───────────────────────────────────────────── */

describe('readFile', () => {
    it('reads project.yaml from the scaffolded project', async () => {
        const file = await readFile(TEST_SLUG, 'project.yaml');
        expect(file).toHaveProperty('path', 'project.yaml');
        expect(file).toHaveProperty('content');
        expect(typeof file.content).toBe('string');
        expect(file.content.length).toBeGreaterThan(0);
        expect(file).toHaveProperty('kind', 'yaml');
    });

    it('throws for a file that does not exist', async () => {
        await expect(readFile(TEST_SLUG, 'nope.txt')).rejects.toThrow();
    });
});

/* ── File Write ──────────────────────────────────────────── */

describe('saveFile', () => {
    const TEST_PATH = 'data/integration-test-note.tsv';
    const TEST_CONTENT = 'Column A\tColumn B\nValue 1\tValue 2\n';

    it('writes a file (204) and reads it back', async () => {
        // write — should not throw (returns undefined on 204)
        await saveFile(TEST_SLUG, TEST_PATH, TEST_CONTENT);

        // read back
        const file = await readFile(TEST_SLUG, TEST_PATH);
        expect(file.content).toBe(TEST_CONTENT);
    });
});

/* ── Security ────────────────────────────────────────────── */

describe('slug validation', () => {
    it('rejects slug with path traversal (../)', async () => {
        await expect(getProjectSummary('../etc')).rejects.toThrow();
    });

    it('rejects slug with special characters', async () => {
        await expect(getProjectSummary('foo/bar')).rejects.toThrow();
    });
});

/* ── Error Handling ──────────────────────────────────────── */

describe('error handling', () => {
    it('non-existent project summary → ApiError with status', async () => {
        try {
            await getProjectSummary('zzz-no-such-project-999');
            expect.fail('should have thrown');
        } catch (err) {
            expect(err).toBeInstanceOf(ApiError);
            expect((err as InstanceType<typeof ApiError>).status).toBeGreaterThanOrEqual(400);
        }
    });
});

/* ── Cleanup ─────────────────────────────────────────────── */

import { rmSync } from 'node:fs';
import { resolve } from 'node:path';

afterAll(() => {
    // Best-effort removal of the scaffolded test project
    try {
        rmSync(resolve('projects', TEST_SLUG), { recursive: true, force: true });
    } catch {
        // ignore — CI or permissions may prevent cleanup
    }
});
