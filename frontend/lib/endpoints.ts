import { api, buildQuery } from './api';
import type {
  DashboardData,
  Favorite,
  Genre,
  Movie,
  Paginated,
  Playlist,
  PlaylistMovieEntry,
  Rating,
  User,
  WatchedEntry,
  WatchlistEntry,
} from '@/types';

// --- Auth ---
export const authApi = {
  register: (data: { username: string; email: string; password: string; password_confirm: string }) =>
    api.post<{ user: User; access: string; refresh: string }>('/auth/register/', data, { skipAuth: true }),

  login: (data: { username: string; password: string }) =>
    api.post<{ user: User; access: string; refresh: string }>('/auth/login/', data, { skipAuth: true }),

  logout: (refresh: string) => api.post<void>('/auth/logout/', { refresh }),

  me: () => api.get<User>('/auth/me/'),

  updateProfile: (data: Partial<Pick<User, 'username' | 'email' | 'bio' | 'avatar_url'>>) =>
    api.patch<User>('/auth/me/', data),

  changePassword: (data: { old_password: string; new_password: string }) =>
    api.post<void>('/auth/change-password/', data),

  requestPasswordReset: (email: string) =>
    api.post<{ detail: string }>('/auth/password-reset/', { email }, { skipAuth: true }),

  confirmPasswordReset: (data: { uid: string; token: string; new_password: string }) =>
    api.post<void>('/auth/password-reset/confirm/', data, { skipAuth: true }),
};

// --- Movies ---
export interface MovieFilters {
  search?: string;
  genre?: string;
  year?: number;
  min_rating?: number;
  watched?: boolean;
  ordering?: string;
  page?: number;
}

export const moviesApi = {
  list: (filters: MovieFilters = {}) =>
    api.get<Paginated<Movie>>(`/movies/${buildQuery(filters as Record<string, string | number>)}`),

  detail: (id: number) => api.get<Movie>(`/movies/${id}/`),

  genres: () => api.get<Genre[]>('/movies/genres/'),
};

// --- Playlists ---
export const playlistsApi = {
  list: (page = 1) => api.get<Paginated<Playlist>>(`/playlists/${buildQuery({ page })}`),

  detail: (id: number) => api.get<Playlist>(`/playlists/${id}/`),

  publicDetail: (id: number) => api.get<Playlist>(`/public/playlists/${id}/`, { skipAuth: true }),

  create: (data: { name: string; description: string; is_public: boolean }) =>
    api.post<Playlist>('/playlists/', data),

  update: (id: number, data: Partial<{ name: string; description: string; is_public: boolean }>) =>
    api.patch<Playlist>(`/playlists/${id}/`, data),

  remove: (id: number) => api.delete<void>(`/playlists/${id}/`),

  addMovie: (playlistId: number, movieId: number) =>
    api.post<PlaylistMovieEntry>(`/playlists/${playlistId}/movies/`, { movie_id: movieId }),

  removeMovie: (playlistId: number, movieId: number) =>
    api.delete<void>(`/playlists/${playlistId}/movies/${movieId}/`),

  updateMovieEntry: (playlistId: number, movieId: number, data: { watched?: boolean; notes?: string }) =>
    api.patch<PlaylistMovieEntry>(`/playlists/${playlistId}/movies/${movieId}/`, data),

  reorder: (playlistId: number, movieIds: number[]) =>
    api.patch<Playlist>(`/playlists/${playlistId}/reorder/`, { movie_ids: movieIds }),
};

// --- Library: favorites / watchlist / watched / ratings ---
export const libraryApi = {
  dashboard: () => api.get<DashboardData>('/dashboard/'),

  favorites: (page = 1) => api.get<Paginated<Favorite>>(`/favorites/${buildQuery({ page })}`),
  addFavorite: (movieId: number) => api.post<Favorite>('/favorites/', { movie_id: movieId }),
  removeFavorite: (movieId: number) => api.delete<void>(`/favorites/${movieId}/`),

  watchlist: (page = 1) => api.get<Paginated<WatchlistEntry>>(`/watchlist/${buildQuery({ page })}`),
  addToWatchlist: (movieId: number) => api.post<WatchlistEntry>('/watchlist/', { movie_id: movieId }),
  removeFromWatchlist: (movieId: number) => api.delete<void>(`/watchlist/${movieId}/`),

  watched: (page = 1) => api.get<Paginated<WatchedEntry>>(`/watched/${buildQuery({ page })}`),
  markWatched: (movieId: number) => api.post<WatchedEntry>('/watched/', { movie_id: movieId }),
  markUnwatched: (movieId: number) => api.delete<void>(`/watched/${movieId}/`),

  ratings: () => api.get<Paginated<Rating>>('/ratings/'),
  rateMovie: (movieId: number, data: { score: number; review?: string }) =>
    api.put<Rating>(`/ratings/${movieId}/`, data),
  removeRating: (movieId: number) => api.delete<void>(`/ratings/${movieId}/`),
};
