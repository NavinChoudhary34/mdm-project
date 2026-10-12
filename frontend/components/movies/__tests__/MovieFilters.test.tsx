import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MovieFilters, type MovieFilterState } from '../MovieFilters';

// vi.hoisted lets the mock factories below share these functions safely.
const { push, autocomplete } = vi.hoisted(() => ({ push: vi.fn(), autocomplete: vi.fn() }));

// The component only needs router.push from Next's router.
vi.mock('next/navigation', () => ({ useRouter: () => ({ push }) }));

// Replace the network layer: no genres, and a controllable autocomplete.
vi.mock('@/lib/endpoints', () => ({
  moviesApi: { genres: vi.fn().mockResolvedValue([]) },
  dsaApi: { autocomplete },
}));

// A plain anchor stands in for next/link (no router context needed in tests).
vi.mock('next/link', () => ({
  default: ({ href, children, ...rest }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

const FILTERS: MovieFilterState = { search: '', genre: '', year: '', min_rating: '', watched: '', ordering: '-created_at' };

function setup() {
  const user = userEvent.setup();
  render(<MovieFilters filters={FILTERS} onChange={vi.fn()} />);
  // The Sort dropdown is also a combobox, so find the search box by its placeholder.
  return { user, input: screen.getByPlaceholderText(/search movies/i) };
}

describe('MovieFilters title autocomplete', () => {
  beforeEach(() => {
    push.mockClear();
    autocomplete.mockReset();
  });

  it('does not ask for suggestions until at least 2 characters are typed', async () => {
    const { user, input } = setup();
    await user.type(input, 'i');
    // Wait longer than the 150ms debounce, then confirm nothing was requested.
    await new Promise((r) => setTimeout(r, 250));
    expect(autocomplete).not.toHaveBeenCalled();
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
  });

  it('shows suggestions as links to the movie pages', async () => {
    autocomplete.mockResolvedValue([
      { id: 1, title: 'Inception' },
      { id: 2, title: 'Interstellar' },
    ]);
    const { user, input } = setup();
    await user.type(input, 'in');

    const list = await screen.findByRole('listbox');
    expect(within(list).getAllByRole('option')).toHaveLength(2);
    expect(screen.getByRole('link', { name: 'Inception' })).toHaveAttribute('href', '/movies/1');
    expect(autocomplete).toHaveBeenCalledWith('in');
  });

  it('opens the highlighted movie with ArrowDown + Enter', async () => {
    autocomplete.mockResolvedValue([
      { id: 1, title: 'Inception' },
      { id: 2, title: 'Interstellar' },
    ]);
    const { user, input } = setup();
    await user.type(input, 'in');
    await screen.findByRole('listbox'); // suggestions must be on screen before using the keyboard

    await user.keyboard('{ArrowDown}{ArrowDown}{Enter}');
    expect(push).toHaveBeenCalledWith('/movies/2');
  });

  it('closes the list on Escape', async () => {
    autocomplete.mockResolvedValue([{ id: 1, title: 'Inception' }]);
    const { user, input } = setup();
    await user.type(input, 'in');
    await screen.findByRole('listbox');

    await user.keyboard('{Escape}');
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
  });

  it('keeps showing the previous suggestions while a longer query is loading (no flicker)', async () => {
    // "in" resolves immediately; "inc" never resolves during this test.
    autocomplete.mockImplementation((q: string) =>
      q === 'in' ? Promise.resolve([{ id: 1, title: 'Inception' }]) : new Promise(() => {})
    );
    const { user, input } = setup();
    await user.type(input, 'in');
    await screen.findByRole('link', { name: 'Inception' });

    await user.type(input, 'c'); // request for "inc" is now pending
    await waitFor(() => expect(autocomplete).toHaveBeenCalledWith('inc'));
    expect(screen.getByRole('link', { name: 'Inception' })).toBeInTheDocument();
  });

  it('hides old suggestions when the text changes to something unrelated', async () => {
    autocomplete.mockImplementation((q: string) =>
      q === 'in' ? Promise.resolve([{ id: 1, title: 'Inception' }]) : new Promise(() => {})
    );
    const { user, input } = setup();
    await user.type(input, 'in');
    await screen.findByRole('link', { name: 'Inception' });

    await user.clear(input);
    await user.type(input, 'ma'); // "ma" is unrelated to "in"; its request is still pending
    await waitFor(() => expect(autocomplete).toHaveBeenCalledWith('ma'));
    expect(screen.queryByRole('link', { name: 'Inception' })).not.toBeInTheDocument();
  });

  it('never lets a slow response for an older query overwrite newer suggestions', async () => {
    // The response for "in" is held back until after the response for "inc" has arrived.
    let resolveOld: (v: { id: number; title: string }[]) => void = () => {};
    autocomplete.mockImplementation((q: string) =>
      q === 'in'
        ? new Promise((resolve) => {
            resolveOld = resolve;
          })
        : Promise.resolve([{ id: 9, title: 'Inception' }])
    );
    const { user, input } = setup();
    await user.type(input, 'in');
    await waitFor(() => expect(autocomplete).toHaveBeenCalledWith('in'));
    await user.type(input, 'c');
    await screen.findByRole('link', { name: 'Inception' });

    // Late arrival of the OLD response must not replace the newer suggestions.
    resolveOld([{ id: 1, title: 'Interstellar' }]);
    await new Promise((r) => setTimeout(r, 50));
    expect(screen.queryByRole('link', { name: 'Interstellar' })).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Inception' })).toBeInTheDocument();
  });

  it('keeps working (no list, no crash) when the suggestion request fails', async () => {
    autocomplete.mockRejectedValue(new Error('boom'));
    const { user, input } = setup();
    await user.type(input, 'in');
    await waitFor(() => expect(autocomplete).toHaveBeenCalled());
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
  });
});
