"""Shared FastAPI dependencies, including user resolution.

Production auth is Clerk (PRD Section 11). To keep the MVP runnable without
external services, the user is identified by a Clerk-issued id passed in the
`X-User-Id` header; when Clerk is wired up this becomes a verified JWT subject.
The internal user id stays opaque and server-issued, never derived from input.
"""
from __future__ import annotations

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from .database import get_db
from .models import User

DEMO_USER_EXTERNAL_ID = "demo-user"


def get_current_user(
    db: Session = Depends(get_db),
    x_user_id: str = Header(default=DEMO_USER_EXTERNAL_ID, alias="X-User-Id"),
) -> User:
    """Resolve (or lazily create) the current user from the auth header."""
    external_id = (x_user_id or DEMO_USER_EXTERNAL_ID).strip()
    user = db.query(User).filter(User.external_id == external_id).one_or_none()
    if user is None:
        user = User(external_id=external_id, display_name="TeaSpoon User")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
