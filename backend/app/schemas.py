from datetime import datetime

from pydantic import BaseModel, ConfigDict


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


class ScreeningSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    datetime: datetime
    format: str
    language: str
    complex: CinemaComplexSchema
    movie: MovieSchema
