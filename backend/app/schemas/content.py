from datetime import datetime
from enum import Enum
from pydantic import BaseModel, constr


class ContentStatus(str, Enum):
    draft = 'draft'
    published = 'published'


class ContentItemBase(BaseModel):
    title: constr(strip_whitespace=True, min_length=3, max_length=255)
    body: constr(strip_whitespace=True, min_length=10)
    status: ContentStatus = ContentStatus.draft


class ContentItemCreate(ContentItemBase):
    pass


class ContentItemUpdate(BaseModel):
    title: constr(strip_whitespace=True, min_length=3, max_length=255) | None = None
    body: constr(strip_whitespace=True, min_length=10) | None = None
    status: ContentStatus | None = None


class ContentItemOut(ContentItemBase):
    id: int
    owner_id: int
    created_at: datetime

    model_config = {
        'from_attributes': True,
    }
