/**
 * Diagram API client — render one architecture diagram to SVG in-pod.
 *
 * The backend renders the saved `.puml` source with a local PlantUML process
 * and answers inline SVG, so confidential diagrams never leave the cluster.
 */

import { get } from '@/api/client';
import { ENDPOINTS } from '@/api/endpoints';
import type { components } from '@/api/generated/types';
import { mapDiagramSvg } from '@/api/mappers/projectMapper';
import type { DiagramSvg } from '@/models/types';

/**
 * Render the named architecture diagram to SVG.
 *
 * `name` is the bare `.puml` filename (e.g. `P1-overview.puml`); the backend
 * resolves it inside the project's architecture folder. Render failures surface
 * as an `ApiError` whose `detail` carries the reason.
 */
export async function renderDiagram(slug: string, name: string): Promise<DiagramSvg> {
    const dto = await get<components['schemas']['DiagramSvgResponse']>(
        ENDPOINTS.diagram(slug, name),
    );
    return mapDiagramSvg(dto);
}
