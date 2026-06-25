import stripe

from .config import get_settings

settings = get_settings()
stripe.api_key = settings.stripe_secret_key
from starlette.concurrency import run_in_threadpool


async def create_checkout_session(success_url: str, cancel_url: str, customer_email: str, user_id: int, plan: str = 'basic') -> dict:
    # Create or retrieve a Stripe customer in a threadpool to avoid blocking the event loop
    def _create_customer():
        return stripe.Customer.create(email=customer_email, metadata={'user_id': str(user_id), 'plan': plan})

    customer = await run_in_threadpool(_create_customer)

    def _create_session():
        return stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='payment',
            customer=customer.id,
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {'name': f'VEX AI {plan.title()}'},
                        'unit_amount': 1999,
                    },
                    'quantity': 1,
                }
            ],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={'user_id': str(user_id), 'plan': plan},
        )

    session = await run_in_threadpool(_create_session)
    return {'checkout_url': session.url, 'customer_id': customer.id}
