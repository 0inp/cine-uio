import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import Depends, FastAPI, Query  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.database import get_all_cities, get_all_screenings, get_db  # noqa: E402
from app.schemas import ScreeningSchema  # noqa: E402

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


def mount_frontend(app: FastAPI, dist_dir: Path) -> bool:
    """Serve the built SPA from the same origin as the API, if it has been built.

    A single origin means one Tailscale Serve target, no CORS, and a frontend that
    keeps working whatever hostname it is reached through — VITE_API_URL is the
    relative "/api". Mounted last so the API routes above match first.

    Returns False when there is no build, which is the normal case in development:
    Vite then serves the frontend on its own port and CORS applies.
    """
    if not (dist_dir / "index.html").is_file():
        return False
    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="frontend")
    return True


FRONTEND_DIST = Path(os.environ.get("FRONTEND_DIST", Path(__file__).resolve().parents[2] / "frontend" / "dist"))
mount_frontend(app, FRONTEND_DIST)
