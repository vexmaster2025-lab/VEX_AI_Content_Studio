from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_item import ContentItem
from app.schemas.content import ContentItemCreate, ContentItemUpdate


class ContentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_owner(self, owner_id: int) -> list[ContentItem]:
        result = await self.session.execute(
            select(ContentItem).where(ContentItem.owner_id == owner_id).order_by(ContentItem.created_at.desc())
        )
        return result.scalars().all()

    async def get_by_owner(self, owner_id: int, content_id: int) -> ContentItem | None:
        result = await self.session.execute(
            select(ContentItem).where(ContentItem.owner_id == owner_id, ContentItem.id == content_id)
        )
        return result.scalar_one_or_none()

    async def create(self, owner_id: int, content_in: ContentItemCreate) -> ContentItem:
        content = ContentItem(
            owner_id=owner_id,
            title=content_in.title,
            body=content_in.body,
            status=content_in.status.value,
        )
        self.session.add(content)
        await self.session.commit()
        await self.session.refresh(content)
        return content

    async def update(self, content: ContentItem, content_in: ContentItemUpdate) -> ContentItem:
        updates = content_in.model_dump(exclude_unset=True)
        for key, value in updates.items():
            setattr(content, key, value.value if key == 'status' and value is not None else value)
        self.session.add(content)
        await self.session.commit()
        await self.session.refresh(content)
        return content

    async def delete(self, content: ContentItem) -> None:
        await self.session.delete(content)
        await self.session.commit()
