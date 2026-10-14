/**
 * ViewModel: Home page.
 *
 * Handles project discovery, creating new projects, and opening existing ones.
 */

import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    scaffoldProject,
    checkHealth,
    discoverProjects,
    deleteProject as deleteProjectApi,
    renameProject as renameProjectApi,
    archiveProject as archiveProjectApi,
    unarchiveProject as unarchiveProjectApi,
} from '@/api/clients/projectClient';

export function useHomeViewModel() {
    const navigate = useNavigate();

    /* ── Discovered projects ──────────────────────────────── */
    const [projects, setProjects] = useState<string[]>([]);
    const [archivedProjects, setArchivedProjects] = useState<string[]>([]);
    const [projectsLoading, setProjectsLoading] = useState(true);

    const loadProjects = useCallback(async () => {
        setProjectsLoading(true);
        try {
            const listing = await discoverProjects();
            setProjects(listing.projects);
            setArchivedProjects(listing.archived);
        } catch {
            // Non-critical — the project list just won't show
        } finally {
            setProjectsLoading(false);
        }
    }, []);

    /* ── Open existing ────────────────────────────────────── */
    const [openSlug, setOpenSlug] = useState('');
    const [openError, setOpenError] = useState<string | null>(null);

    const openProject = useCallback(
        (slugOverride?: string) => {
            const slug = (slugOverride ?? openSlug).trim();
            if (!slug) {
                setOpenError('Enter a project slug.');
                return;
            }
            setOpenError(null);
            navigate(`/projects/${encodeURIComponent(slug)}`);
        },
        [openSlug, navigate],
    );

    /* ── Create new ───────────────────────────────────────── */
    const [newSlug, setNewSlug] = useState('');
    const [creating, setCreating] = useState(false);
    const [createError, setCreateError] = useState<string | null>(null);

    const createProject = useCallback(async () => {
        const slug = newSlug.trim();
        if (!slug) {
            setCreateError('Enter a project slug.');
            return;
        }

        setCreating(true);
        setCreateError(null);
        try {
            await scaffoldProject(slug);
            navigate(`/projects/${encodeURIComponent(slug)}`);
        } catch (err) {
            setCreateError(err instanceof Error ? err.message : 'Failed to create project.');
        } finally {
            setCreating(false);
        }
    }, [newSlug, navigate]);

    /* ── Delete existing ──────────────────────────────────── */
    const [deletingSlug, setDeletingSlug] = useState<string | null>(null);
    const [deleteError, setDeleteError] = useState<string | null>(null);

    const deleteProject = useCallback(async (slug: string) => {
        setDeletingSlug(slug);
        setDeleteError(null);
        try {
            await deleteProjectApi(slug);
            // Drop it from the gallery immediately — no full reload needed.
            setProjects((prev) => prev.filter((s) => s !== slug));
        } catch (err) {
            setDeleteError(err instanceof Error ? err.message : `Failed to delete ${slug}.`);
        } finally {
            setDeletingSlug(null);
        }
    }, []);

    /* ── Rename existing ──────────────────────────────────── */
    const [renamingSlug, setRenamingSlug] = useState<string | null>(null);
    const [renameError, setRenameError] = useState<string | null>(null);

    const renameProject = useCallback(
        async (slug: string, newSlug?: string, newName?: string): Promise<boolean> => {
            setRenamingSlug(slug);
            setRenameError(null);
            try {
                const finalSlug = await renameProjectApi(slug, { newSlug, newName });
                setProjects((prev) => prev.map((s) => (s === slug ? finalSlug : s)));
                return true;
            } catch (err) {
                setRenameError(err instanceof Error ? err.message : `Failed to rename ${slug}.`);
                return false;
            } finally {
                setRenamingSlug(null);
            }
        },
        [],
    );

    /* ── Archive / unarchive ──────────────────────────────── */
    const [archivingSlug, setArchivingSlug] = useState<string | null>(null);
    const [archiveError, setArchiveError] = useState<string | null>(null);

    const archiveProject = useCallback(async (slug: string) => {
        setArchivingSlug(slug);
        setArchiveError(null);
        try {
            await archiveProjectApi(slug);
            setProjects((prev) => prev.filter((s) => s !== slug));
            setArchivedProjects((prev) => [...prev, slug].sort());
        } catch (err) {
            setArchiveError(err instanceof Error ? err.message : `Failed to archive ${slug}.`);
        } finally {
            setArchivingSlug(null);
        }
    }, []);

    const unarchiveProject = useCallback(async (slug: string) => {
        setArchivingSlug(slug);
        setArchiveError(null);
        try {
            await unarchiveProjectApi(slug);
            setArchivedProjects((prev) => prev.filter((s) => s !== slug));
            setProjects((prev) => [...prev, slug].sort());
        } catch (err) {
            setArchiveError(err instanceof Error ? err.message : `Failed to unarchive ${slug}.`);
        } finally {
            setArchivingSlug(null);
        }
    }, []);

    /* ── Backend health ───────────────────────────────────── */
    const [healthy, setHealthy] = useState<boolean | null>(null);

    const pingHealth = useCallback(async () => {
        try {
            await checkHealth();
            setHealthy(true);
        } catch {
            setHealthy(false);
        }
    }, []);

    /* ── Auto-load on mount ───────────────────────────────── */
    useEffect(() => {
        void pingHealth();
        void loadProjects();
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    return {
        // Discovered projects
        projects,
        archivedProjects,
        projectsLoading,
        // Open existing
        openSlug,
        setOpenSlug,
        openError,
        openProject,
        // Create new
        newSlug,
        setNewSlug,
        creating,
        createError,
        createProject,
        // Delete existing
        deletingSlug,
        deleteError,
        deleteProject,
        // Rename existing
        renamingSlug,
        renameError,
        renameProject,
        // Archive / unarchive
        archivingSlug,
        archiveError,
        archiveProject,
        unarchiveProject,
        // Health
        healthy,
        pingHealth,
    } as const;
}
