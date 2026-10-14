import { Appearance } from '../../vodafone/Appearance';
import React from 'react';
import { useHomeViewModel } from '@/viewmodels/useHomeViewModel';
import { useTheme } from '@/viewmodels/useThemeViewModel';
import { Lockup } from '@/components/Lockup';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ConnectAgentMenu } from '@/views/molecules/ConnectAgentMenu';
import {
    Archive,
    ArchiveRestore,
    ArrowRight,
    Plus,
    Loader2,
    Pencil,
    Wifi,
    WifiOff,
    FolderOpen,
    Terminal,
    Trash2,
} from 'lucide-react';

/**
 * Landing page — a split-panel workspace launcher.
 *
 * Left panel:  Branding, create new project (terminal-inspired).
 * Right panel: Discovered projects gallery + direct slug entry.
 *
 * The blueprint grid background and monospace touches convey
 * "estimation engineering tool," not "generic SaaS."
 */
export const HomePage: React.FC = () => {
    const vm = useHomeViewModel();
    const { theme } = useTheme();

    // Which card is showing its inline "confirm delete" state (null = none).
    const [confirmingSlug, setConfirmingSlug] = React.useState<string | null>(null);

    // Which card is showing its inline rename form (null = none).
    const [renamingCard, setRenamingCard] = React.useState<string | null>(null);
    const [renameSlugInput, setRenameSlugInput] = React.useState('');
    const [renameNameInput, setRenameNameInput] = React.useState('');

    const openRename = (slug: string) => {
        setRenameSlugInput(slug);
        setRenameNameInput('');
        setRenamingCard(slug);
    };

    const submitRename = async (slug: string) => {
        const newSlug = renameSlugInput.trim();
        const newName = renameNameInput.trim();
        const slugChanged = newSlug !== '' && newSlug !== slug;
        if (!slugChanged && newName === '') {
            setRenamingCard(null);
            return;
        }
        const ok = await vm.renameProject(
            slug,
            slugChanged ? newSlug : undefined,
            newName !== '' ? newName : undefined,
        );
        if (ok) setRenamingCard(null);
    };

    return (
        <div className="app-home flex min-h-screen text-foreground">
            {/* ── Left panel: branding + create ─────────────── */}
            <div className="relative flex w-full flex-col justify-between border-r md:w-[420px] lg:w-[480px]">
                {/* Blueprint grid overlay */}
                <div
                    className="pointer-events-none absolute inset-0 opacity-[0.04] dark:opacity-[0.06]"
                    style={{
                        backgroundImage:
                            'linear-gradient(hsl(var(--foreground)) 1px, transparent 1px), linear-gradient(90deg, hsl(var(--foreground)) 1px, transparent 1px)',
                        backgroundSize: '40px 40px',
                    }}
                />

                <div className="relative z-10 flex flex-1 flex-col justify-center px-10 py-12">
                    {/* Logo & title */}
                    <div className="mb-12">
                        <div className="mb-4 flex items-end gap-3">
                            {/* One mark: the speechmark (see Toolbar). */}
                            <Lockup mode={theme} height={36} className="mb-1" />
                            <div className="h-px flex-1 bg-border" />
                        </div>
                        <h1 className="text-3xl font-bold tracking-tight">EstimateKit</h1>
                        <p className="mt-1 font-mono text-xs tracking-widest text-muted-foreground uppercase">
                            Estimation &amp; Planning Engine
                        </p>
                    </div>

                    {/* Create section — terminal-inspired */}
                    <div className="space-y-4">
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <Terminal className="h-3.5 w-3.5" />
                            <span className="font-mono uppercase tracking-wider">New Project</span>
                            <div className="h-px flex-1 bg-border" />
                        </div>

                        <div className="rounded-lg border bg-card p-4 shadow-sm">
                            <div className="flex items-center gap-1 text-[11px] text-muted-foreground font-mono mb-3">
                                <span className="text-link">$</span>
                                <span>estimatekit scaffold</span>
                                <span className="inline-block h-3.5 w-1.5 animate-pulse bg-primary/60" />
                            </div>

                            <div className="flex gap-2">
                                <Input
                                    placeholder="my-project"
                                    value={vm.newSlug}
                                    onChange={(e) => vm.setNewSlug(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter') void vm.createProject();
                                    }}
                                    className="font-mono text-sm h-9"
                                />
                                <Button
                                    size="sm"
                                    className="gap-1.5 h-9 px-4 shrink-0"
                                    disabled={vm.creating}
                                    onClick={() => void vm.createProject()}
                                >
                                    {vm.creating ? (
                                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                    ) : (
                                        <Plus className="h-3.5 w-3.5" />
                                    )}
                                    Create
                                </Button>
                            </div>

                            {vm.createError && (
                                <p className="mt-2 text-xs text-destructive font-mono">
                                    {vm.createError}
                                </p>
                            )}
                        </div>
                    </div>
                </div>

                {/* Bottom bar: health + MCP connect + theme */}
                <div className="relative z-10 flex items-center justify-between border-t px-10 py-3">
                    <div className="flex items-center gap-1.5 text-xs text-muted-foreground font-mono">
                        {vm.healthy === true && (
                            <>
                                <Wifi className="h-3 w-3 text-green-500" />
                                <span>engine connected</span>
                            </>
                        )}
                        {vm.healthy === false && (
                            <>
                                <WifiOff className="h-3 w-3 text-red-500" />
                                <span>engine offline</span>
                            </>
                        )}
                        {vm.healthy === null && (
                            <>
                                <Loader2 className="h-3 w-3 animate-spin" />
                                <span>checking&hellip;</span>
                            </>
                        )}
                    </div>
                    <div className="flex items-center gap-1">
                        <ConnectAgentMenu dropUp />
                        <Appearance />
                    </div>
                </div>
            </div>

            {/* ── Right panel: project gallery ─────────────── */}
            <div className="hidden flex-1 flex-col md:flex">
                {/* Header */}
                <div className="flex items-center gap-2 border-b px-8 py-3">
                    <FolderOpen className="h-4 w-4 text-muted-foreground" />
                    <span className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
                        Projects
                    </span>
                    <div className="h-px flex-1 bg-border" />
                    {!vm.projectsLoading && (
                        <span className="text-xs font-mono text-muted-foreground tabular-nums">
                            {vm.projects.length}
                        </span>
                    )}
                </div>

                {/* Project grid */}
                <div className="flex-1 overflow-y-auto px-8 py-6">
                    {vm.projectsLoading ? (
                        <div className="flex items-center justify-center py-20 text-muted-foreground">
                            <Loader2 className="h-5 w-5 animate-spin mr-2" />
                            <span className="text-sm font-mono">Scanning&hellip;</span>
                        </div>
                    ) : vm.projects.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
                            <div className="mb-4 h-16 w-16 rounded-xl border-2 border-dashed border-muted flex items-center justify-center">
                                <Plus className="h-6 w-6 opacity-40" />
                            </div>
                            <p className="text-sm">No projects yet</p>
                            <p className="text-xs mt-1 font-mono">
                                Create one using the panel on the left
                            </p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                            {vm.projects.map((slug) => (
                                <div key={slug} className="group relative">
                                    <button
                                        type="button"
                                        onClick={() => vm.openProject(slug)}
                                        className="flex w-full flex-col items-start rounded-lg border bg-card p-4 text-left transition-all hover:border-link/40 hover:shadow-md active:scale-[0.98]"
                                    >
                                        {/* Top row: avatar only. The top-right corner is
                                            reserved for the delete affordance below. */}
                                        <div className="mb-2 flex h-7 w-7 items-center justify-center rounded bg-muted text-[10px] font-bold text-muted-foreground group-hover:bg-primary/10 group-hover:text-link transition-colors">
                                            {slug.slice(0, 2).toUpperCase()}
                                        </div>
                                        <span className="text-sm font-medium truncate w-full pr-6">
                                            {slug}
                                        </span>
                                        {/* Bottom row: path + the open cue (bottom-right),
                                            kept clear of the trash button at top-right. */}
                                        <div className="mt-0.5 flex w-full items-center gap-1">
                                            <span className="flex-1 truncate text-[11px] font-mono text-muted-foreground">
                                                /projects/{slug}
                                            </span>
                                            <ArrowRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground/0 group-hover:text-link transition-all group-hover:translate-x-0.5" />
                                        </div>
                                    </button>

                                    {/* Card actions — fade in on hover, top-right corner */}
                                    <div className="absolute right-2 top-2 flex items-center gap-0.5">
                                        <button
                                            type="button"
                                            aria-label={`Rename ${slug}`}
                                            title={`Rename ${slug}`}
                                            onClick={() => openRename(slug)}
                                            className="flex h-6 w-6 items-center justify-center rounded-md text-muted-foreground opacity-0 transition-all hover:bg-primary/10 hover:text-link focus-visible:opacity-100 group-hover:opacity-100"
                                        >
                                            <Pencil className="h-3.5 w-3.5" />
                                        </button>
                                        <button
                                            type="button"
                                            aria-label={`Archive ${slug}`}
                                            title={`Archive ${slug}`}
                                            disabled={vm.archivingSlug === slug}
                                            onClick={() => void vm.archiveProject(slug)}
                                            className="flex h-6 w-6 items-center justify-center rounded-md text-muted-foreground opacity-0 transition-all hover:bg-primary/10 hover:text-link focus-visible:opacity-100 group-hover:opacity-100"
                                        >
                                            {vm.archivingSlug === slug ? (
                                                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                            ) : (
                                                <Archive className="h-3.5 w-3.5" />
                                            )}
                                        </button>
                                        <button
                                            type="button"
                                            aria-label={`Delete ${slug}`}
                                            title={`Delete ${slug}`}
                                            onClick={() => setConfirmingSlug(slug)}
                                            className="flex h-6 w-6 items-center justify-center rounded-md text-muted-foreground opacity-0 transition-all hover:bg-destructive/10 hover:text-destructive focus-visible:opacity-100 group-hover:opacity-100"
                                        >
                                            <Trash2 className="h-3.5 w-3.5" />
                                        </button>
                                    </div>

                                    {/* Inline rename overlay */}
                                    {renamingCard === slug && (
                                        <form
                                            className="absolute inset-0 z-20 flex flex-col justify-center gap-1.5 rounded-lg border border-link/50 bg-card p-3 shadow-md"
                                            onSubmit={(e) => {
                                                e.preventDefault();
                                                void submitRename(slug);
                                            }}
                                        >
                                            <Input
                                                aria-label="New slug"
                                                placeholder="new-slug"
                                                value={renameSlugInput}
                                                onChange={(e) => setRenameSlugInput(e.target.value)}
                                                className="h-7 font-mono text-xs"
                                                autoFocus
                                            />
                                            <Input
                                                aria-label="New display name"
                                                placeholder="Display name (optional)"
                                                value={renameNameInput}
                                                onChange={(e) => setRenameNameInput(e.target.value)}
                                                className="h-7 text-xs"
                                            />
                                            <div className="flex gap-2">
                                                <Button
                                                    type="button"
                                                    size="sm"
                                                    variant="outline"
                                                    className="h-7 flex-1 text-xs"
                                                    disabled={vm.renamingSlug === slug}
                                                    onClick={() => setRenamingCard(null)}
                                                >
                                                    Cancel
                                                </Button>
                                                <Button
                                                    type="submit"
                                                    size="sm"
                                                    className="h-7 flex-1 gap-1 text-xs"
                                                    disabled={vm.renamingSlug === slug}
                                                >
                                                    {vm.renamingSlug === slug ? (
                                                        <Loader2 className="h-3 w-3 animate-spin" />
                                                    ) : (
                                                        <Pencil className="h-3 w-3" />
                                                    )}
                                                    Rename
                                                </Button>
                                            </div>
                                        </form>
                                    )}

                                    {/* Inline confirm overlay */}
                                    {confirmingSlug === slug && (
                                        <div className="absolute inset-0 z-20 flex flex-col justify-center gap-2 rounded-lg border border-destructive/50 bg-card p-3 shadow-md">
                                            <p className="text-[11px] leading-tight text-foreground">
                                                Delete{' '}
                                                <span className="font-mono font-medium">
                                                    {slug}
                                                </span>
                                                ? This can&apos;t be undone.
                                            </p>
                                            <div className="flex gap-2">
                                                <Button
                                                    size="sm"
                                                    variant="outline"
                                                    className="h-7 flex-1 text-xs"
                                                    disabled={vm.deletingSlug === slug}
                                                    onClick={() => setConfirmingSlug(null)}
                                                >
                                                    Cancel
                                                </Button>
                                                <Button
                                                    size="sm"
                                                    variant="destructive"
                                                    className="h-7 flex-1 gap-1 text-xs"
                                                    disabled={vm.deletingSlug === slug}
                                                    onClick={async () => {
                                                        await vm.deleteProject(slug);
                                                        setConfirmingSlug(null);
                                                    }}
                                                >
                                                    {vm.deletingSlug === slug ? (
                                                        <Loader2 className="h-3 w-3 animate-spin" />
                                                    ) : (
                                                        <Trash2 className="h-3 w-3" />
                                                    )}
                                                    Delete
                                                </Button>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                    {vm.deleteError && (
                        <p className="mt-3 text-xs text-destructive font-mono">{vm.deleteError}</p>
                    )}
                    {vm.renameError && (
                        <p className="mt-3 text-xs text-destructive font-mono">{vm.renameError}</p>
                    )}
                    {vm.archiveError && (
                        <p className="mt-3 text-xs text-destructive font-mono">{vm.archiveError}</p>
                    )}

                    {/* Archived projects — parked, visible, revivable */}
                    {vm.archivedProjects.length > 0 && (
                        <div className="mt-8">
                            <div className="mb-3 flex items-center gap-2">
                                <Archive className="h-3.5 w-3.5 text-muted-foreground" />
                                <span className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
                                    Archived
                                </span>
                                <div className="h-px flex-1 bg-border" />
                                <span className="text-xs font-mono text-muted-foreground tabular-nums">
                                    {vm.archivedProjects.length}
                                </span>
                            </div>
                            <div className="flex flex-wrap gap-2">
                                {vm.archivedProjects.map((slug) => (
                                    <div
                                        key={slug}
                                        className="flex items-center gap-2 rounded-md border border-dashed bg-muted/30 px-3 py-1.5"
                                    >
                                        <span className="font-mono text-xs text-muted-foreground">
                                            {slug}
                                        </span>
                                        <button
                                            type="button"
                                            aria-label={`Unarchive ${slug}`}
                                            title={`Unarchive ${slug}`}
                                            disabled={vm.archivingSlug === slug}
                                            onClick={() => void vm.unarchiveProject(slug)}
                                            className="flex h-5 w-5 items-center justify-center rounded text-muted-foreground transition-colors hover:bg-primary/10 hover:text-link"
                                        >
                                            {vm.archivingSlug === slug ? (
                                                <Loader2 className="h-3 w-3 animate-spin" />
                                            ) : (
                                                <ArchiveRestore className="h-3 w-3" />
                                            )}
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* Direct slug entry */}
                <div className="border-t px-8 py-4">
                    <form
                        onSubmit={(e) => {
                            e.preventDefault();
                            vm.openProject();
                        }}
                        className="flex items-center gap-2"
                    >
                        <span className="text-xs font-mono text-muted-foreground whitespace-nowrap">
                            Open by slug:
                        </span>
                        <Input
                            placeholder="project-slug"
                            value={vm.openSlug}
                            onChange={(e) => vm.setOpenSlug(e.target.value)}
                            className="flex-1 font-mono text-xs h-8 max-w-xs"
                        />
                        <Button type="submit" variant="outline" size="sm" className="gap-1.5 h-8">
                            Go
                            <ArrowRight className="h-3 w-3" />
                        </Button>
                    </form>
                    {vm.openError && (
                        <p className="mt-1.5 text-xs text-destructive font-mono">{vm.openError}</p>
                    )}
                </div>
            </div>

            {/* ── Mobile fallback (projects below create) ──── */}
            <div className="flex flex-col md:hidden w-full">
                {vm.projects.length > 0 && (
                    <div className="border-t px-6 py-6 space-y-3">
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <FolderOpen className="h-3.5 w-3.5" />
                            <span className="font-mono uppercase tracking-wider">Projects</span>
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                            {vm.projects.map((slug) => (
                                <div key={slug} className="relative">
                                    <button
                                        type="button"
                                        onClick={() => vm.openProject(slug)}
                                        className="w-full rounded-lg border bg-card p-3 pr-9 text-left text-sm font-medium transition-colors hover:border-link/40"
                                    >
                                        {slug}
                                    </button>
                                    <button
                                        type="button"
                                        aria-label={`Delete ${slug}`}
                                        onClick={() => setConfirmingSlug(slug)}
                                        className="absolute right-1.5 top-1/2 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded-md text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                                    >
                                        <Trash2 className="h-3.5 w-3.5" />
                                    </button>
                                    {confirmingSlug === slug && (
                                        <div className="absolute inset-0 z-20 flex items-center gap-1.5 rounded-lg border border-destructive/50 bg-card px-2 shadow-md">
                                            <span className="flex-1 truncate text-[11px]">
                                                Delete {slug}?
                                            </span>
                                            <Button
                                                size="sm"
                                                variant="outline"
                                                className="h-6 px-2 text-[11px]"
                                                disabled={vm.deletingSlug === slug}
                                                onClick={() => setConfirmingSlug(null)}
                                            >
                                                No
                                            </Button>
                                            <Button
                                                size="sm"
                                                variant="destructive"
                                                className="h-6 px-2 text-[11px]"
                                                disabled={vm.deletingSlug === slug}
                                                onClick={async () => {
                                                    await vm.deleteProject(slug);
                                                    setConfirmingSlug(null);
                                                }}
                                            >
                                                {vm.deletingSlug === slug ? (
                                                    <Loader2 className="h-3 w-3 animate-spin" />
                                                ) : (
                                                    'Yes'
                                                )}
                                            </Button>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
