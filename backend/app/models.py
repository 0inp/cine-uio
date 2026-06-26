import datetime as _dt

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class CinemaCompany(Base):
    __tablename__ = "cinema_companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    base_url: Mapped[str] = mapped_column(String)

    complexes: Mapped[list[CinemaComplex]] = relationship(back_populates="company")


class CinemaComplex(Base):
    __tablename__ = "cinema_complexes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    url_part: Mapped[str] = mapped_column(String)
    company_id: Mapped[int] = mapped_column(ForeignKey("cinema_companies.id"))

    company: Mapped[CinemaCompany] = relationship(back_populates="complexes")
    screenings: Mapped[list[Screening]] = relationship(back_populates="complex")


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String)

    screenings: Mapped[list[Screening]] = relationship(back_populates="movie")


class Screening(Base):
    __tablename__ = "screenings"

    id: Mapped[int] = mapped_column(primary_key=True)
    datetime: Mapped[_dt.datetime] = mapped_column()
    format: Mapped[str] = mapped_column(String)
    language: Mapped[str] = mapped_column(String)
    complex_id: Mapped[int] = mapped_column(ForeignKey("cinema_complexes.id"))
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"))

    complex: Mapped[CinemaComplex] = relationship(back_populates="screenings")
    movie: Mapped[Movie] = relationship(back_populates="screenings")
