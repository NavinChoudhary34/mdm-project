import { Film } from 'lucide-react';
import type { Movie } from '@/types';
import { MovieCard } from './MovieCard';
import { EmptyState } from '../ui/EmptyState';

export function MovieGrid({ movies }: { movies: Movie[] }) {
  if (movies.length === 0) {
    return (
      <EmptyState
        icon={<Film size={32} />}
        title="No movies found"
        description="Try adjusting your search or filters."
      />
    );
  }

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
      {movies.map((movie) => (
        <MovieCard key={movie.id} movie={movie} />
      ))}
    </div>
  );
}
