"""Seed the cinema chains and their complexes.

The complex lists are static. Both chains do expose a discoverable venue list
(Multicines at `api/v3/stores?accountId=19`, Supercines as `initialTheaters`
embedded in any cartelera page), so this could be discovered at scrape time
instead. It is hardcoded by choice — with 49 venues across 20 cities, expect this
list to go stale silently when a chain opens or closes one. Re-run this module
after updating it; it upserts, so it is safe to run repeatedly.

Verified 2026-09-09: all 25 Supercines URLs return a page carrying `initialData`,
and every Multicines storeId resolves to a distinct cinemaId.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.logging import logger
from app.models import CinemaCompany, CinemaComplex

# (city, name, url_part)
_MULTICINES: list[tuple[str, str, str]] = [
    ("Ambato", "Mall De Los Andes", "/?cityId=8&storeId=3571"),
    ("Cuenca", "Batan", "/?cityId=10&storeId=3561"),
    ("Cuenca", "Mall Del Alto", "/?cityId=10&storeId=4095"),
    ("Cuenca", "Mall Del Rio", "/?cityId=10&storeId=3560"),
    ("Cuenca", "Milenium Plaza", "/?cityId=10&storeId=3559"),
    ("Guayaquil", "City Mall", "/?cityId=12&storeId=3569"),
    ("Guayaquil", "Mall Del Norte", "/?cityId=12&storeId=3563"),
    ("Guayaquil", "Mall Del Rio GYE", "/?cityId=12&storeId=3562"),
    ("Guayaquil", "Mall Del Sol", "/?cityId=12&storeId=3567"),
    ("Guayaquil", "Mall Del Sur", "/?cityId=12&storeId=3568"),
    ("Guayaquil", "San Marino", "/?cityId=12&storeId=3576"),
    ("Guayaquil", "Village Plaza", "/?cityId=12&storeId=3570"),
    ("Latacunga", "Maltería Plaza", "/?cityId=24&storeId=3572"),
    ("Machala", "Gran Piazza", "/?cityId=15&storeId=3577"),
    ("Manta", "Mall Del Pacifico", "/?cityId=16&storeId=3575"),
    ("Quito", "CCI", "/?cityId=19&storeId=3555"),
    ("Quito", "Condado", "/?cityId=19&storeId=3557"),
    ("Quito", "El Portal", "/?cityId=19&storeId=3574"),
    ("Quito", "Paseo San Francisco", "/?cityId=19&storeId=3565"),
    ("Quito", "Plaza Americas", "/?cityId=19&storeId=3566"),
    ("Quito", "Quicentro Norte", "/?cityId=19&storeId=3573"),
    ("Quito", "Recreo", "/?cityId=19&storeId=3556"),
    ("Quito", "Scala", "/?cityId=19&storeId=3558"),
    ("Santo Domingo", "Bombolí", "/?cityId=22&storeId=4088"),
]

_SUPERCINES: list[tuple[str, str, str]] = [
    ("Ambato", "Ambato", "/cartelera/ambato/ambato/307"),
    ("Babahoyo", "Babahoyo", "/cartelera/babahoyo/babahoyo/168"),
    ("Bahia De Caraquez", "Bahia", "/cartelera/bahia-de-caraquez/bahia/296"),
    ("Daule", "Daule", "/cartelera/daule/daule/173"),
    ("Duran", "Supercines Duran", "/cartelera/duran/supercines-duran/207"),
    ("Guayaquil", "9 de Octubre", "/cartelera/guayaquil/9-de-octubre/209"),
    ("Guayaquil", "Ceibos", "/cartelera/guayaquil/ceibos/213"),
    ("Guayaquil", "Dorado", "/cartelera/guayaquil/dorado/236"),
    ("Guayaquil", "EntreRios", "/cartelera/guayaquil/entrerios/212"),
    ("Guayaquil", "Norte", "/cartelera/guayaquil/norte/211"),
    ("Guayaquil", "Orellana", "/cartelera/guayaquil/orellana/484"),
    ("Guayaquil", "Sur", "/cartelera/guayaquil/sur/214"),
    ("La Libertad", "Libertad", "/cartelera/la-libertad/libertad/220"),
    ("Machala", "Machala", "/cartelera/machala/machala/223"),
    ("Manta", "Manta", "/cartelera/manta/manta/224"),
    ("Milagro", "Milagro", "/cartelera/milagro/milagro/218"),
    ("Playas", "Playas", "/cartelera/playas/playas/183"),
    ("Portoviejo", "Portoviejo", "/cartelera/portoviejo/portoviejo/221"),
    ("Quevedo", "Quevedo", "/cartelera/quevedo/quevedo/219"),
    ("Quito", "6 de Diciembre", "/cartelera/quito/6-de-diciembre/187"),
    ("Quito", "Quicentro Sur", "/cartelera/quito/quicentro-sur/217"),
    ("Quito", "Riocentro Quito", "/cartelera/quito/riocentro-quito/430"),
    ("Quito", "San Luis", "/cartelera/quito/san-luis/216"),
    ("Riobamba", "Riobamba", "/cartelera/riobamba/riobamba/161"),
    ("Santo Domingo", "Sto Domingo", "/cartelera/santo-domingo/sto-domingo/222"),
]


def _upsert_company(db: Session, name: str, base_url: str) -> CinemaCompany:
    company = db.execute(select(CinemaCompany).where(CinemaCompany.name == name)).scalar_one_or_none()
    if company is None:
        company = CinemaCompany(name=name, base_url=base_url)
        db.add(company)
        db.flush()
    else:
        company.base_url = base_url
    return company


def _upsert_complexes(db: Session, company: CinemaCompany, rows: list[tuple[str, str, str]]) -> tuple[int, int]:
    """Add complexes that are missing and refresh the ones that already exist.

    Upserting rather than skipping the whole chain: the previous version bailed out
    as soon as the company existed, so a complex added to this list would never have
    reached a database that had already been seeded.
    """
    existing = {
        c.name: c
        for c in db.execute(select(CinemaComplex).where(CinemaComplex.company_id == company.id)).scalars().all()
    }
    added = 0
    for city, name, url_part in rows:
        found = existing.get(name)
        if found is None:
            db.add(CinemaComplex(name=name, city=city, url_part=url_part, company_id=company.id))
            added += 1
        else:
            found.city = city
            found.url_part = url_part
    return added, len(rows) - added


def seed_database() -> None:
    db: Session = SessionLocal()
    try:
        multicines = _upsert_company(db, "Multicines", "https://www.multicines.com.ec")
        supercines = _upsert_company(db, "Supercines", "https://www.supercines.com")

        for company, rows in ((multicines, _MULTICINES), (supercines, _SUPERCINES)):
            added, updated = _upsert_complexes(db, company, rows)
            logger.info(f"{company.name}: {added} complex(es) added, {updated} updated")

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
