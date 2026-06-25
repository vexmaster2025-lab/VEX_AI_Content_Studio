from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, constr


class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class TokenPayload(BaseModel):
    sub: int
    email: EmailStr


class UserBase(BaseModel):
    email: EmailStr
    full_name: constr(strip_whitespace=True, max_length=255) | None = None


class UserCreate(UserBase):
    password: constr(min_length=8)


class UserOut(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime

    class Config:
        orm_mode = True


class ContentStatus(str, Enum):
    draft = 'draft'
    published = 'published'


class ContentItemBase(BaseModel):
    title: constr(strip_whitespace=True, min_length=3, max_length=255)
    body: constr(strip_whitespace=True, min_length=10)
    status: ContentStatus = ContentStatus.draft


class ContentItemCreate(ContentItemBase):
    pass


class ContentItemOut(ContentItemBase):
    id: int
    owner_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class PaymentSession(BaseModel):
    checkout_url: str
