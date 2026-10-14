/**
 * ViewModel: Workspace (the IDE view for a project).
 *
 * Manages file tree, open tabs, editor content, auditor runs, and generation.
 * This is the largest ViewModel — it orchestrates the full project editing experience.
 */

import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { getProjectSummary, generateProject, listOutputs } from '@/api/clients/projectClient';
import {
    listFiles,
    readFile,
    saveFile,
    deleteFile as deleteFileRequest,
    exportProject,
    importProject,
} from '@/api/clients/fileClient';
import { runAudit } from '@/api/clients/auditorClient';
import { fetchGuide } from '@/api/clients/guideClient';
import type {
    ProjectSummary,
    ProjectFile,
    EditorTab,
    AuditorResult,
    GenerationResult,
    GenerationStatus,
    Pipeline,
    OutputFile,
    Guide,
} from '@/models/types';
import { ALL_PIPELINES } from '@/models/types';

/* ── TSV helpers ─────────────────────────────────────────── */

export function parseTsv(content: string): { headers: string[]; rows: string[][] } {
    const lines = content.split('\n').filter((l) => l.trim() !== '');
    const headers = lines[0]?.split('\t') ?? [];
    const rows = lines.slice(1).map((l) => l.split('\t'));
    return { headers, rows };
}

export function serializeTsv(headers: string[], rows: string[][]): string {
    const headerLine = headers.join('\t');
    const dataLines = rows.map((r) => r.join('\t'));
    return [headerLine, ...dataLines].join('\n') + '\n';
}

/* ── ViewModel ───────────────────────────────────────────── */

export function useWorkspaceViewModel(slug: string) {
    /* ── Project summary ──────────────────────────────────── */
    const [summary, setSummary] = useState<ProjectSummary | null>(null);
    const [loadError, setLoadError] = useState<string | null>(null);

    /* ── File tree ────────────────────────────────────────── */
    const [files, setFiles] = useState<ProjectFile[]>([]);
    const [filesLoading, setFilesLoading] = useState(true);

    /* ── Editor tabs ──────────────────────────────────────── */
    const [tabs, setTabs] = useState<EditorTab[]>([]);
    const [activeTabPath, setActiveTabPath] = useState<string | null>(null);
    const [saving, setSaving] = useState(false);
    const [saveError, setSaveError] = useState<string | null>(null);
    const [deletingPath, setDeletingPath] = useState<string | null>(null);

    const activeTab = useMemo(
        () => tabs.find((t) => t.path === activeTabPath) ?? null,
        [tabs, activeTabPath],
    );

    const dirtyTabs = useMemo(() => tabs.filter((t) => t.content !== t.originalContent), [tabs]);

    /* ── Auditor ──────────────────────────────────────────── */
    const [auditResult, setAuditResult] = useState<AuditorResult | null>(null);
    const [auditing, setAuditing] = useState(false);
    const auditTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    /* ── Generation ───────────────────────────────────────── */
    const [genStatus, setGenStatus] = useState<GenerationStatus>('idle');
    const [genResult, setGenResult] = useState<GenerationResult | null>(null);
    const [genError, setGenError] = useState<string | null>(null);
    const [selectedPipelines, setSelectedPipelines] = useState<Pipeline[]>([...ALL_PIPELINES]);
    const [outputs, setOutputs] = useState<OutputFile[]>([]);
    // The operator's pick from the toolbar of the phase the slide deck sells.
    const [pickedPhase, setPickedPhase] = useState<string | null>(null);
    const phases = useMemo(() => summary?.phases ?? [], [summary]);
    // The phase the slide deck sells: the pick while it names a defined phase,
    // otherwise the newest phase.
    const selectedPhase = useMemo(
        () =>
            pickedPhase && phases.includes(pickedPhase)
                ? pickedPhase
                : (phases[phases.length - 1] ?? null),
        [pickedPhase, phases],
    );

    /* ── Panels ───────────────────────────────────────────── */
    const [auditorPanelOpen, setAuditorPanelOpen] = useState(true);

    /* ── Guide ────────────────────────────────────────────── */
    const [guideData, setGuideData] = useState<Guide | null>(null);
    const [guideTabOpen, setGuideTabOpen] = useState(false);

    /* ── Export / Import ──────────────────────────────────── */
    const [exporting, setExporting] = useState(false);
    const [importing, setImporting] = useState(false);

    /* ── Load project on mount ────────────────────────────── */
    const loadProject = useCallback(async () => {
        setLoadError(null);
        setFilesLoading(true);
        try {
            const [summaryData, fileList] = await Promise.all([
                getProjectSummary(slug),
                listFiles(slug),
            ]);
            setSummary(summaryData);
            setFiles(fileList);
        } catch (err) {
            setLoadError(err instanceof Error ? err.message : 'Failed to load project.');
        } finally {
            setFilesLoading(false);
        }
    }, [slug]);

    useEffect(() => {
        void loadProject();
    }, [loadProject]);

    /* ── Hydrate existing outputs on mount ────────────────── */
    // Generation writes artifacts to the server that outlive the session, but
    // `outputs` only ever gets populated as a side effect of runGeneration.
    // Without this, the Downloads dropdown and Slides link stay hidden on a
    // fresh page load even when a past generation exists — forcing a needless
    // re-generate to reveal them. Load them up front, mirroring loadProject.
    useEffect(() => {
        void (async () => {
            try {
                setOutputs(await listOutputs(slug));
            } catch {
                // No outputs yet (or endpoint unavailable) — leave empty.
            }
        })();
    }, [slug]);

    /* ── Load guide once on mount & auto-open ─────────────── */
    useEffect(() => {
        void (async () => {
            try {
                const guide = await fetchGuide();
                setGuideData(guide);
                // Auto-open guide tab when no file tabs are open
                setGuideTabOpen(true);
            } catch {
                // Guide is optional — fail silently
            }
        })();
    }, []);

    /* ── File operations ──────────────────────────────────── */

    const openFile = useCallback(
        async (path: string) => {
            // If already open, just activate
            const existing = tabs.find((t) => t.path === path);
            if (existing) {
                setActiveTabPath(path);
                return;
            }

            try {
                const content = await readFile(slug, path);
                const file = files.find((f) => f.path === path);
                const tab: EditorTab = {
                    path: content.path,
                    name: file?.name ?? path.split('/').pop() ?? path,
                    kind: content.kind,
                    content: content.content,
                    originalContent: content.content,
                };
                setTabs((prev) => [...prev, tab]);
                setActiveTabPath(path);
            } catch (err) {
                setSaveError(err instanceof Error ? err.message : 'Failed to open file.');
            }
        },
        [slug, tabs, files],
    );

    const closeTab = useCallback(
        (path: string) => {
            setTabs((prev) => prev.filter((t) => t.path !== path));
            if (activeTabPath === path) {
                setActiveTabPath((_prev) => {
                    const remaining = tabs.filter((t) => t.path !== path);
                    return remaining.length > 0 ? remaining[remaining.length - 1]!.path : null;
                });
            }
        },
        [activeTabPath, tabs],
    );

    const openGuide = useCallback(() => {
        setGuideTabOpen(true);
        setActiveTabPath(null);
    }, []);

    const closeGuide = useCallback(() => {
        setGuideTabOpen(false);
        // Activate the last open file tab, if any
        setActiveTabPath((prev) => prev ?? (tabs.length > 0 ? tabs[tabs.length - 1]!.path : null));
    }, [tabs]);

    /* ── Auditor ──────────────────────────────────────────── */

    const triggerAudit = useCallback(async () => {
        setAuditing(true);
        try {
            const result = await runAudit(slug);
            setAuditResult(result);
        } catch {
            // Silently fail — auditor is a background check
        } finally {
            setAuditing(false);
        }
    }, [slug]);

    // Stable ref so debounce timers always call the latest triggerAudit
    const triggerAuditRef = useRef(triggerAudit);
    triggerAuditRef.current = triggerAudit;

    const updateTabContent = useCallback((path: string, content: string) => {
        setTabs((prev) => prev.map((t) => (t.path === path ? { ...t, content } : t)));
        // Schedule an audit after the user stops typing (debounce 2s)
        if (auditTimerRef.current) clearTimeout(auditTimerRef.current);
        auditTimerRef.current = setTimeout(() => {
            void triggerAuditRef.current();
        }, 2000);
    }, []);

    const saveActiveFile = useCallback(async () => {
        if (!activeTab || activeTab.content === activeTab.originalContent) return;
        setSaving(true);
        setSaveError(null);
        try {
            await saveFile(slug, activeTab.path, activeTab.content);
            setTabs((prev) =>
                prev.map((t) =>
                    t.path === activeTab.path ? { ...t, originalContent: t.content } : t,
                ),
            );
            // Auto-audit after save
            void triggerAudit();
        } catch (err) {
            setSaveError(err instanceof Error ? err.message : 'Failed to save file.');
        } finally {
            setSaving(false);
        }
    }, [activeTab, slug, triggerAudit]);

    const saveAllFiles = useCallback(async () => {
        setSaving(true);
        setSaveError(null);
        try {
            await Promise.all(dirtyTabs.map((t) => saveFile(slug, t.path, t.content)));
            setTabs((prev) => prev.map((t) => ({ ...t, originalContent: t.content })));
            void triggerAudit();
        } catch (err) {
            setSaveError(err instanceof Error ? err.message : 'Failed to save files.');
        } finally {
            setSaving(false);
        }
    }, [dirtyTabs, slug, triggerAudit]);

    const deleteFile = useCallback(
        async (path: string) => {
            setDeletingPath(path);
            setSaveError(null);
            try {
                await deleteFileRequest(slug, path);
                // Drop it from the tree immediately — no full reload needed.
                setFiles((prev) => prev.filter((f) => f.path !== path));
                // Close its tab if open, keeping another tab active when possible.
                setTabs((prev) => prev.filter((t) => t.path !== path));
                if (activeTabPath === path) {
                    const remaining = tabs.filter((t) => t.path !== path);
                    setActiveTabPath(
                        remaining.length > 0 ? remaining[remaining.length - 1]!.path : null,
                    );
                }
                // The file set changed; re-audit.
                void triggerAudit();
            } catch (err) {
                setSaveError(err instanceof Error ? err.message : 'Failed to delete file.');
            } finally {
                setDeletingPath(null);
            }
        },
        [slug, tabs, activeTabPath, triggerAudit],
    );

    /* ── Generation ───────────────────────────────────────── */

    const togglePipeline = useCallback((pipeline: Pipeline) => {
        setSelectedPipelines((prev) =>
            prev.includes(pipeline) ? prev.filter((p) => p !== pipeline) : [...prev, pipeline],
        );
    }, []);

    const runGeneration = useCallback(async () => {
        // Save all dirty files first
        if (dirtyTabs.length > 0) {
            await saveAllFiles();
        }

        setGenStatus('running');
        setGenResult(null);
        setGenError(null);
        try {
            const result = await generateProject(
                slug,
                selectedPipelines.length < ALL_PIPELINES.length ? selectedPipelines : undefined,
                selectedPipelines.includes('slides') && selectedPhase ? selectedPhase : undefined,
            );
            setGenResult(result);
            setGenStatus(result.success ? 'success' : 'error');

            // Refresh outputs
            try {
                const outs = await listOutputs(slug);
                setOutputs(outs);
            } catch {
                // Outputs endpoint may not exist yet
            }
        } catch (err) {
            setGenError(err instanceof Error ? err.message : 'Generation failed.');
            setGenStatus('error');
        }
    }, [slug, selectedPipelines, selectedPhase, dirtyTabs, saveAllFiles]);

    /* ── Export / Import ──────────────────────────────────── */

    const exportZip = useCallback(async () => {
        setExporting(true);
        try {
            const blob = await exportProject(slug);
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${slug}.zip`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
        } catch {
            // Best-effort — user will see nothing downloaded
        } finally {
            setExporting(false);
        }
    }, [slug]);

    const importZip = useCallback(
        async (file: File) => {
            setImporting(true);
            try {
                await importProject(slug, file);
                // Reload the project to pick up new file contents
                await loadProject();
                // Close all tabs since file contents may have changed
                setTabs([]);
                setActiveTabPath(null);
            } catch {
                // Best-effort
            } finally {
                setImporting(false);
            }
        },
        [slug, loadProject],
    );

    /* ── File tree grouping ───────────────────────────────── */

    const fileTree = useMemo(() => {
        const dirs = new Map<string, ProjectFile[]>();
        for (const f of files) {
            const dir = f.directory || '.';
            if (!dirs.has(dir)) dirs.set(dir, []);
            dirs.get(dir)!.push(f);
        }
        // Sort files within each directory
        for (const [, items] of dirs) {
            items.sort((a, b) => a.name.localeCompare(b.name));
        }
        return dirs;
    }, [files]);

    return {
        // Project
        slug,
        summary,
        loadError,
        // File tree
        files,
        fileTree,
        filesLoading,
        // Editor
        tabs,
        activeTab,
        activeTabPath,
        dirtyTabs,
        saving,
        saveError,
        deletingPath,
        openFile,
        closeTab,
        updateTabContent,
        saveActiveFile,
        saveAllFiles,
        deleteFile,
        setActiveTabPath,
        // Guide
        guideData,
        guideTabOpen,
        openGuide,
        closeGuide,
        // Auditor
        auditResult,
        auditing,
        triggerAudit,
        auditorPanelOpen,
        setAuditorPanelOpen,
        // Generation
        selectedPipelines,
        togglePipeline,
        phases,
        selectedPhase,
        setSelectedPhase: setPickedPhase,
        genStatus,
        genResult,
        genError,
        runGeneration,
        outputs,
        // Export / Import
        exporting,
        importing,
        exportZip,
        importZip,
    } as const;
}
