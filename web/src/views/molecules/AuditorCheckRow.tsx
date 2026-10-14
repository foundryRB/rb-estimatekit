import React from 'react';
import { cn } from '@/utils';
import { AlertCircle, AlertTriangle, CheckCircle2 } from 'lucide-react';
import type { AuditorCheck, CheckOutcome } from '@/models/types';

interface AuditorCheckRowProps {
    check: AuditorCheck;
}

const OUTCOME_META: Record<CheckOutcome, { icon: React.ElementType; color: string }> = {
    failed: { icon: AlertCircle, color: 'text-red-600' },
    skipped: { icon: AlertTriangle, color: 'text-yellow-600' },
    passed: { icon: CheckCircle2, color: 'text-green-600' },
};

export const AuditorCheckRow: React.FC<AuditorCheckRowProps> = ({ check }) => {
    const meta = OUTCOME_META[check.outcome];
    const Icon = meta.icon;

    return (
        <div className="flex items-start gap-2 px-3 py-1.5 text-sm hover:bg-muted/50">
            <Icon className={cn('h-4 w-4 mt-0.5 flex-shrink-0', meta.color)} />
            <div className="flex-1 min-w-0">
                <span className="text-foreground">{check.message}</span>
                <span className="ml-2 text-xs text-muted-foreground">{check.category}</span>
            </div>
            <span className="text-xs text-muted-foreground flex-shrink-0">{check.name}</span>
        </div>
    );
};
