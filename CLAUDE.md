# Cine UIO

Movie screening aggregator for Quito, Ecuador — scrapes Multicines and Supercines, stores in SQLite, serves via FastAPI, displayed in React.

## Key Files

- `docs/CONTEXT.md` — full domain glossary, architecture diagram, data flow, run instructions
- `ARCHITECTURE_PLAN.md` — backlog of planned improvements (service layer extraction, hooks, components)
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
```

## Conventions

- Python: `uv` for package management, `ruff` for lint/format, `mypy` for type checking (strict)
- Frontend: `bun`, `biome` for lint/format, `vitest` for tests
- Domain dataclasses live in `entities.py`; ORM models in `models.py`; Pydantic schemas in `schemas.py`
- All scraper subclasses self-register via `__init_subclass__` in `base.py`

## Environment Variables

| Variable          | Default                     | Where         |
|-------------------|-----------------------------|---------------|
| `VITE_API_URL`    | `http://localhost:8000/api` | frontend      |
| `ALLOWED_ORIGINS` | `http://localhost:5173`     | backend CORS  |
