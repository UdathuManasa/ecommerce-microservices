import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)
):
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token",
        headers={"WWW-Authenticate": "Bearer"}
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=["HS256"],
            issuer=settings.JWT_ISSUER,
            audience=settings.JWT_AUDIENCE,
            options={
                "require": ["sub", "exp", "iat", "iss", "aud", "jti", "type"]
            }
        )

        if payload.get("type") != "access":
            raise unauthorized

        return {
            "user_id": payload["sub"]
        }

    except jwt.InvalidTokenError:
        raise unauthorized


def require_admin(
    current_user: dict = Depends(get_current_user)
):
    # Temporary implementation:
    # We'll replace this with an Auth Service role lookup
    # before allowing product writes.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Admin role verification is not configured yet"
    )