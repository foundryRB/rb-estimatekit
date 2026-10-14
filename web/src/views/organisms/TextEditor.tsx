import React from 'react';

interface TextEditorProps {
    content: string;
    onChange: (content: string) => void;
    readOnly?: boolean;
    language?: string;
}

/**
 * Plain-text editor for YAML, PlantUML, and other non-TSV files.
 * Uses a styled textarea. A future upgrade could swap in Monaco/CodeMirror.
 */
export const TextEditor: React.FC<TextEditorProps> = ({ content, onChange, readOnly = false }) => (
    <div className="h-full flex flex-col">
        <textarea
            value={content}
            onChange={(e) => onChange(e.target.value)}
            readOnly={readOnly}
            spellCheck={false}
            className="flex-1 w-full resize-none bg-background p-4 font-mono text-sm leading-relaxed outline-none focus:ring-0 border-0"
            style={{ tabSize: 2 }}
        />
    </div>
);
