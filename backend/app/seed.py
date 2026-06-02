from database import SessionLocal
from models import CinemaCompany, CinemaComplex
from sqlalchemy.orm import Session


def seed_database():
    db: Session = SessionLocal()

    # Seed CinemaCompany
    multicines = CinemaCompany(
        name="Multicines", base_url="https://www.multicines.com.ec"
    )
    supercines = CinemaCompany(name="Supercines", base_url="https://www.supercines.com")

    db.add(multicines)
    db.add(supercines)
    db.commit()

    # Seed CinemaComplex for Multicines
    cci = CinemaComplex(
        name="CCI", url_part="/?cityId=19&storeId=3555", company_id=multicines.id
    )
    plaza_americas = CinemaComplex(
        name="Plaza Americas",
        url_part="/?cityId=19&storeId=3566",
        company_id=multicines.id,
    )

    db.add(cci)
    db.add(plaza_americas)

    # Seed CinemaComplex for Supercines
    san_luis = CinemaComplex(
        name="San Luis",
        url_part="/cartelera/quito/san-luis/216",
        company_id=supercines.id,
    )
    seis_de_diciembre = CinemaComplex(
        name="6 de Diciembre",
        url_part="/cartelera/quito/6-de-diciembre/187",
        company_id=supercines.id,
    )

    db.add(san_luis)
    db.add(seis_de_diciembre)

    db.commit()
    db.close()


if __name__ == "__main__":
    seed_database()
