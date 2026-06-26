import os

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import get_all_screenings, get_db
from app.schemas import ScreeningSchema

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
    db: Session = Depends(get_db),
) -> list[ScreeningSchema]:
    screenings = get_all_screenings(db, cinema_company_name, cinema_complex_name)
    return [ScreeningSchema.model_validate(s) for s in screenings]
