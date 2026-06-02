from datetime import datetime
from typing import cast

from sqlalchemy import create_engine, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, joinedload, sessionmaker

from app.entities import (
    CinemaCompany,
    CinemaComplex,
    Movie,
    Screening,
)
from app.models import (
    CinemaCompany as CinemaCompanyModel,
)
from app.models import (
    CinemaComplex as CinemaComplexModel,
)
from app.models import (
    Movie as MovieModel,
)
from app.models import (
    Screening as ScreeningModel,
)

SQLALCHEMY_DATABASE_URL = "sqlite:///./cine_uio.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_all_screenings(
    db: Session,
    cinema_company_name: str | None = None,
    cinema_complex_name: str | None = None,
) -> list[Screening]:
    query = (
        select(ScreeningModel)
        .options(
            joinedload(ScreeningModel.movie),
            joinedload(ScreeningModel.complex).joinedload(CinemaComplexModel.company),
        )
        .order_by(ScreeningModel.datetime)
    )

    if cinema_company_name:
        query = (
            query.join(ScreeningModel.complex)
            .join(CinemaComplexModel.company)
            .where(CinemaCompanyModel.name == cinema_company_name)
        )
    if cinema_complex_name:
        query = query.join(ScreeningModel.complex).where(
            CinemaComplexModel.name == cinema_complex_name
        )

    result = db.execute(query)
    orm_screenings: list[ScreeningModel] = list(result.scalars().all())

    companies = {}
    complexes = {}
    movies = {}

    for s in orm_screenings:
        if s.movie.id not in movies:
            movies[s.movie.id] = Movie(title=s.movie.title)

        if s.complex.company.id not in companies:
            companies[s.complex.company.id] = CinemaCompany(
                name=s.complex.company.name,
                base_url=s.complex.company.base_url,
                # complexes=[],
            )

        if s.complex.id not in complexes:
            complex_entity = CinemaComplex(
                name=s.complex.name,
                url_part=s.complex.url_part,
                company=companies[s.complex.company.id],
            )
            complexes[s.complex.id] = complex_entity

    return [
        Screening(
            datetime=cast(datetime, s.datetime),
            format=cast(str, s.format),
            language=cast(str, s.language),
            complex=complexes[s.complex.id],
            movie=movies[s.movie.id],
        )
        for s in orm_screenings
    ]


def get_all_cinema_companies(
    db: Session, cinema_company_name: str | None = None
) -> list[CinemaCompany]:
    query = select(CinemaCompanyModel)
    if cinema_company_name:
        query = query.where(CinemaCompanyModel.name == cinema_company_name)
    result = db.execute(query)
    orm_companies = result.unique().scalars().all()

    companies = []
    for orm_company in orm_companies:
        company_entity = CinemaCompany(
            name=cast(str, orm_company.name),
            base_url=cast(str, orm_company.base_url),
        )
        companies.append(company_entity)

    return companies


def get_all_cinema_complexes_from_cinema_company(
    db: Session, cinema_company_name: str
) -> list[CinemaComplex]:
    query = (
        select(CinemaComplexModel)
        .join(CinemaComplexModel.company)
        .where(CinemaCompanyModel.name == cinema_company_name)
    )
    result = db.execute(query)
    orm_complexes = result.unique().scalars().all()

    complexes = []
    for orm_complex in orm_complexes:
        complex_entity = CinemaComplex(
            name=str(orm_complex.name),
            url_part=str(orm_complex.url_part),
            company=CinemaCompany(
                name=cast(str, orm_complex.company.name),
                base_url=cast(str, orm_complex.company.base_url),
            ),
        )
        complexes.append(complex_entity)

    return complexes


def save_screenings(db: Session, screenings: list[Screening]) -> None:
    # Fetch all existing movies in a single query
    existing_movies_result = db.execute(select(MovieModel))
    existing_movies: dict[str, int] = {
        str(movie.title): cast(int, movie.id)
        for movie in existing_movies_result.scalars().all()
    }

    # Fetch all existing complexes in a single query
    existing_complexes_result = db.execute(select(CinemaComplexModel))
    existing_complexes: dict[str, int] = {
        cast(str, complex.name): cast(int, complex.id)
        for complex in existing_complexes_result.scalars().all()
    }

    for screening in screenings:
        # Check if the movie already exists in the database
        if screening.movie.title not in existing_movies:
            new_movie = MovieModel(title=screening.movie.title)
            db.add(new_movie)
            db.flush()
            db.refresh(new_movie)
            existing_movies[screening.movie.title] = cast(int, new_movie.id)

        # Get the existing movie model
        movie_model_id = existing_movies[screening.movie.title]

        # Find the complex model
        if screening.complex.name not in existing_complexes:
            raise ValueError(
                f"Complex {screening.complex.name} with company {screening.complex.company.name} not found in the database."
            )
        complex_model_id = existing_complexes[screening.complex.name]

        # Create and save the screening
        screening_model = ScreeningModel(
            datetime=screening.datetime,
            format=screening.format,
            language=screening.language,
            complex_id=complex_model_id,
            movie_id=movie_model_id,
        )
        db.add(screening_model)

    db.commit()


def delete_all_screenings(db: Session) -> None:
    db.query(ScreeningModel).delete()
    db.commit()
