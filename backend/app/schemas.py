from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CinemaCompanySchema(BaseModel):
    name: str
    base_url: str


class CinemaComplexSchema(BaseModel):
    name: str
    url_part: str
    company: CinemaCompanySchema


class MovieSchema(BaseModel):
    title: str


class ScreeningSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    datetime: datetime
    format: str
    language: str
    complex: CinemaComplexSchema
    movie: MovieSchema
