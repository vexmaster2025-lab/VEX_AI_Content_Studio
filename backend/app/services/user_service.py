from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import AppException
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserLogin
from app.utils.security import hash_password, verify_password


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = UserRepository(session)

    async def register(self, user_in: UserCreate):
        existing = await self.repository.get_by_email(user_in.email)
        if existing:
            raise AppException('Email already registered', status_code=409)
        hashed = hash_password(user_in.password)
        try:
            return await self.repository.create(user_in=user_in, hashed_password=hashed)
        except IntegrityError as exc:
            raise AppException('Email already registered', status_code=409) from exc

    async def authenticate(self, credentials: UserLogin):
        user = await self.repository.get_by_email(credentials.email)
        if not user or not verify_password(credentials.password, user.hashed_password):
            raise AppException('Invalid email or password', status_code=401)
        if not user.is_active:
            raise AppException('User account is disabled', status_code=403)
        return user

    async def get_user(self, user_id: int):
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise AppException('User not found', status_code=404)
        return user
