from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, computed_field

_TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


class CinemaCompanySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    base_url: str


class CinemaComplexSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    city: str
    url_part: str
    company: CinemaCompanySchema


class MovieSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    tmdb_id: int | None = None
    tmdb_title: str | None = None
    poster_path: str | None = None
    overview: str | None = None
    runtime: int | None = None
    certification: str | None = None
    release_date: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def poster_url(self) -> str | None:
        if self.poster_path:
            return f"{_TMDB_IMAGE_BASE_URL}{self.poster_path}"
        return None


class ScreeningSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    datetime: datetime
    format: str
    language: str
    complex: CinemaComplexSchema
    movie: MovieSchema


class HealthSchema(BaseModel):
    """Whether what the site is serving can be trusted, and why."""

    model_config = ConfigDict(from_attributes=True)

    status: Literal["ok", "stale", "failing", "unknown"]
    detail: str
    last_run_at: datetime | None
    last_success_at: datetime | None
    hours_since_success: float | None
    complexes_total: int
    complexes_with_screenings: int
    upcoming_screenings: int
