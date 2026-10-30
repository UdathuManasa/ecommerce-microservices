
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.schemas.user import UserRegister
from app.core.security import hash_password


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
