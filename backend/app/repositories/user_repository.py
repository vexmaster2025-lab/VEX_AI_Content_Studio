from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_stripe_customer_id(self, stripe_customer_id: str) -> User | None:
        result = await self.session.execute(select(User).where(User.stripe_customer_id == stripe_customer_id))
        return result.scalar_one_or_none()

    async def create(self, user_in: UserCreate, hashed_password: str) -> User:
        user = User(
            email=user_in.email,
            full_name=user_in.full_name,
            hashed_password=hashed_password,
        )
        self.session.add(user)
        try:
            await self.session.commit()
            await self.session.refresh(user)
        except IntegrityError:
            await self.session.rollback()
            raise
        return user

    async def save(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
