from collections.abc import Generator
from datetime import datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base
from app.models import CinemaCompany as CinemaCompanyModel
from app.models import CinemaComplex as CinemaComplexModel
from app.models import Movie as MovieModel
from app.models import Screening as ScreeningModel


@pytest.fixture
def db() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Sess = sessionmaker(bind=engine)
    session = Sess()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def bare_db(db: Session) -> Session:
    """Companies and complexes seeded; no movies or screenings."""
    company1 = CinemaCompanyModel(name="Multicines", base_url="https://www.multicines.com.ec")
    company2 = CinemaCompanyModel(name="Supercines", base_url="https://www.supercines.com")
    db.add_all([company1, company2])
    db.flush()

    db.add_all([
        CinemaComplexModel(name="CCI", url_part="/?cityId=19&storeId=3555", company_id=company1.id),
        CinemaComplexModel(name="San Luis", url_part="/cartelera/quito/san-luis/216", company_id=company2.id),
    ])
    db.commit()
    return db


@pytest.fixture
def seeded_db(bare_db: Session) -> Session:
    """Adds one movie + screening per complex on top of bare_db."""
    cci_id = bare_db.execute(select(CinemaComplexModel.id).where(CinemaComplexModel.name == "CCI")).scalar_one()
    san_luis_id = bare_db.execute(
        select(CinemaComplexModel.id).where(CinemaComplexModel.name == "San Luis")
    ).scalar_one()

    movie1 = MovieModel(title="Toy Story 5")
    movie2 = MovieModel(title="Supergirl")
    bare_db.add_all([movie1, movie2])
    bare_db.flush()

    bare_db.add_all([
        ScreeningModel(
            datetime=datetime(2026, 6, 25, 14, 30),
            format="2D",
            language="Doblada",
            complex_id=cci_id,
            movie_id=movie1.id,
        ),
        ScreeningModel(
            datetime=datetime(2026, 6, 25, 20, 0),
            format="3D",
            language="Subtitulada",
            complex_id=san_luis_id,
            movie_id=movie2.id,
        ),
    ])
    bare_db.commit()
    return bare_db
