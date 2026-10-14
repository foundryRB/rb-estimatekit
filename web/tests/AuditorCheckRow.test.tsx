import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AuditorCheckRow } from '@/views/molecules/AuditorCheckRow';
import type { AuditorCheck } from '@/models/types';

const makeCheck = (overrides: Partial<AuditorCheck> = {}): AuditorCheck => ({
    nodeId: 'checks/brd/test_check_001',
    name: 'test_check_001',
    category: 'brd',
    outcome: 'failed',
    message: 'Effort seems too low',
    ...overrides,
});

describe('AuditorCheckRow', () => {
    it('renders check message', () => {
        render(<AuditorCheckRow check={makeCheck()} />);
        expect(screen.getByText('Effort seems too low')).toBeInTheDocument();
    });

    it('renders category', () => {
        render(<AuditorCheckRow check={makeCheck()} />);
        expect(screen.getByText('brd')).toBeInTheDocument();
    });

    it('renders check name', () => {
        render(<AuditorCheckRow check={makeCheck()} />);
        expect(screen.getByText('test_check_001')).toBeInTheDocument();
    });
});
