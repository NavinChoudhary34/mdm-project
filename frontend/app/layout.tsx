import type { Metadata } from 'next';
import { Fraunces, Inter, IBM_Plex_Mono } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';

const inter = Inter({
  variable: '--font-inter',
  subsets: ['latin'],
});

// Display face for movie titles, the wordmark, and section headers — a nod to
// the elegant serifed lettering on old cinema marquees and film posters.
const fraunces = Fraunces({
  variable: '--font-fraunces',
  subsets: ['latin'],
  weight: 'variable',
  axes: ['opsz', 'SOFT', 'WONK'],
});

// Utility face for numeric metadata — runtimes, years, ratings — styled a
// little like the printed numbers on a ticket stub.
const plexMono = IBM_Plex_Mono({
  variable: '--font-plex-mono',
  subsets: ['latin'],
  weight: ['400', '500'],
});

export const metadata: Metadata = {
  title: 'Movie Playlist Manager',
  description: 'Track, rate, and organize the movies you love.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${fraunces.variable} ${plexMono.variable} h-full`}>
      <body className="min-h-full bg-background text-foreground antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
