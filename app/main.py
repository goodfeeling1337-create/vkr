from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from app.api.routes import auth, downloads, student, teacher
from app.api.views import templates
from app.core.config import get_settings
from app.core.logging_config import setup_logging
from app.db.seed import seed_if_empty
from app.db.session import SessionLocal

setup_logging()
log = logging.getLogger(__name__)

app = FastAPI(title="DB Normalization Checker", docs_url=None, redoc_url=None)

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(auth.router)
app.include_router(teacher.router)
app.include_router(student.router)
app.include_router(downloads.router)


@app.on_event("startup")
def _startup() -> None:
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()


@app.exception_handler(HTTPException)
async def http_exc_handler(request: Request, exc: HTTPException) -> Response:
    accept = request.headers.get("accept", "")
    if "text/html" in accept and exc.status_code in (403, 404):
        detail = exc.detail if isinstance(exc.detail, str) else "Ошибка"
        title = "Доступ запрещён" if exc.status_code == 403 else "Не найдено"
        return templates.TemplateResponse(
            request,
            "error.html",
            {"title": title, "message": detail},
            status_code=exc.status_code,
        )
    return JSONResponse(
        {"detail": exc.detail},
        status_code=exc.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_exc(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse({"detail": exc.errors()}, status_code=422)


@app.exception_handler(Exception)
async def unhandled_exc(request: Request, exc: Exception) -> HTMLResponse:
    log.exception("unhandled error: %s", exc)
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "title": "Ошибка сервера",
            "message": "Произошла внутренняя ошибка. Попробуйте позже или обратитесь к преподавателю.",
        },
        status_code=500,
    )
