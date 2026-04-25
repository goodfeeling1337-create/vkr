from __future__ import annotations

from fastapi import FastAPI, Form
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


def test_post_rejected_with_invalid_csrf_token() -> None:
    with TestClient(_build_app()) as client:
        client.get("/ping")
        response = client.post("/submit", data={CSRF_FIELD_NAME: "not-a-valid-signed-token"})
        assert response.status_code == 403


def test_post_allowed_with_cookie_matched_csrf_token() -> None:
    with TestClient(_build_app()) as client:
        client.get("/ping")
        cookie_token = client.cookies.get(CSRF_COOKIE_NAME)
        assert cookie_token
        response = client.post("/submit", data={CSRF_FIELD_NAME: cookie_token})
        assert response.status_code == 200


def test_login_path_skips_csrf_so_form_body_reaches_handler() -> None:
    """Регрессия: /login не должен парсить form в middleware (ломает Form() в роуте)."""
    app = FastAPI()
    app.add_middleware(CSRFMiddleware)

    @app.post("/login")
    async def fake_login(username: str = Form(...), password: str = Form(...)) -> PlainTextResponse:
        return PlainTextResponse(f"{username}:{password}")

    with TestClient(app) as client:
        response = client.post("/login", data={"username": "u", "password": "p"})
        assert response.status_code == 200
        assert response.text == "u:p"
