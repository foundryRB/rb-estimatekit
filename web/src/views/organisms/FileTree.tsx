import React, { useState } from 'react';
import { cn } from '@/utils';
import { FileTreeItem } from '@/views/molecules/FileTreeItem';
import { ChevronRight, FolderOpen, Folder } from 'lucide-react';
import type { ProjectFile } from '@/models/types';

interface FileTreeProps {
    fileTree: Map<string, ProjectFile[]>;
    activeFilePath: string | null;
    dirtyPaths: Set<string>;
    deletingPath: string | null;
    onFileClick: (path: string) => void;
    onFileDelete: (path: string) => void;
}

export const FileTree: React.FC<FileTreeProps> = ({
    fileTree,
    activeFilePath,
    dirtyPaths,
    deletingPath,
    onFileClick,
    onFileDelete,
}) => {
    const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
    const [confirmingPath, setConfirmingPath] = useState<string | null>(null);

    const toggleDir = (dir: string) => {
        setCollapsed((prev) => {
            const next = new Set(prev);
            if (next.has(dir)) next.delete(dir);
            else next.add(dir);
            return next;
        });
    };

    const sortedDirs = [...fileTree.keys()].sort((a, b) => {
        // Root files (".") first, then alphabetical
        if (a === '.') return -1;
        if (b === '.') return 1;
        return a.localeCompare(b);
    });

    return (
        <div className="py-2 text-sm">
            {sortedDirs.map((dir) => {
                const files = fileTree.get(dir) ?? [];
                const isRoot = dir === '.';
                const isCollapsed = collapsed.has(dir);

                return (
                    <div key={dir}>
                        {/* Directory header */}
                        {!isRoot && (
                            <button
                                type="button"
                                onClick={() => toggleDir(dir)}
                                className="flex w-full items-center gap-1.5 px-2 py-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground hover:text-foreground transition-colors"
                            >
                                <ChevronRight
                                    className={cn(
                                        'h-3 w-3 transition-transform',
                                        !isCollapsed && 'rotate-90',
                                    )}
                                />
                                {isCollapsed ? (
                                    <Folder className="h-3.5 w-3.5" />
                                ) : (
                                    <FolderOpen className="h-3.5 w-3.5" />
                                )}
                                {dir}
                            </button>
                        )}

                        {/* Files */}
                        {(isRoot || !isCollapsed) && (
                            <div className={cn(!isRoot && 'ml-3')}>
                                {files.map((file) => (
                                    <FileTreeItem
                                        key={file.path}
                                        file={file}
                                        active={file.path === activeFilePath}
                                        dirty={dirtyPaths.has(file.path)}
                                        confirming={confirmingPath === file.path}
                                        deleting={deletingPath === file.path}
                                        onClick={() => onFileClick(file.path)}
                                        onRequestDelete={() => setConfirmingPath(file.path)}
                                        onConfirmDelete={() => {
                                            onFileDelete(file.path);
                                            setConfirmingPath(null);
                                        }}
                                        onCancelDelete={() => setConfirmingPath(null)}
                                    />
                                ))}
                            </div>
                        )}
                    </div>
                );
            })}
        </div>
    );
};
