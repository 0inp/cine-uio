import datetime as _dt

from sqlalchemy import ForeignKey, String, UniqueConstraint
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
    # Screenings are attributed to a complex by (company, name), so a chain opening a
    # second venue under an existing name must fail loudly at seed time rather than
    # silently folding its listings into the other one.
    __table_args__ = (UniqueConstraint("company_id", "name", name="uq_complex_company_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    city: Mapped[str] = mapped_column(String, index=True)
    url_part: Mapped[str] = mapped_column(String)
    company_id: Mapped[int] = mapped_column(ForeignKey("cinema_companies.id"))

    company: Mapped[CinemaCompany] = relationship(back_populates="complexes")
    screenings: Mapped[list[Screening]] = relationship(back_populates="complex")


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String)
    tmdb_id: Mapped[int | None] = mapped_column(nullable=True, unique=True, index=True)
    tmdb_title: Mapped[str | None] = mapped_column(String, nullable=True)
    poster_path: Mapped[str | None] = mapped_column(String, nullable=True)
    overview: Mapped[str | None] = mapped_column(String, nullable=True)
    runtime: Mapped[int | None] = mapped_column(nullable=True)
    certification: Mapped[str | None] = mapped_column(String, nullable=True)
    release_date: Mapped[str | None] = mapped_column(String, nullable=True)
    # Bookkeeping only, never exposed through the API: how many times TMDB has been
    # asked about this title. Lets enrichment stop retrying titles TMDB cannot resolve.
    tmdb_attempts: Mapped[int] = mapped_column(default=0, server_default="0")

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
