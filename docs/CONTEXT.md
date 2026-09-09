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
│   │   ├── scrape.py       — Scrape run orchestration: collect results, publish per complex
│   │   ├── tmdb.py         — TMDB API client (search + enrichment)
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
2. **Scrape**: `scraper_entrypoint.py` runs every registered `Scraper`, which **returns** the screenings it found per complex rather than writing them. `scrape.apply_scrape_results` then swaps each complex's screenings in its own transaction.
   - A reader never sees an empty cartelera: the delete and the inserts for a complex commit together, so a request during a scrape sees either the previous listing or the new one.
   - A complex that fails — or that scrapes zero screenings, which is indistinguishable from a broken scrape — keeps its previous screenings instead of being wiped. The other complexes still refresh.
   - The run exits non-zero when anything failed, so a partial scrape is visible in the launchd log rather than passing for success.
3. **Enrich**: After all scrapers finish, `database.enrich_movies_with_tmdb` looks up each un-enriched `Movie` on TMDB, stores canonical metadata (title, poster, overview, runtime, certification), and merges any duplicate `Movie` rows that resolved to the same `tmdb_id`. Progress is committed per movie, so a crash mid-run keeps the API work already done.
4. **Serve**: `main.py` / `app/api.py` exposes `GET /api/screenings` (with optional `cinema_company_name` and `cinema_complex_name` filters).
5. **Display**: Frontend fetches all screenings, filters to today's date (Ecuador TZ), groups by `tmdb_id` (falling back to scraped title), displays the canonical `tmdb_title`, and renders poster, runtime, certification, and overview alongside showtimes. When today has no screenings, it falls back to the nearest *upcoming* date — never a past one — and shows an empty state if nothing is upcoming.

## Running in "Production" (a laptop)

Production is currently a developer laptop reachable over Tailscale. See
`docs/hosting.md` for the deferred plan to move it somewhere public.

```bash
mise run start    # build the SPA, serve it and the API from :8000 (single origin)
mise run serve    # expose that port on the tailnet over HTTPS
mise run unserve  # stop exposing it
```

`start` binds to loopback on purpose — `tailscale serve` proxies from the tailnet
to localhost, so the port is never open on the local network. The site is then at
`https://<machine>.<tailnet>.ts.net`, reachable from any device signed into the
tailnet, including a phone on mobile data.

Single origin is what makes this simple: `VITE_API_URL` is the relative `/api`
(see `frontend/.env.production`), so the build works under any hostname and no
CORS configuration is involved. FastAPI mounts `frontend/dist` at `/`, after the
API routes, so `/api/*` still resolves and an unknown API path still 404s.

The daily refresh runs through a launchd agent:

```bash
./ops/install-scrape-agent.sh          # daily at 05:00
./ops/install-scrape-agent.sh 7 30     # or at 07:30
./ops/install-scrape-agent.sh --uninstall
launchctl kickstart -p gui/$(id -u)/dev.cine-uio.scrape   # run it now
```

Logs go to `~/Library/Logs/cine-uio/scrape.log`. If the laptop is asleep or off at
the scheduled time, launchd runs the job at the next opportunity rather than
skipping the day. The site itself is unreachable while the laptop sleeps — that is
inherent to hosting on a laptop.

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

| Variable                  | Default                     | Description                              |
|---------------------------|-----------------------------|------------------------------------------|
| `VITE_API_URL`            | `http://localhost:8000/api` | API base URL (frontend)                  |
| `ALLOWED_ORIGINS`         | `http://localhost:5173`     | Comma-separated CORS origins (backend)   |
| `TMDB_READ_ACCESS_TOKEN`  | *(required for enrichment)* | TMDB Bearer token for movie metadata     |

## Domain Glossary

### CinemaCompany
- **name**: String (e.g., `"Multicines"`, `"Supercines"`)
- **base_url**: String (e.g., `"https://www.multicines.com.ec"`)

### CinemaComplex
- **name**: String (e.g., `"CCI"`, `"San Luis"`)
- **url_part**: String (e.g., `"/?cityId=19&storeId=3555"`, `"/cartelera/quito/san-luis/216"`)

### Movie
- **title**: String — raw title as returned by the cinema scraper
- **tmdb_id**: Integer | None — TMDB movie ID (unique); populated after enrichment
- **tmdb_title**: String | None — canonical title from TMDB (used as display title when available)
- **poster_path**: String | None — TMDB poster path (e.g. `/abc123.jpg`); combine with `https://image.tmdb.org/t/p/w500` for the full URL
- **overview**: String | None — TMDB plot summary
- **runtime**: Integer | None — duration in minutes
- **certification**: String | None — age rating (prefers Ecuador, falls back to US then GB)
- **release_date**: String | None — ISO date string (`YYYY-MM-DD`)
- **tmdb_attempts**: Integer — internal bookkeeping, never exposed by the API; how many times TMDB has been asked about this title

### Screening
- **datetime**: DateTime (naive, local time as returned by the cinema API)
- **format**: String (e.g., `"2D"`, `"3D"`)
- **language**: String (e.g., `"Original + subtitulos"`, `"Doblada"`)

### Relationships
- A **CinemaCompany** has many **CinemaComplexes**.
- A **CinemaComplex** has many **Screenings**.
- A **Movie** has many **Screenings**.

## Known Constraints

- SQLite is the database — single-file, no concurrency concerns at this scale. Connections are put in **WAL** journal mode with a 5s `busy_timeout` (`database.configure_sqlite`): the daily scrape rewrites every screening while the API may be serving, and SQLite's default `delete` mode has a writer block readers outright.
- Scraping uses Playwright to load pages and capture XHR requests; API tokens/headers are harvested from the browser session.
- Screenings are replaced per complex, not globally. `Movie` rows are **not** deleted between runs, so TMDB metadata persists and only new movies need enrichment.
- The Supercines scraper parses embedded Next.js `__next_f.push` data; this is fragile to site changes.
- TMDB enrichment requires `TMDB_READ_ACCESS_TOKEN` to be set. If missing, enrichment is silently skipped (movies remain without TMDB data).
- TMDB search issues **one** request per title variant. Retrying the same query in other languages was tried and removed: TMDB's index spans alternative and translated titles, so English titles resolve fine under `es-LA`. The `language` parameter is still kept because it reorders results for ambiguous titles, and only the top hit is used.
- Titles TMDB cannot match (TV-series arcs like Bleach, non-films like a football match) stay unenriched. Each miss bumps `tmdb_attempts`; after `MAX_TMDB_ATTEMPTS` (3) the title stops being retried, so a permanently unmatchable title costs 3 lookups total rather than a few on every run forever.
- TMDB ranks search results by textual relevance, which for a *current* cartelera sometimes floats an obscure old film above the one actually showing — "Código: Venganza" matched a 2002 film with popularity 1.2 over the 2026 release billed under exactly that title in Ecuador. When the top hit is below `_LOW_POPULARITY`, enrichment prefers a candidate whose **registered alternative title** matches the scraped title exactly, then a dramatically more popular recent release. It never rejects a match: worst case TMDB's own pick stands.
- Fuzzy title similarity was tried as a guard and **rejected**: Ecuadorian cinemas bill films under localized titles that share almost no characters with TMDB's (`La Noche Del Demonio 6` → `Insidious: Fuera del más allá`, `Moana Live Action` → `Vaiana`). Measured against the real catalogue, no threshold separated good matches from bad — it discarded 10 correct matches out of 43 while missing the case that motivated it.
- TMDB deduplication: if two scrapers produce different raw titles for the same film, they start as separate `Movie` rows. Enrichment merges them when both resolve to the same `tmdb_id` by redirecting `Screening.movie_id` to the canonical row and deleting the duplicate.
