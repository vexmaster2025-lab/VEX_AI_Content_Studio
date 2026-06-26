from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stripe_event import StripeEvent
from app.models.user import User
from app.repositories.user_repository import UserRepository


class BillingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)

    async def mark_event_processed(self, stripe_event_id: str) -> bool:
        event = StripeEvent(stripe_event_id=stripe_event_id)
        self.session.add(event)
        try:
            await self.session.commit()
            return True
        except IntegrityError:
            await self.session.rollback()
            return False

    async def find_user_for_event(self, user_id: int | None, stripe_customer_id: str | None) -> User | None:
        if user_id is not None:
            user = await self.users.get_by_id(user_id)
            if user:
                return user
        if stripe_customer_id:
            return await self.users.get_by_stripe_customer_id(stripe_customer_id)
        return None

    async def update_subscription(
        self,
        user: User,
        *,
        stripe_customer_id: str | None = None,
        stripe_subscription_id: str | None = None,
        subscription_status: str = 'inactive',
        plan: str | None = None,
        current_period_end: datetime | None = None,
    ) -> User:
        if stripe_customer_id is not None:
            user.stripe_customer_id = stripe_customer_id
        if stripe_subscription_id is not None:
            user.stripe_subscription_id = stripe_subscription_id
        if plan is not None:
            user.plan = plan
        user.subscription_status = subscription_status
        user.current_period_end = current_period_end
        user.has_active_subscription = subscription_status in {'active', 'trialing', 'paid'}
        return await self.users.save(user)

    async def event_exists(self, stripe_event_id: str) -> bool:
        result = await self.session.execute(select(StripeEvent).where(StripeEvent.stripe_event_id == stripe_event_id))
        return result.scalar_one_or_none() is not None
