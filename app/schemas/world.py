from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from .user import UserOutPublic


class BaseWorld(BaseModel):
    name: str
    description: str | None = None
    cover_image: str | None = None
    map_image: str


class WorldIn(BaseWorld):
    ...


class WorldOut(BaseWorld):
    id: UUID
    created_at: datetime
    creator: UserOutPublic | None

    class Config:
        orm_mode = True


class WorldUpdate(BaseModel):
    name: str | None
    description: str | None
    cover_image: str | None
    map_image: str | None
    creator_id: int | None
