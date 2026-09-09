# Cine UIO

Movie screening aggregator for Quito, Ecuador — scrapes Multicines and Supercines, stores in SQLite, serves via FastAPI, displayed in React.

## Key Files

- `docs/CONTEXT.md` — full domain glossary, architecture diagram, data flow, run instructions
- `docs/hosting.md` — deferred plan for public hosting (Neon + Fly + Cloudflare Pages); production is a laptop for now
- `backend/app/api.py` — single FastAPI route: `GET /api/screenings`
- `backend/app/database.py` — all DB query helpers + session management
- `backend/app/scrapers/` — `base.py` (abstract + registry), `multicines.py`, `supercines.py`
- `frontend/src/App.tsx` — entire frontend (fetch → filter today → group → render)

## Commands

```bash
# Backend
cd backend
uv run alembic upgrade head          # migrate DB (run once per fresh clone)
uv run python -m app.seed            # seed companies & complexes (run once)
uv run python scraper_entrypoint.py  # refresh screenings
uv run uvicorn app.api:app --reload  # dev server on :8000

# Frontend
cd frontend && bun dev               # dev server on :5173

# From root (mise)
mise lint    # mypy + ruff + biome
mise format  # ruff format + biome write
mise test    # pytest + vitest

mise run install_hooks  # install the pre-commit hook (once per clone)

mise run dev     # API + Vite dev servers (two origins, CORS applies)
mise run start   # build SPA, serve it + API from :8000 (single origin) — "prod"
mise run serve   # expose :8000 on the tailnet over HTTPS
mise run scrape  # refresh screenings + TMDB metadata
```

## Production

Production is this laptop, served over Tailscale — see `docs/CONTEXT.md`.
The daily refresh is a launchd agent: `./ops/install-scrape-agent.sh`.

## Conventions

- Python: `uv` for package management, `ruff` for lint/format, `mypy` for type checking (strict)
- Frontend: `bun`, `biome` for lint/format, `vitest` for tests
- Domain dataclasses live in `entities.py`; ORM models in `models.py`; Pydantic schemas in `schemas.py`
- All scraper subclasses self-register via `__init_subclass__` in `base.py`

## Environment Variables

| Variable                 | Default                     | Where                       |
|--------------------------|-----------------------------|-----------------------------|
| `VITE_API_URL`           | `http://localhost:8000/api` | frontend                    |
| `ALLOWED_ORIGINS`        | `http://localhost:5173`     | backend CORS                |
| `TMDB_READ_ACCESS_TOKEN` | *(required)*                | backend — TMDB Bearer token |
