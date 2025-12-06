from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from auth.auth import authenticate_user, create_access_token
from config import ACCESS_TOKEN_EXPIRE_MINUTES
from models import schemas, crud
from models.database import get_db
from utils.hash_utils import get_password_hash

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


@router.post("/register")
async def register_user(
        user_data: schemas.UserRegister,
        db: AsyncSession = Depends(get_db)
):
    hashed_password = get_password_hash(user_data.password)
    user_to_db = schemas.UserToDB(
        username=user_data.username,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        patronymic_name=user_data.patronymic_name,
        hashed_password=hashed_password
    )

    await crud.add_user(db=db,
                        user_to_db=user_to_db)
    return {"message": "Пользователь успешно добавлен"}


@router.post("/token")
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: AsyncSession = Depends(get_db)
) -> schemas.Token:
    user = await authenticate_user(db=db,
                                   username=form_data.username,
                                   password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    access_token_expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return schemas.Token(access_token=access_token, token_type="bearer")
