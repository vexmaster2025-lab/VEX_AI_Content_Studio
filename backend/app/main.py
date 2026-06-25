from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi.security import OAuth2PasswordRequestForm
from starlette.concurrency import run_in_threadpool
import stripe
import logging
from datetime import datetime, timezone

from .config import get_settings
from .crud import create_content_item, create_user, get_user_by_email, list_content_items
from .database import get_db, engine, redis_client
from .dependencies import get_current_active_user
from .exceptions import conflict_error, validation_error
from .payments import create_checkout_session
from .schemas import (ContentItemCreate, ContentItemOut, PaymentSession, Token,
                      UserCreate, UserOut)
from .security import create_access_token, verify_password
from . import crud
from . import models

settings = get_settings()
app = FastAPI(title='VEX AI Content Studio MVP')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={'detail': exc.detail})


@app.post('/register', response_model=UserOut)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_email(db, user_in.email)
    if existing:
        raise conflict_error('Email already registered')
    return await create_user(db, user_in)


@app.post('/token', response_model=Token)
async def token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect username or password')
    return {'access_token': create_access_token(subject=user.id, email=user.email), 'token_type': 'bearer'}


@app.post('/login', response_model=Token)
async def login(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, user_in.email)
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect email or password')
    return {'access_token': create_access_token(subject=user.id, email=user.email), 'token_type': 'bearer'}


@app.get('/me', response_model=UserOut)
async def read_me(current_user=Depends(get_current_active_user)):
    return current_user


@app.post('/content', response_model=ContentItemOut)
async def create_content(content: ContentItemCreate, current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    return await create_content_item(db, content, current_user.id)


@app.get('/content', response_model=list[ContentItemOut])
async def get_content(current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    return await list_content_items(db, current_user.id)


@app.post('/pay', response_model=PaymentSession)
async def pay(plan: str = 'basic', current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    result = await create_checkout_session(
        success_url=f'{settings.backend_url}/success',
        cancel_url=f'{settings.backend_url}/cancel',
        customer_email=current_user.email,
        user_id=current_user.id,
        plan=plan,
    )

    # persist stripe customer id to user record (subscription not active until webhook confirms)
    customer_id = result.get('customer_id')
    if customer_id:
        await crud.set_user_subscription(db, current_user.id, False, stripe_customer_id=customer_id)

    return {'checkout_url': result.get('checkout_url')}


@app.post('/webhook')
async def webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    if not sig_header:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Missing signature header')

    try:
        def _construct_event():
            return stripe.Webhook.construct_event(payload=payload, sig_header=sig_header, secret=settings.stripe_webhook_secret)

        event = await run_in_threadpool(_construct_event)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid webhook payload or signature')
    evt_type = event.get('type')
    data = event.get('data', {}).get('object', {})

    event_id = event.get('id')

    # Idempotency: attempt to mark the event as processed; if already exists, skip processing
    try:
        created, _ = await crud.mark_stripe_event_processed(db, event_id)
        if not created:
            logging.info('Stripe event %s already processed', event_id)
            return {'status': 'already_processed'}
    except Exception:
        logging.exception('Failed to mark stripe event %s before processing', event_id)
        # continue processing cautiously

    try:
        # Only handle specified event types
        if evt_type == 'checkout.session.completed':
            session = data
            metadata = session.get('metadata', {}) or {}
            user = None
            if metadata.get('user_id'):
                try:
                    uid = int(metadata.get('user_id'))
                    user = await crud.get_user(db, uid)
                except Exception:
                    user = None
            if not user and session.get('customer'):
                res = await db.execute(__import__('sqlalchemy').select(models.User).where(models.User.stripe_customer_id == session.get('customer')))
                user = res.scalar_one_or_none()

            if user:
                subscription_id = session.get('subscription')
                plan = metadata.get('plan')
                await crud.update_user_subscription(db, user.id, active=True, stripe_customer_id=session.get('customer'), stripe_subscription_id=subscription_id, subscription_status='active', plan=plan)

        elif evt_type == 'invoice.paid':
            invoice = data
            customer_id = invoice.get('customer')
            subscription_id = invoice.get('subscription')
            plan = None
            # try to capture plan from invoice lines
            try:
                lines = invoice.get('lines', {}).get('data', [])
                if lines:
                    plan = lines[0].get('plan', {}).get('nickname') or lines[0].get('plan', {}).get('id')
            except Exception:
                plan = None

            # current period end
            period_end = None
            period_end_ts = invoice.get('current_period_end') or invoice.get('period_end')
            if isinstance(period_end_ts, (int, float)):
                period_end = datetime.fromtimestamp(period_end_ts, tz=timezone.utc)

            user = None
            if invoice.get('metadata', {}).get('user_id'):
                try:
                    uid = int(invoice.get('metadata', {}).get('user_id'))
                    user = await crud.get_user(db, uid)
                except Exception:
                    user = None
            if not user and customer_id:
                res = await db.execute(__import__('sqlalchemy').select(models.User).where(models.User.stripe_customer_id == customer_id))
                user = res.scalar_one_or_none()

            if user:
                await crud.update_user_subscription(db, user.id, active=True, stripe_customer_id=customer_id, stripe_subscription_id=subscription_id, subscription_status='active', plan=plan, current_period_end=period_end)

        elif evt_type == 'invoice.payment_failed':
            invoice = data
            customer_id = invoice.get('customer')
            subscription_id = invoice.get('subscription')
            user = None
            if invoice.get('metadata', {}).get('user_id'):
                try:
                    uid = int(invoice.get('metadata', {}).get('user_id'))
                    user = await crud.get_user(db, uid)
                except Exception:
                    user = None
            if not user and customer_id:
                res = await db.execute(__import__('sqlalchemy').select(models.User).where(models.User.stripe_customer_id == customer_id))
                user = res.scalar_one_or_none()
            if user:
                # mark as not active subscription (failed)
                await crud.update_user_subscription(db, user.id, active=False, stripe_customer_id=customer_id, stripe_subscription_id=subscription_id, subscription_status='past_due')

        else:
            logging.info('Unhandled stripe event type: %s', evt_type)

    except Exception:
        logging.exception('Error processing stripe event %s', event_id)
        # Don't crash webhook; return 200 so Stripe doesn't endlessly retry if we choose to swallow the error
        return {'status': 'error'}

    return {'status': 'processed'}



@app.on_event('startup')
async def on_startup():
    # nothing required at startup for now
    pass


@app.on_event('shutdown')
async def on_shutdown():
    try:
        await engine.dispose()
    except Exception:
        pass
    try:
        await redis_client.close()
        await redis_client.wait_closed()
    except Exception:
        pass
