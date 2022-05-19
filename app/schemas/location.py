from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from .user import UserOutPublic


class LocationImage(BaseModel):
    image: str
    name: str | None
    description: str | None

    class Config:
        orm_mode = True


class BaseLocation(BaseModel):
    name: str
    description: str | None = None
    world_id: UUID

    class Config:
        orm_mode = True


class LocationIn(BaseLocation):
    ...


class LocationCreated(BaseLocation):
    id: UUID
    created_at: datetime
    creator: UserOutPublic | None


class LocationOut(LocationCreated):
    images: list[LocationImage]


class LocationUpdate(BaseModel):
    name: str | None
    description: str | None
    creator_id: UUID | None


class LocationOwnedByUser(BaseLocation):
    id: UUID
