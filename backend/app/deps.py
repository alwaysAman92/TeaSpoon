"""Shared FastAPI dependencies, including user resolution.

Production auth is Clerk (PRD Section 11). When CLERK_SECRET_KEY is configured,
the dependency verifies the JWT from the Authorization header against Clerk's
JWKS. Otherwise it falls back to the X-User-Id header for local development.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

import httpx
import jwt
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db
from .models import User

logger = logging.getLogger(__name__)

DEMO_USER_EXTERNAL_ID = "demo-user"


@lru_cache(maxsize=1)
def _fetch_clerk_jwks() -> dict:
    """Fetch Clerk's JWKS (cached for the process lifetime)."""
    settings = get_settings()
    resp = httpx.get(
        "https://api.clerk.com/v1/jwks",
        headers={"Authorization": f"Bearer {settings.clerk_secret_key}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def _verify_clerk_token(token: str) -> Optional[str]:
    """Decode and verify a Clerk JWT. Returns the subject (user id) or None."""
    try:
        jwks_data = _fetch_clerk_jwks()
        public_keys = {}
        for key_data in jwks_data.get("keys", []):
            kid = key_data.get("kid")
            if kid:
                public_keys[kid] = jwt.algorithms.RSAAlgorithm.from_jwk(key_data)

        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if kid not in public_keys:
            logger.warning("Clerk JWT kid %s not found in JWKS", kid)
            return None

        payload = jwt.decode(
            token,
            key=public_keys[kid],
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return payload.get("sub")
    except (jwt.PyJWTError, httpx.HTTPError, KeyError, ValueError) as exc:
        logger.warning("Clerk JWT verification failed: %s", exc)
        return None


def get_current_user(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    x_user_id: str = Header(default=DEMO_USER_EXTERNAL_ID, alias="X-User-Id"),
) -> User:
    """Resolve (or lazily create) the current user.

    When CLERK_SECRET_KEY is set, expects Authorization: Bearer <JWT>.
    Otherwise falls back to X-User-Id for local development.
    """
    settings = get_settings()
    external_id: str = DEMO_USER_EXTERNAL_ID

    if settings.clerk_secret_key and authorization:
        # Production path: verify Clerk JWT.
        parts = authorization.split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            clerk_user_id = _verify_clerk_token(parts[1])
            if clerk_user_id is None:
                raise HTTPException(status_code=401, detail="Invalid or expired token.")
            external_id = clerk_user_id
        else:
            raise HTTPException(status_code=401, detail="Malformed Authorization header.")
    else:
        # Dev fallback: trust X-User-Id header.
        external_id = (x_user_id or DEMO_USER_EXTERNAL_ID).strip()

    user = db.query(User).filter(User.external_id == external_id).one_or_none()
    if user is None:
        user = User(external_id=external_id, display_name="TeaSpoon User")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
