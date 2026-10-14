import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

vi.mock('@/api/clients/projectClient', () => ({
    getProjectSummary: vi.fn(),
    generateProject: vi.fn(),
    listOutputs: vi.fn(),
}));

vi.mock('@/api/clients/fileClient', () => ({
    listFiles: vi.fn(),
    readFile: vi.fn(),
    saveFile: vi.fn(),
    deleteFile: vi.fn(),
    exportProject: vi.fn(),
    importProject: vi.fn(),
}));

vi.mock('@/api/clients/guideClient', () => ({
    fetchGuide: vi.fn(),
}));

vi.mock('@/api/clients/auditorClient', () => ({
    runAudit: vi.fn(),
}));

vi.mock('@/viewmodels/useThemeViewModel', () => ({
    useTheme: () => ({ theme: 'light', toggleTheme: vi.fn() }),
}));

import { getProjectSummary, listOutputs } from '@/api/clients/projectClient';
import { listFiles, readFile } from '@/api/clients/fileClient';
import { fetchGuide } from '@/api/clients/guideClient';
import { WorkspacePage } from '@/views/pages/WorkspacePage';

function renderWorkspace() {
    return render(
        <MemoryRouter initialEntries={['/projects/demo-proj']}>
            <Routes>
                <Route path="/projects/:slug" element={<WorkspacePage />} />
            </Routes>
        </MemoryRouter>,
    );
}

describe('WorkspacePage Guide round trip (#4)', () => {
    beforeEach(() => {
        vi.mocked(getProjectSummary).mockResolvedValue({
            name: 'Demo Project',
            client: 'Acme',
            description: '',
            phaseCount: 0,
            phases: [],
            requirementCount: 0,
            assumptionCount: 0,
            archived: false,
        });
        vi.mocked(listOutputs).mockResolvedValue([]);
        vi.mocked(listFiles).mockResolvedValue([
            { path: 'plan.yaml', name: 'plan.yaml', kind: 'yaml', directory: '.' },
        ]);
        vi.mocked(readFile).mockResolvedValue({
            path: 'plan.yaml',
            content: 'title: hello',
            kind: 'yaml',
        });
        vi.mocked(fetchGuide).mockResolvedValue({
            title: 'Getting Started',
            intro: 'Welcome',
            stages: [
                {
                    id: 'stage-1',
                    name: 'Stage One',
                    description: 'First stage description',
                    files: [],
                    tips: [],
                },
                {
                    id: 'stage-2',
                    name: 'Stage Two',
                    description: 'Second stage description',
                    files: ['plan.yaml'],
                    tips: [],
                },
            ],
        });
    });

    it('keeps a stage expanded and the scroll offset after a Guide → file → Guide round trip', async () => {
        const { container } = renderWorkspace();

        await screen.findByText('Getting Started');

        // Stage Two starts collapsed (only index 0 auto-expands) — expand it.
        fireEvent.click(screen.getByText('Stage Two'));
        expect(await screen.findByText('Second stage description')).toBeInTheDocument();

        // Simulate the user having scrolled the guide down.
        const scrollContainer = container.querySelector('.overflow-y-auto') as HTMLElement;
        expect(scrollContainer).toBeTruthy();
        scrollContainer.scrollTop = 240;

        // Open a file from the expanded stage — this switches the active tab away from Guide.
        fireEvent.click(within(scrollContainer).getByText('plan.yaml'));
        await waitFor(() => {
            expect(readFile).toHaveBeenCalledWith('demo-proj', 'plan.yaml');
        });
        expect(await screen.findByDisplayValue('title: hello')).toBeInTheDocument();

        // Return to the Guide tab (both the toolbar button and the tab-bar
        // pseudo-tab render the label "Guide" and call the same handler).
        fireEvent.click(screen.getAllByText('Guide')[0]!);

        // The stage is still expanded and the scroll offset survived the round trip.
        expect(await screen.findByText('Second stage description')).toBeInTheDocument();
        expect(scrollContainer.scrollTop).toBe(240);
    });
});
