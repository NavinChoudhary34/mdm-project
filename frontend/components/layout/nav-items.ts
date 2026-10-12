import type { LucideIcon } from 'lucide-react';

import {
  Clapperboard,
  Eye,
  Film,
  Heart,
  LayoutDashboard,
  ListVideo,
  ListChecks,
  Network,
} from 'lucide-react';

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

// Primary navigation
export const primaryNavItems: NavItem[] = [
  {
    label: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
  },
  {
    label: 'Movies',
    href: '/movies',
    icon: Clapperboard,
  },
  {
    label: 'My Movies',
    href: '/movies/my',
    icon: Film,
  },
  {
    label: 'My Playlists',
    href: '/playlists',
    icon: ListVideo,
  },
  { label: 'DSA Lab', href: '/dsa', icon: Network },
  {
    label: 'Watchlist',
    href: '/watchlist',
    icon: ListChecks,
  },
  {
    label: 'Watched',
    href: '/watched',
    icon: Eye,
  },
  {
    label: 'Favorites',
    href: '/favorites',
    icon: Heart,
  },
];

/**
 * Whether a nav item should be highlighted for the current URL path.
 *
 * A plain "starts with" check highlighted both "Movies" (/movies) and "My Movies"
 * (/movies/my) on /movies/my. Here an item is active only if no OTHER nav item with a
 * longer (more specific) href also matches the path.
 */
export function isNavItemActive(pathname: string, href: string): boolean {
  const matches = (h: string) => pathname === h || pathname.startsWith(`${h}/`);
  if (!matches(href)) return false;
  return !primaryNavItems.some((other) => other.href.length > href.length && matches(other.href));
}
