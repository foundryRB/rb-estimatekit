import { Appearance } from '../../vodafone/Appearance';
import React, { useState, useRef, useEffect } from 'react';
import { cn } from '@/utils';
import { Lockup } from '@/components/Lockup';
import { useTheme } from '@/viewmodels/useThemeViewModel';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
    Save,
    Play,
    Download,
    Presentation,
    Loader2,
    CheckCircle2,
    XCircle,
    Upload,
    Archive,
    ChevronDown,
    BookOpen,
} from 'lucide-react';
import type { Pipeline, GenerationStatus, OutputFile } from '@/models/types';
import { ALL_PIPELINES } from '@/models/types';
import { ENDPOINTS } from '@/api/endpoints';
import { ConnectAgentMenu } from '@/views/molecules/ConnectAgentMenu';

interface ToolbarProps {
    projectName: string;
    slug: string;
    dirtyCount: number;
    saving: boolean;
    onSaveAll: () => void;
    /* Guide */
    onOpenGuide?: () => void;
    /* Generation */
    selectedPipelines: Pipeline[];
    onTogglePipeline: (p: Pipeline) => void;
    /** The defined phase ids; the slide deck sells one of them. */
    phases?: string[];
    selectedPhase?: string | null;
    onSelectPhase?: (phase: string) => void;
    genStatus: GenerationStatus;
    onGenerate: () => void;
    /* Outputs */
    outputs: OutputFile[];
    /* Export / Import */
    onExport: () => void;
    exporting: boolean;
    onImport: (file: File) => void;
    importing: boolean;
}

const PIPELINE_LABELS: Record<Pipeline, string> = {
    roadmap: 'Roadmap',
    excel: 'Excel',
    slides: 'Slides',
};

/**
 * Top toolbar for the workspace.
 *
 * Shows project name, save button, pipeline selector, the phase the deck
 * sells (when the project defines several), generate button, and download
 * links for outputs.
 */
export const Toolbar: React.FC<ToolbarProps> = ({
    projectName,
    slug,
    dirtyCount,
    saving,
    onSaveAll,
    onOpenGuide,
    selectedPipelines,
    onTogglePipeline,
    phases = [],
    selectedPhase = null,
    onSelectPhase,
    genStatus,
    onGenerate,
    outputs,
    onExport,
    exporting,
    onImport,
    importing,
}) => {
    const isGenerating = genStatus === 'running';
    const slidesSelected = selectedPipelines.includes('slides');
    const phaseNeeded = phases.length > 1;
    const excelOutputs = outputs.filter((o) => o.pipeline === 'excel');
    const hasSlides = outputs.some((o) => o.pipeline === 'slides');
    const hasDownloads = excelOutputs.length > 0;
    const { theme } = useTheme();
    const importInputRef = React.useRef<HTMLInputElement>(null);
    const [downloadsOpen, setDownloadsOpen] = useState(false);
    const downloadsRef = useRef<HTMLDivElement>(null);

    // Close dropdown on outside click
    useEffect(() => {
        if (!downloadsOpen) return;
        const onClickOutside = (e: MouseEvent) => {
            if (downloadsRef.current && !downloadsRef.current.contains(e.target as Node)) {
                setDownloadsOpen(false);
            }
        };
        document.addEventListener('mousedown', onClickOutside);
        return () => document.removeEventListener('mousedown', onClickOutside);
    }, [downloadsOpen]);

    const handleImportClick = () => importInputRef.current?.click();
    const handleFileSelected = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) onImport(file);
        e.target.value = '';
    };

    return (
        <div className="flex items-center gap-2 border-b bg-background px-3 py-1.5 flex-shrink-0">
            {/* Project name */}
            <a
                href="/"
                className="flex items-center gap-2 mr-2 hover:opacity-80 transition-opacity"
            >
                {/* One mark: the speechmark. The EK badge beside it read as a second logo. */}
                <Lockup mode={theme} height={28} />
            </a>
            <h1 className="text-sm font-semibold truncate mr-4 max-w-[200px]">{projectName}</h1>

            {/* Guide */}
            {onOpenGuide && (
                <Button
                    variant="ghost"
                    size="sm"
                    className="gap-1.5 text-xs"
                    onClick={onOpenGuide}
                    title="Open Getting Started guide"
                >
                    <BookOpen className="h-3.5 w-3.5" />
                    Guide
                </Button>
            )}

            <div className="flex-1 min-w-0" />

            {/* Save all */}
            <Button
                variant="ghost"
                size="sm"
                className="gap-1.5 text-xs"
                disabled={dirtyCount === 0 || saving}
                onClick={onSaveAll}
            >
                {saving ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                    <Save className="h-3.5 w-3.5" />
                )}
                Save All
                {dirtyCount > 0 && (
                    <Badge variant="secondary" className="h-4 px-1 text-[10px] leading-none ml-0.5">
                        {dirtyCount}
                    </Badge>
                )}
            </Button>

            {/* Divider */}
            <div className="w-px h-5 bg-border mx-1 flex-shrink-0" />

            {/* Pipeline toggles */}
            <div className="flex items-center gap-0.5 flex-shrink-0">
                {ALL_PIPELINES.map((p) => (
                    <button
                        key={p}
                        type="button"
                        onClick={() => onTogglePipeline(p)}
                        className={cn(
                            'px-2 py-0.5 rounded text-xs font-medium transition-colors',
                            selectedPipelines.includes(p)
                                ? 'bg-primary/10 text-link'
                                : 'text-muted-foreground hover:text-foreground',
                        )}
                    >
                        {PIPELINE_LABELS[p]}
                    </button>
                ))}
            </div>

            {/* Phase the deck sells (a multi-phase project refuses slides without one) */}
            {phaseNeeded && (
                <select
                    aria-label="Phase the slide deck sells"
                    title="Phase the slide deck sells"
                    value={selectedPhase ?? ''}
                    disabled={!slidesSelected}
                    onChange={(e) => onSelectPhase?.(e.target.value)}
                    className={cn(
                        'h-7 rounded border bg-background px-1.5 text-xs font-medium',
                        slidesSelected ? 'text-foreground' : 'text-muted-foreground',
                    )}
                >
                    {phases.map((p) => (
                        <option key={p} value={p}>
                            {p}
                        </option>
                    ))}
                </select>
            )}

            {/* Generate */}
            <Button
                variant="default"
                size="sm"
                className="gap-1.5 text-xs"
                disabled={
                    isGenerating ||
                    selectedPipelines.length === 0 ||
                    (slidesSelected && phaseNeeded && !selectedPhase)
                }
                onClick={onGenerate}
            >
                {isGenerating ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : genStatus === 'success' ? (
                    <CheckCircle2 className="h-3.5 w-3.5" />
                ) : genStatus === 'error' ? (
                    <XCircle className="h-3.5 w-3.5" />
                ) : (
                    <Play className="h-3.5 w-3.5" />
                )}
                Generate
            </Button>

            {/* Divider */}
            {(hasDownloads || hasSlides) && (
                <div className="w-px h-5 bg-border mx-1 flex-shrink-0" />
            )}

            {/* Downloads dropdown */}
            {hasDownloads && (
                <div className="relative" ref={downloadsRef}>
                    <Button
                        variant="ghost"
                        size="sm"
                        className="gap-1.5 text-xs"
                        onClick={() => setDownloadsOpen((v) => !v)}
                    >
                        <Download className="h-3.5 w-3.5" />
                        Downloads
                        <Badge
                            variant="secondary"
                            className="h-4 px-1 text-[10px] leading-none ml-0.5"
                        >
                            {excelOutputs.length}
                        </Badge>
                        <ChevronDown
                            className={cn(
                                'h-3 w-3 transition-transform',
                                downloadsOpen && 'rotate-180',
                            )}
                        />
                    </Button>

                    {downloadsOpen && (
                        <div className="absolute right-0 top-full mt-1 z-50 min-w-[180px] rounded-md border bg-popover p-1 shadow-md">
                            {excelOutputs.map((o) => {
                                const relPath = o.path.replace(/^output\//, '');
                                return (
                                    <a
                                        key={o.name}
                                        href={`/api${ENDPOINTS.outputDownload(slug, relPath)}`}
                                        download
                                        className="flex items-center gap-2 rounded-sm px-2 py-1.5 text-xs text-popover-foreground hover:bg-accent transition-colors"
                                        onClick={() => setDownloadsOpen(false)}
                                    >
                                        <Download className="h-3.5 w-3.5 flex-shrink-0" />
                                        {o.name.replace(/\.xlsx?$/i, '')}
                                    </a>
                                );
                            })}
                        </div>
                    )}
                </div>
            )}

            {/* Slides link (separate — opens in new tab, not a download) */}
            {hasSlides && (
                <a
                    href={`/projects/${slug}/slides`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
                    title="View slides"
                >
                    <Presentation className="h-3.5 w-3.5" />
                    Slides
                </a>
            )}

            {/* Divider */}
            <div className="w-px h-5 bg-border mx-1" />

            {/* Export / Import */}
            <Button
                variant="ghost"
                size="sm"
                className="gap-1.5 text-xs"
                disabled={exporting}
                onClick={onExport}
                title="Export project data as ZIP"
            >
                {exporting ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                    <Archive className="h-3.5 w-3.5" />
                )}
                Export
            </Button>
            <Button
                variant="ghost"
                size="sm"
                className="gap-1.5 text-xs"
                disabled={importing}
                onClick={handleImportClick}
                title="Import project data from ZIP"
            >
                {importing ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                    <Upload className="h-3.5 w-3.5" />
                )}
                Import
            </Button>
            <input
                ref={importInputRef}
                type="file"
                accept=".zip"
                className="hidden"
                onChange={handleFileSelected}
            />

            {/* Divider */}
            <div className="w-px h-5 bg-border mx-1" />

            {/* MCP connect */}
            <ConnectAgentMenu />

            {/* Theme toggle */}
            <Appearance />
        </div>
    );
};
