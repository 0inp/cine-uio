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

from typing import NamedTuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.logging import logger
from app.models import CinemaCompany, CinemaComplex


class SeedComplex(NamedTuple):
    city: str
    name: str
    url_part: str
    latitude: float
    longitude: float


_MULTICINES: list[SeedComplex] = [
    SeedComplex("Ambato", "Mall De Los Andes", "/?cityId=8&storeId=3571", -1.26528, -78.63075),
    SeedComplex("Cuenca", "Batan", "/?cityId=10&storeId=3561", -2.89713, -79.0244),
    SeedComplex("Cuenca", "Mall Del Alto", "/?cityId=10&storeId=4095", -2.92149, -79.0139),
    SeedComplex("Cuenca", "Mall Del Rio", "/?cityId=10&storeId=3560", -2.91866, -79.04152),
    SeedComplex("Cuenca", "Milenium Plaza", "/?cityId=10&storeId=3559", -2.906, -79.00455),
    SeedComplex("Guayaquil", "City Mall", "/?cityId=12&storeId=3569", -2.13936, -79.90932),
    SeedComplex("Guayaquil", "Mall Del Norte", "/?cityId=12&storeId=3563", -2.0947, -79.91263),
    SeedComplex("Guayaquil", "Mall Del Rio GYE", "/?cityId=12&storeId=3562", -2.12486, -79.90536),
    SeedComplex("Guayaquil", "Mall Del Sol", "/?cityId=12&storeId=3567", -2.1557, -79.8941),
    SeedComplex("Guayaquil", "Mall Del Sur", "/?cityId=12&storeId=3568", -2.2281, -79.8987),
    SeedComplex("Guayaquil", "San Marino", "/?cityId=12&storeId=3576", -2.16877, -79.89863),
    SeedComplex("Guayaquil", "Village Plaza", "/?cityId=12&storeId=3570", -2.13905, -79.86417),
    SeedComplex("Latacunga", "Maltería Plaza", "/?cityId=24&storeId=3572", -0.92648, -78.62801),
    SeedComplex("Machala", "Gran Piazza", "/?cityId=15&storeId=3577", -3.27029, -79.94373),
    SeedComplex("Manta", "Mall Del Pacifico", "/?cityId=16&storeId=3575", -0.94262, -80.73225),
    SeedComplex("Quito", "CCI", "/?cityId=19&storeId=3555", -0.17737, -78.48497),
    SeedComplex("Quito", "Condado", "/?cityId=19&storeId=3557", -0.1033, -78.493),
    SeedComplex("Quito", "El Portal", "/?cityId=19&storeId=3574", -0.10796, -78.45857),
    SeedComplex("Quito", "Paseo San Francisco", "/?cityId=19&storeId=3565", -0.1983, -78.4369),
    SeedComplex("Quito", "Plaza Americas", "/?cityId=19&storeId=3566", -0.1746, -78.4925),
    SeedComplex("Quito", "Quicentro Norte", "/?cityId=19&storeId=3573", -0.1752, -78.48029),
    SeedComplex("Quito", "Recreo", "/?cityId=19&storeId=3556", -0.25226, -78.55791),
    SeedComplex("Quito", "Scala", "/?cityId=19&storeId=3558", -0.20698, -78.4277),
    SeedComplex("Santo Domingo", "Bombolí", "/?cityId=22&storeId=4088", -0.25436, -79.19193),
]

_SUPERCINES: list[SeedComplex] = [
    SeedComplex("Ambato", "Ambato", "/cartelera/ambato/ambato/307", -1.249, -78.6167),
    SeedComplex("Babahoyo", "Babahoyo", "/cartelera/babahoyo/babahoyo/168", -1.814, -79.5459),
    SeedComplex("Bahia De Caraquez", "Bahia", "/cartelera/bahia-de-caraquez/bahia/296", -0.611, -80.4244),
    SeedComplex("Daule", "Daule", "/cartelera/daule/daule/173", -1.8543, -79.9759),
    SeedComplex("Duran", "Supercines Duran", "/cartelera/duran/supercines-duran/207", -2.1789, -79.8246),
    SeedComplex("Guayaquil", "9 de Octubre", "/cartelera/guayaquil/9-de-octubre/209", -2.1905, -79.8856),
    SeedComplex("Guayaquil", "Ceibos", "/cartelera/guayaquil/ceibos/213", -2.1753, -79.9443),
    SeedComplex("Guayaquil", "Dorado", "/cartelera/guayaquil/dorado/236", -2.0524, -79.873),
    SeedComplex("Guayaquil", "EntreRios", "/cartelera/guayaquil/entrerios/212", -2.1414, -79.8651),
    SeedComplex("Guayaquil", "Norte", "/cartelera/guayaquil/norte/211", -2.1272, -79.907),
    SeedComplex("Guayaquil", "Orellana", "/cartelera/guayaquil/orellana/484", -2.1685, -79.8975),
    SeedComplex("Guayaquil", "Sur", "/cartelera/guayaquil/sur/214", -2.2416, -79.8951),
    SeedComplex("La Libertad", "Libertad", "/cartelera/la-libertad/libertad/220", -2.2262, -80.9211),
    SeedComplex("Machala", "Machala", "/cartelera/machala/machala/223", -3.2806, -79.9321),
    SeedComplex("Manta", "Manta", "/cartelera/manta/manta/224", -0.9664, -80.7053),
    SeedComplex("Milagro", "Milagro", "/cartelera/milagro/milagro/218", -2.1275, -79.5917),
    SeedComplex("Playas", "Playas", "/cartelera/playas/playas/183", -2.6432, -80.3853),
    SeedComplex("Portoviejo", "Portoviejo", "/cartelera/portoviejo/portoviejo/221", -1.0611, -80.4655),
    SeedComplex("Quevedo", "Quevedo", "/cartelera/quevedo/quevedo/219", -1.0252, -79.4665),
    SeedComplex("Quito", "6 de Diciembre", "/cartelera/quito/6-de-diciembre/187", -0.1796, -78.4789),
    SeedComplex("Quito", "Quicentro Sur", "/cartelera/quito/quicentro-sur/217", -0.2846, -78.5438),
    SeedComplex("Quito", "Riocentro Quito", "/cartelera/quito/riocentro-quito/430", -0.1667, -78.4762),
    SeedComplex("Quito", "San Luis", "/cartelera/quito/san-luis/216", -0.3074, -78.4496),
    SeedComplex("Riobamba", "Riobamba", "/cartelera/riobamba/riobamba/161", -1.6552, -78.645),
    SeedComplex("Santo Domingo", "Sto Domingo", "/cartelera/santo-domingo/sto-domingo/222", -2.2416, -79.8951),
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


def _upsert_complexes(db: Session, company: CinemaCompany, rows: list[SeedComplex]) -> tuple[int, int]:
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
    for row in rows:
        found = existing.get(row.name)
        if found is None:
            db.add(
                CinemaComplex(
                    name=row.name,
                    city=row.city,
                    url_part=row.url_part,
                    latitude=row.latitude,
                    longitude=row.longitude,
                    company_id=company.id,
                )
            )
            added += 1
        else:
            found.city = row.city
            found.url_part = row.url_part
            found.latitude = row.latitude
            found.longitude = row.longitude
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
