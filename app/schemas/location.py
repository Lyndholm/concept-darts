from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from .user import UserOutPublic


class BaseLocation(BaseModel):
    name: str
    description: str | None = None
    world_id: UUID


class LocationIn(BaseLocation):
    ...


class LocationOut(BaseLocation):
    id: UUID
    created_at: datetime
    creator: UserOutPublic | None

    class Config:
        orm_mode = True


class LocationUpdate(BaseModel):
    name: str | None
    description: str | None
    creator_id: UUID | None
