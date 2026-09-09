import os
from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine, delete, event, select
from sqlalchemy import update as sa_update
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, contains_eager, selectinload, sessionmaker

from app.entities import (
    CinemaCompany,
    CinemaComplex,
    Movie,
    Screening,
)
from app.logging import logger
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

# How many times a title may be looked up on TMDB before we stop retrying it.
MAX_TMDB_ATTEMPTS = 3


def configure_sqlite(engine: Engine) -> None:
    """Put SQLite connections in WAL mode with a patient lock timeout.

    The daily scrape deletes and rewrites every screening while the API may be
    serving requests. SQLite's default `delete` journal mode has a writer block
    readers outright; WAL lets them run concurrently. busy_timeout then makes the
    rare genuine contention wait rather than fail immediately.

    A no-op on other backends, so it stays correct if this ever moves to Postgres.
    """
    if not engine.url.get_backend_name().startswith("sqlite"):
        return

    @event.listens_for(engine, "connect")
    def _set_pragmas(dbapi_connection: Any, _record: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()


engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
configure_sqlite(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_all_cities(db: Session) -> list[str]:
    """Distinct cities that have at least one complex, alphabetically."""
    rows = db.execute(select(CinemaComplexModel.city).distinct().order_by(CinemaComplexModel.city)).scalars().all()
    return [city for city in rows if city]


def get_all_screenings(
    db: Session,
    cinema_company_name: str | None = None,
    cinema_complex_name: str | None = None,
    city: str | None = None,
) -> list[Screening]:
    query = (
        select(ScreeningModel)
        .options(
            selectinload(ScreeningModel.movie),
            selectinload(ScreeningModel.complex).selectinload(CinemaComplexModel.company),
        )
        .order_by(ScreeningModel.datetime)
    )

    if cinema_company_name or cinema_complex_name or city:
        query = query.join(ScreeningModel.complex)

    if city:
        query = query.where(CinemaComplexModel.city == city)

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
            movies[s.movie.id] = Movie(
                title=s.movie.title,
                tmdb_id=s.movie.tmdb_id,
                tmdb_title=s.movie.tmdb_title,
                poster_path=s.movie.poster_path,
                overview=s.movie.overview,
                runtime=s.movie.runtime,
                certification=s.movie.certification,
                release_date=s.movie.release_date,
            )

        if s.complex.company.id not in companies:
            companies[s.complex.company.id] = CinemaCompany(
                name=s.complex.company.name,
                base_url=s.complex.company.base_url,
            )

        if s.complex.id not in complexes:
            complexes[s.complex.id] = CinemaComplex(
                name=s.complex.name,
                city=s.complex.city,
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

    return [CinemaCompany(name=orm_company.name, base_url=orm_company.base_url) for orm_company in orm_companies]


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
            city=orm_complex.city,
            url_part=orm_complex.url_part,
            company=CinemaCompany(
                name=orm_complex.company.name,
                base_url=orm_complex.company.base_url,
            ),
        )
        for orm_complex in orm_complexes
    ]


def _complex_ids_by_company_and_name(db: Session) -> dict[tuple[str, str], int]:
    """Complex ids keyed by (company name, complex name).

    Keyed on the pair, not the complex name alone: two chains can bill a complex
    with the same name, and a name-only lookup would silently attribute one's
    screenings to the other.
    """
    rows = db.execute(
        select(CinemaCompanyModel.name, CinemaComplexModel.name, CinemaComplexModel.id).join(CinemaComplexModel.company)
    ).all()
    return {(company_name, complex_name): complex_id for company_name, complex_name, complex_id in rows}


def _insert_screenings(db: Session, screenings: list[Screening]) -> None:
    """Add screenings to the session without committing, creating movies as needed."""
    movie_ids: dict[str, int] = {movie.title: movie.id for movie in db.execute(select(MovieModel)).scalars().all()}
    complex_ids = _complex_ids_by_company_and_name(db)

    for screening in screenings:
        title = screening.movie.title
        if title not in movie_ids:
            new_movie = MovieModel(title=title)
            db.add(new_movie)
            db.flush()
            movie_ids[title] = new_movie.id

        company_name = screening.complex.company.name
        complex_key = (company_name, screening.complex.name)
        if complex_key not in complex_ids:
            raise ValueError(f"Complex {screening.complex.name} with company {company_name} not found in the database.")

        db.add(
            ScreeningModel(
                datetime=screening.datetime,
                format=screening.format,
                language=screening.language,
                complex_id=complex_ids[complex_key],
                movie_id=movie_ids[title],
            )
        )


def save_screenings(db: Session, screenings: list[Screening]) -> None:
    _insert_screenings(db, screenings)
    db.commit()


def replace_screenings_for_complex(
    db: Session, company_name: str, complex_name: str, screenings: list[Screening]
) -> None:
    """Swap one complex's screenings in a single transaction.

    The delete and the inserts commit together, so a request arriving mid-scrape sees
    either the previous cartelera or the new one, never an empty one. Scoped to a
    single complex so that a chain or a venue failing to scrape leaves the others —
    and its own previous screenings — untouched.
    """
    complex_id = _complex_ids_by_company_and_name(db).get((company_name, complex_name))
    if complex_id is None:
        raise ValueError(f"Complex {complex_name} with company {company_name} not found in the database.")

    try:
        db.execute(delete(ScreeningModel).where(ScreeningModel.complex_id == complex_id))
        _insert_screenings(db, screenings)
        db.commit()
    except Exception:
        db.rollback()
        raise


def enrich_movies_with_tmdb(db: Session) -> None:
    """Fetch TMDB metadata for movies that lack it, merging duplicates by tmdb_id.

    Titles TMDB cannot resolve (TV-series arcs like Bleach, or non-films like a football
    match) would otherwise be re-queried on every single run, forever. Each miss bumps
    tmdb_attempts and the movie leaves the queue once it hits MAX_TMDB_ATTEMPTS — a few
    retries still give a genuinely new release time to appear in TMDB's catalogue.

    Progress is committed per movie so a crash mid-run keeps the API work already done.
    """
    from app.tmdb import search_movie  # local import avoids circular dependency at module load

    unenriched: list[MovieModel] = list(
        db.execute(
            select(MovieModel).where(
                MovieModel.tmdb_id.is_(None),
                MovieModel.tmdb_attempts < MAX_TMDB_ATTEMPTS,
            )
        )
        .scalars()
        .all()
    )
    logger.info(f"TMDB enrichment: {len(unenriched)} movies to look up")

    for movie in unenriched:
        result = search_movie(movie.title)

        if result is None:
            movie.tmdb_attempts += 1
            if movie.tmdb_attempts >= MAX_TMDB_ATTEMPTS:
                logger.info(f"TMDB: giving up on '{movie.title}' after {MAX_TMDB_ATTEMPTS} attempts")
            db.commit()
            continue

        existing: MovieModel | None = db.execute(
            select(MovieModel).where(
                MovieModel.tmdb_id == result.tmdb_id,
                MovieModel.id != movie.id,
            )
        ).scalar_one_or_none()

        if existing is not None:
            logger.info(f"Merging '{movie.title}' → '{existing.title}' (tmdb_id={result.tmdb_id})")
            db.execute(
                sa_update(ScreeningModel).where(ScreeningModel.movie_id == movie.id).values(movie_id=existing.id)
            )
            db.delete(movie)
        else:
            movie.tmdb_id = result.tmdb_id
            movie.tmdb_title = result.tmdb_title
            movie.poster_path = result.poster_path
            movie.overview = result.overview
            movie.runtime = result.runtime
            movie.certification = result.certification
            movie.release_date = result.release_date

        # Commit rather than flush: keeps progress durable and makes tmdb_id visible
        # to the duplicate check of every later movie in this same run.
        db.commit()

    logger.info("TMDB enrichment complete")
