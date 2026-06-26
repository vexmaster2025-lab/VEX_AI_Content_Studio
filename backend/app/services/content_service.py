from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.repositories.content_repository import ContentRepository
from app.schemas.content import ContentItemCreate, ContentItemUpdate


class ContentService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = ContentRepository(session)

    async def list_for_user(self, owner_id: int):
        return await self.repository.list_by_owner(owner_id=owner_id)

    async def create_for_user(self, owner_id: int, content_in: ContentItemCreate):
        return await self.repository.create(owner_id=owner_id, content_in=content_in)

    async def get_for_user(self, owner_id: int, content_id: int):
        content = await self.repository.get_by_owner(owner_id=owner_id, content_id=content_id)
        if not content:
            raise AppException('Content item not found', status_code=404)
        return content

    async def update_for_user(self, owner_id: int, content_id: int, content_in: ContentItemUpdate):
        content = await self.get_for_user(owner_id=owner_id, content_id=content_id)
        return await self.repository.update(content=content, content_in=content_in)

    async def delete_for_user(self, owner_id: int, content_id: int) -> None:
        content = await self.get_for_user(owner_id=owner_id, content_id=content_id)
        await self.repository.delete(content)
