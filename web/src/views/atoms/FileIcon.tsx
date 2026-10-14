import React from 'react';
import { FileText, FileSpreadsheet, FileCode, File } from 'lucide-react';
import type { FileKind } from '@/models/types';

interface FileIconProps {
    kind: FileKind;
    className?: string;
}

const ICON_MAP: Record<FileKind, React.ElementType> = {
    yaml: FileCode,
    tsv: FileSpreadsheet,
    puml: FileText,
    text: File,
};

export const FileIcon: React.FC<FileIconProps> = ({ kind, className = 'h-4 w-4' }) => {
    const Icon = ICON_MAP[kind];
    return <Icon className={className} />;
};
