from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy.ext.asyncio import AsyncSession

from config import SECRET_KEY, ALGORITHM
from models import crud, schemas
from models.database import get_db

password_hash = PasswordHash.recommended()

oath2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


async def authenticate_user(
        username: str,
        password: str,
        db: AsyncSession = Depends(get_db)
) -> schemas.UserInDB | bool:
    try:
        user_data = await crud.get_user(db=db, username=username)
        user = schemas.UserInDB(
            id=user_data.id,
            username=user_data.username,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            patronymic_name=user_data.patronymic_name,
            disabled=user_data.disabled,
            hashed_password=user_data.hashed_password
        )
    except Exception:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
        token: Annotated[str, Depends(oath2_scheme)],
        db: AsyncSession = Depends(get_db)
) -> schemas.UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception

    try:
        user_data = await crud.get_user(db=db, username=token_data.username)
        user = schemas.UserInDB(
            id=user_data.id,
            username=user_data.username,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            patronymic_name=user_data.patronymic_name,
            disabled=user_data.disabled,
            hashed_password=user_data.hashed_password
            )
    except Exception:
        raise credentials_exception
    return user


async def get_current_active_user(
        current_user: Annotated[schemas.User, Depends(get_current_user)]
) -> schemas.User:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
