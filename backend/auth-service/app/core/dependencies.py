
import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.core.security import decode_access_token


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:

    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token",
        headers={"WWW-Authenticate": "Bearer"}
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = decode_access_token(credentials.credentials)

        user_id = payload.get("sub")

        if not user_id:
            raise unauthorized
    except jwt.ExpiredSignatureError:
        print("JWT ERROR: Access token expired")
        raise unauthorized

    except jwt.InvalidAudienceError:
        print("JWT ERROR: Invalid audience")
        raise unauthorized

    except jwt.InvalidIssuerError:
        print("JWT ERROR: Invalid issuer")
        raise unauthorized

    except jwt.InvalidTokenError as e:
        print("JWT ERROR:", str(e))
        raise unauthorized

    user = db.get(User, user_id)

    if not user or not user.is_active:
        raise unauthorized

    return user


def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:

    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return current_user
