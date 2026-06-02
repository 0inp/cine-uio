from typing import Optional

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import database, models, entities
from app.entities import CinemaCompany, CinemaComplex, Movie, Screening

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/api/movies")
def get_movies(
    cinema_company: Optional[str] = Query(None),
    cinema_complex: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = (
        db.query(
            models.Movie.title,
            models.CinemaComplex.name.label("cinema_complex"),
            models.CinemaCompany.name.label("cinema_company"),
            models.Screening.datetime,
            models.Screening.format,
            models.Screening.language,
        )
        .join(models.Screening, models.Movie.id == models.Screening.movie_id)
        .join(
            models.CinemaComplex, models.Screening.complex_id == models.CinemaComplex.id
        )
        .join(
            models.CinemaCompany,
            models.CinemaComplex.company_id == models.CinemaCompany.id,
        )
    )

    if cinema_company:
        query = query.filter(models.CinemaCompany.name == cinema_company)
    if cinema_complex:
        query = query.filter(models.CinemaComplex.name == cinema_complex)

    results = query.all()

    movies_dict = {}
    for movie_title, complex_name, company_name, datetime, format, language in results:
        if movie_title not in movies_dict:
            movies_dict[movie_title] = {}
        if complex_name not in movies_dict[movie_title]:
            movies_dict[movie_title][complex_name] = {
                "cinema_company": company_name,
                "screenings": [],
            }
        movies_dict[movie_title][complex_name]["screenings"].append(
            {"datetime": datetime, "format": format, "language": language}
        )

    return movies_dict
