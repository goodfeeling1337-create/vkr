from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.orm import Role, User
from app.repositories.users import ensure_role

log = logging.getLogger(__name__)


def seed_if_empty(db: Session) -> None:
    n = db.scalar(select(func.count()).select_from(Role))
    if n and n > 0:
        return
    log.info("Seeding roles and demo users")
    for name in ("admin", "teacher", "student"):
        ensure_role(db, name)
    db.flush()
    roles = {r.name: r for r in db.scalars(select(Role)).all()}
    users = [
        ("admin", "admin", "admin"),
        ("teacher", "teacher", "teacher"),
        ("student", "student", "student"),
    ]
    for uname, pwd, rname in users:
        u = User(
            username=uname,
            password_hash=hash_password(pwd),
            role_id=roles[rname].id,
            display_name=uname,
        )
        db.add(u)
    db.commit()
