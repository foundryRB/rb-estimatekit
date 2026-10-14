import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AuditorPanel } from '@/views/organisms/AuditorPanel';
import type { AuditorResult, AuditorSuggestion } from '@/models/types';

const suggestion = (overrides: Partial<AuditorSuggestion> = {}): AuditorSuggestion => ({
    code: 'zero-design-lead',
    title: 'No design lead',
    detail: 'Phases P1 and P2 start build with a design lead of 0 days.',
    category: 'scheduling',
    severity: 'warning',
    ...overrides,
});

const result = (overrides: Partial<AuditorResult> = {}): AuditorResult => ({
    checks: [],
    suggestions: [],
    passedCount: 40,
    failedCount: 0,
    skippedCount: 0,
    passed: true,
    durationMs: 12,
    ...overrides,
});

const noop = () => {};

describe('AuditorPanel', () => {
    it('renders advisory suggestions even when all hard checks pass', () => {
        render(
            <AuditorPanel
                result={result({ suggestions: [suggestion()] })}
                loading={false}
                open
                onToggle={noop}
                onRefresh={noop}
            />,
        );
        expect(screen.getByText('No design lead')).toBeInTheDocument();
        // "advisory" appears in the header badge and the section subheader.
        expect(screen.getAllByText(/advisory/i).length).toBeGreaterThan(0);
    });

    it('does not show "All clear" while suggestions are present', () => {
        render(
            <AuditorPanel
                result={result({ suggestions: [suggestion()] })}
                loading={false}
                open
                onToggle={noop}
                onRefresh={noop}
            />,
        );
        expect(screen.queryByText(/all clear/i)).not.toBeInTheDocument();
    });

    it('shows "All clear" when there are no failures and no suggestions', () => {
        render(
            <AuditorPanel
                result={result()}
                loading={false}
                open
                onToggle={noop}
                onRefresh={noop}
            />,
        );
        expect(screen.getByText(/all clear/i)).toBeInTheDocument();
    });
});
