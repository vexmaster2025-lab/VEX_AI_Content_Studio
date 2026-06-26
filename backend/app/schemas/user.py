from datetime import datetime
from pydantic import BaseModel, EmailStr, constr


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


class UserLogin(BaseModel):
    email: EmailStr
    password: constr(min_length=8)


class UserOut(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    plan: str
    subscription_status: str
    has_active_subscription: bool
    created_at: datetime

    model_config = {
        'from_attributes': True,
    }
