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


@dataclass
class Movie:
    title: str


@dataclass
class Screening:
    datetime: datetime
    format: str
    language: str
    complex: CinemaComplex
    movie: Movie