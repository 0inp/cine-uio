import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import Depends, FastAPI, Query  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.database import get_all_cities, get_all_screenings, get_db  # noqa: E402
from app.logging import logger  # noqa: E402
from app.observability import current_health  # noqa: E402
from app.schemas import HealthSchema, ScreeningSchema  # noqa: E402

app = FastAPI()

_raw_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173")
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/screenings", response_model=list[ScreeningSchema])
def get_screenings(
    cinema_company_name: str | None = Query(None),
    cinema_complex_name: str | None = Query(None),
    city: str | None = Query(None, description="Restrict to one city; the payload is large without it"),
    db: Session = Depends(get_db),
) -> list[ScreeningSchema]:
    screenings = get_all_screenings(db, cinema_company_name, cinema_complex_name, city)
    return [ScreeningSchema.model_validate(s) for s in screenings]


@app.get("/api/cities", response_model=list[str])
def get_cities(db: Session = Depends(get_db)) -> list[str]:
    return get_all_cities(db)


@app.get("/api/health", response_model=HealthSchema)
def get_health(db: Session = Depends(get_db)) -> HealthSchema:
    """Always 200: the payload carries the verdict, so a monitor reads `status`.

    Returning 5xx for stale data would make the API look down when it is merely
    serving old listings, which is a different problem with a different fix.
    """
    return HealthSchema.model_validate(current_health(db))


SERVE_FRONTEND_ENV_VAR = "CINE_UIO_SERVE_FRONTEND"
_OFF = {"0", "false", "no"}


def _serving_is_switched_off() -> bool:
    """Default to serving: production must not depend on a variable being set."""
    return os.environ.get(SERVE_FRONTEND_ENV_VAR, "1").strip().lower() in _OFF


def mount_frontend(app: FastAPI, dist_dir: Path) -> bool:
    """Serve the built SPA from the same origin as the API, if it has been built.

    A single origin means one Tailscale Serve target, no CORS, and a frontend that
    keeps working whatever hostname it is reached through — VITE_API_URL is the
    relative "/api". Mounted last so the API routes above match first.

    Returns False when there is no build, or when serving is switched off. A build
    is a snapshot taken at some point in the past and nothing about the page it
    renders says how old it is, so the two ways of ending up with a stale one are
    closed here: development opts out of serving entirely, and a mount that does
    happen announces the build's date.
    """
    index = dist_dir / "index.html"

    if _serving_is_switched_off():
        if index.is_file():
            logger.info(f"Not serving {dist_dir}: {SERVE_FRONTEND_ENV_VAR} is off (the SPA is Vite's job in dev)")
        return False

    if not index.is_file():
        return False

    built = datetime.fromtimestamp(index.stat().st_mtime)
    logger.info(f"Serving the SPA from {dist_dir}, built {built:%Y-%m-%d %H:%M}")
    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="frontend")
    return True


FRONTEND_DIST = Path(os.environ.get("FRONTEND_DIST", Path(__file__).resolve().parents[2] / "frontend" / "dist"))
mount_frontend(app, FRONTEND_DIST)
