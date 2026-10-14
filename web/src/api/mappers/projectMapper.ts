/**
 * Mappers: OpenAPI-generated DTO types → frontend domain models.
 */

import type { components } from '@/api/generated/types';
import type {
    ProjectSummary,
    GenerationResult,
    ProjectFile,
    FileContent,
    FileKind,
    OutputFile,
    Pipeline,
    AuditorCheck,
    AuditorSuggestion,
    AuditorResult,
    CheckOutcome,
    DiagramSvg,
} from '@/models/types';

/* ── Helpers ─────────────────────────────────────────────── */

function inferKind(filename: string): FileKind {
    const ext = filename.split('.').pop()?.toLowerCase() ?? '';
    const map: Record<string, FileKind> = {
        yaml: 'yaml',
        yml: 'yaml',
        tsv: 'tsv',
        puml: 'puml',
    };
    return map[ext] ?? 'text';
}

/* ── Project ─────────────────────────────────────────────── */

export function mapProjectSummary(
    dto: components['schemas']['ProjectSummaryResponse'],
): ProjectSummary {
    return {
        name: dto.name,
        client: dto.client,
        description: dto.description,
        phaseCount: dto.phase_count,
        phases: [...dto.phases],
        requirementCount: dto.requirement_count,
        assumptionCount: dto.assumption_count,
        archived: dto.archived,
    };
}

/* ── Files ───────────────────────────────────────────────── */

export function mapProjectFile(dto: components['schemas']['FileInfoItem']): ProjectFile {
    return {
        path: dto.path,
        name: dto.name,
        kind: dto.kind as FileKind,
        directory: dto.directory,
    };
}

export function mapFileContent(dto: components['schemas']['FileContentResponse']): FileContent {
    return {
        path: dto.path,
        content: dto.content,
        kind: inferKind(dto.path),
    };
}

/* ── Architecture Diagrams ───────────────────────────────── */

export function mapDiagramSvg(dto: components['schemas']['DiagramSvgResponse']): DiagramSvg {
    return {
        name: dto.name,
        svg: dto.svg,
    };
}

/* ── Generation ──────────────────────────────────────────── */

export function mapGenerationResult(
    dto: components['schemas']['GenerateResponse'],
): GenerationResult {
    return {
        outcomes: dto.results,
        success: dto.success,
        phase: dto.phase ?? null,
    };
}

export function mapOutputFile(dto: components['schemas']['OutputFileItem']): OutputFile {
    return {
        name: dto.name,
        pipeline: dto.pipeline as Pipeline,
        path: dto.path,
        size: dto.size,
    };
}

/* ── Audit ───────────────────────────────────────────────── */

export function mapAuditCheck(dto: components['schemas']['AuditCheckItem']): AuditorCheck {
    return {
        nodeId: dto.node_id,
        name: dto.name,
        category: dto.category,
        outcome: dto.outcome as CheckOutcome,
        message: dto.message,
    };
}

export function mapAuditSuggestion(
    dto: components['schemas']['AuditSuggestionItem'],
): AuditorSuggestion {
    return {
        code: dto.code,
        title: dto.title,
        detail: dto.detail,
        category: dto.category,
        severity: dto.severity,
    };
}

export function mapAuditReport(dto: components['schemas']['AuditReportResponse']): AuditorResult {
    return {
        checks: dto.checks.map(mapAuditCheck),
        suggestions: (dto.suggestions ?? []).map(mapAuditSuggestion),
        passedCount: dto.passed_count,
        failedCount: dto.failed_count,
        skippedCount: dto.skipped_count,
        passed: dto.passed,
        durationMs: dto.duration_ms,
    };
}
