import { describe, it, expect } from 'vitest';
import { isNavItemActive, primaryNavItems } from '../nav-items';

// Returns the labels of every nav item that would be highlighted for a path.
function activeLabels(pathname: string): string[] {
  return primaryNavItems.filter((item) => isNavItemActive(pathname, item.href)).map((i) => i.label);
}

describe('isNavItemActive', () => {
  it('highlights only "My Movies" on /movies/my (was highlighting Movies too)', () => {
    expect(activeLabels('/movies/my')).toEqual(['My Movies']);
  });

  it('highlights "Movies" on the list, detail and add pages', () => {
    expect(activeLabels('/movies')).toEqual(['Movies']);
    expect(activeLabels('/movies/42')).toEqual(['Movies']);
    expect(activeLabels('/movies/add')).toEqual(['Movies']);
  });

  it('highlights playlists for nested playlist pages', () => {
    expect(activeLabels('/playlists')).toEqual(['My Playlists']);
    expect(activeLabels('/playlists/7')).toEqual(['My Playlists']);
  });

  it('does not match on a partial segment (e.g. /movies-archive)', () => {
    expect(activeLabels('/movies-archive')).toEqual([]);
  });

  it('highlights exactly one item on every top-level page', () => {
    for (const item of primaryNavItems) {
      expect(activeLabels(item.href)).toEqual([item.label]);
    }
  });
});
