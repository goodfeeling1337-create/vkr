"""Общие Jinja2 templates для веб-слоёв (избегаем циклических импортов с main)."""
from __future__ import annotations

from pathlib import Path

from fastapi.templating import Jinja2Templates

from app.core.csrf import CSRF_FIELD_NAME, generate_csrf_token

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))
templates.env.globals["csrf_field_name"] = CSRF_FIELD_NAME
templates.env.globals["csrf_token"] = generate_csrf_token
