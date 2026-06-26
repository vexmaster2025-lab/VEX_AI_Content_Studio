from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint

from app.models.base import Base


class StripeEvent(Base):
    __tablename__ = 'stripe_events'

    id = Column(Integer, primary_key=True, index=True)
    stripe_event_id = Column(String(255), unique=True, nullable=False, index=True)
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (UniqueConstraint('stripe_event_id', name='uq_stripe_event_id'),)
