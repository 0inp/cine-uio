import os

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import get_all_screenings, get_db
from app.entities import Screening
from app.schemas import (
    CinemaCompanySchema,
    CinemaComplexSchema,
    MovieSchema,
    ScreeningSchema,
)

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

    screenings: list[Screening] = get_all_screenings(db, cinema_company_name, cinema_complex_name)

    # Convert dataclass entities to dictionaries
    screenings_schemas: list[ScreeningSchema] = []
    for screening in screenings:
        screening_schema = ScreeningSchema(
            datetime=screening.datetime,
            format=screening.format,
            language=screening.language,
            complex=CinemaComplexSchema(
                name=screening.complex.name,
                url_part=screening.complex.url_part,
                company=CinemaCompanySchema(
                    name=screening.complex.company.name,
                    base_url=screening.complex.company.base_url,
                ),
            ),
            movie=MovieSchema(title=screening.movie.title),
        )
        screenings_schemas.append(screening_schema)

    return screenings_schemas
