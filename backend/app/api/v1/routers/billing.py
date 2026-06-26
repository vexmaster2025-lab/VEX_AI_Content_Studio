from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.billing import BillingStatusOut, CheckoutRequest, CheckoutSessionOut, WebhookResponse
from app.services.billing_service import BillingService

router = APIRouter(prefix='/billing', tags=['Billing'])
webhook_router = APIRouter(prefix='/stripe', tags=['Stripe'])


@router.get('/status', response_model=BillingStatusOut)
async def billing_status(current_user: User = Depends(get_current_user)) -> BillingStatusOut:
    return BillingStatusOut(
        plan=current_user.plan,
        subscription_status=current_user.subscription_status,
        has_active_subscription=current_user.has_active_subscription,
        current_period_end=current_user.current_period_end,
    )


@router.post('/checkout', response_model=CheckoutSessionOut)
async def create_checkout(
    checkout: CheckoutRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CheckoutSessionOut:
    checkout_url = await BillingService(session).create_checkout_session(current_user, checkout.plan)
    return CheckoutSessionOut(checkout_url=checkout_url)


@webhook_router.post('/webhook', response_model=WebhookResponse)
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias='Stripe-Signature'),
    session: AsyncSession = Depends(get_db),
) -> WebhookResponse:
    result = await BillingService(session).handle_webhook(await request.body(), stripe_signature)
    return WebhookResponse(status=result)
