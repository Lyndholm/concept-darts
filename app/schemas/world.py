from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, validator

from app.config import config
from .location import LocationOut
from .user import UserOutPublic


class BaseWorld(BaseModel):
    name: str
    description: str | None = None
    map_image: str
    cover_image: str | None = None

    class Config:
        orm_mode = True


class WorldIn(BaseWorld):
    ...


class WorldCreated(BaseWorld):
    id: UUID
    created_at: datetime
    creator: UserOutPublic | None

    @validator('map_image', 'cover_image')
    def format_image_url(cls, value) -> str:
        if value is None:
            return value
        return config.STATIC_STORAGE_BASE_URL + value if config.STATIC_STORAGE_BASE_URL not in value else value


class WorldOut(WorldCreated):
    locations: list[LocationOut] | None


class WorldUpdate(BaseModel):
    name: str | None
    description: str | None
    map_image: str | None
    cover_image: str | None
    creator_id: UUID | None


class WorldOwnedByUser(BaseWorld):
    id: UUID

    @validator('map_image', 'cover_image')
    def format_image_url(cls, value) -> str:
        if value is None:
            return value
        return config.STATIC_STORAGE_BASE_URL + value if config.STATIC_STORAGE_BASE_URL not in value else value
