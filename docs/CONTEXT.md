# Cine UIO — Domain & Architecture Context

## Purpose

Cine UIO aggregates movie screenings from cinema chains in Quito, Ecuador. It scrapes showtime data from Multicines and Supercines, stores it in a local SQLite database, and exposes it via a REST API consumed by a React frontend.

## Tech Stack

| Layer      | Technology                                      |
|------------|-------------------------------------------------|
| Backend    | Python 3.14, FastAPI, SQLAlchemy 2, SQLite      |
| Migrations | Alembic                                         |
| Scraping   | Playwright (browser automation) + requests      |
| Frontend   | React 19, TypeScript, Vite, Biome               |
| Testing    | pytest (backend), Vitest + Testing Library (FE) |
| Tooling    | uv (Python pkg manager), Bun, mise (task runner)|

## Architecture

```
cine-uio/
├── backend/
│   ├── app/
│   │   ├── api.py          — FastAPI routes
│   │   ├── database.py     — SQLAlchemy engine, session, query helpers
│   │   ├── models.py       — ORM models (SQLAlchemy DeclarativeBase)
│   │   ├── entities.py     — Pure domain dataclasses (no ORM coupling)
│   │   ├── schemas.py      — Pydantic response schemas
│   │   ├── seed.py         — Seed CinemaCompany + CinemaComplex rows
│   │   ├── logging.py      — Shared logger
│   │   └── scrapers/
│   │       ├── base.py         — Abstract Scraper + registry pattern
│   │       ├── multicines.py   — Multicines scraper (intercepts XHR)
│   │       └── supercines.py   — Supercines scraper (parses Next.js data)
│   ├── migrations/         — Alembic migration scripts
│   ├── main.py             — uvicorn entrypoint
│   └── scraper_entrypoint.py — CLI entrypoint for the scraper
└── frontend/
    └── src/
        ├── App.tsx         — Main component: fetch, filter, group, render
        └── config.ts       — API base URL (env-configurable)
```

## Data Flow

1. **Seed**: `app/seed.py` populates `CinemaCompany` and `CinemaComplex` rows (must run before scraping).
2. **Scrape**: `scraper_entrypoint.py` deletes all screenings, iterates over companies, picks the right `Scraper` subclass via registry, scrapes each complex, and saves `Screening` rows.
3. **Serve**: `main.py` / `app/api.py` exposes `GET /api/screenings` (with optional `cinema_company_name` and `cinema_complex_name` filters).
4. **Display**: Frontend fetches all screenings, filters to today's date (UTC), groups by movie then by company+complex, and renders a sorted list.

## Running Locally

```bash
# Backend
cd backend
uv run alembic upgrade head   # create/migrate DB schema
uv run python -m app.seed     # seed companies & complexes (once)
uv run python scraper_entrypoint.py  # populate screenings
uv run uvicorn app.api:app --reload  # start API on :8000

# Frontend
cd frontend
bun install
bun dev                       # start dev server on :5173
```

## Mise Tasks

```bash
mise lint     # mypy + ruff (backend) + biome lint (frontend)
mise format   # ruff format (backend) + biome check --write (frontend)
mise test     # pytest (backend) + vitest (frontend)
```

## Environment Variables

| Variable          | Default                  | Description                              |
|-------------------|--------------------------|------------------------------------------|
| `VITE_API_URL`    | `http://localhost:8000/api` | API base URL (frontend)               |
| `ALLOWED_ORIGINS` | `http://localhost:5173`  | Comma-separated CORS origins (backend)   |

## Domain Glossary

### CinemaCompany
- **name**: String (e.g., `"Multicines"`, `"Supercines"`)
- **base_url**: String (e.g., `"https://www.multicines.com.ec"`)

### CinemaComplex
- **name**: String (e.g., `"CCI"`, `"San Luis"`)
- **url_part**: String (e.g., `"/?cityId=19&storeId=3555"`, `"/cartelera/quito/san-luis/216"`)

### Movie
- **title**: String

### Screening
- **datetime**: DateTime (naive, local time as returned by the cinema API)
- **format**: String (e.g., `"2D"`, `"3D"`)
- **language**: String (e.g., `"Original + subtitulos"`, `"Doblada"`)

### Relationships
- A **CinemaCompany** has many **CinemaComplexes**.
- A **CinemaComplex** has many **Screenings**.
- A **Movie** has many **Screenings**.

## Known Constraints

- SQLite is the database — single-file, no concurrency concerns at this scale.
- Scraping uses Playwright to load pages and capture XHR requests; API tokens/headers are harvested from the browser session.
- `delete_all_screenings` is called at the start of every scrape run (full refresh, no incremental update).
- The Supercines scraper parses embedded Next.js `__next_f.push` data; this is fragile to site changes.
