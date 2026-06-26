from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class BillingPlan(str, Enum):
    free = 'free'
    go = 'go'
    pro = 'pro'
    business = 'business'


class CheckoutRequest(BaseModel):
    plan: BillingPlan = BillingPlan.go


class CheckoutSessionOut(BaseModel):
    checkout_url: str


class BillingStatusOut(BaseModel):
    plan: str
    subscription_status: str
    has_active_subscription: bool
    current_period_end: datetime | None = None


class WebhookResponse(BaseModel):
    status: str
