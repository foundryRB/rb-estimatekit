import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

vi.mock('@/viewmodels/useThemeViewModel', () => ({
    useTheme: () => ({ theme: 'light', toggleTheme: vi.fn() }),
}));

vi.mock('@/views/molecules/ConnectAgentMenu', () => ({
    ConnectAgentMenu: () => null,
}));

import { Toolbar } from '@/views/organisms/Toolbar';
import type { Pipeline } from '@/models/types';

function renderToolbar(
    overrides: Partial<React.ComponentProps<typeof Toolbar>> = {},
    pipelines: Pipeline[] = ['roadmap', 'excel', 'slides'],
) {
    const onSelectPhase = vi.fn();
    const onGenerate = vi.fn();
    render(
        <Toolbar
            projectName="Demo"
            slug="demo"
            dirtyCount={0}
            saving={false}
            onSaveAll={vi.fn()}
            selectedPipelines={pipelines}
            onTogglePipeline={vi.fn()}
            genStatus="idle"
            onGenerate={onGenerate}
            outputs={[]}
            onExport={vi.fn()}
            exporting={false}
            onImport={vi.fn()}
            importing={false}
            {...overrides}
            onSelectPhase={onSelectPhase}
        />,
    );
    return { onSelectPhase, onGenerate };
}

describe('Toolbar phase picker (#24)', () => {
    it('offers the phases the deck can sell when the project defines several', () => {
        const { onSelectPhase } = renderToolbar({ phases: ['P1', 'P2'], selectedPhase: 'P2' });
        const picker = screen.getByLabelText('Phase the slide deck sells') as HTMLSelectElement;
        expect(picker.value).toBe('P2');
        expect(Array.from(picker.options).map((o) => o.value)).toEqual(['P1', 'P2']);
        fireEvent.change(picker, { target: { value: 'P1' } });
        expect(onSelectPhase).toHaveBeenCalledWith('P1');
    });

    it('shows no picker on a single-phase project', () => {
        renderToolbar({ phases: ['P1'], selectedPhase: 'P1' });
        expect(screen.queryByLabelText('Phase the slide deck sells')).toBeNull();
    });

    it('disables the picker when the slides pipeline is not selected', () => {
        renderToolbar({ phases: ['P1', 'P2'], selectedPhase: 'P2' }, ['roadmap', 'excel']);
        const picker = screen.getByLabelText('Phase the slide deck sells') as HTMLSelectElement;
        expect(picker.disabled).toBe(true);
    });

    it('refuses to generate slides on a multi-phase project until a phase is picked', () => {
        renderToolbar({ phases: ['P1', 'P2'], selectedPhase: null });
        const generate = screen.getByRole('button', { name: /generate/i }) as HTMLButtonElement;
        expect(generate.disabled).toBe(true);
    });
});
