import React, { useMemo } from 'react';
import { useParams, Navigate } from 'react-router-dom';
import { useWorkspaceViewModel } from '@/viewmodels/useWorkspaceViewModel';
import { WorkspaceLayout } from '@/views/templates/WorkspaceLayout';
import { Toolbar } from '@/views/organisms/Toolbar';
import { FileTree } from '@/views/organisms/FileTree';
import { EditorTabBar } from '@/views/molecules/EditorTabBar';
import { TsvEditor } from '@/views/organisms/TsvEditor';
import { TextEditor } from '@/views/organisms/TextEditor';
import { PlantUmlViewer } from '@/views/organisms/PlantUmlViewer';
import { AuditorPanel } from '@/views/organisms/AuditorPanel';
import { GuidePanel } from '@/views/organisms/GuidePanel';
import { Loader2, FileText } from 'lucide-react';

/**
 * The main IDE workspace for a project.
 *
 * Composes the workspace layout with: file tree, tab bar, content editor,
 * auditor panel, and toolbar — all driven by useWorkspaceViewModel.
 */
export const WorkspacePage: React.FC = () => {
    const { slug } = useParams<{ slug: string }>();
    if (!slug) return <Navigate to="/" replace />;

    return <WorkspaceInner slug={slug} />;
};

/** Inner component that uses the hook (hooks can't be called after early return). */
const WorkspaceInner: React.FC<{ slug: string }> = ({ slug }) => {
    const vm = useWorkspaceViewModel(slug);

    const dirtyPaths = useMemo(() => new Set(vm.dirtyTabs.map((t) => t.path)), [vm.dirtyTabs]);

    /* ── Loading / error states ────────────────────────────── */
    if (vm.loadError) {
        return (
            <div className="flex min-h-screen items-center justify-center">
                <div className="text-center space-y-3">
                    <p className="text-destructive font-medium">{vm.loadError}</p>
                    <a href="/" className="text-sm text-link hover:underline">
                        &larr; Back to Home
                    </a>
                </div>
            </div>
        );
    }

    if (vm.filesLoading) {
        return (
            <div className="flex min-h-screen items-center justify-center gap-2 text-muted-foreground">
                <Loader2 className="h-5 w-5 animate-spin" />
                Loading project&hellip;
            </div>
        );
    }

    /* ── Editor content ───────────────────────────────────── */
    const guideActive = vm.guideTabOpen && !vm.activeTabPath;

    const renderEditor = () => {
        if (!vm.activeTab) {
            return (
                <div className="flex h-full items-center justify-center text-muted-foreground">
                    <div className="text-center space-y-2">
                        <FileText className="h-10 w-10 mx-auto opacity-30" />
                        <p className="text-sm">Select a file to edit</p>
                    </div>
                </div>
            );
        }

        if (vm.activeTab.kind === 'tsv') {
            return (
                <TsvEditor
                    content={vm.activeTab.content}
                    onChange={(c) => vm.updateTabContent(vm.activeTab!.path, c)}
                />
            );
        }

        if (vm.activeTab.kind === 'puml') {
            return (
                <PlantUmlViewer
                    slug={slug}
                    name={vm.activeTab.name}
                    content={vm.activeTab.content}
                    savedContent={vm.activeTab.originalContent}
                    onChange={(c) => vm.updateTabContent(vm.activeTab!.path, c)}
                />
            );
        }

        return (
            <TextEditor
                content={vm.activeTab.content}
                onChange={(c) => vm.updateTabContent(vm.activeTab!.path, c)}
                language={vm.activeTab.kind}
            />
        );
    };

    /* ── Compose layout ───────────────────────────────────── */
    return (
        <WorkspaceLayout
            toolbar={
                <Toolbar
                    projectName={vm.summary?.name ?? slug}
                    slug={slug}
                    dirtyCount={vm.dirtyTabs.length}
                    saving={vm.saving}
                    onSaveAll={() => void vm.saveAllFiles()}
                    onOpenGuide={vm.guideData ? vm.openGuide : undefined}
                    selectedPipelines={vm.selectedPipelines}
                    onTogglePipeline={vm.togglePipeline}
                    phases={vm.phases}
                    selectedPhase={vm.selectedPhase}
                    onSelectPhase={vm.setSelectedPhase}
                    genStatus={vm.genStatus}
                    onGenerate={() => void vm.runGeneration()}
                    outputs={vm.outputs}
                    onExport={() => void vm.exportZip()}
                    exporting={vm.exporting}
                    onImport={(file) => void vm.importZip(file)}
                    importing={vm.importing}
                />
            }
            sidebar={
                <FileTree
                    fileTree={vm.fileTree}
                    activeFilePath={vm.activeTabPath}
                    dirtyPaths={dirtyPaths}
                    deletingPath={vm.deletingPath}
                    onFileClick={(path) => void vm.openFile(path)}
                    onFileDelete={(path) => void vm.deleteFile(path)}
                />
            }
            editor={
                <div className="flex h-full flex-col">
                    <EditorTabBar
                        tabs={vm.tabs}
                        activeTabPath={vm.activeTabPath}
                        dirtyPaths={dirtyPaths}
                        onSelect={vm.setActiveTabPath}
                        onClose={vm.closeTab}
                        guideOpen={vm.guideTabOpen}
                        guideActive={guideActive}
                        onSelectGuide={vm.openGuide}
                        onCloseGuide={vm.closeGuide}
                    />
                    <div className="flex-1 min-h-0 relative">
                        {/* Kept mounted (hidden, not unmounted) while inactive so its
                            scroll position and expanded stages survive switching to a
                            file and back (#4). */}
                        {vm.guideData && (
                            <div className={`h-full ${guideActive ? '' : 'hidden'}`}>
                                <GuidePanel
                                    guide={vm.guideData}
                                    onOpenFile={(path) => void vm.openFile(path)}
                                />
                            </div>
                        )}
                        {!guideActive && <div className="h-full">{renderEditor()}</div>}
                    </div>
                </div>
            }
            bottomPanel={
                <AuditorPanel
                    result={vm.auditResult}
                    loading={vm.auditing}
                    open={vm.auditorPanelOpen}
                    onToggle={() => vm.setAuditorPanelOpen(!vm.auditorPanelOpen)}
                    onRefresh={() => void vm.triggerAudit()}
                />
            }
        />
    );
};
