from datetime import datetime
from typing import Any

import stripe
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.models.user import User
from app.repositories.billing_repository import BillingRepository
from app.schemas.billing import BillingPlan

settings = get_settings()

PLAN_PRICES = {
    BillingPlan.go: 1900,
    BillingPlan.pro: 4900,
    BillingPlan.business: 9900,
}


class BillingService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = BillingRepository(session)
        if settings.stripe_secret_key:
            stripe.api_key = settings.stripe_secret_key

    async def create_checkout_session(self, user: User, plan: BillingPlan) -> str:
        if plan == BillingPlan.free:
            raise AppException('Free plan does not require checkout', status_code=400)
        if not settings.stripe_secret_key:
            raise AppException('Stripe is not configured', status_code=503)

        amount = PLAN_PRICES[plan]
        success_url = f'{settings.backend_url}/api/v1/billing/success'
        cancel_url = f'{settings.backend_url}/api/v1/billing/cancel'

        def create_session():
            customer = stripe.Customer.create(
                email=user.email,
                metadata={'user_id': str(user.id), 'plan': plan.value},
            )
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                mode='subscription',
                customer=customer.id,
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {'name': f'VEX AI {plan.value.title()}'},
                            'unit_amount': amount,
                            'recurring': {'interval': 'month'},
                        },
                        'quantity': 1,
                    }
                ],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={'user_id': str(user.id), 'plan': plan.value},
                subscription_data={'metadata': {'user_id': str(user.id), 'plan': plan.value}},
            )
            return {'checkout_url': session.url, 'customer_id': customer.id}

        result = await run_in_threadpool(create_session)
        user.stripe_customer_id = result['customer_id']
        await self.repository.users.save(user)
        return result['checkout_url']

    async def handle_webhook(self, payload: bytes, signature: str | None) -> str:
        if not settings.stripe_webhook_secret:
            raise AppException('Stripe webhook secret is not configured', status_code=503)
        if not signature:
            raise AppException('Missing Stripe signature', status_code=400)

        try:
            event = await run_in_threadpool(
                stripe.Webhook.construct_event,
                payload,
                signature,
                settings.stripe_webhook_secret,
            )
        except ValueError as exc:
            raise AppException('Invalid Stripe webhook payload', status_code=400) from exc
        except stripe.SignatureVerificationError as exc:
            raise AppException('Invalid Stripe webhook signature', status_code=400) from exc

        inserted = await self.repository.mark_event_processed(event['id'])
        if not inserted:
            return 'duplicate'

        event_type = event['type']
        data = event['data']['object']
        if event_type == 'checkout.session.completed':
            await self._apply_checkout_completed(data)
        elif event_type in {'customer.subscription.created', 'customer.subscription.updated'}:
            await self._apply_subscription_event(data)
        elif event_type == 'customer.subscription.deleted':
            await self._apply_subscription_event(data, deleted=True)
        elif event_type == 'invoice.payment_failed':
            await self._apply_invoice_event(data, status='past_due')
        elif event_type == 'invoice.paid':
            await self._apply_invoice_event(data, status='active')
        return 'processed'

    async def _apply_checkout_completed(self, data: dict[str, Any]) -> None:
        metadata = data.get('metadata') or {}
        user = await self.repository.find_user_for_event(_int_or_none(metadata.get('user_id')), data.get('customer'))
        if not user:
            return
        await self.repository.update_subscription(
            user,
            stripe_customer_id=data.get('customer'),
            stripe_subscription_id=data.get('subscription'),
            subscription_status='active',
            plan=metadata.get('plan') or user.plan,
        )

    async def _apply_subscription_event(self, data: dict[str, Any], deleted: bool = False) -> None:
        metadata = data.get('metadata') or {}
        user = await self.repository.find_user_for_event(_int_or_none(metadata.get('user_id')), data.get('customer'))
        if not user:
            return
        period_end = data.get('current_period_end')
        await self.repository.update_subscription(
            user,
            stripe_customer_id=data.get('customer'),
            stripe_subscription_id=data.get('id'),
            subscription_status='canceled' if deleted else data.get('status', 'inactive'),
            plan=metadata.get('plan') or user.plan,
            current_period_end=datetime.utcfromtimestamp(period_end) if period_end else None,
        )

    async def _apply_invoice_event(self, data: dict[str, Any], status: str) -> None:
        metadata = data.get('metadata') or {}
        user = await self.repository.find_user_for_event(_int_or_none(metadata.get('user_id')), data.get('customer'))
        if not user:
            return
        await self.repository.update_subscription(
            user,
            stripe_customer_id=data.get('customer'),
            stripe_subscription_id=data.get('subscription'),
            subscription_status=status,
            plan=metadata.get('plan') or user.plan,
        )


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
