from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api import app
from app.database import get_db


@pytest.fixture
def client(seeded_db: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield seeded_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


class TestGetScreenings:
    def test_returns_200(self, client: TestClient) -> None:
        assert client.get("/api/screenings").status_code == 200

    def test_returns_list_of_all_screenings(self, client: TestClient) -> None:
        data = client.get("/api/screenings").json()
        assert isinstance(data, list)
        assert len(data) == 2

    def test_screening_has_required_fields(self, client: TestClient) -> None:
        s = client.get("/api/screenings").json()[0]
        assert {"id", "datetime", "format", "language", "movie", "complex"} <= s.keys()
        assert "title" in s["movie"]
        assert "name" in s["complex"]
        assert "company" in s["complex"]
        assert "name" in s["complex"]["company"]

    def test_filter_by_company_name(self, client: TestClient) -> None:
        data = client.get("/api/screenings", params={"cinema_company_name": "Multicines"}).json()
        assert len(data) == 1
        assert data[0]["complex"]["company"]["name"] == "Multicines"

    def test_filter_by_complex_name(self, client: TestClient) -> None:
        data = client.get("/api/screenings", params={"cinema_complex_name": "San Luis"}).json()
        assert len(data) == 1
        assert data[0]["complex"]["name"] == "San Luis"

    def test_unknown_company_returns_empty_list(self, client: TestClient) -> None:
        data = client.get("/api/screenings", params={"cinema_company_name": "Ghost"}).json()
        assert data == []
