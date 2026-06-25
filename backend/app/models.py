from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    stripe_customer_id = Column(String(255), nullable=True, index=True)
    has_active_subscription = Column(Boolean, default=False, nullable=False)
    stripe_subscription_id = Column(String(255), nullable=True, index=True)
    subscription_status = Column(String(50), nullable=True, index=True)
    plan = Column(String(100), nullable=True)
    current_period_end = Column(DateTime, nullable=True)

    items = relationship('ContentItem', back_populates='owner')


class ContentItem(Base):
    __tablename__ = 'content_items'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String(50), default='draft', nullable=False)
    owner_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    owner = relationship('User', back_populates='items')


class StripeEvent(Base):
    __tablename__ = 'stripe_events'
    id = Column(Integer, primary_key=True, index=True)
    stripe_event_id = Column(String(255), unique=True, nullable=False, index=True)
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('stripe_event_id', name='uq_stripe_event_id'),
    )
