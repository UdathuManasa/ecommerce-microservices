import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import settings


password_hash = PasswordHash.recommended()


# -------------------------
# Password hashing
# -------------------------

def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    return password_hash.verify(
        plain_password,
        hashed_password
    )


# -------------------------
# Access token generation
# -------------------------

def create_access_token(user_id: str) -> str:

    now = datetime.now(timezone.utc)

    expires_at = now + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": user_id,
        "type": "access",
        "iat": now,
        "exp": expires_at,
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "jti": secrets.token_urlsafe(16)
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm="HS256"
    )


# -------------------------
# Access token verification
# -------------------------

def decode_access_token(token: str) -> dict:

    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=["HS256"],
        issuer=settings.JWT_ISSUER,
        audience=settings.JWT_AUDIENCE,
        options={
            "require": [
                "sub",
                "exp",
                "iat",
                "iss",
                "aud",
                "jti",
                "type"
            ]
        }
    )

    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Invalid token type")

    return payload


# -------------------------
# Refresh token generation
# -------------------------

def generate_refresh_token() -> str:

    return secrets.token_urlsafe(64)


# -------------------------
# Refresh token hashing
# -------------------------

def hash_refresh_token(token: str) -> str:

    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()
