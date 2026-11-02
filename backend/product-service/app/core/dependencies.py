import jwt
import httpx

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)

from app.core.config import settings


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    )
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
                "require": [
                    "sub", "exp", "iat",
                    "iss", "aud", "jti", "type"
                ]
            }
        )

        if payload.get("type") != "access":
            raise unauthorized

        return {
            "user_id": payload["sub"],
            "access_token": credentials.credentials
        }

    except jwt.InvalidTokenError:
        raise unauthorized


def require_admin(
    current_user: dict = Depends(get_current_user)
):
    try:
        response = httpx.get(
            f"{settings.AUTH_SERVICE_URL}/api/v1/users/me",
            headers={
                "Authorization": (
                    f"Bearer {current_user['access_token']}"
                )
            },
            timeout=3.0
        )

        if response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail="Authentication failed"
            )

        response.raise_for_status()

        user = response.json()

    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=503,
            detail="Unable to verify user authorization"
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Auth Service is unavailable"
        )

    if user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return user