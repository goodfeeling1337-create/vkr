from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.testclient import TestClient

from app.core.csrf import CSRF_COOKIE_NAME, CSRF_FIELD_NAME, generate_csrf_token
from app.core.csrf_middleware import CSRFMiddleware


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(CSRFMiddleware)

    @app.get("/ping")
    async def ping() -> PlainTextResponse:
        return PlainTextResponse("ok")

    @app.post("/submit")
    async def submit() -> PlainTextResponse:
        return PlainTextResponse("ok")

    return app


def test_post_rejected_without_csrf_token() -> None:
    with TestClient(_build_app()) as client:
        client.get("/ping")
        response = client.post("/submit", data={})
        assert response.status_code == 403


def test_post_rejected_with_mismatched_csrf_token() -> None:
    with TestClient(_build_app()) as client:
        client.get("/ping")
        response = client.post("/submit", data={CSRF_FIELD_NAME: generate_csrf_token()})
        assert response.status_code == 403


def test_post_allowed_with_cookie_matched_csrf_token() -> None:
    with TestClient(_build_app()) as client:
        client.get("/ping")
        cookie_token = client.cookies.get(CSRF_COOKIE_NAME)
        assert cookie_token
        response = client.post("/submit", data={CSRF_FIELD_NAME: cookie_token})
        assert response.status_code == 200
