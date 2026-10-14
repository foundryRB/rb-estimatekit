/**
 * File API client — list, read, write project files, export/import.
 */

import { get, put, del, download, upload } from '@/api/client';
import { ENDPOINTS } from '@/api/endpoints';
import type { components } from '@/api/generated/types';
import { mapProjectFile, mapFileContent } from '@/api/mappers/projectMapper';
import type { ProjectFile, FileContent } from '@/models/types';

export async function listFiles(slug: string): Promise<ProjectFile[]> {
    const dto = await get<components['schemas']['ListFilesResponse']>(ENDPOINTS.projectFiles(slug));
    return dto.files.map(mapProjectFile);
}

export async function readFile(slug: string, path: string): Promise<FileContent> {
    const dto = await get<components['schemas']['FileContentResponse']>(
        ENDPOINTS.fileContent(slug, path),
    );
    return mapFileContent(dto);
}

export async function saveFile(slug: string, path: string, content: string): Promise<void> {
    const body: components['schemas']['SaveFileRequest'] = { content };
    await put<void>(ENDPOINTS.fileContent(slug, path), body);
}

export async function deleteFile(slug: string, path: string): Promise<void> {
    await del<void>(ENDPOINTS.fileContent(slug, path));
}

/** Download all project data files as a ZIP. */
export async function exportProject(slug: string): Promise<Blob> {
    return download(ENDPOINTS.exportZip(slug));
}

/** Upload a ZIP of data files to overwrite project contents. */
export async function importProject(slug: string, file: File): Promise<void> {
    return upload(ENDPOINTS.importZip(slug), file);
}
