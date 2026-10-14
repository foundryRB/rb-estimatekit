/**
 * GuidePanel — static getting-started guide rendered as a pseudo-tab.
 *
 * Shows a Welcome-style panel with numbered stages, relevant files,
 * and tips. Users can click file links to open them.
 */

import React, { useState } from 'react';
import { BookOpen, ChevronDown, ChevronRight, FileText, Lightbulb } from 'lucide-react';
import type { Guide, GuideStage } from '@/models/types';

interface GuidePanelProps {
    guide: Guide;
    onOpenFile: (path: string) => void;
}

const StageCard: React.FC<{
    stage: GuideStage;
    index: number;
    onOpenFile: (path: string) => void;
}> = ({ stage, index, onOpenFile }) => {
    const [expanded, setExpanded] = useState(index === 0);

    return (
        <div className="border rounded-lg overflow-hidden">
            <button
                type="button"
                className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-muted/50 transition-colors"
                onClick={() => setExpanded((v) => !v)}
            >
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-link text-xs font-bold flex-shrink-0">
                    {index + 1}
                </span>
                <div className="flex-1 min-w-0">
                    <span className="text-sm font-medium">{stage.name}</span>
                </div>
                {expanded ? (
                    <ChevronDown className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                ) : (
                    <ChevronRight className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                )}
            </button>

            {expanded && (
                <div className="px-4 pb-4 space-y-3 border-t pt-3">
                    <p className="text-sm text-muted-foreground">{stage.description}</p>

                    {/* File links */}
                    {stage.files.length > 0 && (
                        <div className="space-y-1">
                            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Files
                            </p>
                            <div className="flex flex-wrap gap-1.5">
                                {stage.files.map((file) => (
                                    <button
                                        key={file}
                                        type="button"
                                        className="inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-xs font-mono hover:bg-accent hover:text-accent-foreground transition-colors"
                                        onClick={() => onOpenFile(file)}
                                    >
                                        <FileText className="h-3 w-3 flex-shrink-0" />
                                        {file}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Tips */}
                    {stage.tips.length > 0 && (
                        <div className="space-y-1.5">
                            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Tips
                            </p>
                            <ul className="space-y-1">
                                {stage.tips.map((tip, i) => (
                                    <li
                                        key={i}
                                        className="flex items-start gap-2 text-xs text-muted-foreground"
                                    >
                                        <Lightbulb className="h-3 w-3 mt-0.5 text-yellow-500 flex-shrink-0" />
                                        <span>{tip}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export const GuidePanel: React.FC<GuidePanelProps> = ({ guide, onOpenFile }) => {
    return (
        <div className="h-full overflow-y-auto">
            <div className="max-w-2xl mx-auto px-6 py-8 space-y-6">
                {/* Header */}
                <div className="space-y-2">
                    <div className="flex items-center gap-2">
                        <BookOpen className="h-5 w-5 text-link" />
                        <h2 className="text-lg font-semibold">{guide.title}</h2>
                    </div>
                    {guide.intro && (
                        <p className="text-sm text-muted-foreground leading-relaxed">
                            {guide.intro}
                        </p>
                    )}
                </div>

                {/* Stages */}
                <div className="space-y-2">
                    {guide.stages.map((stage, i) => (
                        <StageCard key={stage.id} stage={stage} index={i} onOpenFile={onOpenFile} />
                    ))}
                </div>
            </div>
        </div>
    );
};
