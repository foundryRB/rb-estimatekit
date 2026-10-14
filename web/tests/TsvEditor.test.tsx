import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TsvEditor } from '@/views/organisms/TsvEditor';

describe('TsvEditor', () => {
    const sampleTsv = 'Name\tEffort\nLogin\t5\nDashboard\t8\n';

    it('renders column headers', () => {
        render(<TsvEditor content={sampleTsv} onChange={() => {}} />);
        expect(screen.getByText('Name')).toBeInTheDocument();
        expect(screen.getByText('Effort')).toBeInTheDocument();
    });

    it('renders row data as inputs', () => {
        render(<TsvEditor content={sampleTsv} onChange={() => {}} />);
        const inputs = screen.getAllByRole('textbox');
        // 2 rows × 2 columns = 4 inputs
        expect(inputs).toHaveLength(4);
        expect(inputs[0]).toHaveValue('Login');
        expect(inputs[1]).toHaveValue('5');
    });

    it('shows Add Row button', () => {
        render(<TsvEditor content={sampleTsv} onChange={() => {}} />);
        expect(screen.getByText('Add Row')).toBeInTheDocument();
    });

    it('shows empty state for empty content', () => {
        render(<TsvEditor content="" onChange={() => {}} />);
        expect(screen.getByText(/empty file/i)).toBeInTheDocument();
    });

    it('hides Add Row in readOnly mode', () => {
        render(<TsvEditor content={sampleTsv} onChange={() => {}} readOnly />);
        expect(screen.queryByText('Add Row')).not.toBeInTheDocument();
    });

    it('sizes each column with a fixed-layout colgroup', () => {
        const { container } = render(<TsvEditor content={sampleTsv} onChange={() => {}} />);
        const table = container.querySelector('table')!;
        expect(table.style.tableLayout).toBe('fixed');
        // row-number col + 2 data cols + delete col = 4 cols, each with a width
        const cols = [...container.querySelectorAll('colgroup col')];
        expect(cols).toHaveLength(4);
        expect(cols.every((c) => (c as HTMLElement).style.width !== '')).toBe(true);
    });

    it('renders a resize handle per data column', () => {
        const { container } = render(<TsvEditor content={sampleTsv} onChange={() => {}} />);
        const handles = container.querySelectorAll('thead th [role="separator"]');
        expect(handles).toHaveLength(2); // Name, Effort
    });

    it('auto-fits a column to its widest value on double-click', () => {
        // A long value in the Name column should widen it past its capped initial size.
        const longName = 'x'.repeat(90);
        const wide = `Name\tEffort\n${longName}\t5\n`;
        const { container } = render(<TsvEditor content={wide} onChange={() => {}} />);
        const nameCol = container.querySelector('colgroup col:nth-child(2)') as HTMLElement;
        const before = parseFloat(nameCol.style.width);
        const handle = container.querySelectorAll('thead th [role="separator"]')[0]!;
        fireEvent.doubleClick(handle);
        const after = parseFloat(nameCol.style.width);
        expect(after).toBeGreaterThan(before);
    });
});
