import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AuditorSuggestionRow } from '@/views/molecules/AuditorSuggestionRow';
import type { AuditorSuggestion } from '@/models/types';

const makeSuggestion = (overrides: Partial<AuditorSuggestion> = {}): AuditorSuggestion => ({
    code: 'zero-design-lead',
    title: 'No design lead',
    detail: 'Phases P1 and P2 start build with a design lead of 0 days.',
    category: 'scheduling',
    severity: 'warning',
    ...overrides,
});

describe('AuditorSuggestionRow', () => {
    it('renders the suggestion title and detail', () => {
        render(<AuditorSuggestionRow suggestion={makeSuggestion()} />);
        expect(screen.getByText('No design lead')).toBeInTheDocument();
        expect(screen.getByText(/start build with a design lead of 0 days/)).toBeInTheDocument();
    });

    it('renders the category', () => {
        render(<AuditorSuggestionRow suggestion={makeSuggestion()} />);
        expect(screen.getByText('scheduling')).toBeInTheDocument();
    });
});
