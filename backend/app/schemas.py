from datetime import datetime

from pydantic import BaseModel


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
    datetime: datetime
    format: str
    language: str
    complex: CinemaComplexSchema
    movie: MovieSchema

    class Config:
        from_attributes = True
