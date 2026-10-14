import React from 'react';
import { Card, CardContent } from '@/components/ui/card';

interface KpiCardProps {
    title: string;
    value: number | string;
    icon?: React.ReactNode;
}

export const KpiCard: React.FC<KpiCardProps> = ({ title, value, icon }) => (
    <Card>
        <CardContent className="p-4">
            <div className="flex items-center justify-between">
                <div>
                    <p className="text-sm text-muted-foreground">{title}</p>
                    <p className="text-2xl font-bold">{value}</p>
                </div>
                {icon && <div className="text-muted-foreground">{icon}</div>}
            </div>
        </CardContent>
    </Card>
);
