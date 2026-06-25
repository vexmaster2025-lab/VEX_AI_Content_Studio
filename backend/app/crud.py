from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from datetime import datetime

from . import models, schemas
from .security import hash_password


async def get_user_by_email(db: AsyncSession, email: str) -> models.User | None:
    result = await db.execute(select(models.User).where(models.User.email == email))
    return result.scalar_one_or_none()


async def get_user(db: AsyncSession, user_id: int) -> models.User | None:
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_in: schemas.UserCreate) -> models.User:
    user = models.User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
    )
    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Email already registered') from exc
    return user


async def set_user_subscription(db: AsyncSession, user_id: int, active: bool, stripe_customer_id: str | None = None) -> models.User | None:
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return None
    user.has_active_subscription = active
    if stripe_customer_id:
        user.stripe_customer_id = stripe_customer_id
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user_subscription(db: AsyncSession, user_id: int, *, active: bool | None = None, stripe_customer_id: str | None = None, stripe_subscription_id: str | None = None, subscription_status: str | None = None, plan: str | None = None, current_period_end: datetime | None = None) -> models.User | None:
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return None
    if active is not None:
        user.has_active_subscription = active
    if stripe_customer_id is not None:
        user.stripe_customer_id = stripe_customer_id
    if stripe_subscription_id is not None:
        user.stripe_subscription_id = stripe_subscription_id
    if subscription_status is not None:
        user.subscription_status = subscription_status
    if plan is not None:
        user.plan = plan
    if current_period_end is not None:
        user.current_period_end = current_period_end
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def is_stripe_event_processed(db: AsyncSession, stripe_event_id: str) -> bool:
    result = await db.execute(select(models.StripeEvent).where(models.StripeEvent.stripe_event_id == stripe_event_id))
    return result.scalar_one_or_none() is not None


async def mark_stripe_event_processed(db: AsyncSession, stripe_event_id: str) -> tuple[bool, models.StripeEvent]:
    ev = models.StripeEvent(stripe_event_id=stripe_event_id)
    db.add(ev)
    try:
        await db.commit()
        await db.refresh(ev)
        return True, ev
    except IntegrityError:
        await db.rollback()
        # Another worker may have processed it concurrently
        result = await db.execute(select(models.StripeEvent).where(models.StripeEvent.stripe_event_id == stripe_event_id))
        existing = result.scalar_one_or_none()
        return False, existing
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_content_item(db: AsyncSession, content_in: schemas.ContentItemCreate, owner_id: int) -> models.ContentItem:
    content = models.ContentItem(**content_in.model_dump(), owner_id=owner_id)
    db.add(content)
    await db.commit()
    await db.refresh(content)
    return content


async def list_content_items(db: AsyncSession, owner_id: int) -> list[models.ContentItem]:
    result = await db.execute(select(models.ContentItem).where(models.ContentItem.owner_id == owner_id).order_by(models.ContentItem.created_at.desc()))
    return result.scalars().all()
