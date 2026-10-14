import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { FileIcon } from '@/views/atoms/FileIcon';

describe('FileIcon', () => {
    it('renders without crashing', () => {
        const { container } = render(<FileIcon kind="tsv" />);
        expect(container.querySelector('svg')).toBeTruthy();
    });

    it('accepts className prop', () => {
        const { container } = render(<FileIcon kind="yaml" className="text-red-500" />);
        expect(container.querySelector('svg')?.classList.contains('text-red-500')).toBe(true);
    });
});
