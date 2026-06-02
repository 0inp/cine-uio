from typing import List

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import get_all_screenings, get_db
from app.entities import Screening
from app.schemas import ScreeningSchema

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/screenings", response_model=List[ScreeningSchema])
def get_screenings(
    cinema_company_name: str | None = Query(None),
    cinema_complex_name: str | None = Query(None),
    db: Session = Depends(get_db),
):

    screenings: list[Screening] = get_all_screenings(
        db, cinema_company_name, cinema_complex_name
    )

    # Convert dataclass entities to dictionaries
    screenings_dicts = []
    for screening in screenings:
        screening_dict = {
            "datetime": screening.datetime.isoformat(),
            "format": screening.format,
            "language": screening.language,
            "complex": {
                "name": screening.complex.name,
                "url_part": screening.complex.url_part,
                "company": {
                    "name": screening.complex.company.name,
                    "base_url": screening.complex.company.base_url,
                },
            },
            "movie": {
                "title": screening.movie.title,
            },
        }
        screenings_dicts.append(screening_dict)

    # Convert dictionaries to Pydantic models
    return [ScreeningSchema(**screening_dict) for screening_dict in screenings_dicts]
