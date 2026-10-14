/**
 * Project API client — discovery, scaffold, summary, generation, outputs.
 */

import { get, post, del } from '@/api/client';
import { ENDPOINTS } from '@/api/endpoints';
import type { components } from '@/api/generated/types';
import { mapProjectSummary, mapGenerationResult, mapOutputFile } from '@/api/mappers/projectMapper';
import type { ProjectSummary, ProjectListing, GenerationResult, OutputFile } from '@/models/types';

export async function checkHealth(): Promise<Record<string, unknown>> {
    return get<Record<string, unknown>>(ENDPOINTS.health);
}

export async function discoverProjects(): Promise<ProjectListing> {
    const dto = await get<components['schemas']['DiscoverProjectsResponse']>(ENDPOINTS.projects);
    return { projects: dto.projects, archived: dto.archived };
}

export async function getProjectSummary(slug: string): Promise<ProjectSummary> {
    const dto = await get<components['schemas']['ProjectSummaryResponse']>(
        ENDPOINTS.projectSummary(slug),
    );
    return mapProjectSummary(dto);
}

export async function scaffoldProject(slug: string, force = false): Promise<string> {
    const body = { slug, force };
    const dto = await post<components['schemas']['ScaffoldProjectResponse']>(
        ENDPOINTS.scaffold,
        body,
    );
    return dto.path;
}

export async function deleteProject(slug: string): Promise<void> {
    await del<components['schemas']['DeleteProjectResponse']>(ENDPOINTS.deleteProject(slug));
}

export interface RenameOptions {
    newSlug?: string;
    newName?: string;
}

/** Rename a project's display name and/or slug. Returns the slug after the rename. */
export async function renameProject(slug: string, options: RenameOptions): Promise<string> {
    const body: components['schemas']['RenameRequest'] = {
        new_slug: options.newSlug ?? null,
        new_name: options.newName ?? null,
    };
    const dto = await post<components['schemas']['RenameProjectResponse']>(
        ENDPOINTS.renameProject(slug),
        body,
    );
    return dto.new_slug;
}

export async function archiveProject(slug: string): Promise<void> {
    await post<components['schemas']['ArchiveProjectResponse']>(ENDPOINTS.archiveProject(slug), {});
}

export async function unarchiveProject(slug: string): Promise<void> {
    await post<components['schemas']['ArchiveProjectResponse']>(
        ENDPOINTS.unarchiveProject(slug),
        {},
    );
}

/**
 * Run generation pipelines. `phase` names the phase the slide deck sells; a
 * multi-phase project refuses the slides pipeline without it.
 */
export async function generateProject(
    slug: string,
    pipelines?: string[],
    phase?: string,
): Promise<GenerationResult> {
    const body: components['schemas']['GenerateRequest'] = {
        ...(pipelines ? { pipelines } : {}),
        ...(phase ? { phase } : {}),
    };
    const dto = await post<components['schemas']['GenerateResponse']>(
        ENDPOINTS.generate(slug),
        body,
    );
    return mapGenerationResult(dto);
}

export async function listOutputs(slug: string): Promise<OutputFile[]> {
    const dto = await get<components['schemas']['ListOutputsResponse']>(ENDPOINTS.outputs(slug));
    return dto.outputs.map(mapOutputFile);
}
