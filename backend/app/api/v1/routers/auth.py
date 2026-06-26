from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserLogin, UserOut
from app.security import create_access_token
from app.services.user_service import UserService

router = APIRouter(prefix='/auth', tags=['Auth'])


@router.post('/register', response_model=UserOut, status_code=201)
async def register(user_in: UserCreate, session: AsyncSession = Depends(get_db)) -> User:
    return await UserService(session).register(user_in)


@router.post('/login', response_model=Token)
async def login(credentials: UserLogin, session: AsyncSession = Depends(get_db)) -> Token:
    user = await UserService(session).authenticate(credentials)
    return Token(access_token=create_access_token(user.id, user.email))


@router.post('/token', response_model=Token)
async def token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db),
) -> Token:
    credentials = UserLogin(email=form_data.username, password=form_data.password)
    user = await UserService(session).authenticate(credentials)
    return Token(access_token=create_access_token(user.id, user.email))


@router.get('/me', response_model=UserOut)
async def read_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
