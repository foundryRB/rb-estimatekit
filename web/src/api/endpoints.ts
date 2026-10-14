/**
 * API endpoint URL constants.
 */

export const ENDPOINTS = {
    health: '/health',
    guide: '/guide',

    // Project lifecycle
    projects: '/projects/',
    scaffold: '/projects/scaffold',
    projectSummary: (slug: string) => `/projects/${e(slug)}/summary`,
    deleteProject: (slug: string) => `/projects/${e(slug)}`,
    renameProject: (slug: string) => `/projects/${e(slug)}/rename`,
    archiveProject: (slug: string) => `/projects/${e(slug)}/archive`,
    unarchiveProject: (slug: string) => `/projects/${e(slug)}/unarchive`,

    // File operations
    projectFiles: (slug: string) => `/projects/${e(slug)}/files`,
    fileContent: (slug: string, path: string) => `/projects/${e(slug)}/files/${path}`,

    // Architecture diagrams
    /** Render one architecture diagram to SVG. `name` is the bare .puml filename. */
    diagram: (slug: string, name: string) =>
        `/projects/${e(slug)}/architecture/diagrams/${e(name)}`,

    // Auditor
    audit: (slug: string) => `/projects/${e(slug)}/audit`,

    // Generation & outputs
    generate: (slug: string) => `/projects/${e(slug)}/generate`,
    outputs: (slug: string) => `/projects/${e(slug)}/outputs`,
    /** Download a single output file. `relPath` is relative to output/ (e.g. "excel/P1.xlsx"). */
    outputDownload: (slug: string, relPath: string) => `/projects/${e(slug)}/outputs/${relPath}`,

    // Export / Import
    exportZip: (slug: string) => `/projects/${e(slug)}/export`,
    importZip: (slug: string) => `/projects/${e(slug)}/import`,
} as const;

function e(s: string) {
    return encodeURIComponent(s);
}
