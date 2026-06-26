from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.content import ContentItemCreate, ContentItemOut, ContentItemUpdate
from app.services.content_service import ContentService

router = APIRouter(prefix='/content', tags=['Content'])


@router.get('', response_model=list[ContentItemOut])
async def list_content(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list:
    return await ContentService(session).list_for_user(current_user.id)


@router.post('', response_model=ContentItemOut, status_code=status.HTTP_201_CREATED)
async def create_content(
    content_in: ContentItemCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ContentService(session).create_for_user(current_user.id, content_in)


@router.get('/{content_id}', response_model=ContentItemOut)
async def get_content(
    content_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ContentService(session).get_for_user(current_user.id, content_id)


@router.patch('/{content_id}', response_model=ContentItemOut)
async def update_content(
    content_id: int,
    content_in: ContentItemUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ContentService(session).update_for_user(current_user.id, content_id, content_in)


@router.delete('/{content_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(
    content_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    await ContentService(session).delete_for_user(current_user.id, content_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
