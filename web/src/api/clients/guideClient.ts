/**
 * Guide API client — fetches static getting-started content from the engine.
 */

import { get } from '@/api/client';
import { ENDPOINTS } from '@/api/endpoints';
import type { Guide, GuideStage } from '@/models/types';

/** Raw shape returned by the backend (snake_case YAML keys). */
interface GuideDTO {
    title: string;
    intro: string;
    stages: Array<{
        id: string;
        name: string;
        description: string;
        files: string[];
        tips: string[];
        auditor_category?: string;
        feature_flag?: string;
    }>;
}

function mapStage(dto: GuideDTO['stages'][number]): GuideStage {
    return {
        id: dto.id,
        name: dto.name,
        description: dto.description,
        files: dto.files,
        tips: dto.tips,
        auditorCategory: dto.auditor_category,
        featureFlag: dto.feature_flag,
    };
}

export async function fetchGuide(): Promise<Guide> {
    const dto = await get<GuideDTO>(ENDPOINTS.guide);
    return {
        title: dto.title,
        intro: dto.intro,
        stages: dto.stages.map(mapStage),
    };
}
