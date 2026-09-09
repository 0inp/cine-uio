from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field

_TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


class CinemaCompanySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    base_url: str


class CinemaComplexSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
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
