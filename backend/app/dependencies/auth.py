from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.database.session import get_db
from app.models.user import User
from app.schemas.user import TokenPayload
from app.security import decode_access_token
from app.services.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/v1/auth/token')


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = TokenPayload(**decode_access_token(token))
    except (ValueError, ValidationError) as exc:
        raise AppException('Invalid authentication credentials', status_code=401) from exc

    user = await UserService(session).get_user(payload.sub)
    if not user.is_active:
        raise AppException('User account is disabled', status_code=403)
    return user


async def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_superuser:
        raise AppException('Administrator privileges required', status_code=403)
    return current_user
