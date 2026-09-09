from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api import app, mount_frontend
from app.database import get_db


@pytest.fixture
def client(seeded_db: Session) -> Generator[TestClient]:
    def override_get_db() -> Generator[Session]:
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

    def test_movie_exposes_tmdb_fields(self, client: TestClient) -> None:
        movie = client.get("/api/screenings").json()[0]["movie"]
        assert {
            "tmdb_id",
            "tmdb_title",
            "poster_url",
            "overview",
            "runtime",
            "certification",
            "release_date",
        } <= movie.keys()

    def test_movie_tmdb_fields_are_nullable_when_unenriched(self, client: TestClient) -> None:
        movie = client.get("/api/screenings").json()[0]["movie"]
        assert movie["tmdb_id"] is None
        assert movie["tmdb_title"] is None
        assert movie["poster_url"] is None

    def test_complex_exposes_its_city(self, client: TestClient) -> None:
        complex_ = client.get("/api/screenings").json()[0]["complex"]
        assert complex_["city"] == "Quito"

    def test_lists_cities(self, client: TestClient) -> None:
        assert client.get("/api/cities").json() == ["Quito"]

    def test_filter_by_city(self, client: TestClient) -> None:
        assert len(client.get("/api/screenings", params={"city": "Quito"}).json()) == 2
        assert client.get("/api/screenings", params={"city": "Guayaquil"}).json() == []

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


class TestFrontendMount:
    """The SPA is served from the same origin as the API, so a Tailscale Serve
    target is a single port and no CORS configuration is involved."""

    def _dist(self, tmp_path: Path) -> Path:
        dist = tmp_path / "dist"
        dist.mkdir()
        (dist / "index.html").write_text("<html>SPA</html>")
        return dist

    def test_serves_index_html_at_the_root(self, tmp_path: Path) -> None:
        app = FastAPI()
        assert mount_frontend(app, self._dist(tmp_path)) is True
        assert TestClient(app).get("/").text == "<html>SPA</html>"

    def test_api_routes_still_win_over_the_static_mount(self, tmp_path: Path) -> None:
        app = FastAPI()

        @app.get("/api/ping")
        def ping() -> dict[str, bool]:
            return {"ok": True}

        mount_frontend(app, self._dist(tmp_path))
        assert TestClient(app).get("/api/ping").json() == {"ok": True}

    def test_does_nothing_without_a_build(self, tmp_path: Path) -> None:
        # Normal in development: Vite serves the frontend on its own port.
        assert mount_frontend(FastAPI(), tmp_path) is False
