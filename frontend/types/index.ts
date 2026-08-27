export interface User {
  id: number;
  username: string;
  email: string;
  bio: string;
  avatar_url: string;
  date_joined: string;
}

export interface Genre {
  id: number;
  name: string;
}

export interface Person {
  id: number;
  name: string;
  photo_url: string;
}

export interface CastMember {
  id: number;
  name: string;
  photo_url: string;
  character_name: string;
  billing_order: number;
}

export interface Movie {
  id: number;
  title: string;
  description?: string;
  poster_url: string;
  backdrop_url: string;
  release_date: string | null;
  release_year: number | null;
  runtime_minutes: number | null;
  rating: string | null;
  genres: Genre[];
  director: Person | null;
  is_favorited: boolean;
  is_in_watchlist: boolean;
  is_watched: boolean;
  cast_members?: CastMember[];
  my_rating?: { score: number; review: string } | null;
  created_at?: string;
  updated_at?: string;
}

export interface PlaylistMovieEntry {
  id: number;
  movie: Movie;
  position: number;
  watched: boolean;
  notes: string;
  added_at: string;
}

export interface Playlist {
  id: number;
  name: string;
  description: string;
  is_public: boolean;
  movie_count: number;
  owner_username: string;
  created_at: string;
  updated_at: string;
  movies?: PlaylistMovieEntry[];
}

export interface Favorite {
  id: number;
  movie: Movie;
  created_at: string;
}

export interface WatchlistEntry {
  id: number;
  movie: Movie;
  added_at: string;
}

export interface WatchedEntry {
  id: number;
  movie: Movie;
  watched_at: string;
}

export interface Rating {
  id: number;
  movie: Movie;
  score: number;
  review: string;
  created_at: string;
  updated_at: string;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface DashboardStats {
  total_playlists: number;
  total_movies: number;
  movies_watched: number;
  movies_unwatched: number;
  favorite_count: number;
  watchlist_count: number;
}

export interface DashboardData {
  stats: DashboardStats;
  recent_favorites: Movie[];
  recently_watched: Movie[];
  recently_updated_playlists: { id: number; name: string; updated_at: string }[];
}

export interface ApiError {
  detail?: string;
  [field: string]: unknown;
}
