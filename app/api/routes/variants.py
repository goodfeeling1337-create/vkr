"""Варианты заданий: режим тренировка/тестирование, список."""

from __future__ import annotations

from collections import Counter
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import require_teacher
from app.api.views import templates
from app.db.session import get_db
from app.models.orm import User
from app.repositories import reference as ref_repo
from app.repositories import variants as var_repo

router = APIRouter()


@router.get("/teacher/variants", response_class=HTMLResponse)
async def teacher_variants(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher),
) -> HTMLResponse:
    variants = var_repo.list_variants(db, user.id)
    works = ref_repo.list_reference_works_for_teacher(db, user.id)
    by_vid = Counter(w.variant_id for w in works)
    stats = [{"variant": v, "works_count": by_vid.get(v.id, 0)} for v in variants]
    return templates.TemplateResponse(
        request,
        "variants.html",
        {"user": user, "stats": stats},
    )


@router.post("/teacher/variants/new")
async def teacher_variant_create(
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher),
    name: str = Form(...),
    scoring_mode: Literal["training", "testing"] = Form("training"),
) -> RedirectResponse:
    if not name.strip():
        raise HTTPException(status_code=400, detail="Укажите название")
    var_repo.create_variant(db, teacher_id=user.id, name=name.strip(), scoring_mode=scoring_mode)
    db.commit()
    return RedirectResponse("/teacher/variants", status_code=302)


@router.post("/teacher/variants/{variant_id}/edit")
async def teacher_variant_edit(
    variant_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher),
    name: Optional[str] = Form(None),
    scoring_mode: Optional[str] = Form(None),
) -> RedirectResponse:
    v = var_repo.get_variant_for_teacher(db, variant_id, user.id)
    if v is None:
        raise HTTPException(status_code=404, detail="Вариант не найден")
    if name and name.strip():
        v.name = name.strip()
    if scoring_mode in ("training", "testing"):
        v.scoring_mode = scoring_mode
    db.commit()
    return RedirectResponse("/teacher/variants", status_code=302)
