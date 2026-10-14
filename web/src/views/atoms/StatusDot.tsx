import React from 'react';
import { cn } from '@/utils';
import { cva, type VariantProps } from 'class-variance-authority';

const dotVariants = cva('inline-block h-2 w-2 rounded-full', {
    variants: {
        status: {
            success: 'bg-green-500',
            warning: 'bg-yellow-500',
            error: 'bg-red-500',
            info: 'bg-blue-500',
            muted: 'bg-gray-400',
        },
    },
    defaultVariants: { status: 'muted' },
});

interface StatusDotProps extends VariantProps<typeof dotVariants> {
    className?: string;
}

export const StatusDot: React.FC<StatusDotProps> = ({ status, className }) => (
    <span className={cn(dotVariants({ status }), className)} />
);
