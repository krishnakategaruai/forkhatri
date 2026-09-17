"""TR20 Origin guard and no-store header, with and without the deployment edge's root path.

The guard answers before any route runs, so no database is needed (the app's
lifespan is not started: TestClient is used without a context manager).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.mark.parametrize("root_path", ["", "/api/identity"])
def test_foreign_origin_is_refused_behind_any_root_path(root_path: str) -> None:
    client = TestClient(create_app(), root_path=root_path)
    response = client.post(
        f"{root_path}/v1/auth/password",
        json={"identifier": "+919800000001", "password": "x"},
        headers={"Origin": "https://evil.example"},
    )
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "origin_not_allowed"
    assert response.headers.get("cache-control") is None or "no-store" in response.headers["cache-control"]


@pytest.mark.parametrize("root_path", ["", "/api/identity"])
def test_unknown_paths_outside_the_api_are_not_guarded(root_path: str) -> None:
    client = TestClient(create_app(), root_path=root_path)
    response = client.post(f"{root_path}/not-an-api", headers={"Origin": "https://evil.example"})
    assert response.status_code == 404
