'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowRight, History, RotateCcw, Search, Trophy } from 'lucide-react';
import { dsaApi } from '@/lib/endpoints';
import type { Movie } from '@/types';
import { MovieGrid } from '@/components/movies/MovieGrid';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { getErrorMessage } from '@/lib/utils';
import { useToast } from '@/hooks/useToast';

export default function DsaPage() {
  const { showToast } = useToast();
  const [topRated, setTopRated] = useState<Movie[]>([]);
  const [recent, setRecent] = useState<Movie[]>([]);
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<{ id:number; title:string }[]>([]);
  const [error, setError] = useState<string|null>(null);
  useEffect(() => { Promise.all([dsaApi.topRated(), dsaApi.recentlyViewed()]).then(([a,b]) => { setTopRated(a); setRecent(b); }).catch(e => setError(getErrorMessage(e))); }, []);
  // Autocomplete is synchronized from the query state and intentionally updates suggestions.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { const q=query.trim(); if(q.length<2){setSuggestions([]);return;} const t=setTimeout(()=>dsaApi.autocomplete(q).then(setSuggestions).catch(()=>setSuggestions([])),150); return ()=>clearTimeout(t); },[query]);
  async function undo(){try{showToast((await dsaApi.undoLastPlaylistAction()).detail,'success');}catch(e){showToast(getErrorMessage(e),'error');}}
  return <div className="mx-auto max-w-7xl pb-16">
    <h1 className="font-display text-2xl font-medium text-foreground sm:text-3xl">DSA Lab</h1>
    <p className="mt-1 text-sm text-foreground-muted">Four classic data structures powering real Movie Manager features.</p>
    {error && <p className="mt-6 rounded-lg border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">{error}</p>}
    <section className="mt-8 rounded-xl border border-border bg-surface p-5"><div className="flex items-center gap-2"><Search size={18}/><h2 className="font-display text-lg font-medium">Trie autocomplete</h2></div><p className="mt-1 text-sm text-foreground-muted">Prefix search for movie titles.</p><div className="relative mt-4 max-w-xl"><Input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Try a movie title prefix…"/>{suggestions.length>0&&<div className="absolute left-0 right-0 top-full z-10 mt-1 rounded-lg border border-border bg-surface shadow-lg">{suggestions.map(s=><Link key={s.id} href={`/movies/${s.id}`} className="block px-3 py-2 text-sm hover:bg-surface-raised">{s.title}</Link>)}</div>}</div></section>
    <section className="mt-8"><div className="flex items-center gap-2"><Trophy size={18}/><h2 className="font-display text-xl font-medium">Top Rated</h2></div><p className="mt-1 text-sm text-foreground-muted">Max heap extracts the highest-rated movies first.</p><div className="mt-4"><MovieGrid movies={topRated}/></div></section>
    <section className="mt-10"><div className="flex items-center gap-2"><History size={18}/><h2 className="font-display text-xl font-medium">Recently Viewed</h2></div><p className="mt-1 text-sm text-foreground-muted">Doubly linked list: add-to-front, duplicate removal and oldest-entry eviction.</p><div className="mt-4"><MovieGrid movies={recent}/></div></section>
    <section className="mt-10 rounded-xl border border-border bg-surface p-5"><div className="flex flex-wrap items-center justify-between gap-3"><div><div className="flex items-center gap-2"><RotateCcw size={18}/><h2 className="font-display text-lg font-medium">Playlist undo</h2></div><p className="mt-1 text-sm text-foreground-muted">Stack-based LIFO undo for playlist changes.</p></div><Button variant="secondary" onClick={undo}>Undo last change</Button></div><Link href="/playlists" className="mt-4 inline-flex items-center gap-1 text-sm text-accent hover:underline">Open playlists <ArrowRight size={14}/></Link></section>
  </div>;
}
