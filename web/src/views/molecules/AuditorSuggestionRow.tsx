import React from 'react';
import { Lightbulb } from 'lucide-react';
import type { AuditorSuggestion } from '@/models/types';

interface AuditorSuggestionRowProps {
    suggestion: AuditorSuggestion;
}

/**
 * One advisory delivery-risk suggestion.
 *
 * Styled distinctly from a failing check (amber lightbulb, not a red alert):
 * a suggestion is advice, not an error, and never blocks delivery.
 */
export const AuditorSuggestionRow: React.FC<AuditorSuggestionRowProps> = ({ suggestion }) => {
    return (
        <div className="flex items-start gap-2 px-3 py-1.5 text-sm hover:bg-muted/50">
            <Lightbulb className="h-4 w-4 mt-0.5 flex-shrink-0 text-amber-500" />
            <div className="flex-1 min-w-0">
                <span className="text-foreground font-medium">{suggestion.title}</span>
                <span className="ml-2 text-muted-foreground">{suggestion.detail}</span>
            </div>
            <span className="text-xs text-muted-foreground flex-shrink-0">
                {suggestion.category}
            </span>
        </div>
    );
};
