import React from 'react';
import { cn } from '@/utils';
import { X, BookOpen } from 'lucide-react';
import { FileIcon } from '@/views/atoms/FileIcon';
import type { EditorTab } from '@/models/types';

interface EditorTabBarProps {
    tabs: EditorTab[];
    activeTabPath: string | null;
    dirtyPaths: Set<string>;
    onSelect: (path: string) => void;
    onClose: (path: string) => void;
    /** Guide pseudo-tab */
    guideOpen?: boolean;
    guideActive?: boolean;
    onSelectGuide?: () => void;
    onCloseGuide?: () => void;
}

export const EditorTabBar: React.FC<EditorTabBarProps> = ({
    tabs,
    activeTabPath,
    dirtyPaths,
    onSelect,
    onClose,
    guideOpen,
    guideActive,
    onSelectGuide,
    onCloseGuide,
}) => {
    if (tabs.length === 0 && !guideOpen) return null;

    return (
        <div className="flex items-center border-b bg-muted/30 overflow-x-auto">
            {/* Guide pseudo-tab */}
            {guideOpen && (
                <div
                    className={cn(
                        'group flex items-center gap-1.5 border-r px-3 py-2 text-sm cursor-pointer transition-colors',
                        guideActive
                            ? 'bg-background text-foreground border-b-2 border-b-link'
                            : 'text-muted-foreground hover:bg-muted hover:text-foreground',
                    )}
                    onClick={onSelectGuide}
                >
                    <BookOpen className="h-3.5 w-3.5" />
                    <span className="truncate max-w-[140px]">Guide</span>
                    <button
                        type="button"
                        onClick={(e) => {
                            e.stopPropagation();
                            onCloseGuide?.();
                        }}
                        className="ml-1 rounded p-0.5 opacity-0 group-hover:opacity-100 hover:bg-muted-foreground/10 transition-opacity"
                    >
                        <X className="h-3 w-3" />
                    </button>
                </div>
            )}

            {/* File tabs */}
            {tabs.map((tab) => {
                const isActive = tab.path === activeTabPath;
                const isDirty = dirtyPaths.has(tab.path);

                return (
                    <div
                        key={tab.path}
                        className={cn(
                            'group flex items-center gap-1.5 border-r px-3 py-2 text-sm cursor-pointer transition-colors',
                            isActive
                                ? 'bg-background text-foreground border-b-2 border-b-link'
                                : 'text-muted-foreground hover:bg-muted hover:text-foreground',
                        )}
                        onClick={() => onSelect(tab.path)}
                        onAuxClick={(e) => {
                            if (e.button === 1) {
                                e.preventDefault();
                                onClose(tab.path);
                            }
                        }}
                    >
                        <FileIcon kind={tab.kind} className="h-3.5 w-3.5" />
                        <span className="truncate max-w-[140px]">
                            {tab.name}
                            {isDirty && <span className="text-link ml-0.5">*</span>}
                        </span>
                        <button
                            type="button"
                            onClick={(e) => {
                                e.stopPropagation();
                                onClose(tab.path);
                            }}
                            className="ml-1 rounded p-0.5 opacity-0 group-hover:opacity-100 hover:bg-muted-foreground/10 transition-opacity"
                        >
                            <X className="h-3 w-3" />
                        </button>
                    </div>
                );
            })}
        </div>
    );
};
