import { describe, it, expect } from 'vitest';
import { parseTsv, serializeTsv } from '@/viewmodels/useWorkspaceViewModel';

describe('parseTsv', () => {
    it('parses headers and rows from TSV text', () => {
        const tsv = 'Name\tEffort\tPhase\nLogin\t5\tP1\nDashboard\t8\tP2\n';
        const { headers, rows } = parseTsv(tsv);
        expect(headers).toEqual(['Name', 'Effort', 'Phase']);
        expect(rows).toHaveLength(2);
        expect(rows[0]).toEqual(['Login', '5', 'P1']);
        expect(rows[1]).toEqual(['Dashboard', '8', 'P2']);
    });

    it('returns empty arrays for empty input', () => {
        const { headers, rows } = parseTsv('');
        expect(headers).toEqual([]);
        expect(rows).toHaveLength(0);
    });

    it('handles header-only TSV', () => {
        const { headers, rows } = parseTsv('Col1\tCol2\n');
        expect(headers).toEqual(['Col1', 'Col2']);
        expect(rows).toHaveLength(0);
    });

    it('ignores blank lines', () => {
        const tsv = 'A\tB\n1\t2\n\n3\t4\n';
        const { rows } = parseTsv(tsv);
        expect(rows).toHaveLength(2);
    });
});

describe('serializeTsv', () => {
    it('serialises headers and rows back to TSV', () => {
        const result = serializeTsv(
            ['X', 'Y'],
            [
                ['1', '2'],
                ['3', '4'],
            ],
        );
        expect(result).toBe('X\tY\n1\t2\n3\t4\n');
    });

    it('round-trips through parseTsv', () => {
        const original = 'Req\tPriority\nR1\tHigh\nR2\tLow\n';
        const { headers, rows } = parseTsv(original);
        const serialised = serializeTsv(headers, rows);
        expect(serialised).toBe(original);
    });
});
