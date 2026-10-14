import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

vi.mock('@/api/client', () => ({ get: vi.fn() }));

import { get } from '@/api/client';
import { ConnectAgentMenu } from '@/views/molecules/ConnectAgentMenu';

// base64('demo:pass')
const CRED = 'ZGVtbzpwYXNz';

describe('ConnectAgentMenu', () => {
    beforeEach(() => {
        vi.mocked(get).mockReset();
        vi.mocked(get).mockResolvedValue({ credential: CRED });
    });

    it('renders the connect entry point', () => {
        render(<ConnectAgentMenu />);
        expect(screen.getByText('Connect agent')).toBeInTheDocument();
    });

    it('fetches and fills the real credential into the one-liner on open', async () => {
        render(<ConnectAgentMenu />);
        fireEvent.click(screen.getByText('Connect agent'));

        const line = await screen.findByText(
            /claude mcp add --scope user --transport http estimatekit/,
        );
        expect(line.textContent).toContain(`${window.location.origin}/mcp`);

        await waitFor(() => {
            expect(screen.getByText(/claude mcp add/).textContent).toContain(
                `Authorization: Basic ${CRED}`,
            );
        });
        expect(screen.getByText(/claude mcp add/).textContent).not.toContain('<credentials>');
        expect(get).toHaveBeenCalledWith('/agent-credential');
    });

    it('falls back to the placeholder when the credential is unavailable', async () => {
        vi.mocked(get).mockRejectedValue(new Error('503'));
        render(<ConnectAgentMenu />);
        fireEvent.click(screen.getByText('Connect agent'));

        await waitFor(() => {
            expect(screen.getByText(/claude mcp add/).textContent).toContain('<credentials>');
        });
    });

    it('offers a copy button once open', () => {
        render(<ConnectAgentMenu />);
        fireEvent.click(screen.getByText('Connect agent'));
        expect(screen.getByText('Copy connect command')).toBeInTheDocument();
    });
});
