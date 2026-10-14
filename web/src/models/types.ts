/**
 * Frontend domain types — pure TypeScript, no logic, no I/O, no React.
 *
 * These represent the multi-tenant hosted EstimateKit concepts:
 * projects, editable files, auditor checks, generation outputs.
 */

/* ── Project ─────────────────────────────────────────────── */

export interface ProjectSummary {
    name: string;
    client: string;
    description: string;
    phaseCount: number;
    /** The defined phase ids in phase-table order; the slide deck is built for one of them. */
    phases: string[];
    requirementCount: number;
    assumptionCount: number;
    archived: boolean;
}

/** Discovered projects: active slugs and archived (parked) slugs. */
export interface ProjectListing {
    projects: string[];
    archived: string[];
}

/* ── File System ─────────────────────────────────────────── */

export type FileKind = 'yaml' | 'tsv' | 'puml' | 'text';

export interface ProjectFile {
    path: string;
    name: string;
    kind: FileKind;
    directory: string;
}

export interface FileContent {
    path: string;
    content: string;
    kind: FileKind;
}

/** A single open editor tab. */
export interface EditorTab {
    path: string;
    name: string;
    kind: FileKind;
    content: string;
    originalContent: string;
}

/* ── Architecture Diagrams ───────────────────────────────── */

/** A rendered architecture diagram: its source name and inline SVG markup. */
export interface DiagramSvg {
    name: string;
    svg: string;
}

/* ── TSV Editing ─────────────────────────────────────────── */

export interface TsvData {
    headers: string[];
    rows: string[][];
}

/* ── Auditor ─────────────────────────────────────────────── */

export type CheckOutcome = 'passed' | 'failed' | 'skipped';

export interface AuditorCheck {
    nodeId: string;
    name: string;
    category: string;
    outcome: CheckOutcome;
    message: string;
}

/** Advisory delivery-risk finding — never affects pass/fail. */
export interface AuditorSuggestion {
    code: string;
    title: string;
    detail: string;
    category: string;
    severity: string;
}

export interface AuditorResult {
    checks: AuditorCheck[];
    suggestions: AuditorSuggestion[];
    passedCount: number;
    failedCount: number;
    skippedCount: number;
    passed: boolean;
    durationMs: number;
}

/* ── Generation ──────────────────────────────────────────── */

export type Pipeline = 'roadmap' | 'excel' | 'slides';

export const ALL_PIPELINES: Pipeline[] = ['roadmap', 'excel', 'slides'];

export interface GenerationResult {
    outcomes: Record<string, boolean>;
    success: boolean;
    /** The phase the slide deck was built for; null when the slides pipeline did not run. */
    phase: string | null;
}

export type GenerationStatus = 'idle' | 'running' | 'success' | 'error';

export interface OutputFile {
    name: string;
    pipeline: Pipeline;
    path: string;
    size: number;
}

/* ── Health ──────────────────────────────────────────────── */

export interface HealthStatus {
    status: string;
    service: string;
}

/* ── Guide ───────────────────────────────────────────────── */

export interface GuideStage {
    id: string;
    name: string;
    description: string;
    files: string[];
    tips: string[];
    auditorCategory?: string;
    featureFlag?: string;
}

export interface Guide {
    title: string;
    intro: string;
    stages: GuideStage[];
}
