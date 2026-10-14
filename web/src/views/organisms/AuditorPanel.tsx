import React from 'react';
import { cn } from '@/utils';
import { AuditorCheckRow } from '@/views/molecules/AuditorCheckRow';
import { AuditorSuggestionRow } from '@/views/molecules/AuditorSuggestionRow';
import { Badge } from '@/components/ui/badge';
import { ChevronDown, ChevronUp, RefreshCw, CheckCircle2 } from 'lucide-react';
import type { AuditorResult } from '@/models/types';

interface AuditorPanelProps {
    result: AuditorResult | null;
    loading: boolean;
    open: boolean;
    onToggle: () => void;
    onRefresh: () => void;
}

/**
 * VS Code "Problems" panel clone.
 *
 * Shows auditor checks grouped by severity, with a header bar
 * that summarises counts and allows collapse / manual audit.
 */
export const AuditorPanel: React.FC<AuditorPanelProps> = ({
    result,
    loading,
    open,
    onToggle,
    onRefresh,
}) => {
    const failedCount = result?.failedCount ?? 0;
    const passedCount = result?.passedCount ?? 0;
    const suggestions = result?.suggestions ?? [];
    const suggestionCount = suggestions.length;
    // Suggestions are advisory: "all clear" means no hard failures AND no advice.
    const nothingToShow = failedCount === 0 && suggestionCount === 0;

    return (
        <div className="flex flex-col border-t bg-background h-full">
            {/* Header bar */}
            <button
                type="button"
                onClick={onToggle}
                className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted/50 select-none"
            >
                {open ? (
                    <ChevronDown className="h-3.5 w-3.5" />
                ) : (
                    <ChevronUp className="h-3.5 w-3.5" />
                )}
                <span className="uppercase tracking-wider">Problems</span>

                {failedCount > 0 && (
                    <Badge variant="destructive" className="h-4 px-1.5 text-[10px] leading-none">
                        {failedCount}
                    </Badge>
                )}
                {suggestionCount > 0 && (
                    <Badge
                        variant="outline"
                        className="h-4 px-1.5 text-[10px] leading-none border-amber-500/50 text-amber-600"
                    >
                        {suggestionCount} advisory
                    </Badge>
                )}
                {passedCount > 0 && (
                    <Badge variant="secondary" className="h-4 px-1.5 text-[10px] leading-none">
                        {passedCount} passed
                    </Badge>
                )}

                {result && nothingToShow && (
                    <span className="flex items-center gap-1 text-green-600">
                        <CheckCircle2 className="h-3 w-3" /> All clear
                    </span>
                )}

                <span className="flex-1" />

                <span
                    role="button"
                    tabIndex={0}
                    className={cn(
                        'inline-flex items-center justify-center h-5 w-5 rounded-sm hover:bg-muted/80 transition-colors',
                        loading && 'pointer-events-none opacity-50',
                    )}
                    onClick={(e) => {
                        e.stopPropagation();
                        onRefresh();
                    }}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                            e.stopPropagation();
                            onRefresh();
                        }
                    }}
                    title="Run auditor"
                >
                    <RefreshCw className={cn('h-3 w-3', loading && 'animate-spin')} />
                </span>
            </button>

            {/* Checks list */}
            {open && (
                <div className="flex-1 min-h-0 overflow-y-auto border-t">
                    {!result && !loading && (
                        <p className="px-3 py-4 text-sm text-muted-foreground text-center">
                            No audit results yet. Edit files or click refresh to run.
                        </p>
                    )}
                    {loading && !result && (
                        <p className="px-3 py-4 text-sm text-muted-foreground text-center">
                            Running auditor&hellip;
                        </p>
                    )}
                    {result && nothingToShow && (
                        <p className="px-3 py-4 text-sm text-muted-foreground text-center">
                            No issues found.
                        </p>
                    )}
                    {result?.checks
                        .filter((c) => c.outcome === 'failed')
                        .map((check) => (
                            <AuditorCheckRow key={check.nodeId} check={check} />
                        ))}

                    {suggestionCount > 0 && (
                        <>
                            <div className="flex items-center gap-2 px-3 pt-3 pb-1 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                                Suggestions
                                <span className="font-normal normal-case tracking-normal">
                                    advisory &middot; do not block delivery
                                </span>
                            </div>
                            {suggestions.map((s) => (
                                <AuditorSuggestionRow key={s.code} suggestion={s} />
                            ))}
                        </>
                    )}
                </div>
            )}
        </div>
    );
};
