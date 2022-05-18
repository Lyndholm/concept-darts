from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app import schemas


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
    creator: schemas.UserOutPublic | None


class WorldOut(WorldCreated):
    locations: list[schemas.LocationOut] | None


class WorldUpdate(BaseModel):
    name: str | None
    description: str | None
    map_image: str | None
    cover_image: str | None
    creator_id: UUID | None
