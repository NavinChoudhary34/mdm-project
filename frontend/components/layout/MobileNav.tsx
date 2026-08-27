'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LogOut, Menu, Settings, User as UserIcon, X } from 'lucide-react';
import { primaryNavItems } from './nav-items';
import { useAuth } from '@/hooks/useAuth';
import { useFocusTrap } from '@/hooks/useFocusTrap';
import { cn } from '@/lib/utils';

/**
 * Mobile top bar with a slide-out drawer, shown below the `lg` breakpoint
 * (spec section 5: "responsive navigation menu / drawer" on mobile).
 */
export function MobileNav() {
  const [isOpen, setIsOpen] = useState(false);
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const drawerRef = useFocusTrap(isOpen);

  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setIsOpen(false);
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [isOpen]);

  return (
    <div className="lg:hidden">
      <div className="flex h-14 items-center justify-between border-b border-border bg-surface px-4">
        <span className="font-display text-base font-medium tracking-tight text-foreground">
          Movie Manager
        </span>
        <button
          onClick={() => setIsOpen(true)}
          aria-label="Open menu"
          className="icon-btn-focus rounded-md p-2 text-foreground-muted hover:bg-surface-raised hover:text-foreground"
        >
          <Menu size={22} />
        </button>
      </div>

      {isOpen && (
        <div className="fixed inset-0 z-50 flex">
          {/* Backdrop */}
          <button
            aria-label="Close menu"
            className="absolute inset-0 bg-black/60"
            onClick={() => setIsOpen(false)}
          />

          {/* Drawer */}
          <div
            ref={drawerRef}
            tabIndex={-1}
            role="dialog"
            aria-modal="true"
            aria-label="Navigation menu"
            className="relative flex h-full w-72 flex-col bg-surface shadow-xl focus:outline-none"
          >
            <div className="flex h-14 items-center justify-between px-4">
              <span className="font-display text-base font-medium text-foreground">Movie Manager</span>
              <button
                onClick={() => setIsOpen(false)}
                aria-label="Close menu"
                className="icon-btn-focus rounded-md p-2 text-foreground-muted hover:bg-surface-raised hover:text-foreground"
              >
                <X size={20} />
              </button>
            </div>

            <nav aria-label="Primary" className="flex flex-1 flex-col gap-1 overflow-y-auto px-3">
              {primaryNavItems.map((item) => {
                const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setIsOpen(false)}
                    aria-current={isActive ? 'page' : undefined}
                    className={cn(
                      'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
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

            <div className="px-3 pb-6">
              <div className="sprocket-rail mb-3" />
              <Link
                href="/settings"
                onClick={() => setIsOpen(false)}
                className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-foreground-muted hover:bg-surface-raised hover:text-foreground"
              >
                <UserIcon size={18} strokeWidth={2} />
                <span className="truncate">{user?.username ?? 'Profile'}</span>
              </Link>
              <Link
                href="/settings"
                onClick={() => setIsOpen(false)}
                className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-foreground-muted hover:bg-surface-raised hover:text-foreground"
              >
                <Settings size={18} strokeWidth={2} />
                Settings
              </Link>
              <button
                onClick={() => {
                  setIsOpen(false);
                  logout();
                }}
                className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm font-medium text-foreground-muted hover:bg-danger/10 hover:text-danger"
              >
                <LogOut size={18} strokeWidth={2} />
                Logout
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
