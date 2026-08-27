# Movie Playlist Manager

A full-stack app for browsing movies, building personal playlists, and tracking what you've watched, favorited, and rated.

- **Backend:** Django + Django REST Framework + PostgreSQL, JWT authentication
- **Frontend:** Next.js (App Router) + TypeScript + Tailwind CSS

```
Next.js (frontend/)  →  REST API / JSON  →  Django REST Framework (backend/)  →  PostgreSQL
```

The frontend never touches the database directly — all data access, validation, and authorization live in Django.

---

## Requirements

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+ (running locally, or reachable over the network)

---

## 1. PostgreSQL setup

Create a database and a user for the app (values are examples — anything you choose here just needs to match your `.env` in the next step):

```sql
CREATE USER movie_playlist_manager WITH PASSWORD 'devpassword' CREATEDB;
CREATE DATABASE movie_playlist_manager OWNER movie_playlist_manager;
```

On Windows, run this from **SQL Shell (psql)** (installed alongside PostgreSQL) or pgAdmin's Query Tool.

---

## 2. Backend setup

```powershell
cd backend

python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate

pip install -r requirements.txt

copy .env.example .env         # macOS/Linux: cp .env.example .env
# then edit .env — set SECRET_KEY and the DATABASE_* values to match step 1

python manage.py migrate
python manage.py createsuperuser
python manage.py seed_movies

python manage.py runserver
```

The API is now live at `http://localhost:8000/api/`, the admin site at `http://localhost:8000/admin/`, and interactive API docs (Swagger UI — try any endpoint straight from the browser) at `http://localhost:8000/api/docs/`.

### Running backend tests

```powershell
python manage.py test
```

Runs against a temporary test database that Django creates and destroys automatically — your dev database is untouched.

---

## 3. Frontend setup

Open a **second terminal** (the backend needs to keep running in the first one):

```powershell
cd frontend

npm install

copy .env.example .env.local   # macOS/Linux: cp .env.example .env.local
# .env.local should point at your running backend:
# NEXT_PUBLIC_API_URL=http://localhost:8000/api

npm run dev
```

The app is now live at `http://localhost:3000/`.

### Running frontend tests

```powershell
npm test
```

Uses Vitest + React Testing Library, covering the API client (including token-refresh behavior), utility functions, and key interactive components.

### Frontend build check

```powershell
npm run build
```

Compiles the production bundle and runs a full TypeScript check.

---

## 4. Using the app

```
Register → Login → Dashboard → Browse Movies → Open a movie
   → Create a playlist → Add the movie to it → Mark it watched
   → Rate it → Favorite it → Logout
```

All of this goes through the real Django API and PostgreSQL — nothing in the frontend is mocked or hardcoded.

---

## Environment variables

**`backend/.env`** (see `backend/.env.example`):

| Variable | Purpose |
|---|---|
| `DEBUG` | `True` for local dev, `False` in production |
| `SECRET_KEY` | Django's cryptographic signing key — any long random string locally |
| `ALLOWED_HOSTS` | Comma-separated hostnames Django will serve |
| `DATABASE_NAME` / `DATABASE_USER` / `DATABASE_PASSWORD` / `DATABASE_HOST` / `DATABASE_PORT` | PostgreSQL connection |
| `CORS_ALLOWED_ORIGINS` | Origins allowed to call the API (the frontend's URL) |
| `FRONTEND_URL` | Used to build password-reset email links |

**`frontend/.env.local`** (see `frontend/.env.example`):

| Variable | Purpose |
|---|---|
| `NEXT_PUBLIC_API_URL` | Base URL of the Django API |

Never commit `.env` or `.env.local` — both are already in `.gitignore`.

---

## Project structure

```
movie-playlist-manager/
├── backend/
│   ├── config/settings/       # base.py / development.py / production.py
│   ├── apps/
│   │   ├── accounts/          # custom User model, JWT auth endpoints
│   │   ├── movies/            # Movie/Genre/Person models + browsing API
│   │   ├── playlists/         # Playlist CRUD + movie ordering
│   │   └── library/           # favorites, watchlist, watched, ratings, dashboard
│   └── requirements.txt
│
└── frontend/
    ├── app/                   # Next.js App Router pages
    ├── components/            # layout, movies, playlists, ui primitives
    ├── hooks/                 # useAuth, useToast, useFocusTrap
    ├── lib/                   # API client, endpoint wrappers, utils
    └── types/                 # TypeScript types matching the backend serializers
```

---

## Production considerations

Before deploying:

- Set `DEBUG=False` and use `config.settings.production` (`DJANGO_SETTINGS_MODULE`)
- Set a real, secret `SECRET_KEY` (never reuse the dev one)
- Put PostgreSQL, `SECRET_KEY`, and any other secrets in your host's secret manager — not in the repo
- Serve Django behind a real WSGI/ASGI server (gunicorn/uvicorn), not `runserver`
- Run `python manage.py collectstatic`
- Set `CORS_ALLOWED_ORIGINS` and `ALLOWED_HOSTS` to your real production domains
- Build the frontend with `npm run build` and serve it with `npm run start` or deploy to a platform like Vercel
- Point `NEXT_PUBLIC_API_URL` at your production API URL
