/**
 * Auditor API client — run data checks on a project.
 */

import { post } from '@/api/client';
import { ENDPOINTS } from '@/api/endpoints';
import type { components } from '@/api/generated/types';
import { mapAuditReport } from '@/api/mappers/projectMapper';
import type { AuditorResult } from '@/models/types';

export async function runAudit(slug: string): Promise<AuditorResult> {
    const dto = await post<components['schemas']['AuditReportResponse']>(ENDPOINTS.audit(slug));
    return mapAuditReport(dto);
}
