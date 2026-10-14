import React from 'react';
import { useResizable } from '@/hooks/useResizable';

interface WorkspaceLayoutProps {
    toolbar: React.ReactNode;
    sidebar: React.ReactNode;
    editor: React.ReactNode;
    bottomPanel: React.ReactNode;
}

/** Thin draggable divider between panels. */
const ResizeHandle: React.FC<{
    direction: 'horizontal' | 'vertical';
    onMouseDown: (e: React.MouseEvent) => void;
}> = ({ direction, onMouseDown }) => (
    <div
        onMouseDown={onMouseDown}
        className={
            direction === 'horizontal'
                ? 'w-1 flex-shrink-0 cursor-col-resize bg-transparent hover:bg-primary/20 active:bg-primary/30 transition-colors'
                : 'h-1 flex-shrink-0 cursor-row-resize bg-transparent hover:bg-primary/20 active:bg-primary/30 transition-colors'
        }
    />
);

/**
 * IDE-like workspace layout with resizable panes.
 *
 * ┌─────────────────────────────────────────────────┐
 * │ Toolbar                                         │
 * ├──────────┬──────────────────────────────────────┤
 * │ Sidebar  │ Editor                               │
 * │  ↔ drag  │                                      │
 * │          │                                      │
 * │          ├──────────────────────────────────────┤
 * │          │ ↕ drag                               │
 * │          │ Bottom Panel (auditor)               │
 * └──────────┴──────────────────────────────────────┘
 */
export const WorkspaceLayout: React.FC<WorkspaceLayoutProps> = ({
    toolbar,
    sidebar,
    editor,
    bottomPanel,
}) => {
    const sidebarResize = useResizable({
        direction: 'horizontal',
        initialSize: 224, // w-56 equivalent
        minSize: 120,
        maxSize: 480,
    });

    const bottomResize = useResizable({
        direction: 'vertical',
        initialSize: 200,
        minSize: 32, // collapsed header only
        maxSize: 500,
        inverted: true,
    });

    return (
        <div className="app-workspace flex h-screen flex-col text-foreground">
            {/* Toolbar */}
            {toolbar}

            {/* Main area */}
            <div className="flex flex-1 min-h-0">
                {/* Sidebar — file tree */}
                <aside
                    className="flex-shrink-0 border-r overflow-y-auto bg-muted/20"
                    style={{ width: sidebarResize.size }}
                >
                    {sidebar}
                </aside>

                {/* Sidebar resize handle */}
                <ResizeHandle direction="horizontal" onMouseDown={sidebarResize.onMouseDown} />

                {/* Editor + bottom panel */}
                <main className="flex flex-1 flex-col min-w-0">
                    {/* Editor area */}
                    <div className="flex-1 min-h-0 overflow-auto">{editor}</div>

                    {/* Bottom panel resize handle */}
                    <ResizeHandle direction="vertical" onMouseDown={bottomResize.onMouseDown} />

                    {/* Bottom panel */}
                    <div
                        className="flex-shrink-0 overflow-hidden"
                        style={{ height: bottomResize.size }}
                    >
                        {bottomPanel}
                    </div>
                </main>
            </div>
        </div>
    );
};
