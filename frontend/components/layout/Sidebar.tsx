'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LogOut, Settings, User as UserIcon } from 'lucide-react';
import { primaryNavItems } from './nav-items';
import { useAuth } from '@/hooks/useAuth';
import { cn } from '@/lib/utils';

/**
 * Desktop-only left sidebar (spec section 5). Hidden below the `lg` breakpoint,
 * where MobileNav takes over via a drawer instead.
 */
export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  // Pick the longest href that matches the current path, so nested routes
  // (e.g. /movies/my) don't also mark their parent (/movies) as active.
  const activeHref = primaryNavItems
    .filter((item) => pathname === item.href || pathname.startsWith(`${item.href}/`))
    .sort((a, b) => b.href.length - a.href.length)[0]?.href;

  return (
    <aside className="hidden lg:flex lg:w-64 lg:flex-col lg:border-r lg:border-border lg:bg-surface">
      <div className="flex h-16 items-center gap-2 px-6">
        <span className="font-display text-lg font-medium tracking-tight text-foreground">
          Movie Manager
        </span>
      </div>

      <nav aria-label="Primary" className="flex flex-1 flex-col gap-1 px-3">
        {primaryNavItems.map((item) => {
          // Only the most specific matching href is active, so a parent route
          // (e.g. /movies) doesn't also light up alongside a nested one that's
          // currently open (e.g. /movies/my).
          const isActive = item.href === activeHref;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={isActive ? 'page' : undefined}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-accent-soft text-accent'
                  : 'text-foreground-muted hover:bg-surface-raised hover:text-foreground'
              )}
            >
              <Icon size={18} strokeWidth={2} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="px-3 pb-4">
        <div className="sprocket-rail mb-3" />

        <Link
          href="/settings"
          className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-foreground-muted transition-colors hover:bg-surface-raised hover:text-foreground"
        >
          <UserIcon size={18} strokeWidth={2} />
          <span className="truncate">{user?.username ?? 'Profile'}</span>
        </Link>
        <Link
          href="/settings"
          className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-foreground-muted transition-colors hover:bg-surface-raised hover:text-foreground"
        >
          <Settings size={18} strokeWidth={2} />
          Settings
        </Link>
        <button
          onClick={logout}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm font-medium text-foreground-muted transition-colors hover:bg-danger/10 hover:text-danger"
        >
          <LogOut size={18} strokeWidth={2} />
          Logout
        </button>
      </div>
    </aside>
  );
}