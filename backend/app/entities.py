from dataclasses import dataclass
from datetime import datetime


@dataclass
class CinemaCompany:
    name: str
    base_url: str


@dataclass
class CinemaComplex:
    name: str
    url_part: str
    company: CinemaCompany
    city: str = ""


@dataclass
class Movie:
    title: str
    tmdb_id: int | None = None
    tmdb_title: str | None = None
    poster_path: str | None = None
    overview: str | None = None
    runtime: int | None = None
    certification: str | None = None
    release_date: str | None = None


@dataclass
class Screening:
    datetime: datetime
    format: str
    language: str
    complex: CinemaComplex
    movie: Movie
    id: int = 0
