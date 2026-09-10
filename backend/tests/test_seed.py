import re

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CinemaCompany as CinemaCompanyModel
from app.models import CinemaComplex as CinemaComplexModel
from app.seed import _MULTICINES, _SUPERCINES, SeedComplex, _upsert_company, _upsert_complexes

ALL_ROWS = [("Multicines", r) for r in _MULTICINES] + [("Supercines", r) for r in _SUPERCINES]


class TestSeedData:
    """The complex list is static, so its main failure mode is a typo nobody notices
    until a venue silently stops being scraped. Validate every row's shape."""

    def test_covers_both_chains(self) -> None:
        assert len(_MULTICINES) > 0 and len(_SUPERCINES) > 0

    @pytest.mark.parametrize("row", _MULTICINES)
    def test_multicines_url_carries_a_city_and_a_store(self, row: SeedComplex) -> None:
        assert re.fullmatch(r"/\?cityId=\d+&storeId=\d+", row.url_part), row.url_part

    @pytest.mark.parametrize("row", _SUPERCINES)
    def test_supercines_url_is_a_cartelera_path(self, row: SeedComplex) -> None:
        assert re.fullmatch(r"/cartelera/[a-z0-9-]+/[a-z0-9-]+/\d+", row.url_part), row.url_part

    @pytest.mark.parametrize(("company", "row"), ALL_ROWS)
    def test_city_and_name_are_present_and_trimmed(self, company: str, row: SeedComplex) -> None:
        for value in (row.city, row.name):
            assert value and value == value.strip()

    @pytest.mark.parametrize(("company", "row"), ALL_ROWS)
    def test_coordinates_land_in_ecuador(self, company: str, row: SeedComplex) -> None:
        # Swapping latitude and longitude is the classic way this goes wrong, and it
        # would silently sort every venue by a nonsense distance.
        assert -5.5 < row.latitude < 2.0, f"{row.name}: latitude {row.latitude}"
        assert -82.0 < row.longitude < -74.0, f"{row.name}: longitude {row.longitude}"

    def test_no_duplicate_name_within_a_chain(self) -> None:
        for label, rows in (("Multicines", _MULTICINES), ("Supercines", _SUPERCINES)):
            names = [row.name for row in rows]
            assert len(names) == len(set(names)), f"{label} has a duplicate complex name"

    def test_no_duplicate_url_part_anywhere(self) -> None:
        urls = [row.url_part for _, row in ALL_ROWS]
        assert len(urls) == len(set(urls))


class TestUpsertComplexes:
    def _company(self, db: Session) -> CinemaCompanyModel:
        return _upsert_company(db, "Multicines", "https://www.multicines.com.ec")

    def test_adds_missing_complexes(self, db: Session) -> None:
        company = self._company(db)
        added, updated = _upsert_complexes(
            db, company, [SeedComplex("Quito", "CCI", "/?cityId=19&storeId=3555", -0.17737, -78.48497)]
        )
        db.commit()
        assert (added, updated) == (1, 0)
        assert db.execute(select(CinemaComplexModel)).scalar_one().city == "Quito"

    def test_running_twice_adds_nothing(self, db: Session) -> None:
        # The previous seed bailed out once the company existed, so complexes added to
        # the list never reached an already-seeded database.
        company = self._company(db)
        rows = [SeedComplex("Quito", "CCI", "/?cityId=19&storeId=3555", -0.17737, -78.48497)]
        _upsert_complexes(db, company, rows)
        db.commit()
        added, updated = _upsert_complexes(db, company, rows)
        db.commit()
        assert (added, updated) == (0, 1)
        assert len(list(db.execute(select(CinemaComplexModel)).scalars().all())) == 1

    def test_refreshes_city_and_url_of_an_existing_complex(self, db: Session) -> None:
        company = self._company(db)
        _upsert_complexes(db, company, [SeedComplex("Quito", "CCI", "/old", -0.1, -78.4)])
        db.commit()
        _upsert_complexes(db, company, [SeedComplex("Guayaquil", "CCI", "/new", -2.1, -79.9)])
        db.commit()
        complex_ = db.execute(select(CinemaComplexModel)).scalar_one()
        assert (complex_.city, complex_.url_part) == ("Guayaquil", "/new")

    def test_seeds_the_real_list_without_collisions(self, db: Session) -> None:
        multicines = _upsert_company(db, "Multicines", "https://www.multicines.com.ec")
        supercines = _upsert_company(db, "Supercines", "https://www.supercines.com")
        _upsert_complexes(db, multicines, _MULTICINES)
        _upsert_complexes(db, supercines, _SUPERCINES)
        db.commit()  # the (company, name) unique constraint must hold
        assert len(list(db.execute(select(CinemaComplexModel)).scalars().all())) == len(ALL_ROWS)
