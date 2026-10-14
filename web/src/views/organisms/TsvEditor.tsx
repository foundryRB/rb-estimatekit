import React, { useMemo, useCallback, useRef, useState, useLayoutEffect, useEffect } from 'react';
import { parseTsv, serializeTsv } from '@/viewmodels/useWorkspaceViewModel';
import { Button } from '@/components/ui/button';
import { Plus, Trash2 } from 'lucide-react';

interface TsvEditorProps {
    content: string;
    onChange: (content: string) => void;
    readOnly?: boolean;
}

/** Column sizing bounds, in pixels. */
const MIN_COL = 56;
const MAX_DEFAULT = 320; // cap for the auto-computed starting width
const MAX_AUTOFIT = 640; // cap when the user double-clicks to fit
const MAX_DRAG = 1000; // cap while dragging a handle
const CELL_PAD = 26; // input padding + border + handle slack, added to measured text

/** Lazily-resolved 2d context for off-DOM text measurement (`undefined` = not tried). */
let measureCtx: CanvasRenderingContext2D | null | undefined;
function textWidth(text: string, font: string): number {
    if (measureCtx === undefined) {
        try {
            measureCtx = document.createElement('canvas').getContext('2d');
        } catch {
            measureCtx = null; // no canvas (SSR, some test envs) — fall back below
        }
    }
    if (!measureCtx) return text.length * 8;
    measureCtx.font = font;
    return measureCtx.measureText(text).width;
}

const clamp = (n: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, n));

/** Preview popover state for a hovered, clipped cell. */
interface Preview {
    text: string;
    top: number;
    left: number;
    width: number;
}

const PREVIEW_MAX = 460; // widest the hover preview grows before it wraps

/**
 * Spreadsheet-like TSV editor.
 *
 * Displays TSV data as an editable table. Each cell is an input field.
 * Supports adding and removing rows, drag-to-resize columns (double-click a
 * handle to auto-fit the column to its widest value), and a hover preview
 * that shows the full text of any cell too narrow to display it.
 */
export const TsvEditor: React.FC<TsvEditorProps> = ({ content, onChange, readOnly = false }) => {
    const { headers, rows } = useMemo(() => parseTsv(content), [content]);

    const updateCell = useCallback(
        (rowIdx: number, colIdx: number, value: string) => {
            const newRows = rows.map((r, ri) =>
                ri === rowIdx ? r.map((c, ci) => (ci === colIdx ? value : c)) : [...r],
            );
            onChange(serializeTsv(headers, newRows));
        },
        [headers, rows, onChange],
    );

    const addRow = useCallback(() => {
        const empty = headers.map(() => '');
        const newRows = [...rows, empty];
        onChange(serializeTsv(headers, newRows));
    }, [headers, rows, onChange]);

    const removeRow = useCallback(
        (rowIdx: number) => {
            const newRows = rows.filter((_, i) => i !== rowIdx);
            onChange(serializeTsv(headers, newRows));
        },
        [headers, rows, onChange],
    );

    // --- Column widths -----------------------------------------------------
    const tableRef = useRef<HTMLTableElement>(null);
    const fonts = useRef<{ cell: string; header: string }>({
        cell: '14px sans-serif',
        header: '600 14px sans-serif',
    });
    const [colWidths, setColWidths] = useState<number[]>([]);
    // Signature of the current columns; when it changes we recompute widths.
    const headerSig = headers.join('');

    /** Read the live font off the rendered table so measurement matches paint. */
    const refreshFonts = useCallback(() => {
        const el = tableRef.current;
        if (!el) return;
        const cs = getComputedStyle(el);
        const size = cs.fontSize || '14px';
        const family = cs.fontFamily || 'sans-serif';
        fonts.current = { cell: `${size} ${family}`, header: `600 ${size} ${family}` };
    }, []);

    /** Widest content in a column (header + every cell), clamped to `cap`. */
    const fitWidth = useCallback(
        (colIdx: number, cap: number) => {
            let w = textWidth(headers[colIdx] ?? '', fonts.current.header);
            for (const row of rows) {
                const cell = row[colIdx] ?? '';
                if (cell) w = Math.max(w, textWidth(cell, fonts.current.cell));
            }
            return clamp(Math.ceil(w) + CELL_PAD, MIN_COL, cap);
        },
        [headers, rows],
    );

    // Compute starting widths whenever the column set changes. useLayoutEffect
    // runs before paint, so there is no flash from a placeholder width.
    useLayoutEffect(() => {
        refreshFonts();
        setColWidths(headers.map((_, ci) => fitWidth(ci, MAX_DEFAULT)));
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [headerSig]);

    const widthOf = (ci: number) => colWidths[ci] ?? 160;

    // --- Drag-to-resize ----------------------------------------------------
    const drag = useRef<{ col: number; startX: number; startW: number } | null>(null);

    const onHandleDown = useCallback(
        (e: React.MouseEvent, colIdx: number) => {
            e.preventDefault();
            e.stopPropagation();
            drag.current = { col: colIdx, startX: e.clientX, startW: widthOf(colIdx) };
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        },
        // widthOf reads colWidths; recreate when they change
        // eslint-disable-next-line react-hooks/exhaustive-deps
        [colWidths],
    );

    useEffect(() => {
        const onMove = (e: MouseEvent) => {
            const d = drag.current;
            if (!d) return;
            const next = clamp(d.startW + (e.clientX - d.startX), MIN_COL, MAX_DRAG);
            setColWidths((prev) => {
                const copy = prev.slice();
                copy[d.col] = next;
                return copy;
            });
        };
        const onUp = () => {
            if (!drag.current) return;
            drag.current = null;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        };
        window.addEventListener('mousemove', onMove);
        window.addEventListener('mouseup', onUp);
        return () => {
            window.removeEventListener('mousemove', onMove);
            window.removeEventListener('mouseup', onUp);
        };
    }, []);

    const autoFit = useCallback(
        (colIdx: number) => {
            refreshFonts();
            setColWidths((prev) => {
                const copy = prev.slice();
                copy[colIdx] = fitWidth(colIdx, MAX_AUTOFIT);
                return copy;
            });
        },
        [fitWidth, refreshFonts],
    );

    // --- Hover preview for clipped cells -----------------------------------
    const [preview, setPreview] = useState<Preview | null>(null);

    const onCellEnter = useCallback((e: React.MouseEvent<HTMLInputElement>, value: string) => {
        const el = e.currentTarget;
        // Only preview when the value is actually clipped by the column width.
        if (!value || el.scrollWidth <= el.clientWidth + 1) {
            setPreview(null);
            return;
        }
        const r = el.getBoundingClientRect();
        // Size the box to the text (up to PREVIEW_MAX) instead of relying on
        // shrink-to-fit, which is unreliable for a fixed-position element.
        const width = clamp(Math.ceil(textWidth(value, fonts.current.cell)) + 24, 80, PREVIEW_MAX);
        const vw = window.innerWidth || document.documentElement.clientWidth || 1280;
        const left = clamp(r.left, 8, Math.max(8, vw - width - 12));
        setPreview({ text: value, top: r.bottom + 4, left, width });
    }, []);

    const clearPreview = useCallback(() => setPreview(null), []);

    // The scroll container moves cells out from under the popover; hide on scroll.
    const onScroll = useCallback(() => {
        if (preview) setPreview(null);
    }, [preview]);

    if (headers.length === 0) {
        return (
            <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                Empty file — no TSV data found.
            </div>
        );
    }

    const totalWidth =
        40 + headers.reduce((sum, _, ci) => sum + widthOf(ci), 0) + (readOnly ? 0 : 40);

    return (
        <div className="flex flex-col h-full">
            {/* Scrollable table */}
            <div className="flex-1 overflow-auto" onScroll={onScroll}>
                <table
                    ref={tableRef}
                    className="border-collapse text-sm"
                    style={{ tableLayout: 'fixed', width: totalWidth }}
                >
                    <colgroup>
                        <col style={{ width: 40 }} />
                        {headers.map((_, ci) => (
                            <col key={ci} style={{ width: widthOf(ci) }} />
                        ))}
                        {!readOnly && <col style={{ width: 40 }} />}
                    </colgroup>
                    <thead className="sticky top-0 z-10">
                        <tr className="bg-muted">
                            <th className="border-b border-r px-2 py-1.5 text-center text-xs font-medium text-muted-foreground">
                                #
                            </th>
                            {headers.map((h, i) => (
                                <th
                                    key={i}
                                    className="relative border-b border-r px-2 py-1.5 text-left text-xs font-semibold text-foreground overflow-hidden text-ellipsis whitespace-nowrap"
                                    title={h}
                                >
                                    {h}
                                    {/* Drag to resize; double-click to auto-fit. */}
                                    <span
                                        role="separator"
                                        aria-orientation="vertical"
                                        onMouseDown={(e) => onHandleDown(e, i)}
                                        onDoubleClick={() => autoFit(i)}
                                        title="Drag to resize · double-click to fit"
                                        className="absolute top-0 right-0 z-20 h-full w-1.5 translate-x-1/2 cursor-col-resize select-none bg-transparent hover:bg-primary/40"
                                    />
                                </th>
                            ))}
                            {!readOnly && <th className="border-b px-1 py-1.5" />}
                        </tr>
                    </thead>
                    <tbody>
                        {rows.map((row, ri) => (
                            <tr key={ri} className="hover:bg-muted/30 group">
                                <td className="border-b border-r px-2 py-0.5 text-center text-xs text-muted-foreground tabular-nums">
                                    {ri + 1}
                                </td>
                                {headers.map((_, ci) => (
                                    <td key={ci} className="border-b border-r p-0">
                                        <input
                                            type="text"
                                            value={row[ci] ?? ''}
                                            onChange={(e) => updateCell(ri, ci, e.target.value)}
                                            onMouseEnter={(e) => onCellEnter(e, row[ci] ?? '')}
                                            onMouseLeave={clearPreview}
                                            onFocus={clearPreview}
                                            readOnly={readOnly}
                                            className="w-full bg-transparent px-2 py-1 text-sm outline-none focus:bg-primary/5 focus:ring-1 focus:ring-inset focus:ring-link/30"
                                        />
                                    </td>
                                ))}
                                {!readOnly && (
                                    <td className="border-b px-1 py-0.5 text-center">
                                        <button
                                            type="button"
                                            onClick={() => removeRow(ri)}
                                            className="rounded p-0.5 opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive transition-opacity"
                                            title="Remove row"
                                        >
                                            <Trash2 className="h-3.5 w-3.5" />
                                        </button>
                                    </td>
                                )}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Hover preview: full text of a clipped cell, floating beside it. */}
            {preview && (
                <div
                    className="pointer-events-none fixed z-50 whitespace-pre-wrap break-words rounded-md border bg-popover px-3 py-1.5 text-sm text-popover-foreground shadow-md"
                    style={{ top: preview.top, left: preview.left, width: preview.width }}
                >
                    {preview.text}
                </div>
            )}

            {/* Footer actions */}
            {!readOnly && (
                <div className="flex items-center gap-3 border-t bg-muted/30 px-3 py-2">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={addRow}
                        className="gap-1.5 text-xs"
                    >
                        <Plus className="h-3.5 w-3.5" />
                        Add Row
                    </Button>
                    <span className="text-xs text-muted-foreground">
                        {rows.length} row{rows.length !== 1 ? 's' : ''} &middot; {headers.length}{' '}
                        column{headers.length !== 1 ? 's' : ''}
                    </span>
                </div>
            )}
        </div>
    );
};
