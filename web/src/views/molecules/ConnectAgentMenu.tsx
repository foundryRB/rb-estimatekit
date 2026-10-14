import React, { useEffect, useRef, useState } from 'react';
import { cn } from '@/utils';
import { get } from '@/api/client';
import { Button } from '@/components/ui/button';
import { Plug } from 'lucide-react';

interface ConnectAgentMenuProps {
    /** Open the panel upward (for bottom-bar placements). */
    dropUp?: boolean;
}

/**
 * Entry point for the MCP door: the copyable connect one-liner, one click away.
 *
 * The engine serves MCP at /mcp on this same origin (ADR-002); an agent
 * connected once gets every estimation tool (scaffold, edit data, audit,
 * generate). The one-liner carries the site's HTTP Basic credential, fetched
 * from /api/agent-credential when the panel opens (lazily, never on a bare page
 * load). That endpoint sits behind the same gate as this SPA (oauth2-proxy under
 * scope=mcp, Basic under scope=all), so an already-authenticated human gets a
 * paste-ready command; if it is unavailable the one-liner falls back to a
 * placeholder.
 */
export const ConnectAgentMenu: React.FC<ConnectAgentMenuProps> = ({ dropUp = false }) => {
    const [open, setOpen] = useState(false);
    const [copied, setCopied] = useState(false);
    const [credential, setCredential] = useState<string | null>(null);
    const [credFailed, setCredFailed] = useState(false);
    const rootRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!open || credential !== null || credFailed) return;
        let cancelled = false;
        get<{ credential: string }>('/agent-credential')
            .then((r) => {
                if (!cancelled) setCredential(r.credential);
            })
            .catch(() => {
                if (!cancelled) setCredFailed(true);
            });
        return () => {
            cancelled = true;
        };
    }, [open, credential, credFailed]);

    const basic = credential ?? '<credentials>';
    const oneLiner = `claude mcp add --scope user --transport http estimatekit ${window.location.origin}/mcp --header "Authorization: Basic ${basic}"`;

    useEffect(() => {
        if (!open) return;
        const onClickOutside = (e: MouseEvent) => {
            if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
                setOpen(false);
            }
        };
        document.addEventListener('mousedown', onClickOutside);
        return () => document.removeEventListener('mousedown', onClickOutside);
    }, [open]);

    const copy = () => {
        void navigator.clipboard.writeText(oneLiner).then(() => {
            setCopied(true);
            window.setTimeout(() => setCopied(false), 2000);
        });
    };

    return (
        <div className="relative" ref={rootRef}>
            <Button
                variant="ghost"
                size="sm"
                className="gap-1.5 text-xs"
                onClick={() => setOpen((v) => !v)}
                title="Connect an MCP agent to this instance"
            >
                <Plug className="h-3.5 w-3.5" />
                Connect agent
            </Button>
            {open && (
                <div
                    className={cn(
                        'absolute right-0 z-50 w-96 rounded-lg border bg-popover p-3 shadow-lg',
                        dropUp ? 'bottom-full mb-1' : 'top-full mt-1',
                    )}
                >
                    <p className="mb-2 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/70">
                        MCP
                    </p>
                    <div className="flex flex-col gap-2">
                        <p className="text-xs text-muted-foreground">
                            Connect your agent once; it gets every estimation tool (scaffold a
                            project, edit its data, run the audit, generate the artifacts):
                        </p>
                        <pre className="overflow-x-auto whitespace-pre rounded-md border bg-background/80 p-2 font-mono text-[10px] leading-relaxed text-muted-foreground">
                            {oneLiner}
                        </pre>
                        <Button
                            variant="outline"
                            className="h-6 w-full px-2 text-xs"
                            onClick={copy}
                        >
                            {copied ? 'Copied' : 'Copy connect command'}
                        </Button>
                        <p className="text-[10px] text-muted-foreground/70">
                            {credFailed
                                ? "Credential unavailable right now; replace <credentials> with this site's base64 HTTP Basic pair (user:password)."
                                : 'The command carries this site’s HTTP Basic credential, already filled in. The estimate-project prompt then carries the full estimation runbook.'}
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
};
