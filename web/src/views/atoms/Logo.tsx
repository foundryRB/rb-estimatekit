import React from 'react';
import { cn } from '@/utils';
import { Lockup } from '@/components/Lockup';

interface LogoProps {
    collapsed?: boolean;
}

export const Logo: React.FC<LogoProps> = ({ collapsed = false }) => (
    <div className="flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-brand-primary text-white font-bold text-sm">
            EK
        </div>
        <span className="dark:hidden"><Lockup mode="light" height={32} /></span>
        <span className="hidden dark:block"><Lockup mode="dark" height={32} /></span>
        {!collapsed && (
            <span className={cn('text-lg font-semibold tracking-tight')}>EstimateKit</span>
        )}
    </div>
);
