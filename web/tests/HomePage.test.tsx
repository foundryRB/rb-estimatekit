import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

vi.mock('@/api/clients/projectClient', () => ({
    checkHealth: vi.fn(),
    discoverProjects: vi.fn(),
    scaffoldProject: vi.fn(),
    deleteProject: vi.fn(),
    renameProject: vi.fn(),
    archiveProject: vi.fn(),
    unarchiveProject: vi.fn(),
}));

vi.mock('@/viewmodels/useThemeViewModel', () => ({
    useTheme: () => ({ theme: 'light', toggleTheme: vi.fn() }),
}));

import {
    checkHealth,
    discoverProjects,
    renameProject,
    archiveProject,
    unarchiveProject,
} from '@/api/clients/projectClient';
import { HomePage } from '@/views/pages/HomePage';

function renderHome() {
    return render(
        <MemoryRouter>
            <HomePage />
        </MemoryRouter>,
    );
}

describe('HomePage project lifecycle', () => {
    beforeEach(() => {
        vi.mocked(checkHealth).mockResolvedValue({ status: 'ok', service: 'estimatekit-engine' });
        vi.mocked(discoverProjects).mockReset();
        vi.mocked(discoverProjects).mockResolvedValue({
            projects: ['live-proj'],
            archived: ['parked-proj'],
        });
        vi.mocked(renameProject).mockReset();
        vi.mocked(archiveProject).mockReset();
        vi.mocked(unarchiveProject).mockReset();
    });

    it('lists active projects in the gallery and archived ones separately', async () => {
        renderHome();
        expect(await screen.findAllByText('live-proj')).not.toHaveLength(0);
        expect(screen.getByText('Archived')).toBeInTheDocument();
        expect(screen.getByText('parked-proj')).toBeInTheDocument();
    });

    it('renames a project through the inline form', async () => {
        vi.mocked(renameProject).mockResolvedValue('renamed-proj');
        renderHome();
        await screen.findAllByText('live-proj');

        fireEvent.click(screen.getByLabelText('Rename live-proj'));
        fireEvent.change(screen.getByLabelText('New slug'), {
            target: { value: 'renamed-proj' },
        });
        fireEvent.change(screen.getByLabelText('New display name'), {
            target: { value: 'Renamed Project' },
        });
        fireEvent.click(screen.getByRole('button', { name: 'Rename' }));

        await waitFor(() => {
            expect(renameProject).toHaveBeenCalledWith('live-proj', {
                newSlug: 'renamed-proj',
                newName: 'Renamed Project',
            });
        });
        expect(await screen.findAllByText('renamed-proj')).not.toHaveLength(0);
    });

    it('archives a project into the archived section', async () => {
        vi.mocked(archiveProject).mockResolvedValue(undefined);
        renderHome();
        await screen.findAllByText('live-proj');

        fireEvent.click(screen.getByLabelText('Archive live-proj'));

        await waitFor(() => {
            expect(archiveProject).toHaveBeenCalledWith('live-proj');
        });
        expect(screen.getByLabelText('Unarchive live-proj')).toBeInTheDocument();
    });

    it('unarchives a parked project back into the gallery', async () => {
        vi.mocked(unarchiveProject).mockResolvedValue(undefined);
        renderHome();
        await screen.findAllByText('live-proj');

        fireEvent.click(screen.getByLabelText('Unarchive parked-proj'));

        await waitFor(() => {
            expect(unarchiveProject).toHaveBeenCalledWith('parked-proj');
        });
        expect(screen.queryByText('Archived')).not.toBeInTheDocument();
        expect(screen.getAllByText('parked-proj')).not.toHaveLength(0);
    });
});
