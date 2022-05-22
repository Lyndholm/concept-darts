from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, validator

from ..config import config
from .user import UserOutPublic


class LocationImageIn(BaseModel):
    image: str
    name: str | None = None
    description: str | None = None

    class Config:
        orm_mode = True


class LocationImageOut(LocationImageIn):
    @validator('image')
    def format_image_url(cls, value) -> str:
        return config.STATIC_STORAGE_BASE_URL + value if config.STATIC_STORAGE_BASE_URL not in value else value


class BaseLocation(BaseModel):
    name: str
    description: str | None = None
    world_id: UUID

    class Config:
        orm_mode = True


class LocationIn(BaseLocation):
    images: list[LocationImageIn] = []


class LocationCreated(BaseLocation):
    id: UUID
    created_at: datetime


class LocationOut(LocationCreated):
    creator: UserOutPublic | None
    images: list[LocationImageOut]


class LocationUpdate(BaseModel):
    name: str | None
    description: str | None
    creator_id: UUID | None


class LocationOwnedByUser(BaseLocation):
    id: UUID
