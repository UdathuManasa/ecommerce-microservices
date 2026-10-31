from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.schemas.user import UserRegister
from app.models.refresh_token import RefreshToken
from app.core.config import settings
from app.core.security import (
    verify_password,
    generate_refresh_token,
    hash_refresh_token,
    create_access_token,
    hash_password
)


class EmailAlreadyRegisteredError(Exception):
    pass


def register_user(
    db: Session,
    user_data: UserRegister
) -> User:

    # 1. Check whether email already exists
    existing_user = db.scalar(
        select(User).where(
            User.email == user_data.email
        )
    )

    if existing_user:
        raise EmailAlreadyRegisteredError(
            "Email is already registered"
        )

    # 2. Hash password
    hashed_password = hash_password(
        user_data.password
    )

    # 3. Create user object
    user = User(
        email=user_data.email,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role="CUSTOMER",
        is_active=True
    )

    # 4. Save to database
    db.add(user)

    try:
        db.commit()
        db.refresh(user)

    except IntegrityError:
        db.rollback()

        # Handle concurrent registration attempts
        # for the same email.
        existing_user = db.scalar(
            select(User).where(
                User.email == user_data.email
            )
        )

        if existing_user:
            raise EmailAlreadyRegisteredError(
                "Email is already registered"
            )

        raise

    return user


def authenticate_user(
    db: Session,
    email: str,
    password: str
):

    user = db.scalar(
        select(User).where(User.email == email.lower())
    )

    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    if not user.is_active:
        return None

    return user

def create_refresh_session(
    db: Session,
    user: User
) -> str:

    raw_token = generate_refresh_token()

    token_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_token),
        expires_at=(
            datetime.now(timezone.utc)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        ).replace(tzinfo=None)
    )

    db.add(token_record)
    db.commit()

    return raw_token

def issue_access_token(user: User) -> str:

    return create_access_token(user.id)

def rotate_refresh_token(
    db: Session,
    raw_token: str
):

    token_hash = hash_refresh_token(raw_token)

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    try:
        # Lock the existing token row during rotation.
        token_record = db.scalar(
            select(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .with_for_update()
        )

        if not token_record:
            return None

        if token_record.revoked_at is not None:
            return None

        if token_record.expires_at <= now:
            return None

        user = db.get(User, token_record.user_id)

        if not user or not user.is_active:
            return None

        # Revoke old refresh token.
        token_record.revoked_at = now

        # Create replacement refresh token.
        new_raw_token = generate_refresh_token()

        new_record = RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(new_raw_token),
            expires_at=(
                datetime.now(timezone.utc)
                + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            ).replace(tzinfo=None)
        )

        db.add(new_record)

        # Both changes happen in one transaction.
        db.commit()

        return user, new_raw_token

    except Exception:
        db.rollback()
        raise

def revoke_refresh_token(
    db: Session,
    raw_token: str
) -> None:

    token_record = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_refresh_token(raw_token)
        )
    )

    if token_record and token_record.revoked_at is None:

        token_record.revoked_at = (
            datetime.now(timezone.utc).replace(tzinfo=None)
        )

        db.commit()