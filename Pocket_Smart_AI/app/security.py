import base64
import hashlib
import hmac
import os

from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request

from jose import JWTError, jwt

from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db
from .models import User


settings = get_settings()

ALGORITHM = "HS256"

COOKIE_NAME = "pocketsmart_token"


def hash_password(password: str) -> str:
    salt = os.urandom(16)

    rounds = 120000

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        rounds
    )

    return (
        f"pbkdf2_sha256${rounds}$"
        f"{base64.urlsafe_b64encode(salt).decode()}$"
        f"{base64.urlsafe_b64encode(digest).decode()}"
    )


def verify_password(
    password: str,
    stored: str
) -> bool:

    try:
        _, rounds, salt_text, digest_text = stored.split("$")

        salt = base64.urlsafe_b64decode(
            salt_text.encode()
        )

        expected = base64.urlsafe_b64decode(
            digest_text.encode()
        )

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt,
            int(rounds)
        )

        return hmac.compare_digest(
            actual,
            expected
        )

    except Exception:
        return False


def create_token(user_id: int) -> str:
    expiry = (
        datetime.now(timezone.utc)
        + timedelta(hours=12)
    )

    return jwt.encode(
        {
            "sub": str(user_id),
            "exp": expiry
        },
        settings.secret_key,
        algorithm=ALGORITHM
    )


def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:

    token = request.cookies.get(
        COOKIE_NAME
    )

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Login required"
        )

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM]
        )

        user_id = int(
            payload["sub"]
        )

    except (
        JWTError,
        KeyError,
        ValueError
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session"
        )

    user = db.get(
        User,
        user_id
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user