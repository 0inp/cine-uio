from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class CinemaCompany(Base):
    __tablename__ = "cinema_companies"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    base_url = Column(String, nullable=False)

    complexes = relationship("CinemaComplex", back_populates="company")


class CinemaComplex(Base):
    __tablename__ = "cinema_complexes"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    url_part = Column(String, nullable=False)
    company_id = Column(Integer, ForeignKey("cinema_companies.id"), nullable=False)

    company = relationship("CinemaCompany", back_populates="complexes")
    screenings = relationship("Screening", back_populates="complex")


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)

    screenings = relationship("Screening", back_populates="movie")


class Screening(Base):
    __tablename__ = "screenings"

    id = Column(Integer, primary_key=True)
    datetime = Column(DateTime, nullable=False)
    format = Column(String, nullable=False)
    language = Column(String, nullable=False)
    complex_id = Column(Integer, ForeignKey("cinema_complexes.id"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)

    complex = relationship("CinemaComplex", back_populates="screenings")
    movie = relationship("Movie", back_populates="screenings")
