import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { EmptyState } from '../EmptyState';

describe('EmptyState', () => {
  it('renders the title and description', () => {
    render(<EmptyState title="No movies found" description="Try adjusting your filters." />);
    expect(screen.getByText('No movies found')).toBeInTheDocument();
    expect(screen.getByText('Try adjusting your filters.')).toBeInTheDocument();
  });

  it('does not render an action button when none is provided', () => {
    render(<EmptyState title="Empty" />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('renders and wires up the action button when both label and handler are given', async () => {
    const user = userEvent.setup();
    const onAction = vi.fn();
    render(<EmptyState title="No playlists yet" actionLabel="Create playlist" onAction={onAction} />);

    const button = screen.getByRole('button', { name: 'Create playlist' });
    await user.click(button);

    expect(onAction).toHaveBeenCalledTimes(1);
  });
});
