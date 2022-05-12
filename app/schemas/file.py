from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class BaseFile(BaseModel):
    filename: str


class FileOut(BaseFile):
    author_id: UUID
    uploaded_at: datetime

    class Config:
        orm_mode = True
