import React from 'react';
import { cn } from '@/utils';
import { FileIcon } from '@/views/atoms/FileIcon';
import { Trash2, Check, X, Loader2 } from 'lucide-react';
import type { ProjectFile } from '@/models/types';

interface FileTreeItemProps {
    file: ProjectFile;
    active: boolean;
    dirty: boolean;
    confirming: boolean;
    deleting: boolean;
    onClick: () => void;
    onRequestDelete: () => void;
    onConfirmDelete: () => void;
    onCancelDelete: () => void;
}

export const FileTreeItem: React.FC<FileTreeItemProps> = ({
    file,
    active,
    dirty,
    confirming,
    deleting,
    onClick,
    onRequestDelete,
    onConfirmDelete,
    onCancelDelete,
}) => {
    if (confirming) {
        return (
            <div className="flex w-full items-center gap-1 rounded-md border border-destructive/50 bg-destructive/10 px-2 py-1.5 text-sm">
                <span className="min-w-0 flex-1 truncate text-destructive" title={file.name}>
                    Delete {file.name}?
                </span>
                <button
                    type="button"
                    aria-label={`Confirm delete ${file.name}`}
                    title="Confirm delete"
                    onClick={onConfirmDelete}
                    disabled={deleting}
                    className="flex-shrink-0 rounded p-0.5 text-destructive transition-colors hover:text-destructive/80 disabled:opacity-50"
                >
                    {deleting ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                        <Check className="h-3.5 w-3.5" />
                    )}
                </button>
                <button
                    type="button"
                    aria-label="Cancel delete"
                    title="Cancel"
                    onClick={onCancelDelete}
                    disabled={deleting}
                    className="flex-shrink-0 rounded p-0.5 text-muted-foreground transition-colors hover:text-foreground disabled:opacity-50"
                >
                    <X className="h-3.5 w-3.5" />
                </button>
            </div>
        );
    }

    return (
        <div
            className={cn(
                'group flex w-full items-center rounded-md transition-colors',
                active ? 'bg-accent text-accent-foreground' : 'hover:bg-muted',
            )}
        >
            <button
                type="button"
                onClick={onClick}
                className={cn(
                    'flex min-w-0 flex-1 items-center gap-2 px-2 py-1.5 text-left text-sm',
                    active ? 'font-medium' : 'text-muted-foreground group-hover:text-foreground',
                )}
            >
                <FileIcon kind={file.kind} className="h-4 w-4 flex-shrink-0" />
                <span className="flex-1 truncate">{file.name}</span>
                {dirty && (
                    <span
                        className="h-2 w-2 flex-shrink-0 rounded-full bg-primary"
                        title="Unsaved changes"
                    />
                )}
            </button>
            <button
                type="button"
                aria-label={`Delete ${file.name}`}
                title="Delete file"
                onClick={onRequestDelete}
                className="mr-1 flex-shrink-0 rounded p-1 text-muted-foreground opacity-0 transition-all hover:text-destructive focus-visible:opacity-100 group-hover:opacity-100"
            >
                <Trash2 className="h-3.5 w-3.5" />
            </button>
        </div>
    );
};
