from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    Cookie,
    status
)

from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.config import settings

from app.schemas.user import (
    UserRegister,
    UserResponse,
    UserLogin,
    TokenResponse
)

from app.services.auth_service import (
    register_user,
    authenticate_user,
    create_refresh_session,
    issue_access_token,
    rotate_refresh_token,
    revoke_refresh_token,
    EmailAlreadyRegisteredError
)


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"]
)


def set_refresh_cookie(
    response: Response,
    token: str
):

    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        path="/api/v1/auth",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )


def clear_refresh_cookie(response: Response):

    response.delete_cookie(
        key="refresh_token",
        path="/api/v1/auth",
        secure=settings.COOKIE_SECURE,
        httponly=True,
        samesite="lax"
    )


# -------------------------
# REGISTER
# -------------------------

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):

    try:
        return register_user(db, user_data)

    except EmailAlreadyRegisteredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered"
        )


# -------------------------
# LOGIN
# -------------------------

@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
    user_data: UserLogin,
    response: Response,
    db: Session = Depends(get_db)
):

    user = authenticate_user(
        db,
        user_data.email,
        user_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    refresh_token = create_refresh_session(db, user)

    access_token = issue_access_token(user)

    set_refresh_cookie(response, refresh_token)

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


# -------------------------
# REFRESH ACCESS TOKEN
# -------------------------

@router.post(
    "/refresh",
    response_model=TokenResponse
)
def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db)
):

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing"
        )

    result = rotate_refresh_token(db, refresh_token)

    if not result:
        error_response = JSONResponse(
            status_code=401,
            content={"detail": "Invalid or expired refresh token"}
        )
        clear_refresh_cookie(error_response)
        return error_response

    user, new_refresh_token = result

    new_access_token = issue_access_token(user)

    set_refresh_cookie(response, new_refresh_token)

    return TokenResponse(
        access_token=new_access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


# -------------------------
# LOGOUT
# -------------------------

@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT
)
def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db)
):

    if refresh_token:
        revoke_refresh_token(db, refresh_token)

    clear_refresh_cookie(response)

    response.status_code = status.HTTP_204_NO_CONTENT
    return response


