import { useState, useCallback, useRef, useEffect } from 'react';

interface UseResizableOptions {
    /** 'horizontal' = drag left/right to change width; 'vertical' = drag up/down to change height */
    direction: 'horizontal' | 'vertical';
    /** Starting size in pixels */
    initialSize: number;
    /** Minimum allowed size in pixels (default 80) */
    minSize?: number;
    /** Maximum allowed size in pixels (default 800) */
    maxSize?: number;
    /**
     * If true, dragging towards negative screen coords _increases_ size.
     * Useful for a bottom panel: dragging up makes it taller.
     */
    inverted?: boolean;
}

/**
 * Hook for drag-to-resize behaviour on a panel.
 *
 * Returns the current `size` and an `onMouseDown` handler to attach
 * to a resize handle element.
 */
export function useResizable({
    direction,
    initialSize,
    minSize = 80,
    maxSize = 800,
    inverted = false,
}: UseResizableOptions) {
    const [size, setSize] = useState(initialSize);
    const dragging = useRef(false);
    const startPos = useRef(0);
    const startSize = useRef(0);

    const onMouseDown = useCallback(
        (e: React.MouseEvent) => {
            e.preventDefault();
            dragging.current = true;
            startPos.current = direction === 'horizontal' ? e.clientX : e.clientY;
            startSize.current = size;

            document.body.style.cursor = direction === 'horizontal' ? 'col-resize' : 'row-resize';
            document.body.style.userSelect = 'none';
        },
        [direction, size],
    );

    useEffect(() => {
        const onMove = (e: MouseEvent) => {
            if (!dragging.current) return;
            const pos = direction === 'horizontal' ? e.clientX : e.clientY;
            const raw = pos - startPos.current;
            const delta = inverted ? -raw : raw;
            setSize(Math.min(maxSize, Math.max(minSize, startSize.current + delta)));
        };

        const onUp = () => {
            if (!dragging.current) return;
            dragging.current = false;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        };

        window.addEventListener('mousemove', onMove);
        window.addEventListener('mouseup', onUp);
        return () => {
            window.removeEventListener('mousemove', onMove);
            window.removeEventListener('mouseup', onUp);
        };
    }, [direction, inverted, minSize, maxSize]);

    return { size, onMouseDown } as const;
}
