import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';

vi.mock('@/api/clients/diagramClient', () => ({ renderDiagram: vi.fn() }));

import { renderDiagram } from '@/api/clients/diagramClient';
import { PlantUmlViewer } from '@/views/organisms/PlantUmlViewer';

const SVG = '<svg xmlns="http://www.w3.org/2000/svg"><rect width="10" height="10" /></svg>';

const noop = () => {};

// jsdom implements neither of these; the viewer turns SVG into a blob URL.
beforeEach(() => {
    URL.createObjectURL = vi.fn(() => 'blob:diagram');
    URL.revokeObjectURL = vi.fn();
    vi.mocked(renderDiagram).mockReset();
    vi.mocked(renderDiagram).mockResolvedValue({ name: 'P1-overview.puml', svg: SVG });
});

describe('PlantUmlViewer', () => {
    it('renders the saved diagram from the in-pod endpoint, not a plantuml.com URL', async () => {
        render(
            <PlantUmlViewer
                slug="acme"
                name="P1-overview.puml"
                content="@startuml\nA -> B\n@enduml"
                savedContent="@startuml\nA -> B\n@enduml"
                onChange={noop}
            />,
        );

        const img = await screen.findByAltText('PlantUML diagram');
        expect(img).toHaveAttribute('src', 'blob:diagram');
        expect(renderDiagram).toHaveBeenCalledWith('acme', 'P1-overview.puml');
    });

    it('surfaces the backend failure detail in the error state', async () => {
        vi.mocked(renderDiagram).mockRejectedValue(new Error('unknown diagram: P9.puml'));
        render(
            <PlantUmlViewer
                slug="acme"
                name="P9.puml"
                content="@startuml\nbroken"
                savedContent="@startuml\nbroken"
                onChange={noop}
            />,
        );

        expect(await screen.findByText('unknown diagram: P9.puml')).toBeInTheDocument();
    });

    it('shows the saved diagram plus an unsaved-changes banner while the buffer is dirty', async () => {
        render(
            <PlantUmlViewer
                slug="acme"
                name="P1-overview.puml"
                content="@startuml\nA -> B\nedited"
                savedContent="@startuml\nA -> B"
                onChange={noop}
            />,
        );

        await screen.findByAltText('PlantUML diagram');
        expect(screen.getByText(/last saved diagram/i)).toBeInTheDocument();
    });

    it('prompts to save before rendering a never-saved diagram', () => {
        render(
            <PlantUmlViewer
                slug="acme"
                name="new.puml"
                content="@startuml\nfresh"
                savedContent=""
                onChange={noop}
            />,
        );

        expect(screen.getByText(/save the diagram to render/i)).toBeInTheDocument();
        expect(renderDiagram).not.toHaveBeenCalled();
    });
});
