"""GET /api/datasets/{name}.csv (#35)."""
from __future__ import annotations

from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import router
from app.database import get_db


def _app():
    app = FastAPI()
    app.include_router(router, prefix="/api")
    app.dependency_overrides[get_db] = lambda: object()
    return app


def test_csv_export_known_dataset_header_and_rows():
    rows = [{"id": 1, "url": "https://a.example/"}, {"id": 2, "url": "https://b.example/"}]
    with patch("app.api.get_dataset_count", return_value=2), patch(
        "app.api.execute_dataset_query", return_value=rows
    ):
        client = TestClient(_app())
        resp = client.get("/api/datasets/urls.csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "attachment" in resp.headers.get("content-disposition", "")
    body = resp.text.strip().splitlines()
    assert body[0] == "id,url"
    assert "https://a.example/" in body[1]


def test_csv_export_unknown_404():
    with patch("app.api.get_dataset_count", side_effect=ValueError("Dataset 'nope' not found")):
        client = TestClient(_app())
        resp = client.get("/api/datasets/nope.csv")
    assert resp.status_code == 404
