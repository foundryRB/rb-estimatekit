import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { FileTreeItem } from '@/views/molecules/FileTreeItem';
import type { ProjectFile } from '@/models/types';

const makeFile = (overrides: Partial<ProjectFile> = {}): ProjectFile => ({
    path: 'data/activities/P2-build.tsv',
    name: 'P2-build.tsv',
    kind: 'tsv',
    directory: 'data/activities',
    ...overrides,
});

const noop = () => {};

const baseProps = {
    file: makeFile(),
    active: false,
    dirty: false,
    confirming: false,
    deleting: false,
    onClick: noop,
    onRequestDelete: noop,
    onConfirmDelete: noop,
    onCancelDelete: noop,
};

describe('FileTreeItem', () => {
    it('opens the file when the row is clicked', () => {
        const onClick = vi.fn();
        render(<FileTreeItem {...baseProps} onClick={onClick} />);
        fireEvent.click(screen.getByText('P2-build.tsv'));
        expect(onClick).toHaveBeenCalledOnce();
    });

    it('requests deletion when the trash button is clicked', () => {
        const onRequestDelete = vi.fn();
        render(<FileTreeItem {...baseProps} onRequestDelete={onRequestDelete} />);
        fireEvent.click(screen.getByLabelText('Delete P2-build.tsv'));
        expect(onRequestDelete).toHaveBeenCalledOnce();
    });

    it('shows an inline confirm and fires confirm / cancel', () => {
        const onConfirmDelete = vi.fn();
        const onCancelDelete = vi.fn();
        render(
            <FileTreeItem
                {...baseProps}
                confirming
                onConfirmDelete={onConfirmDelete}
                onCancelDelete={onCancelDelete}
            />,
        );
        expect(screen.getByText('Delete P2-build.tsv?')).toBeInTheDocument();

        fireEvent.click(screen.getByLabelText('Confirm delete P2-build.tsv'));
        expect(onConfirmDelete).toHaveBeenCalledOnce();

        fireEvent.click(screen.getByLabelText('Cancel delete'));
        expect(onCancelDelete).toHaveBeenCalledOnce();
    });

    it('disables the confirm control while the delete is in flight', () => {
        render(<FileTreeItem {...baseProps} confirming deleting />);
        expect(screen.getByLabelText('Confirm delete P2-build.tsv')).toBeDisabled();
        expect(screen.getByLabelText('Cancel delete')).toBeDisabled();
    });
});
