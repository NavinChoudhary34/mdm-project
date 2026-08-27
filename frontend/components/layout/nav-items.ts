import type { LucideIcon } from 'lucide-react';
import { Clapperboard, Eye, Heart, LayoutDashboard, ListVideo, ListChecks } from 'lucide-react';

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

// Primary navigation, per the application layout spec (dashboard, catalog,
// playlists, and the three personal-library views).
export const primaryNavItems: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { label: 'Movies', href: '/movies', icon: Clapperboard },
  { label: 'My Playlists', href: '/playlists', icon: ListVideo },
  { label: 'Watchlist', href: '/watchlist', icon: ListChecks },
  { label: 'Watched', href: '/watched', icon: Eye },
  { label: 'Favorites', href: '/favorites', icon: Heart },
];
