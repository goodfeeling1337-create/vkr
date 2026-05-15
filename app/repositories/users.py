from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.orm import Role, User


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.execute(select(User).where(User.username == username)).scalar_one_or_none()


def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def list_users(db: Session) -> list[User]:
    return list(
        db.execute(
            select(User).options(joinedload(User.role)).order_by(User.id).limit(500),
        )
        .scalars()
        .unique()
        .all(),
    )


def ensure_role(db: Session, name: str) -> Role:
    r = db.execute(select(Role).where(Role.name == name)).scalar_one_or_none()
    if r:
        return r
    r = Role(name=name)
    db.add(r)
    db.flush()
    return r
