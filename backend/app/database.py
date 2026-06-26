import os
from collections.abc import Generator

from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session, contains_eager, selectinload, sessionmaker

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

SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./cine_uio.db")

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session]:
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
            selectinload(ScreeningModel.movie),
            selectinload(ScreeningModel.complex).selectinload(CinemaComplexModel.company),
        )
        .order_by(ScreeningModel.datetime)
    )

    if cinema_company_name or cinema_complex_name:
        query = query.join(ScreeningModel.complex)

    if cinema_company_name:
        query = query.join(CinemaComplexModel.company).where(CinemaCompanyModel.name == cinema_company_name)

    if cinema_complex_name:
        query = query.where(CinemaComplexModel.name == cinema_complex_name)

    result = db.execute(query)
    orm_screenings: list[ScreeningModel] = list(result.scalars().all())

    companies: dict[int, CinemaCompany] = {}
    complexes: dict[int, CinemaComplex] = {}
    movies: dict[int, Movie] = {}

    for s in orm_screenings:
        if s.movie.id not in movies:
            movies[s.movie.id] = Movie(title=s.movie.title)

        if s.complex.company.id not in companies:
            companies[s.complex.company.id] = CinemaCompany(
                name=s.complex.company.name,
                base_url=s.complex.company.base_url,
            )

        if s.complex.id not in complexes:
            complexes[s.complex.id] = CinemaComplex(
                name=s.complex.name,
                url_part=s.complex.url_part,
                company=companies[s.complex.company.id],
            )

    return [
        Screening(
            id=s.id,
            datetime=s.datetime,
            format=s.format,
            language=s.language,
            complex=complexes[s.complex.id],
            movie=movies[s.movie.id],
        )
        for s in orm_screenings
    ]


def get_all_cinema_companies(db: Session, cinema_company_name: str | None = None) -> list[CinemaCompany]:
    query = select(CinemaCompanyModel)
    if cinema_company_name:
        query = query.where(CinemaCompanyModel.name == cinema_company_name)
    result = db.execute(query)
    orm_companies = result.unique().scalars().all()

    return [
        CinemaCompany(name=orm_company.name, base_url=orm_company.base_url)
        for orm_company in orm_companies
    ]


def get_all_cinema_complexes_from_cinema_company(db: Session, cinema_company_name: str) -> list[CinemaComplex]:
    query = (
        select(CinemaComplexModel)
        .join(CinemaComplexModel.company)
        .where(CinemaCompanyModel.name == cinema_company_name)
        .options(contains_eager(CinemaComplexModel.company))
    )
    result = db.execute(query)
    orm_complexes = result.unique().scalars().all()

    return [
        CinemaComplex(
            name=orm_complex.name,
            url_part=orm_complex.url_part,
            company=CinemaCompany(
                name=orm_complex.company.name,
                base_url=orm_complex.company.base_url,
            ),
        )
        for orm_complex in orm_complexes
    ]


def save_screenings(db: Session, screenings: list[Screening]) -> None:
    existing_movies_result = db.execute(select(MovieModel))
    existing_movies: dict[str, int] = {
        movie.title: movie.id for movie in existing_movies_result.scalars().all()
    }

    existing_complexes_result = db.execute(select(CinemaComplexModel))
    existing_complexes: dict[str, int] = {
        complex.name: complex.id for complex in existing_complexes_result.scalars().all()
    }

    for screening in screenings:
        if screening.movie.title not in existing_movies:
            new_movie = MovieModel(title=screening.movie.title)
            db.add(new_movie)
            db.flush()
            db.refresh(new_movie)
            existing_movies[screening.movie.title] = new_movie.id

        movie_model_id = existing_movies[screening.movie.title]

        if screening.complex.name not in existing_complexes:
            raise ValueError(
                f"Complex {screening.complex.name} with company {screening.complex.company.name} not found in the database."
            )
        complex_model_id = existing_complexes[screening.complex.name]

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
    db.execute(delete(ScreeningModel))
    db.commit()
